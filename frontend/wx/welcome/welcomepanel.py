"""Welcome frame for PieceHunt.

Manages a check if an update is available.
Manages redirect to login / register and delete account
"""

import wx

from frontend.wx.common.setbackground import SetBackground
from settings import BG_IMAGES_DIR


class WelcomePanel(wx.Panel):
    def __init__(self, parent, mainframe):
        super().__init__(parent)

        self.mainframe = mainframe
        # Disable some menu items
        self.mainframe.menubar.logout_item.Enable(False)
        self.mainframe.menubar.disable_instr_menu()

        SetBackground(self, BG_IMAGES_DIR / "piecehunt_bg.png")

        sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(sizer)

        title = wx.StaticText(self, label="Welcome to PieceHunt")
        font = title.GetFont()
        font.PointSize += 8
        font = font.Bold()
        title.SetFont(font)

        login_btn = wx.Button(self, label="Login")
        register_btn = wx.Button(self, label="Register")

        login_btn.Bind(wx.EVT_BUTTON, self.on_login)
        register_btn.Bind(wx.EVT_BUTTON, self.on_register)

        sizer.Add(title, 0, wx.ALIGN_CENTER | wx.TOP, 30)
        sizer.Add(register_btn, 0, wx.ALIGN_CENTER)
        sizer.Add(login_btn, 0, wx.ALIGN_CENTER)

    def on_login(self, event):
        self.mainframe.show_login()

    def on_register(self, event):
        self.mainframe.show_register()
