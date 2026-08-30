import logging

import wx

from settings import NO_IMAGE_FOUND_150x150

logger = logging.getLogger(__name__)


class MinifigTile(wx.Panel):
    """Displays a single minifigure as a tile with image, name, number and quantity.

    Args:
            parent: The parent window.
            fig: A dict containing name, quantity, number_of_parts, img_path and fig_num.
    """

    def __init__(self, parent, fig):
        super().__init__(parent)
        self.name = fig["name"]
        self.quantity = fig["quantity"]
        self.number_of_parts = fig["number_of_parts"]
        self.img_path = fig["img_path"]
        self.number = fig["fig_num"]

        self.default_img = str(NO_IMAGE_FOUND_150x150)

        if not self.img_path or not self.img_path.exists():
            logger.warning("Missing minifig image: %s, number: %s", self.name, self.number)
            self.img_path = self.default_img

        self.SetMinSize((180, 300))
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(main_sizer)

        font_name = wx.Font(8, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
        font_info = wx.Font(8, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)

        self.name_lbl = wx.StaticText(self, label=self.name, style=wx.ALIGN_CENTER)
        self.name_lbl.SetFont(font_name)
        self.name_lbl.SetMaxSize((-1, 40))
        self.name_lbl.SetToolTip(self.name)

        main_sizer.Add(self.name_lbl, 0, wx.ALIGN_CENTER | wx.ALL, 10)

        self.num_lbl = wx.StaticText(self, label=self.number, style=wx.ALIGN_CENTER)
        self.num_lbl.SetFont(font_info)
        main_sizer.Add(self.num_lbl, 0, wx.ALIGN_CENTER | wx.ALL, 5)

        self.quantity_lbl = wx.StaticText(self, label=f"quantity: {self.quantity}", style=wx.ALIGN_CENTER)
        self.quantity_lbl.SetFont(font_info)
        main_sizer.Add(self.quantity_lbl, 0, wx.ALIGN_CENTER | wx.ALL, 5)

        bmp = wx.Bitmap(str(self.img_path))

        image = wx.StaticBitmap(self, bitmap=bmp)
        main_sizer.Add(image, 1, wx.EXPAND | wx.ALL, 10)
        self.SetWindowStyle(wx.BORDER_DOUBLE)
        self.Layout()
