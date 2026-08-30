import logging

import wx

from backend.handlers.user_handler import UserHandler
from frontend.wx.common.setbackground import SetBackground
from services.auth import register
from settings import BG_IMAGES_DIR

logger = logging.getLogger(__name__)


class RegisterPanel(wx.Panel):
    """Registration panel for creating a new user account.

    Includes GDPR consent checkbox and terms of use dialog.
    Navigates to the login panel on successful registration.
    """

    def __init__(self, parent, mainframe):
        super().__init__(parent)
        self.mainframe = mainframe
        self.user_handler = UserHandler()
        SetBackground(self, BG_IMAGES_DIR / "piecehunt_bg.png")

        sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(sizer)

        title = wx.StaticText(self, label="Create a New Account")
        font = title.GetFont()
        font.PointSize += 8
        font = font.Bold()
        title.SetFont(font)
        sizer.Add(title, 0, wx.ALIGN_CENTER | wx.TOP | wx.BOTTOM, 20)

        username_label = wx.StaticText(self, label="Username:")
        self.username_txt = wx.TextCtrl(self, style=wx.TE_PROCESS_ENTER, size=(200, -1))
        self.username_txt.Bind(wx.EVT_TEXT_ENTER, self.on_submit)
        sizer.Add(username_label, 0, wx.ALIGN_CENTER, 10)
        sizer.Add(self.username_txt, 0, wx.ALIGN_CENTER, 10)

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

        password_rpt_label = wx.StaticText(self, label="Repeat Password:")
        self.password_rpt_txt = wx.TextCtrl(self, style=wx.TE_PASSWORD | wx.TE_PROCESS_ENTER, size=(200, -1))
        self.password_rpt_txt.Bind(wx.EVT_TEXT_ENTER, self.on_submit)
        sizer.Add(password_rpt_label, 0, wx.ALIGN_CENTER, 10)
        sizer.Add(self.password_rpt_txt, 0, wx.ALIGN_CENTER, 10)

        sizer.AddStretchSpacer()

        self.gdpr_checkbox = wx.CheckBox(self, label="I agree to the ")
        sizer.Add(self.gdpr_checkbox, 0, wx.ALIGN_CENTER, 10)

        gdpr_link = wx.adv.HyperlinkCtrl(self, label="terms of use", url="")
        gdpr_link.Bind(wx.adv.EVT_HYPERLINK, self.on_show_gdpr)
        sizer.Add(gdpr_link, 0, wx.ALIGN_CENTER, 10)

        sizer.Add(0, 10, 0)

        submit_btn = wx.Button(self, label="Register")
        submit_btn.Bind(wx.EVT_BUTTON, self.on_submit)
        sizer.Add(submit_btn, 0, wx.ALIGN_CENTER | wx.BOTTOM, 20)

        cancel_btn = wx.Button(self, label="Home")
        cancel_btn.Bind(wx.EVT_BUTTON, self.on_cancel)
        cancel_btn.SetForegroundColour("red")
        sizer.Add(cancel_btn, 0, wx.ALIGN_CENTER | wx.BOTTOM, 20)

    def on_submit(self, event):
        username = self.username_txt.GetValue()
        email = self.email_txt.GetValue()
        password = self.password_txt.GetValue()
        password_rpt = self.password_rpt_txt.GetValue()

        if not username.strip() or not email.strip() or not password.strip() or not password_rpt.strip():
            wx.MessageBox("All fields are required.", "Error", wx.OK | wx.ICON_ERROR)
            return

        if password != password_rpt:
            wx.MessageBox("Passwords do not match.", "Error", wx.OK | wx.ICON_ERROR)
            return

        if not self.gdpr_checkbox.IsChecked():
            wx.MessageBox("You have to agree to the terms of use to continue", "Error", wx.OK | wx.ICON_ERROR)
            return

        result, message = self.user_handler.check_password_requirements(password)
        if not result:
            wx.MessageBox(message, "Error", wx.OK | wx.ICON_ERROR)
            return

        result, message = self.user_handler.check_email(email)
        if not result:
            wx.MessageBox(message, "Error", wx.OK | wx.ICON_ERROR)
            return

        result = register(email, password)
        if not result.success:
            logger.warning("Failed registration attempt for username: %s", username)
            wx.MessageBox(result.error, "Error", wx.OK | wx.ICON_ERROR)

        elif result.needs_email_confirmation:
            wx.MessageBox(
                "Registration succesfull, check your email for confirmation",
                "Almost done",
                wx.OK | wx.ICON_INFORMATION,
            )
            self.mainframe.show_login()

        else:
            UserHandler().set_auth_session(result.user_id, result.access_token, result.refresh_token, result.email)
            wx.MessageBox("Registration succesfull, you are logged in", "Welcome", wx.OK | wx.ICON_INFORMATION)
            self.mainframe.show_sets()

    def on_cancel(self, event):
        self.mainframe.show_welcome()

    def on_show_gdpr(self, event):
        dlg = wx.MessageDialog(
            self,
            "By registering, the following data is stored:\n\n"
            "• Your name and email address\n"
            "• Registration date and last login\n"
            "• Your progress within the application\n\n"
            "Feedback & error reporting:\n\n"
            "• Feedback you submit manually may be read by the developer\n"
            "• Errors and technical issues may be logged and sent to the developer automatically\n"
            "• These logs do not contain any personal data\n\n"
            "This data is not shared with third parties.\n"
            "You can request account deletion at any time.",
            "Terms of Use",
            wx.OK,
        )
        dlg.ShowModal()
        dlg.Destroy()
