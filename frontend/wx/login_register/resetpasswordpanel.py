import logging

import wx

from services import api_client

logger = logging.getLogger(__name__)


class ResetPasswordDialog(wx.Dialog):
    """Dialog for requesting a password reset link via email.

    The user enters their email address. The API sends a reset link
    to that address if an account exists. The actual password change
    happens in the browser via the link.
    """

    def __init__(self, parent):
        super().__init__(parent, title="Reset Password", style=wx.DEFAULT_DIALOG_STYLE)

        sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(sizer)

        sizer.Add(
            wx.StaticText(self, label="Enter your email address and we'll send\nyou a link to reset your password."),
            0,
            wx.ALL,
            20,
        )

        sizer.Add(wx.StaticText(self, label="Email:"), 0, wx.LEFT, 20)
        self.email_input = wx.TextCtrl(self, size=(260, -1))
        sizer.Add(self.email_input, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 20)

        send_btn = wx.Button(self, label="Send Reset Link")
        send_btn.Bind(wx.EVT_BUTTON, self.on_send)
        sizer.Add(send_btn, 0, wx.ALIGN_CENTER | wx.BOTTOM, 10)

        cancel_btn = wx.Button(self, label="Cancel")
        cancel_btn.Bind(wx.EVT_BUTTON, self.on_cancel)
        sizer.Add(cancel_btn, 0, wx.ALIGN_CENTER | wx.BOTTOM, 20)

        self.Fit()
        self.CentreOnParent()

    def on_send(self, event):
        email = self.email_input.GetValue().strip()
        if not email:
            wx.MessageBox("Please enter your email address.", "Error", wx.OK | wx.ICON_WARNING)
            return

        try:
            api_client.request_password_reset(email)
        except Exception:
            logger.exception("Failed to request password reset for: %s", email)
            wx.MessageBox(
                "Could not send reset email. Please try again later.",
                "Error",
                wx.OK | wx.ICON_ERROR,
            )
            return

        wx.MessageBox(
            "If an account exists for this email address, a reset link has been sent.\n\n"
            "Please check your inbox and click the link to reset your password.",
            "Email Sent",
            wx.OK | wx.ICON_INFORMATION,
        )
        self.EndModal(wx.ID_OK)

    def on_cancel(self, event):
        self.EndModal(wx.ID_CANCEL)
