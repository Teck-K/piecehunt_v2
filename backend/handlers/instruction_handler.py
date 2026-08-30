import logging

import wx

from backend.handlers.instruction_getter import InstructionGetter
from backend.helper.singletonmeta import SingletonMeta
from settings import INSTR_DIR

logger = logging.getLogger(__name__)


class InstructionHandler(metaclass=SingletonMeta):
    """Manages building instructions for the current Lego set.

    Delegates downloading and sticker detection to InstructionGetter.
    Uses SingletonMeta to ensure only one handler instance exists.
    """

    def __init__(self):
        self.progress_callback = None
        self.current_set_num = ""
        self.simple_set_num = ""
        self.session = None
        self.instructions_path = None
        self.instruction_files = []

    def set_current_set(self, current_set_num):
        """Sets the active set and initialises the instruction paths.

        Args:
            current_set_num: The full set number including suffix (e.g. '42154-1').
        """
        logger.debug("Current set changed to: %s", self.simple_set_num)
        self.current_set_num = current_set_num
        self.simple_set_num = self.current_set_num.replace("-1", "")
        self.instructions_path = INSTR_DIR / self.simple_set_num
        self.instruction_getter = InstructionGetter(self.simple_set_num)

    def existing_instructions(self):
        self.instruction_files = list(self.instructions_path.glob("*.pdf"))
        if self.instruction_files:
            return self.instruction_files
        else:
            logger.debug("No existing instructions found for set: %s", self.simple_set_num)
            return None

    def get_instructions(self):
        logger.info("Instructions requested for set: %s", self.simple_set_num)
        txt = self.instruction_getter.get_from_site()
        self.set_callback(txt)

    def get_stickered_parts(self):
        """Scans instruction PDFs for stickered parts and reports progress via callback."""
        for txt in self.instruction_getter.get_stickered_parts():
            self.set_callback(txt)

    def set_callback(self, txt):
        """Sends a progress message to the callback on the main thread.

        Args:
            txt: The message to send.
        """
        if self.progress_callback:
            wx.CallAfter(self.progress_callback, txt)

    def get_sticker_path(self):
        return INSTR_DIR / str(self.simple_set_num) / "sticker"
