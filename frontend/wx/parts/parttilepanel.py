import logging
import threading

import wx

from backend.handlers.part_handler import PartHandler
from frontend.wx.common.int_validator import IntValidator
from frontend.wx.parts.partdetail import PartDetailDialog
from settings import NO_IMAGE_FOUND, PART_IMAGES_DIR, NO_IMAGE_FOUND_60x60

logger = logging.getLogger(__name__)

# How long to wait after the last click/action before actually writing to the
# database. Rapid clicks (e.g. mashing +) collapse into a single DB write.
DB_SAVE_DEBOUNCE_MS = 400


class PartTilePanel(wx.Panel):
    """Displays a single Lego part as a tile with quantity controls.

    Supports +/- buttons with a custom input field to track found parts.
    Spare parts are highlighted in red. Click the image to show full details.
    """

    def __init__(self, parent, part: dict):
        super().__init__(parent, size=(120, 120))

        self.mainframe = self.GetTopLevelParent()
        self.parent = parent
        self.part_handler = PartHandler()

        self.color_id = part["color_id"]
        self.is_spare = part["is_spare"]
        self.userpart_id = part["id"]
        self.part_img = part["img_path"]
        self.part_name = part["name"]
        self.part_found = part["found_num"]
        self.part_total = part["total_num"]
        self.color = part["color"]
        self.element_ids = part["element_ids"]  # list with all part+color combinations (different designs)
        self.part_num = part["part_num"]

        # debounce state for saving to the db, see update_and_schedule_save()
        self._save_timer = None
        self._pending_value = None

        # set in on_destroy(); guards against touching widgets from the
        # background save thread after this tile has already been destroyed
        self._destroyed = False

        self.SetMinSize((120, 120))

        self.default_bg = wx.Colour(245, 245, 245)
        self.hover_bg = wx.Colour(230, 230, 230)
        self.SetBackgroundColour(self.default_bg)

        if not self.part_img or not self.part_img.exists():
            logger.warning(
                "Missing part image for part: %s, color_id: %s, part_num: %s, element_id's: %s",
                self.part_name,
                self.color_id,
                self.part_num,
                self.element_ids,
            )

            self.part_img = NO_IMAGE_FOUND_60x60
            self.part_img_large = NO_IMAGE_FOUND
        else:
            self.part_img_large = PART_IMAGES_DIR / self.part_img.name

        main_sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(main_sizer)

        middle_sizer = wx.BoxSizer(wx.HORIZONTAL)
        btns_sizer = wx.BoxSizer(wx.VERTICAL)

        bmp = wx.Bitmap(str(self.part_img))
        self.image = wx.StaticBitmap(self, bitmap=bmp)
        self.name_lbl = wx.StaticText(self, label=self.part_name, style=wx.ST_ELLIPSIZE_END)
        self.name_lbl.SetMaxSize((110, -1))
        self.name_lbl.SetToolTip(self.part_name)  # laat de volledige naam zien bij hover
        self.plus_btn = wx.Button(self, label="+", size=(30, 30))
        self.minus_btn = wx.Button(self, label="-", size=(30, 30))
        self.input_field = wx.TextCtrl(self, value="1", size=(30, -1), validator=IntValidator())

        self.progress_lbl = wx.StaticText(self, label=f"{self.part_found}/{self.part_total}")
        if self.is_spare:
            self.name_lbl.SetForegroundColour("red")
            self.name_lbl.SetLabel(f"(S) {self.part_name}")
            self.progress_lbl.SetForegroundColour("red")
        font = self.name_lbl.GetFont()
        font.PointSize -= 1
        self.name_lbl.SetFont(font)
        self.progress_lbl.SetFont(font)

        main_sizer.Add(self.name_lbl, 0, wx.ALIGN_CENTER | wx.TOP, 5)
        btns_sizer.Add(self.plus_btn, 0)
        btns_sizer.Add(self.input_field, 0)
        btns_sizer.Add(self.minus_btn, 0)
        middle_sizer.Add(self.image, 0, wx.ALL | wx.ALIGN_CENTER, 8)
        middle_sizer.Add(btns_sizer, 0, wx.ALIGN_CENTER)
        main_sizer.Add(middle_sizer)
        main_sizer.AddStretchSpacer()
        main_sizer.Add(self.progress_lbl, 0, wx.ALIGN_CENTER)

        self.plus_btn.Bind(wx.EVT_BUTTON, self.on_plus)
        self.minus_btn.Bind(wx.EVT_BUTTON, self.on_minus)

        self.Bind(wx.EVT_ENTER_WINDOW, self.on_hover_tile)
        self.Bind(wx.EVT_LEAVE_WINDOW, self.on_leave_tile)
        for child in self.GetChildren():
            child.Bind(wx.EVT_ENTER_WINDOW, self.on_hover_tile)
            child.Bind(wx.EVT_LEAVE_WINDOW, self.on_leave_tile)

        self.Bind(wx.EVT_CONTEXT_MENU, self.on_context_menu)
        for child in self.GetChildren():
            child.Bind(wx.EVT_CONTEXT_MENU, self.on_context_menu)

        self.image.Bind(wx.EVT_LEFT_UP, self.show_large_image)
        self.SetWindowStyle(wx.BORDER_DOUBLE)

        # Stop any pending debounced save if the tile is destroyed (e.g. user
        # navigates away) before the timer fires, to avoid touching a dead widget.
        self.Bind(wx.EVT_WINDOW_DESTROY, self.on_destroy)

    def on_plus(self, event):
        self.add_sub_input(action="add")

    def on_minus(self, event):
        self.add_sub_input(action="sub")

    def add_sub_input(self, action):
        """Adds or subtracts the input field value from the current found count.

        Args:
            action: Either 'add' or 'sub'.
        """
        input_value = int(self.input_field.GetValue())
        if action == "sub":
            input_value *= -1
        new_value = self.part_found + input_value

        if (new_value) < 0 or (new_value) > self.part_total:
            wx.MessageBox("Invalid Input", "Error", wx.ICON_ERROR)
        else:
            self.update_and_schedule_save(new_value)

    def update_and_schedule_save(self, value):
        """Updates the UI immediately and debounces the actual database write.

        The label updates instantly regardless of database latency (optimistic
        update). The actual save is delayed by DB_SAVE_DEBOUNCE_MS and any
        previously scheduled save is cancelled first, so mashing +/- several
        times in a row results in a single database roundtrip carrying the
        final value, instead of one blocking roundtrip per click.

        Args:
            value: The new absolute found count.
        """
        self.part_found = value
        self.progress_lbl.SetLabel(f"{self.part_found}/{self.part_total}")
        self._pending_value = value

        if self._save_timer is not None and self._save_timer.IsRunning():
            self._save_timer.Stop()

        self._save_timer = wx.CallLater(DB_SAVE_DEBOUNCE_MS, self.commit_pending_value)

    def commit_pending_value(self):
        """Kicks off the database write on a background thread.

        Called by the debounce timer, not directly on every click. Runs off
        the UI thread so the app doesn't freeze during the HTTP roundtrip.
        """
        value = self._pending_value
        threading.Thread(target=self._save_to_db, args=(value,), daemon=True).start()

    def _save_to_db(self, value):
        """Runs on a background thread - must not touch any wx widgets directly."""
        succes, saved_value = self.part_handler.change_quantity(self.mainframe.current_set["id"], self.userpart_id, value)
        wx.CallAfter(self._on_save_result, succes, saved_value)

    def _on_save_result(self, succes, saved_value):
        """Runs back on the UI thread via wx.CallAfter - safe to touch widgets here."""
        if self._destroyed:
            return

        if succes:
            # resync with what the db actually has, in case something else changed it meanwhile
            self.part_found = saved_value
            self.progress_lbl.SetLabel(f"{self.part_found}/{self.part_total}")
        else:
            wx.MessageBox("Invalid Input", "Error", wx.ICON_ERROR)

    def on_destroy(self, event):
        self._destroyed = True
        if self._save_timer is not None and self._save_timer.IsRunning():
            self._save_timer.Stop()
        event.Skip()

    def on_hover_tile(self, event):
        self.SetCursor(wx.Cursor(wx.CURSOR_HAND))
        self.SetBackgroundColour(self.hover_bg)
        self.Refresh()
        event.Skip()

    def on_leave_tile(self, event):
        mouse_pos = wx.GetMousePosition()
        panel_rect = self.GetScreenRect()

        if not panel_rect.Contains(mouse_pos):
            self.SetCursor(wx.Cursor(wx.CURSOR_ARROW))
            self.SetBackgroundColour(self.default_bg)
            self.Refresh()

        event.Skip()

    def on_context_menu(self, event):
        menu = wx.Menu()

        complete_item = menu.Append(wx.ID_ANY, "Set as complete")
        menu.AppendSeparator()
        reset_item = menu.Append(wx.ID_ANY, "Reset to 0")

        self.Bind(wx.EVT_MENU, self.on_complete, complete_item)
        self.Bind(wx.EVT_MENU, self.on_reset, reset_item)

        pos = event.GetPosition()
        pos = self.ScreenToClient(pos)
        self.PopupMenu(menu, pos)
        menu.Destroy()

    def on_complete(self, event):
        self.update_and_schedule_save(self.part_total)

    def on_reset(self, event):
        self.update_and_schedule_save(0)

    def show_large_image(self, event):
        numbers = self.element_ids if self.element_ids else [self.part_num]
        dlg = PartDetailDialog(
            self, img_path=self.part_img_large, name=self.part_name, color=self.color, numbers=numbers, spare=self.is_spare
        )
        dlg.ShowModal()
        dlg.Destroy()

    @property
    def is_completed(self):
        return self.part_found >= self.part_total
