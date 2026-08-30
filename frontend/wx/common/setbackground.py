import wx


class SetBackground:
    """Draws a scaled background image on a wx.Panel.

    Automatically rescales the image when the panel is resized.

    Args:
        panel: The panel to draw the background on.
        image: Path to the background image file.
    """

    def __init__(self, panel: wx.Panel, image):
        self.panel = panel
        self.bg_bitmap = wx.Bitmap(str(image))

        self.panel.Bind(wx.EVT_PAINT, self.on_paint)
        self.panel.Bind(wx.EVT_SIZE, self.on_resize)

    def on_paint(self, event):
        dc = wx.PaintDC(self.panel)
        dc.Clear()
        w, h = self.panel.GetClientSize()
        img = self.bg_bitmap.ConvertToImage().Scale(w, h, wx.IMAGE_QUALITY_HIGH)
        dc.DrawBitmap(wx.Bitmap(img), 0, 0)

    def on_resize(self, event):
        self.panel.Refresh()  # triggert opnieuw tekenen
        event.Skip()  # makes all other events to take place after this one
