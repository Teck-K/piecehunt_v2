"""Sets frame for PieceHunt.

Manages the sets in sub frames.
SetsControlPanel manages the user inputs
SetsContentPanel manages the sets the user selected
"""

import wx

from frontend.wx.sets.setcontrolpanel import SetsControlPanel
from frontend.wx.sets.setscontentpanel import SetsContentPanel


class SetsPanel(wx.Panel):
    def __init__(self, parent, mainframe):
        super().__init__(parent)
        self.mainframe = mainframe

        sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(sizer=sizer)

        title = wx.StaticText(self, label="Sets Panel")
        font = title.GetFont()
        font.PointSize += 8
        font = font.Bold()
        title.SetFont(font)
        sizer.Add(title, 0, wx.ALIGN_CENTER | wx.BOTTOM, 20)

        self.set_ctrl_panel = SetsControlPanel(self, mainframe)
        sizer.Add(self.set_ctrl_panel, 0, wx.EXPAND)

        self.content_panel = SetsContentPanel(self, mainframe)
        sizer.Add(self.content_panel, 1, wx.EXPAND)

    def refresh_sets(self, show_completed, choice, ascending, include_spares):
        self.content_panel.refresh_sets(show_completed, choice, ascending, include_spares)
