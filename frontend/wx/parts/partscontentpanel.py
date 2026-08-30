import logging

import wx

from backend.handlers.part_handler import PartHandler
from frontend.wx.parts.parttilepanel import PartTilePanel

logger = logging.getLogger(__name__)


class PartsContentPanel(wx.Panel):
    """Displays all parts of a Lego set as a responsive grid of tiles.

    Supports filtering by completion status, spare parts and color.
    """

    def __init__(self, parent, mainframe):
        super().__init__(parent)
        self.parent = parent
        self.mainframe = mainframe
        self.part_handler = PartHandler()
        self.show_completed = False
        self.show_spares = False
        self.color_ids = []
        self.sizer = wx.WrapSizer(wx.HORIZONTAL)
        self.SetSizer(self.sizer)
        self.tiles = []

        self.draw_parts()

    def draw_parts(self):
        logger.debug("Loading parts for set: %s", self.mainframe.current_set["set_num"])
        self.Freeze()
        self.tiles.clear()
        self.sizer.Clear(delete_windows=True)

        userset_parts = self.part_handler.get_all_userset_parts(self.mainframe.current_set["id"])
        for part in userset_parts:
            tile = PartTilePanel(self, part)
            self.add_part_tile(tile)
        self.Thaw()
        self.apply_filters()

    def change_filters(self, show_completed, show_spares, color_ids):
        """Updates the filter settings without refreshing the view.

        Call apply_filters() after this to update the visible tiles.

        Args:
            show_completed: Whether to show completed parts.
            show_spares: Whether to show spare parts.
            color_ids: List of color IDs to show.
        """
        self.show_completed = show_completed
        self.show_spares = show_spares
        self.color_ids = color_ids

    def apply_filters(self):
        """Shows or hides tiles based on the current filter settings."""
        self.Freeze()

        for tile in self.tiles:
            visible = True

            if not self.show_completed and tile.is_completed:
                visible = False

            if not self.show_spares and tile.is_spare:
                visible = False

            if tile.color_id not in self.color_ids:
                visible = False

            tile.Show(visible)

        self.Layout()
        self.mainframe.reset_scrollbar()
        self.Thaw()

    def add_part_tile(self, tile):
        self.tiles.append(tile)
        self.sizer.Add(tile, 0, wx.ALL, 10)
