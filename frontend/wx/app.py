"""Main application frame for PieceHunt.

Manages the main window, panel navigation, and session handling.
"""

import logging
import sys

import wx

from backend.handlers.instruction_handler import InstructionHandler
from backend.handlers.part_handler import PartHandler
from backend.handlers.set_handler import SetHandler
from backend.handlers.user_handler import UserHandler

# from database.models import Users
from frontend.wx.keygen import keygen
from frontend.wx.login_register.loginpanel import LoginPanel
from frontend.wx.login_register.registerpanel import RegisterPanel
from frontend.wx.menu.menubar import MainMenuBar
from frontend.wx.parts.allpartspanel import AllPartsPanel
from frontend.wx.sets.setspanel import SetsPanel
from frontend.wx.welcome.welcomepanel import WelcomePanel
from settings import APP_IMAGES_DIR, APP_VERSION

logger = logging.getLogger(__name__)
ID_HOTKEY = wx.NewIdRef()


class MainFrame(wx.Frame):
    def __init__(self, session):
        super().__init__(None, title=f"PieceHunt - {APP_VERSION}", size=(900, 600))

        self.SetIcon(wx.Icon(str(APP_IMAGES_DIR / "piecehunt_logo.ico")))

        self.panel = wx.ScrolledWindow(self)
        self.panel.SetScrollRate(20, 20)
        self.panel.SetDoubleBuffered(True)  # helps a lot to avoid flikkering between screens

        self.main_sizer = wx.BoxSizer(wx.VERTICAL)
        self.panel.SetSizer(self.main_sizer)
        self.current_user = None
        self.current_set = None
        self.session = session
        self.buzy_popup = None
        self.menubar = MainMenuBar(self)
        self.SetMenuBar(self.menubar)
        self.statusbar = self.CreateStatusBar()

        self.RegisterHotKey(ID_HOTKEY, wx.MOD_CONTROL | wx.MOD_SHIFT, ord("K"))
        self.Bind(wx.EVT_HOTKEY, self.on_secret, id=ID_HOTKEY)

        # initialising singletons and passing session
        UserHandler().session = self.session
        SetHandler().session = self.session
        PartHandler().session = self.session
        InstructionHandler().session = self.session

        self.Bind(wx.EVT_CLOSE, self.on_close)

        self.show_welcome()
        self.Show()

    def on_secret(self, event):
        keygen.show_keygen(self)

    def set_status_bar(self, text: str):
        self.statusbar.SetStatusText(text)

    # def set_current_user(self):
    #     user_id = UserHandler().user_id
    #     self.current_user = self.session.query(Users).filter_by(id=UUID(user_id)).one_or_none()

    def set_current_set(self, userset: object):
        self.current_set = userset

    def clear_panel(self):
        self.main_sizer.Clear(delete_windows=True)

    def change_panel(self, build_panel_func):
        """Switches to a new panel by calling the given builder function.

        Disables the UI and sets a wait cursor while the new panel is being
        built to prevent user interaction during the transition.

        Args:
        build_panel_func: A callable that returns the new panel to display.
        """
        self.SetCursor(wx.Cursor(wx.CURSOR_WAIT))
        self.panel.Disable()

        wx.CallAfter(self._build_panel, build_panel_func)

    def _build_panel(self, build_panel_func):
        """Builds and displays the new panel, then restores the UI state.

        Called via wx.CallAfter to ensure execution on the main thread.

        Args:
        build_panel_func: A callable that returns the new panel to display.
        """
        new_panel = build_panel_func()
        new_panel.Freeze()
        self.clear_panel()
        self.main_sizer.Add(new_panel, 1, wx.EXPAND)
        self.panel.Layout()
        self.panel.FitInside()
        new_panel.Thaw()
        self.panel.Enable()
        self.SetCursor(wx.Cursor(wx.CURSOR_ARROW))

    def show_welcome(self):
        self.current_user = None
        self.current_set = None
        self.menubar.missing_parts_item.Enable(False)
        self.menubar.logout_item.Enable(False)
        self.menubar.disable_account_menu()
        self.set_status_bar(text="Welcome To Piecehunt")
        self.change_panel(lambda: WelcomePanel(self.panel, self))

    def show_sets(self):
        self.current_set = None
        self.menubar.missing_parts_item.Enable(True)
        self.menubar.enable_account_menu()
        self.set_status_bar(text=f"Logged in as: {UserHandler().user_email}")
        self.change_panel(lambda: SetsPanel(self.panel, self))

    def show_parts(self):
        self.set_status_bar(text=(f"Logged in as: {UserHandler().user_email}, set: {self.current_set['set_num']}"))
        self.change_panel(lambda: AllPartsPanel(self.panel, self))

    def show_register(self):
        self.menubar.logout_item.Enable(True)
        self.set_status_bar(text="Please Register")
        self.change_panel(lambda: RegisterPanel(self.panel, self))

    def show_login(self):
        self.menubar.logout_item.Enable(True)
        self.set_status_bar(text="Please Login")
        self.change_panel(lambda: LoginPanel(self.panel, self))

    def on_close(self, event):
        self.UnregisterHotKey(ID_HOTKEY)
        self.Destroy()

    def reset_scrollbar(self):
        self.panel.Layout()
        self.panel.FitInside()


def run_app():
    app = wx.App(False)

    def handle_exception(exc_type, exc_value, exc_traceback):
        logger.critical("Unexpected crash", exc_info=(exc_type, exc_value, exc_traceback))

    sys.excepthook = handle_exception

    wx.InitAllImageHandlers()
    # should solve the probleme that from time to time wx doesnt recognise an image
    # ensure_db()
    # session = create_db_session()
    session = None

    frame = MainFrame(session)

    frame.Show()
    app.MainLoop()


if __name__ == "__main__":
    run_app()
