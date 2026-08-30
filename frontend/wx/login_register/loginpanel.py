import logging

import wx

from backend.handlers.user_handler import UserHandler
from frontend.wx.common.setbackground import SetBackground
from frontend.wx.login_register.email_not_verified_dialog import EmailNotVerifiedDialog
from frontend.wx.login_register.resetpasswordpanel import ResetPasswordDialog
from services import api_client
from services.api_retry import call_with_refresh
from services.auth import login
from settings import BG_IMAGES_DIR

logger = logging.getLogger(__name__)


class LoginPanel(wx.Panel):
    """Login panel with email and password fields.

    Checks email verification status after login and shows a dialog
    if the user's email has not been verified yet.
    Provides a password reset link and navigates to the sets panel on success.
    """

    def __init__(self, parent, mainframe):
        super().__init__(parent)
        self.mainframe = mainframe
        self.user_handler = UserHandler()
        SetBackground(self, BG_IMAGES_DIR / "piecehunt_bg.png")

        sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(sizer)

        title = wx.StaticText(self, label="Login to your account")
        font = title.GetFont()
        font.PointSize += 8
        font = font.Bold()
        title.SetFont(font)
        sizer.Add(title, 0, wx.ALIGN_CENTER | wx.TOP | wx.BOTTOM, 20)

        email_label = wx.StaticText(self, label="Email:")
        self.email_txt = wx.TextCtrl(self, style=wx.TE_PROCESS_ENTER, size=(200, -1))
        self.email_txt.Bind(wx.EVT_TEXT_ENTER, self.on_submit)
        sizer.Add(email_label, 0, wx.ALIGN_CENTER, 10)
        sizer.Add(self.email_txt, 0, wx.ALIGN_CENTER, 10)

        password_label = wx.StaticText(self, label="Password:")
        self.password_txt = wx.TextCtrl(self, style=wx.TE_PASSWORD | wx.TE_PROCESS_ENTER, size=(200, -1))
        self.password_txt.Bind(wx.EVT_TEXT_ENTER, self.on_submit)
        sizer.Add(password_label, 0, wx.ALIGN_CENTER, 10)
        sizer.Add(self.password_txt, 0, wx.ALIGN_CENTER, 10)

        sizer.AddStretchSpacer()

        reset_link = wx.adv.HyperlinkCtrl(self, label="forgot password?", url="")
        reset_link.Bind(wx.adv.EVT_HYPERLINK, self.on_reset_password)
        sizer.Add(reset_link, 0, wx.ALIGN_CENTER, 10)

        sizer.Add(0, 10, 0)

        submit_btn = wx.Button(self, label="Login")
        submit_btn.Bind(wx.EVT_BUTTON, self.on_submit)
        sizer.Add(submit_btn, 0, wx.ALIGN_CENTER | wx.BOTTOM, 20)

        cancel_btn = wx.Button(self, label="Home")
        cancel_btn.Bind(wx.EVT_BUTTON, self.on_cancel)
        cancel_btn.SetForegroundColour("red")
        sizer.Add(cancel_btn, 0, wx.ALIGN_CENTER | wx.BOTTOM, 20)

    def on_submit(self, event):
        email = self.email_txt.GetValue()
        password = self.password_txt.GetValue()

        if not email.strip() or not password.strip():
            wx.MessageBox("Both fields are required.", "Error", wx.OK | wx.ICON_ERROR)
            return

        result = login(email, password)
        if not result.success:
            logger.warning("Failed login attempt for email: %s", email)
            wx.MessageBox(result.error, "Error", wx.OK | wx.ICON_ERROR)
            return

        logger.info("User logged in: %s", email)
        self.user_handler.set_auth_session(result.user_id, result.access_token, result.refresh_token, result.email)

        # Check verification status before navigating to sets.
        try:
            status = call_with_refresh(self.user_handler, api_client.get_email_verification_status)
            if not status.get("email_verified", True):
                dlg = EmailNotVerifiedDialog(self, self.user_handler)
                dlg.ShowModal()
        except Exception:
            logger.exception("Could not check email verification status for: %s", email)

        self.mainframe.show_sets()

    def on_cancel(self, event):
        self.mainframe.show_welcome()

    def on_reset_password(self, event):
        dlg = ResetPasswordDialog(self)
        dlg.ShowModal()
        dlg.Destroy()
