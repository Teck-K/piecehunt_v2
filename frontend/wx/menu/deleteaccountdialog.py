import logging

import wx

from backend.handlers.user_handler import UserHandler

logger = logging.getLogger(__name__)


class DeleteAccountDialog(wx.Dialog):
    """Two-step dialog for permanent account deletion.

    Step 1: Verifies the user's credentials before proceeding.
    Step 2: Shows a final warning and confirms the deletion.
    """

    def __init__(self, mainframe):
        super().__init__(mainframe, title="Delete Account", size=(400, 320))
        self.mainframe = mainframe
        self.password = None
        self.panel = wx.Panel(self)
        self.main_sizer = wx.BoxSizer(wx.VERTICAL)
        self.panel.SetSizer(self.main_sizer)
        self.user_handler = UserHandler()
        self.show_step_1()
        self.Centre()

    def show_step_1(self):
        self.main_sizer.Clear(True)

        warning_label = wx.StaticText(self.panel, label="Warning:\nDeleting your account is permanent,\nand cannot be undone!")
        warning_label.SetForegroundColour(wx.Colour(180, 0, 0))
        self.main_sizer.Add(warning_label, 0, wx.ALL, 10)

        self.main_sizer.Add(wx.StaticText(self.panel, label=self.user_handler.auth_session.email), 0, wx.LEFT | wx.BOTTOM, 10)

        self.main_sizer.Add(wx.StaticText(self.panel, label="Please enter your password to continue."), 0, wx.LEFT | wx.BOTTOM, 10)

        self.main_sizer.Add(wx.StaticText(self.panel, label="Password:"), 0, wx.LEFT | wx.TOP, 10)
        self.password_input = wx.TextCtrl(self.panel, style=wx.TE_PASSWORD)
        self.main_sizer.Add(self.password_input, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 10)

        self.main_sizer.Add(0, 10, 0)

        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)

        cancel_btn = wx.Button(self.panel, label="Cancel")
        cancel_btn.Bind(wx.EVT_BUTTON, lambda e: self.EndModal(wx.ID_CANCEL))
        btn_sizer.Add(cancel_btn, 0, wx.RIGHT, 5)

        confirm_btn = wx.Button(self.panel, label="Continue")
        confirm_btn.Bind(wx.EVT_BUTTON, self.on_verify_credentials)
        btn_sizer.Add(confirm_btn, 0)

        self.main_sizer.Add(btn_sizer, 0, wx.ALIGN_RIGHT | wx.RIGHT | wx.BOTTOM, 10)

        self.main_sizer.Layout()
        self.panel.Layout()

    def on_verify_credentials(self, event):
        password = self.password_input.GetValue()

        if not password:
            wx.MessageBox("Please enter your password.", "Error", wx.OK | wx.ICON_WARNING)
            return

        email = self.user_handler.auth_session.email

        if self.user_handler.reauthenticate(email=email, password=password) is None:
            logger.warning("Failed delete attempt, incorrect password for email: %s", email)
            wx.MessageBox("Incorrect password", "Error", wx.OK | wx.ICON_WARNING)
            return

        self.password = password  # bewaren voor stap 2, want het invoerveld verdwijnt zo
        self.show_step_2()

    def show_step_2(self):
        self.main_sizer.Clear(True)

        self.main_sizer.Add(wx.StaticText(self.panel, label=f"Account: {self.user_handler.auth_session.email}"), 0, wx.ALL, 10)

        warning_label = wx.StaticText(
            self.panel, label=("You are about to permanently delete your account.\nAll your data will be removed and cannot be recovered.")
        )
        warning_label.SetForegroundColour(wx.Colour(180, 0, 0))
        self.main_sizer.Add(warning_label, 0, wx.LEFT | wx.BOTTOM, 10)

        self.main_sizer.Add(0, 10, 0)

        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)

        cancel_btn = wx.Button(self.panel, label="Cancel")
        cancel_btn.Bind(wx.EVT_BUTTON, lambda e: self.EndModal(wx.ID_CANCEL))
        btn_sizer.Add(cancel_btn, 0, wx.RIGHT, 5)

        delete_btn = wx.Button(self.panel, label="Delete Account")
        delete_btn.SetBackgroundColour(wx.Colour(180, 0, 0))
        delete_btn.SetForegroundColour(wx.Colour(255, 255, 255))
        delete_btn.Bind(wx.EVT_BUTTON, self.on_delete_account)
        btn_sizer.Add(delete_btn, 0)

        self.main_sizer.Add(btn_sizer, 0, wx.ALIGN_RIGHT | wx.RIGHT | wx.BOTTOM, 10)

        self.main_sizer.Layout()
        self.panel.Layout()
        self.SetSize((400, 320))

    def on_delete_account(self, event):
        email = self.user_handler.auth_session.email
        succes, msg = self.user_handler.delete_account(self.password)

        if succes:
            logger.info("Account deleted: %s", email)
            wx.MessageBox(msg, "Account Deleted", wx.OK | wx.ICON_INFORMATION)
        else:
            wx.MessageBox(msg, "Deletion Failed", wx.OK | wx.ICON_ERROR)

        self.EndModal(wx.ID_OK)
        self.mainframe.show_welcome()
