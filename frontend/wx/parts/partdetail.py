import wx

from backend.handlers.part_handler import PartHandler


class PartDetailDialog(wx.Dialog):
    """A dialog showing the full details of a single Lego part.

    Displays the part name, number(s), color, spare status and image.

    Args:
        parent: The parent window.
        img_path: Path to the part image.
        name: The part name.
        color: The part color.
        numbers: A list of part numbers.
        spare: Whether this is a spare part.
    """

    def __init__(self, parent, img_path, name, color, numbers, spare):
        super().__init__(parent, title=name, size=(350, 450))

        self.parthandler = PartHandler()
        panel = wx.Panel(self)
        sizer = wx.BoxSizer(wx.VERTICAL)

        font_name = wx.Font(14, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
        font_info = wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)

        self.name_lbl = wx.StaticText(panel, label=name, style=wx.ALIGN_CENTER)
        self.name_lbl.SetFont(font_name)
        self.name_lbl.SetMaxSize((-1, 40))
        self.name_lbl.SetToolTip(name)
        sizer.Add(self.name_lbl, 0, wx.ALIGN_CENTER | wx.ALL, 10)

        num_txt_label = "Part Number:" if len(numbers) == 1 else "Part Numbers:"
        self.num_txt = wx.StaticText(panel, label=num_txt_label, style=wx.ALIGN_CENTER)
        self.num_txt.SetFont(font_info)
        sizer.Add(self.num_txt, 0, wx.ALIGN_CENTER | wx.ALL, 5)

        numbers_str = ", ".join(numbers)
        self.num_lbl = wx.StaticText(panel, label=numbers_str, style=wx.ALIGN_CENTER)
        self.num_lbl.SetFont(font_info)
        sizer.Add(self.num_lbl, 0, wx.ALIGN_CENTER | wx.ALL, 5)

        self.color_lbl = wx.StaticText(panel, label=color, style=wx.ALIGN_CENTER)
        self.color_lbl.SetFont(font_info)
        sizer.Add(self.color_lbl, 0, wx.ALIGN_CENTER | wx.ALL, 5)

        spare_txt = "Spare Part" if spare else ""
        self.spare_lbl = wx.StaticText(panel, label=spare_txt, style=wx.ALIGN_CENTER)
        self.spare_lbl.SetFont(font_info)
        sizer.Add(self.spare_lbl, 0, wx.ALIGN_CENTER | wx.ALL, 5)

        result, temp_image = self.parthandler.image_too_large_to_display(img_path=img_path, max_w=250, max_h=250)
        if result:
            img_path = temp_image

        bmp = wx.Bitmap(str(img_path), wx.BITMAP_TYPE_ANY)
        image = wx.StaticBitmap(panel, bitmap=bmp)
        sizer.Add(image, 1, wx.EXPAND | wx.ALL, 10)

        panel.SetSizer(sizer)
        panel.Layout()
