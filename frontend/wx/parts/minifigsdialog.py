import wx

from frontend.wx.parts.minifigtile import MinifigTile
from settings import APP_IMAGES_DIR


class MinifigsDialog(wx.Dialog):
    """A scrollable dialog displaying all minifigures for a Lego set.

    Args:
        parent: The parent window.
        figs: A dict of minifigure data to display as tiles.
    """

    def __init__(self, parent, figs: dict):
        super().__init__(parent, title="Minifigures", size=(800, 400), style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)
        self.SetIcon(wx.Icon(str(APP_IMAGES_DIR / "piecehunt_logo.ico")))
        self.panel = wx.ScrolledWindow(self)
        self.panel.SetScrollRate(20, 20)

        self.main_sizer = wx.BoxSizer(wx.VERTICAL)
        self.panel_sizer = wx.WrapSizer(wx.HORIZONTAL)
        self.panel.SetSizer(self.panel_sizer)
        self.main_sizer.Add(self.panel, 1, wx.EXPAND | wx.ALL, 10)
        self.SetSizer(self.main_sizer)

        self.figs = figs
        self.draw_minifigs()

    def draw_minifigs(self):
        self.Freeze()
        self.panel_sizer.Clear(delete_windows=True)

        for fig in self.figs:
            tile = MinifigTile(self.panel, fig)
            self.panel_sizer.Add(tile, 0, wx.ALL, 10)
        self.panel_sizer.Layout()
        self.panel.SetVirtualSize(self.panel_sizer.GetMinSize())
        self.panel.FitInside()

        self.Thaw()
