import logging
import threading

import wx

from backend.handlers.set_handler import SetHandler
from frontend.wx.sets.addsetdialog import AddSetDialog

logger = logging.getLogger(__name__)


class SetsControlPanel(wx.Panel):
    def __init__(self, parent, mainframe):
        super().__init__(parent)
        self.mainframe = mainframe
        self.set_handler = SetHandler()
        self.parent = parent
        self.order_by = "set_num"
        self.order_ascending = True
        self.show_completed = False
        self.include_spares = False
        self.sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.SetSizer(self.sizer)

        self.add_set_btn = wx.Button(self, label="Add set")
        self.show_completed_chk = wx.CheckBox(self, label="Show completed")
        self.include_spares_chk = wx.CheckBox(self, label="Include Spares in progress")
        self.home_btn = wx.Button(self, label="Logout")
        self.order_by_btn = wx.Button(self, label="Order By")
        self.update_order_by_button("Name")

        order_by_menu = wx.Menu()
        order_by_menu.Append(wx.ID_ANY, "Name")
        order_by_menu.Append(wx.ID_ANY, "Number")
        order_by_menu.Append(wx.ID_ANY, "Progress")

        self.sizer.Add(self.add_set_btn, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        self.sizer.Add(self.order_by_btn, 0, wx.ALL, 5)
        self.sizer.Add(self.show_completed_chk, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        self.sizer.Add(self.include_spares_chk, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        self.sizer.AddStretchSpacer()  # duwt alles naar links
        self.sizer.Add(self.home_btn, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)

        self.add_set_btn.Bind(wx.EVT_BUTTON, self.on_add_set)
        self.show_completed_chk.Bind(wx.EVT_CHECKBOX, self.on_toggle_completed)
        self.include_spares_chk.Bind(wx.EVT_CHECKBOX, self.on_toggle_spares)
        self.home_btn.Bind(wx.EVT_BUTTON, self.on_home)
        self.order_by_btn.Bind(wx.EVT_BUTTON, lambda evt: self.PopupMenu(order_by_menu, self.order_by_btn.GetPosition()))
        for item in order_by_menu.GetMenuItems():
            self.Bind(wx.EVT_MENU, lambda evt, it=item: self.on_order_by(it.GetItemLabel()), item)

    def on_add_set(self, event):
        """Opens the add set dialog and handles the set addition workflow.

        Validates the set number, then adds the set in a background thread
        to keep the UI responsive. Shows a progress dialog during the process.
        """
        sets_dlg = AddSetDialog(self)

        while True:
            result = sets_dlg.ShowModal()
            if result != wx.ID_OK:
                sets_dlg.Destroy()
                return

            set_number = sets_dlg.get_set_number()
            if not set_number:
                sets_dlg.set_error("Please enter a set number")
                continue

            success, msg = self.set_handler.set_exists(set_number)

            if not success:
                sets_dlg.set_error(msg)
                continue

            sets_dlg.Destroy()
            break

        logger.debug("Set number validated: %s", set_number)

        progress_dialog = wx.ProgressDialog(
            "Adding New Images",
            "...",
            maximum=100,
            parent=self,
        )

        def progress(index, total, text):
            """Callback passed to the set handler to update the progress dialog."""
            if not progress_dialog:
                return
            percent = int((index / total) * 100)
            # following is a simple fix to avoid the progressdialog shutting down at the first 100%
            # while trying other styles, the whole app crashed after closing the dialog for no reason
            # could be written as oneliner: percent = min(int(index / total) * 100, 99)
            if percent == 100:
                percent = 99

            if text == "Part":
                wx.CallAfter(progress_dialog.Update, percent, f"{text}: {index}/{total}")
            else:
                wx.CallAfter(progress_dialog.Update, percent, f"{text}")

        self.set_handler.progress_callback = progress

        self.add_set_btn.Disable()  # avoids dubble clicking

        # Worker thread
        def worker():
            success, msg = self.set_handler.add_set()

            def finish():
                self.set_handler.progress_callback = None
                if progress_dialog:
                    progress_dialog.Destroy()

                self.add_set_btn.Enable()

                if success:
                    logger.info("Set added: %s", set_number)

                    self.mainframe.SetCursor(wx.Cursor(wx.CURSOR_WAIT))
                    self.mainframe.panel.Disable()
                    wx.SafeYield()
                    self.refresh_sets()
                    self.mainframe.panel.Enable()
                    self.mainframe.SetCursor(wx.NullCursor)

                else:
                    logger.error("Failed to add set %s: %s", set_number, msg)
                    wx.MessageBox(msg, "Error", wx.OK | wx.ICON_ERROR)

            wx.CallAfter(finish)

        threading.Thread(target=worker, daemon=True).start()

    def on_toggle_completed(self, event):
        self.show_completed = self.show_completed_chk.GetValue()
        self.refresh_sets()

    def on_toggle_spares(self, event):
        self.include_spares = self.include_spares_chk.GetValue()
        self.refresh_sets()

    def on_order_by(self, choice):

        if choice == "Name":
            new_order_by = "set_name"
        elif choice == "Number":
            new_order_by = "set_num"
        elif choice == "Progress":
            new_order_by = "progress_pct"

        if new_order_by == self.order_by:
            self.order_ascending = not self.order_ascending
        else:
            self.order_by = new_order_by
            self.order_ascending = False

        self.order_by = new_order_by

        self.update_order_by_button(choice)

        self.refresh_sets()

    def update_order_by_button(self, choice):
        arrow = "▲" if self.order_ascending else "▼"
        self.order_by_btn.SetLabel(f"Order By {choice} {arrow}")

    def on_home(self, event):
        self.mainframe.show_welcome()

    def refresh_sets(self):
        self.parent.refresh_sets(
            show_completed=self.show_completed, choice=self.order_by, ascending=self.order_ascending, include_spares=self.include_spares
        )
