import logging

import wx

from backend.handlers.user_handler import UserHandler
from services.api_client import ApiError
from services.api_retry import call_with_refresh
from services.feedback import report_feedback
from settings import APP_IMAGES_DIR

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"}

logger = logging.getLogger(__name__)


class ImageViewer(wx.Frame):
    """A frame for browsing and reviewing images with navigation controls.

    Supports keyboard navigation (left/right arrows) and allows reporting
    images as false positives to improve the YOLO model training data.
    """

    def __init__(self, parent, image_dir):
        super().__init__(parent, title="Piecehunt Image Viewer", size=(800, 600), style=wx.DEFAULT_FRAME_STYLE)
        self.SetIcon(wx.Icon(str(APP_IMAGES_DIR / "piecehunt_logo.ico")))
        self.image_dir = image_dir
        self.images = sorted([f.name for f in self.image_dir.iterdir() if f.suffix.lower() in IMAGE_EXTENSIONS])
        self.current_index = 0
        self.user_handler = UserHandler()

        self._build_ui()
        self.show_image()

    def _build_ui(self):
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        self.image_ctrl = wx.StaticBitmap(self)
        main_sizer.Add(self.image_ctrl, 1, wx.EXPAND | wx.ALL, 5)

        self.label = wx.StaticText(self, label="", style=wx.ALIGN_CENTER)
        main_sizer.Add(self.label, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 5)

        self.counter = wx.StaticText(self, label="", style=wx.ALIGN_CENTER)
        main_sizer.Add(self.counter, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 5)

        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.btn_prev = wx.Button(self, label="◀  Previous")
        self.btn_report = wx.Button(self, label="🚩 Report as False Positive")
        self.btn_next = wx.Button(self, label="Next  ▶")

        # self.btn_report.SetBackgroundColour(wx.Colour(220, 80, 80))
        # self.btn_report.SetForegroundColour(wx.WHITE)

        btn_sizer.Add(self.btn_prev, 1, wx.ALL, 5)
        btn_sizer.Add(self.btn_report, 1, wx.ALL, 5)
        btn_sizer.Add(self.btn_next, 1, wx.ALL, 5)

        main_sizer.Add(btn_sizer, 0, wx.EXPAND | wx.ALL, 5)
        self.SetSizer(main_sizer)

        self.btn_prev.Bind(wx.EVT_BUTTON, self.on_prev)
        self.btn_next.Bind(wx.EVT_BUTTON, self.on_next)
        self.btn_report.Bind(wx.EVT_BUTTON, self.on_report)
        self.Bind(wx.EVT_KEY_DOWN, self.on_key)
        self.Bind(wx.EVT_SIZE, self.on_resize)

    def on_resize(self, event):
        event.Skip()
        self.show_image()

    def show_image(self):
        if not self.images:
            self.label.SetLabel("No images found.")
            return

        filename = self.images[self.current_index]
        path = self.image_dir / filename

        # Load at full resolution first
        img = wx.Image(str(path), wx.BITMAP_TYPE_ANY)

        # Use the actual client size minus padding
        panel_w, panel_h = self.image_ctrl.GetClientSize()
        if panel_w < 10 or panel_h < 10:
            panel_w, panel_h = 780, 480

        img_w, img_h = img.GetWidth(), img.GetHeight()
        ratio = min(panel_w / img_w, panel_h / img_h)

        # Never upscale beyond original resolution
        ratio = min(ratio, 1.0)

        new_w = int(img_w * ratio)
        new_h = int(img_h * ratio)

        img = img.Scale(new_w, new_h, wx.IMAGE_QUALITY_BICUBIC)
        self.image_ctrl.SetBitmap(wx.Bitmap(img))

        self.label.SetLabel(str(filename))
        self.counter.SetLabel(f"{self.current_index + 1} / {len(self.images)}")
        self.btn_prev.Enable(self.current_index > 0)
        self.btn_next.Enable(self.current_index < len(self.images) - 1)
        self.Layout()

    def on_prev(self, event):
        if self.current_index > 0:
            self.current_index -= 1
            self.show_image()

    def on_next(self, event):
        if self.current_index < len(self.images) - 1:
            self.current_index += 1
            self.show_image()

    def on_key(self, event):
        key = event.GetKeyCode()
        if key == wx.WXK_LEFT:
            self.on_prev(None)
        elif key == wx.WXK_RIGHT:
            self.on_next(None)
        else:
            event.Skip()

    def on_report(self, event):
        filename = self.images[self.current_index]
        dlg = wx.MessageDialog(self, f"Report '{filename}' as false positive?", "Report As False Positive", wx.YES_NO | wx.ICON_WARNING)
        if dlg.ShowModal() == wx.ID_YES:
            self._handle_report(filename)
        dlg.Destroy()

    def _handle_report(self, filename):
        image_path = self.image_dir / filename
        try:
            call_with_refresh(
                self.user_handler,
                report_feedback,
                feedback_type="false_positive",
                description=f"False positive detected: {filename}",
                image_path=image_path,
            )
        except ApiError:
            pass
        wx.MessageBox(f"'{filename}' has been reported.", "Reported", wx.OK | wx.ICON_INFORMATION)
        logger.info("Reporting false positive: %s, exists: %s", image_path, image_path.exists())
        self.images = sorted([f.name for f in self.image_dir.iterdir() if f.suffix.lower() in IMAGE_EXTENSIONS])
