import logging
import webbrowser

import wx

from backend.handlers.part_handler import PartHandler
from backend.handlers.set_handler import SetHandler
from frontend.wx.common.hover_popup import HoverPopup
from settings import NO_IMAGE_FOUND_160x120

logger = logging.getLogger(__name__)


class SetTilePanel(wx.Panel):
    """Displays a single Lego set as a clickable tile with progress gauge.

    Shows the set image, name, number and completion progress.
    Supports left-click to open, right-click context menu for actions.
    """

    def __init__(self, parent, user_set_id, set_num, set_name, progress, image_path):
        super().__init__(parent, size=(180, 240))
        self.user_set_id = user_set_id
        self.parent = parent
        self.mainframe = self.TopLevelParent
        self.set_handler = SetHandler()
        self.part_handler = PartHandler()

        self.default_img = NO_IMAGE_FOUND_160x120
        self.SetMinSize((180, 240))
        self.popup = None
        self.progress = progress
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(main_sizer)
        self.default_bg = wx.Colour(245, 245, 245)
        self.hover_bg = wx.Colour(230, 230, 230)
        self.SetBackgroundColour(self.default_bg)
        self.set_name = set_name

        if not image_path or not image_path.exists():
            logger.error("Image not found for set %s, using default", set_num)
            image_path = self.default_img
        self.simple_set_num = set_num.replace("-1", "")
        bmp = wx.Bitmap(str(image_path))
        self.image = wx.StaticBitmap(self, bitmap=bmp)
        self.name_lbl = wx.StaticText(self, label=self.set_name, style=wx.ALIGN_CENTER_HORIZONTAL)
        self.num_lbl = wx.StaticText(self, label=self.simple_set_num)

        font = self.name_lbl.GetFont()
        font = font.Bold()
        font.PointSize += 1
        self.name_lbl.SetFont(font)
        self.num_lbl.SetFont(font)

        main_sizer.Add(self.name_lbl, 0, wx.ALIGN_CENTER | wx.TOP, 5)
        main_sizer.AddStretchSpacer()
        main_sizer.Add(self.image, 0, wx.ALL | wx.ALIGN_CENTER, 8)
        main_sizer.AddStretchSpacer()
        main_sizer.Add(self.num_lbl, 0, wx.ALIGN_CENTER | wx.BOTTOM, 5)

        self.gauge = wx.Gauge(self, range=100, size=(140, -1))
        self.gauge.SetValue(self.progress)
        self.gauge.Bind(wx.EVT_ENTER_WINDOW, self.on_hover_gauge)
        self.gauge.Bind(wx.EVT_LEAVE_WINDOW, self.on_leave_gauge)
        self.gauge.Bind(wx.EVT_MOTION, self.on_motion)

        main_sizer.Add(self.gauge, 0, wx.ALIGN_CENTER | wx.BOTTOM, 10)

        self.Bind(wx.EVT_ENTER_WINDOW, self.on_hover_tile)
        self.Bind(wx.EVT_LEAVE_WINDOW, self.on_leave_tile)
        for child in self.GetChildren():  # maakt dat ook de procent bar en de image mee werken
            child.Bind(wx.EVT_ENTER_WINDOW, self.on_hover_tile)
            child.Bind(wx.EVT_LEAVE_WINDOW, self.on_leave_tile)

        self.Bind(wx.EVT_CONTEXT_MENU, self.on_context_menu)  # rechtermuisknop
        for child in self.GetChildren():
            child.Bind(wx.EVT_CONTEXT_MENU, self.on_context_menu)

        self.Bind(wx.EVT_LEFT_UP, self.on_open_set)
        for child in self.GetChildren():
            child.Bind(wx.EVT_LEFT_UP, self.on_open_set)

        self.SetWindowStyle(wx.BORDER_DOUBLE)

    def on_hover_gauge(self, event):
        self.popup = HoverPopup(self)
        self.popup.show_text(f"{self.progress}%")
        self.popup.Show()
        event.Skip()

    def on_leave_gauge(self, event):
        if self.popup:
            self.popup.Destroy()
            self.popup = None
        event.Skip()

    def on_motion(self, event):
        if self.popup:
            pos = wx.GetMousePosition()  # schermcoördinaten
            self.popup.Position(pos, (15, 15))  # offset naast cursor
        event.Skip()

    def on_hover_tile(self, event):
        self.SetCursor(wx.Cursor(wx.CURSOR_HAND))
        self.SetBackgroundColour(self.hover_bg)
        self.Refresh()
        event.Skip()

    def on_leave_tile(self, event):
        """Resets the tile appearance only when the mouse truly leaves the panel.

        Checks actual screen coordinates to avoid flickering when moving
        between child widgets within the tile.
        """
        mouse_pos = wx.GetMousePosition()
        panel_rect = self.GetScreenRect()

        if not panel_rect.Contains(mouse_pos):
            self.SetCursor(wx.Cursor(wx.CURSOR_ARROW))
            self.SetBackgroundColour(self.default_bg)
            self.Refresh()

        event.Skip()

    def on_context_menu(self, event):
        menu = wx.Menu()

        open_item = menu.Append(wx.ID_OPEN, "Open set")
        menu.AppendSeparator()

        search_menu = wx.Menu()
        bricklink_item = search_menu.Append(wx.ID_ANY, "BrickLink")
        rebrickable_item = search_menu.Append(wx.ID_ANY, "Rebrickable")
        lego_item = search_menu.Append(wx.ID_ANY, "Lego.com")
        menu.AppendSubMenu(search_menu, "Search online")
        menu.AppendSeparator()

        reset_item = menu.Append(wx.ID_ANY, "Reset progress")
        complete_item = menu.Append(wx.ID_ANY, "Set as completed")
        menu.AppendSeparator()

        delete_item = menu.Append(wx.ID_DELETE, "Delete set…")

        self.Bind(wx.EVT_MENU, self.on_open_set, open_item)
        self.Bind(wx.EVT_MENU, self.on_search_bricklink, bricklink_item)
        self.Bind(wx.EVT_MENU, self.on_search_rebrickable, rebrickable_item)
        self.Bind(wx.EVT_MENU, self.on_search_lego, lego_item)
        self.Bind(wx.EVT_MENU, self.on_reset_set, reset_item)
        self.Bind(wx.EVT_MENU, self.on_complete_set, complete_item)
        self.Bind(wx.EVT_MENU, self.on_delete_set, delete_item)

        pos = event.GetPosition()
        pos = self.ScreenToClient(pos)
        self.PopupMenu(menu, pos)
        menu.Destroy()

    def on_open_set(self, event):
        succes, userset = self.set_handler.get_userset_object(self.user_set_id)
        if succes:
            self.mainframe.set_current_set(userset)
            self.mainframe.show_parts()
        else:
            logger.error("Failed to open set: %s", self.user_set_id)

    def on_search_bricklink(self, event):
        webbrowser.open(f"https://www.bricklink.com/v2/search.page?q={self.simple_set_num}")

    def on_search_rebrickable(self, event):
        webbrowser.open(f"https://rebrickable.com/sets/?q={self.simple_set_num}")

    def on_search_lego(self, event):
        webbrowser.open(f"https://www.lego.com/nl-be/search?q={self.simple_set_num}")

    def on_reset_set(self, event):
        msg = f"Are you sure you want to reset ALL progress on {self.set_name}"
        self.show_msg_box(msg, "reset_set")

    def on_complete_set(self, event):
        msg = f"Are you sure you want to set All progress on {self.set_name} as completed"
        self.show_msg_box(msg, "complete_set")

    def show_msg_box(self, msg, action):
        """Shows a yes/no confirmation dialog and executes the given action.

        Args:
            msg: The confirmation message to display.
            action: Either 'reset_set' or 'complete_set'.
        """
        dlg = wx.MessageDialog(self, msg, action, wx.YES_NO | wx.NO_DEFAULT | wx.ICON_WARNING)
        if dlg.ShowModal() == wx.ID_YES:
            logger.info("Action '%s' executed on set: %s", action, self.set_name)
            self.part_handler.set_all_parts(self.user_set_id, action)
            self.parent.refresh_sets(self.parent.show_completed, self.parent.order_by, self.parent.ascending, self.parent.include_spares)
        dlg.Destroy()

    def on_delete_set(self, event):
        dlg = wx.MessageDialog(
            self,
            f"Are you sure you want to delete {self.set_name}, {self.simple_set_num}",
            "Delete Set",
            wx.YES_NO | wx.NO_DEFAULT | wx.ICON_WARNING,
        )
        if dlg.ShowModal() == wx.ID_YES:
            succes, msg = self.set_handler.delete_set(self.user_set_id)
            if succes:
                logger.info("Set deleted: %s - %s", self.simple_set_num, self.set_name)
                parent_sizer = self.GetParent().GetSizer()
                parent_sizer.Detach(self)
                self.Destroy()
                wx.MessageBox(msg, "Success", wx.OK | wx.ICON_INFORMATION)

            else:
                logger.error("Failed to delete set %s: %s", self.simple_set_num, msg)
                wx.MessageBox(msg, "Error", wx.OK | wx.ICON_ERROR)

        dlg.Destroy()
