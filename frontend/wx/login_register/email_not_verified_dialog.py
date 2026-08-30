import logging

import wx

from services import api_client
from services.api_retry import call_with_refresh

logger = logging.getLogger(__name__)


class EmailNotVerifiedDialog(wx.Dialog):
    """Dialog shown when a user logs in without a verified email address.

    Explains that verification is required and allows the user to
    request a new verification email.
    """

    def __init__(self, parent, user_handler):
        super().__init__(parent, title="Email Not Verified", style=wx.DEFAULT_DIALOG_STYLE)
        self.user_handler = user_handler

        sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(sizer)

        message = wx.StaticText(
            self,
            label=(
                "Your email address has not been verified yet.\n\n"
                "Please check your inbox and click the verification link.\n"
                "You can request a new link if you did not receive one."
            ),
        )
        message.Wrap(340)
        sizer.Add(message, 0, wx.ALL, 20)

        resend_btn = wx.Button(self, label="Resend Verification Email")
        resend_btn.Bind(wx.EVT_BUTTON, self.on_resend)
        sizer.Add(resend_btn, 0, wx.ALIGN_CENTER | wx.BOTTOM, 10)

        close_btn = wx.Button(self, label="Continue")
        close_btn.Bind(wx.EVT_BUTTON, self.on_close)
        sizer.Add(close_btn, 0, wx.ALIGN_CENTER | wx.BOTTOM, 20)

        self.Fit()
        self.CentreOnParent()

    def on_resend(self, event):
        try:
            call_with_refresh(self.user_handler, api_client.request_email_verification)
            wx.MessageBox(
                "A new verification email has been sent. Please check your inbox.",
                "Email Sent",
                wx.OK | wx.ICON_INFORMATION,
            )
        except Exception:
            logger.exception("Failed to resend verification email")
            wx.MessageBox(
                "Could not send verification email. Please try again later.",
                "Error",
                wx.OK | wx.ICON_ERROR,
            )

    def on_close(self, event):
        self.EndModal(wx.ID_OK)
