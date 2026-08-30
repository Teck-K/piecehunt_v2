import logging
import random
import threading
from functools import partial

import wx
import wx.adv

from backend.handlers.instruction_handler import InstructionHandler
from frontend.wx.menu.deleteaccountdialog import DeleteAccountDialog
from frontend.wx.menu.image_viewer import ImageViewer
from settings import APP_VERSION

logger = logging.getLogger(__name__)


class MainMenuBar(wx.MenuBar):
    """Main menu bar for PieceHunt.

    Handles database updates, backups, restores, instructions, missing parts
    and stickered parts for the current set.
    """

    def __init__(self, mainframe):
        super().__init__()

        self.mainframe = mainframe
        self.instruction_handler = InstructionHandler()

        self.progress_callback = None

        self.main_menu = wx.Menu()
        self.logout_item = self.main_menu.Append(wx.ID_ANY, "Logout")
        self.exit_item = self.main_menu.Append(wx.ID_EXIT, "Close Piecehunt")

        self.help_menu = wx.Menu()
        self.about_item = self.help_menu.Append(wx.ID_ANY, "About")
        self.credits_item = self.help_menu.Append(wx.ID_ANY, "Credits")

        self.instr_menu = wx.Menu()
        self.show_instr_menu = wx.Menu()
        self.get_instr_item = self.instr_menu.Append(wx.ID_ANY, "Get Instructions")
        self.instr_menu.AppendSubMenu(self.show_instr_menu, "Instructions")
        self.sticker_item = self.instr_menu.Append(wx.ID_ANY, "Show Stickered Pieces")

        self.reports_menu = wx.Menu()
        self.missing_parts_item = self.reports_menu.Append(wx.ID_ANY, "Missing Parts Report")

        self.account_menu = wx.Menu()
        self.edit_profile_item = self.account_menu.Append(wx.ID_ANY, "Edit Profile", "Edit your profile information")
        self.change_password_item = self.account_menu.Append(wx.ID_ANY, "Change Password", "Change your account password")
        self.account_menu.AppendSeparator()
        self.delete_account_item = self.account_menu.Append(wx.ID_ANY, "Delete Account...", "Permanently delete your account")

        self.Append(self.main_menu, "Main")
        self.Append(self.instr_menu, "Instructions")
        self.Append(self.reports_menu, "Reports")
        self.Append(self.help_menu, "Help")
        self.Append(self.account_menu, "&Account")

        self.Bind(wx.EVT_MENU, self.on_logout, self.logout_item)
        self.Bind(wx.EVT_MENU, self.on_exit, self.exit_item)
        self.Bind(wx.EVT_MENU, self.on_about, self.about_item)
        self.Bind(wx.EVT_MENU, self.on_credits, self.credits_item)
        self.Bind(wx.EVT_MENU, self.on_get_instr, self.get_instr_item)
        self.Bind(wx.EVT_MENU, self.on_sticker, self.sticker_item)
        self.Bind(wx.EVT_MENU, self.on_missing_parts_report, self.missing_parts_item)
        self.Bind(wx.EVT_MENU, self.on_delete_account, self.delete_account_item)

    def disable_instr_menu(self):
        """Disables the instructions menu during loading."""
        self.get_instr_item.Enable(False)
        self.sticker_item.Enable(False)
        index = self.FindMenu("Instructions")  # this way the index is not hard coded
        self.EnableTop(index, False)

    def enable_instr_menu(self):
        index = self.FindMenu("Instructions")
        self.EnableTop(index, True)

    def disable_account_menu(self):
        index = self.FindMenu("Account")
        self.EnableTop(index, False)

    def enable_account_menu(self):
        index = self.FindMenu("Account")
        self.EnableTop(index, True)

    def on_logout(self, event):
        self.mainframe.show_welcome()

    def on_exit(self, event):
        self.mainframe.on_close(event=None)

    def on_about(self, event):
        self.show_about()

    def on_credits(self, event):
        self.show_credits()

    def on_get_instr(self, event):
        logger.info("Instructions requested for set: %s", self.mainframe.current_set["set_num"])

        def progress(txt):
            wx.CallAfter(self.mainframe.set_status_bar, txt)

        self.disable_instr_menu()
        self.instruction_handler.progress_callback = progress
        self.mainframe.set_status_bar("Handling instructions, menu will become available when ready.")
        threading.Thread(target=self._load_instructions, daemon=True).start()

    def _load_instructions(self):
        self.instruction_handler.get_instructions()
        self.instruction_handler.get_stickered_parts()

        wx.CallAfter(self._on_instructions_loaded)

    def set_instr_menu(self):
        self.mainframe.menubar.enable_instr_menu()

        files = self.instruction_handler.existing_instructions()
        self.make_instr_items(files)

    def _on_instructions_loaded(self):
        self.instruction_handler.progress_callback = None
        self.set_instr_menu()

    def on_sticker(self, event):

        sticker_path = self.instruction_handler.get_sticker_path()
        first_png = next(sticker_path.glob("*.png"), None)
        if first_png:
            dlg = ImageViewer(self.mainframe, image_dir=sticker_path)
            dlg.Show()
        else:
            logger.debug("No stickered parts found for set: %s", self.mainframe.current_set["set_num"])
            self.mainframe.set_status_bar("No Stickered parts were found")

    def make_instr_items(self, files):
        """Populates the instructions submenu with the available PDF files.

        Args:
            files: A list of PDF file paths to add to the menu.
        """
        for item in self.show_instr_menu.MenuItems:
            self.show_instr_menu.Remove(item)
        if not files:
            self.show_instr_menu.Append(wx.ID_ANY, "No Instructions Available")
            self.get_instr_item.Enable(True)
            return

        for pdf_file in files:
            item = self.show_instr_menu.Append(wx.ID_ANY, pdf_file.name)
            self.Bind(wx.EVT_MENU, partial(self.open_pdf, file=pdf_file), item)  # partial to send the file avec
        self.sticker_item.Enable(True)
        self.get_instr_item.Enable(False)

    def open_pdf(self, event, file):
        try:
            wx.LaunchDefaultApplication(str(file))
        except Exception as e:
            logger.error("Failed to open PDF %s: %s", file, e, exc_info=True)

    def show_about(self):
        about = wx.adv.AboutDialogInfo()

        about.SetName("Piecehunt")
        about.SetVersion(APP_VERSION)
        about.SetDescription("Probably The Best Lego Sorting Aid In The World")
        about.SetCopyright("(C) 2026 Kenneth Teck")

        # info.AddDeveloper("Kenneth Teck")
        about.SetWebSite("mailto:piecehunt.app@gmail.com", "Email Support")

        # info.SetWebSite("https://mijnsite.be")

        wx.adv.AboutBox(about)

    def show_credits(self):
        teachers = ["Yves Vindevogel", "Luc Van De Putte", "Fabrice Devaux", "Karsten Naert"]
        random.shuffle(teachers)
        random_teacher_str = ""
        for teacher in teachers:
            random_teacher_str += f"   {teacher}\n"

        credits = wx.adv.AboutDialogInfo()

        credits.SetName("Piecehunt")
        credits.SetVersion(APP_VERSION)
        credits.SetDescription(
            "Special thanks to my python teachers in random order:\n"
            f"{random_teacher_str}\n"
            "Also, heartfelt thanks to my wife and son\n"
            "for giving me the time and support to make this possible."
        )

        wx.adv.AboutBox(credits)

    def on_missing_parts_report(self, event):
        """Opens the Missing Parts Report dialog.

        Lazily imports the dialog to avoid circular imports.
        """
        logger.debug("Opening Missing Parts Report dialog")
        from frontend.wx.menu.missing_parts_dialog import MissingPartsReportDialog

        dlg = MissingPartsReportDialog(self.mainframe)
        dlg.Show()

    def on_delete_account(self, event):
        dlg = DeleteAccountDialog(self.mainframe)
        dlg.ShowModal()
        dlg.Destroy()
