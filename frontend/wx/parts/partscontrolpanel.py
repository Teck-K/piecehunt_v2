import logging

import wx

from backend.handlers.part_handler import PartHandler
from frontend.wx.common.hex_to_rgb import hex_to_rgb
from frontend.wx.parts.minifigsdialog import MinifigsDialog

logger = logging.getLogger(__name__)


class PartsControlPanel(wx.Panel):
    """Control panel for filtering parts by completion, spares and color.

    Displays color toggle buttons generated dynamically from the parts in the set.
    Text color is automatically adjusted based on background brightness.
    """

    def __init__(self, parent, mainframe):
        super().__init__(parent)

        self.mainframe = mainframe
        self.parent = parent
        self.part_handler = PartHandler()

        self.current_userset = mainframe.current_set
        self.show_completed = False
        self.show_spares = False
        self.main_sizer = wx.BoxSizer(wx.VERTICAL)
        self.top_row = wx.BoxSizer(wx.HORIZONTAL)
        self.color_row = wx.WrapSizer(wx.HORIZONTAL)
        self.colors = self.part_handler.get_colors(self.current_userset["id"])
        self.color_buttons = {}
        self.selected_color_ids = []
        self.dlg = None
        self.add_color_btns()

        self.show_completed_chk = wx.CheckBox(self, label="Show completed")
        self.show_spares_chk = wx.CheckBox(self, label="Show spares")
        self.back_btn = wx.Button(self, label="Back to sets")
        self.select_all_btn = wx.Button(self, label="Select All")
        self.select_none_btn = wx.Button(self, label="Select None")
        self.show_minifigs_btn = wx.Button(self, label="Show Minifigs")

        self.top_row.Add(self.show_completed_chk, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        self.top_row.Add(self.show_spares_chk, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        self.top_row.Add(self.select_all_btn, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        self.top_row.Add(self.select_none_btn, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        self.top_row.Add(self.show_minifigs_btn, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        self.top_row.AddStretchSpacer()
        self.top_row.Add(self.back_btn, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)

        self.show_completed_chk.Bind(wx.EVT_CHECKBOX, self.on_toggle_completed)
        self.show_spares_chk.Bind(wx.EVT_CHECKBOX, self.on_toggle_spares)
        self.back_btn.Bind(wx.EVT_BUTTON, self.on_back)
        self.select_none_btn.Bind(wx.EVT_BUTTON, self.on_select_none)
        self.select_all_btn.Bind(wx.EVT_BUTTON, self.on_select_all)
        self.show_minifigs_btn.Bind(wx.EVT_BUTTON, self.on_show_minifigs)

        self.main_sizer.Add(self.top_row, 0, wx.EXPAND)
        self.main_sizer.Add(self.color_row, 0, wx.EXPAND)

        self.SetSizer(self.main_sizer)

    def add_color_btns(self):
        """Creates a toggle button for each color in the current set.

        Button text color is set to black or white based on background brightness
        using the luminance formula.
        """
        for color in self.colors:
            r, g, b = hex_to_rgb(color["rgb"])  # staat als hex in db
            btn = wx.ToggleButton(self, label=color["name"])
            btn.SetBackgroundColour(wx.Colour(r, g, b))
            brightness = (r * 299 + g * 587 + b * 114) / 1000
            if brightness < 128:
                btn.SetForegroundColour(wx.Colour(255, 255, 255))  # wit
            else:
                btn.SetForegroundColour(wx.Colour(0, 0, 0))  # zwart

            btn.Refresh()
            btn.Bind(wx.EVT_TOGGLEBUTTON, lambda evt, c=color: self.on_toggle_color(evt, c))
            self.color_row.Add(btn, 0, wx.ALL, 3)
            self.color_buttons[color["name"]] = btn

    def on_back(self, event):
        self.mainframe.menubar.disable_instr_menu()
        self.mainframe.show_sets()

    def on_toggle_completed(self, event):
        self.show_completed = self.show_completed_chk.GetValue()
        self.refresh_parent()

    def on_toggle_spares(self, event):
        self.show_spares = self.show_spares_chk.GetValue()
        self.refresh_parent()

    def on_toggle_color(self, event, color):
        btn = event.GetEventObject()
        try:
            if btn.GetValue():
                self.selected_color_ids.append(color["id"])
            else:
                self.selected_color_ids.remove(color["id"])

        except ValueError:
            logger.warning("Color id not found in selected list: %s", color.id)

        self.refresh_parent()

    def on_select_all(self, event):
        for btn in self.color_buttons.values():
            btn.SetValue(True)
        self.selected_color_ids = [c["id"] for c in self.colors]
        self.refresh_parent()

    def on_select_none(self, event):
        for btn in self.color_buttons.values():
            btn.SetValue(False)
        self.selected_color_ids.clear()
        self.refresh_parent()

    def on_show_minifigs(self, event):
        if not self.dlg:
            figs = self.part_handler.get_all_minifigs(self.current_userset["id"])
            self.dlg = MinifigsDialog(self, figs)
            self.dlg.ShowModal()
            self.dlg.Destroy()

    def refresh_parent(self):
        self.parent.refresh_parts(show_completed=self.show_completed, show_spares=self.show_spares, colors=self.selected_color_ids)
