import logging

import wx

from backend.handlers.instruction_handler import InstructionHandler
from frontend.wx.parts.partscontentpanel import PartsContentPanel
from frontend.wx.parts.partscontrolpanel import PartsControlPanel

logger = logging.getLogger(__name__)


class AllPartsPanel(wx.Panel):
    """Main panel for displaying and managing parts of a Lego set.

    Combines a control panel for filtering with a content panel
    that displays the actual parts.
    """

    def __init__(self, parent, mainframe):
        super().__init__(parent)
        self.mainframe = mainframe
        self.instruction_handler = InstructionHandler()
        self.current_set = mainframe.current_set
        self.mainframe.allpartspanel = self
        self.instruction_handler.set_current_set(self.current_set["set_num"])
        self.mainframe.menubar.set_instr_menu()

        logger.debug("Loading parts panel for set: %s", self.current_set["set_num"])

        sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(sizer=sizer)

        title = wx.StaticText(self, label=self.current_set["name"])
        font = title.GetFont()
        font.PointSize += 8
        font = font.Bold()
        title.SetFont(font)
        sizer.Add(title, 0, wx.ALIGN_CENTER | wx.BOTTOM, 20)

        self.parts_ctrl_panel = PartsControlPanel(self, self.mainframe)
        sizer.Add(self.parts_ctrl_panel, 0, wx.EXPAND)

        self.content_panel = PartsContentPanel(self, mainframe)
        sizer.Add(self.content_panel, 1, wx.EXPAND)

    def refresh_parts(self, show_completed, show_spares, colors):
        """Refreshes the parts view with the given filter settings.

        Args:
            show_completed: Whether to include completed parts.
            show_spares: Whether to include spare parts.
            colors: List of color filters to apply.
        """
        self.content_panel.change_filters(show_completed, show_spares, colors)
        self.content_panel.apply_filters()
