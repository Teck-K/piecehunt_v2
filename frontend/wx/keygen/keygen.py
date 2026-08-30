import math
import random
import string

import wx
import wx.adv

from settings import APP_IMAGES_DIR, PROJECT_ROOT

GREETZ = (
    "greetz to all piece hunters     "
    "who let the dogs out?   "
    "respect to open source devs     "
    "piecehunt crew salutes you     "
    "keep hunting the missing pieces     "
    "have you found yet? keep looking   "
    "the brick is out there    "
)

STATUS = [
    "decoding alien language...",
    "scrambling lego pieces...",
    "calculating brick count...",
    "generating piecehunt key...",
    "updating existing digits...",
    "erasing Epstein files...",
]


# ------------------------------
# MATRIX BACKGROUND
# ------------------------------


class MatrixPanel(wx.Panel):
    """A completely useless but aesthetically pleasing keygen window.

    Features a matrix background, animated title, spectrum visualizer,
    scrolling greetings, and chiptune music. Generates keys that do
    absolutely nothing.

    Inspired by the golden age of software cracks and demoscene culture.
    """

    def __init__(self, parent):
        super().__init__(parent)

        self.SetBackgroundColour("black")

        self.columns = 60
        self.drops = [random.randint(0, 40) for _ in range(self.columns)]

        self.timer = wx.Timer(self)

        self.Bind(wx.EVT_TIMER, self.update)
        self.Bind(wx.EVT_PAINT, self.paint)

        self.timer.Start(50)

    def update(self, event):

        for i in range(len(self.drops)):
            if random.random() > 0.97:
                self.drops[i] = 0
            else:
                self.drops[i] += 1

        self.Refresh()

    def paint(self, event):

        dc = wx.BufferedPaintDC(self)
        dc.Clear()

        dc.SetTextForeground("#003300")

        w, h = self.GetSize()

        char_height = 15
        char_width = max(10, w // self.columns)

        for i in range(self.columns):
            y = self.drops[i] * char_height
            char = random.choice(string.ascii_uppercase + string.digits)

            dc.DrawText(char, i * char_width, y % h)


# ------------------------------
# SPECTRUM
# ------------------------------


class Spectrum(wx.Panel):
    def __init__(self, parent):
        super().__init__(parent, size=(-1, 40))

        self.SetBackgroundColour("black")

        self.bars = [random.randint(5, 30) for _ in range(40)]

        self.timer = wx.Timer(self)

        self.Bind(wx.EVT_TIMER, self.update)
        self.Bind(wx.EVT_PAINT, self.paint)

        self.timer.Start(120)

    def update(self, event):

        self.bars = [random.randint(5, 30) for _ in range(40)]
        self.Refresh()

    def paint(self, event):

        dc = wx.BufferedPaintDC(self)
        dc.Clear()

        dc.SetBrush(wx.Brush("#00ff66"))
        dc.SetPen(wx.Pen("#00ff66"))

        w = self.GetSize().width
        bw = max(4, w // len(self.bars))

        for i, h in enumerate(self.bars):
            x = i * bw
            y = 40 - h

            dc.DrawRectangle(x, y, bw - 2, h)


# ------------------------------
# KEYGEN WINDOW
# ------------------------------


class KeyGenFrame(wx.Frame):
    def __init__(self, parent=None):

        super().__init__(parent, title="Piecehunt Key Generator", size=(640, 420))

        panel = MatrixPanel(self)

        main = wx.BoxSizer(wx.VERTICAL)
        self.SetIcon(wx.Icon(str(APP_IMAGES_DIR / "piecehunt_logo.ico")))

        # TITLE
        self.title = wx.StaticText(panel, label="PIECEHUNT KEYGEN")

        self.base_font_size = 26

        self.title_font = wx.Font(self.base_font_size, wx.FONTFAMILY_TELETYPE, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)

        self.title.SetFont(self.title_font)
        self.title.SetForegroundColour("#00ff66")

        main.Add(self.title, 0, wx.ALIGN_CENTER | wx.TOP, 20)

        # KEY
        self.key = wx.TextCtrl(panel, style=wx.TE_CENTER | wx.BORDER_NONE)

        keyfont = wx.Font(18, wx.FONTFAMILY_TELETYPE, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)

        self.key.SetFont(keyfont)
        self.key.SetBackgroundColour("black")
        self.key.SetForegroundColour("#00ff66")

        main.Add(self.key, 0, wx.EXPAND | wx.ALL, 20)

        # STATUS

        self.status = wx.StaticText(panel, label="status: ready", style=wx.ALIGN_CENTER_HORIZONTAL)

        self.status.SetForegroundColour("#00ff66")
        status_font = wx.Font(11, wx.FONTFAMILY_TELETYPE, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
        self.status.SetFont(status_font)

        main.Add(self.status, 0, wx.EXPAND | wx.BOTTOM, 10)

        # BUTTON
        btn = wx.Button(panel, label="GENERATE KEY")
        btn.Bind(wx.EVT_BUTTON, self.generate)

        main.Add(btn, 0, wx.ALIGN_CENTER | wx.BOTTOM, 15)

        # SPECTRUM
        self.spec = Spectrum(panel)
        main.Add(self.spec, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 20)

        # SCROLLER
        self.scroll = wx.StaticText(panel, label="", style=wx.ALIGN_CENTER)
        self.scroll.SetForegroundColour("#00ff66")

        scroll_font = wx.Font(10, wx.FONTFAMILY_TELETYPE, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)

        self.scroll.SetFont(scroll_font)

        main.Add(self.scroll, 0, wx.EXPAND | wx.ALL, 10)

        panel.SetSizer(main)

        # SCROLLER
        self.scroll_text = GREETZ
        self.scroll_pos = 0

        self.scroll_timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.update_scroll, self.scroll_timer)

        self.scroll_timer.Start(80)

        # LOGO WOBBLE
        self.wobble = 0

        self.wobble_timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.animate_logo, self.wobble_timer)

        self.wobble_timer.Start(80)

        # MUSIC

        music = str(PROJECT_ROOT / "frontend" / "wx" / "keygen" / "keygen_music.wav")
        self.sound = wx.adv.Sound(music)

        if self.sound.IsOk():
            self.sound.Play(wx.adv.SOUND_ASYNC | wx.adv.SOUND_LOOP)

        self.Bind(wx.EVT_CLOSE, self.on_close)

    # ----------------------

    def set_status(self, text):
        width = 70  # aantal tekens in “console line”
        self.status.SetLabel(text.center(width))

    def animate_logo(self, event):

        self.wobble += 1

        size = self.base_font_size + int(math.sin(self.wobble * 0.3) * 2)

        font = wx.Font(size, wx.FONTFAMILY_TELETYPE, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)

        self.title.SetFont(font)

    # ----------------------

    def generate(self, event):

        chars = string.ascii_uppercase + string.digits

        self.final_key = "-".join("".join(random.choice(chars) for _ in range(4)) for _ in range(4))

        self.set_status(random.choice(STATUS))

        self.scramble_frames = 0

        self.scramble_timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.scramble_step, self.scramble_timer)

        self.scramble_timer.Start(50)

    def scramble_step(self, event):

        chars = string.ascii_uppercase + string.digits

        key = "-".join("".join(random.choice(chars) for _ in range(4)) for _ in range(4))

        self.key.SetValue(key)

        self.scramble_frames += 1

        if self.scramble_frames > 25:
            self.scramble_timer.Stop()

            self.key.SetValue(self.final_key)

            self.set_status("status: key generated")

    # ----------------------

    def update_scroll(self, event):

        txt = self.scroll_text[self.scroll_pos :] + self.scroll_text[: self.scroll_pos]

        self.scroll.SetLabel(txt[:70])

        self.scroll_pos = (self.scroll_pos + 1) % len(self.scroll_text)

    # ----------------------

    def on_close(self, event):

        self.scroll_timer.Stop()
        self.wobble_timer.Stop()

        if self.sound.IsOk():
            self.sound.Stop()

        self.Destroy()


# ------------------------------
# PUBLIC FUNCTION
# ------------------------------


def show_keygen(parent=None):
    """Opens the keygen window. Serves no practical purpose whatsoever."""

    frame = KeyGenFrame(parent)
    frame.Show()
    frame.Centre()
