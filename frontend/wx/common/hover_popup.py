import wx
import wx.adv


class HoverPopup(wx.PopupWindow):
    """A popup window that appears near the cursor to show additional info.

    Supports displaying text, a scaled image, or an animated GIF.
    Position the popup manually using wx.PopupWindow.Position().
    """

    def __init__(self, parent):
        super().__init__(parent)

        self.panel = wx.Panel(self)

    def show_text(self, text):
        self.content = wx.StaticText(self.panel, label=text)
        self.make_panel()

    def show_image(self, image_path):
        """Loads and displays a scaled image, capped at 100x100 pixels.

        Args:
            image_path: Path to the image file.
        """
        img = wx.Image(image_path, wx.BITMAP_TYPE_ANY)
        w, h = img.GetSize()
        max_w, max_h = (100, 100)

        scale = min(max_w / w, max_h / h, 1)  # disable enlarging
        new_w = int(w * scale)
        new_h = int(h * scale)

        img = img.Scale(new_w, new_h, wx.IMAGE_QUALITY_HIGH)

        bmp = wx.Bitmap(img)
        self.content = wx.StaticBitmap(self.panel, bitmap=bmp)
        self.make_panel()

    def show_gif(self, gif_path):
        """Loads and plays an animated GIF.

        Args:
            gif_path: Path to the GIF file.
        """
        # anim = wx.adv.Animation(gif_path)
        self.content = wx.adv.AnimationCtrl(self.panel)
        self.content.LoadFile(str(gif_path))
        self.content.Play()
        self.make_panel()

    def make_panel(self):
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.content, 0, wx.ALL, 6)
        self.panel.SetSizerAndFit(sizer)
        self.Fit()
