import logging

import wx

from backend.handlers.set_handler import SetHandler
from frontend.wx.sets.settilepanel import SetTilePanel

logger = logging.getLogger(__name__)


class SetsContentPanel(wx.Panel):
    """Displays all user sets as a responsive grid of tiles.

    Uses a WrapSizer to automatically reflow tiles when the window is resized.
    """

    def __init__(self, parent, mainframe):
        super().__init__(parent)
        self.mainframe = mainframe
        self.show_completed = False
        self.ascending = False
        self.order_by = "set_num"
        self.include_spares = False

        self.set_handler = SetHandler()

        self.sizer = wx.WrapSizer(wx.HORIZONTAL)
        self.SetSizer(self.sizer)

        self.draw_sets()

    def draw_sets(self):
        self.sizer.Clear(delete_windows=True)
        self.user_sets = self.set_handler.get_all_user_sets(self.include_spares)
        logger.debug("Loaded %d sets", len(self.user_sets))

        self.user_sets.sort(key=lambda x: x[self.order_by], reverse=not self.ascending)
        for user_set in self.user_sets:
            if user_set["progress_pct"] == 100 and not self.show_completed:
                continue
            else:
                tile = SetTilePanel(
                    self,
                    user_set_id=user_set["user_set_id"],
                    set_num=user_set["set_num"],
                    set_name=user_set["set_name"],
                    progress=user_set["progress_pct"],
                    image_path=user_set["img_path"],
                )
                self.add_set_tile(tile)

    def refresh_sets(self, show_completed, choice, ascending, include_spares):
        """Refreshes the displayed sets with updated filter and sort settings."""
        self.show_completed = show_completed
        self.order_by = choice
        self.ascending = ascending
        self.include_spares = include_spares
        self.Freeze()
        self.draw_sets()
        self.Thaw()

    def clear(self):
        self.sizer.Clear(delete_windows=True)
        self.Layout()

    def add_set_tile(self, tile):
        self.sizer.Add(tile, 0, wx.ALL, 10)
        self.Layout()
