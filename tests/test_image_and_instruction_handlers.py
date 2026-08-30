"""Unit tests for InstructionHandler and BricklinkPartImageGetter.

Tests the logic that can be verified in isolation without a real network
connection, YOLO model, PDF files or live database session.

These tests were written with the assistance of Claude (Anthropic) as part of
the PieceHunt project, and reviewed and approved by the project author.

Test coverage:
    InstructionHandler:
        - set_current_set: path initialisation and set number normalisation
        - existing_instructions: returns files when present, None when absent
        - set_callback: calls wx.CallAfter on the main thread when callback is set
        - set_callback: does nothing when no callback is registered

    BricklinkPartImageGetter:
        - get_url: returns correct BrickLink URL using color mapping
        - get_url: returns digits-only URL when alternative=True
        - get_url: returns None when color ID is not in the mapping
        - get_destination_path: returns correct path using Rebrickable filename

    ImageGetter.get_image (via PartImageGetter):
        - returns early when the image already exists on disk
        - returns False when no URL is provided

Out of scope (integration / system tests):
    - InstructionGetter.get_from_site: requires live HTTP + HTML parsing
    - InstructionGetter.get_stickered_parts: requires YOLO + multiprocessing
    - ImageGetter network download: requires live HTTP
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from backend.handlers.instruction_handler import InstructionHandler
from backend.helper.singletonmeta import SingletonMeta

# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture(autouse=True)
def reset_singleton():
    """Reset the InstructionHandler singleton before and after every test."""
    SingletonMeta._instances.pop(InstructionHandler, None)
    yield
    SingletonMeta._instances.pop(InstructionHandler, None)


@pytest.fixture
def handler():
    """Return an InstructionHandler with a mocked session."""
    h = InstructionHandler()
    h.session = MagicMock()
    return h


# ── InstructionHandler – set_current_set ─────────────────────────────────────


class TestSetCurrentSet:
    """Tests for InstructionHandler.set_current_set().

    Verifies that paths and set numbers are correctly initialised
    when switching to a new active set.
    """

    def test_strips_suffix_from_set_num(self, handler):
        """Should remove the '-1' suffix to produce a clean set number."""
        with patch("backend.handlers.instruction_handler.InstructionGetter"):
            handler.set_current_set("42154-1")

        assert handler.simple_set_num == "42154"

    def test_sets_instructions_path(self, handler):
        """Should construct the instructions path from the clean set number."""
        with (
            patch("backend.handlers.instruction_handler.InstructionGetter"),
            patch("backend.handlers.instruction_handler.INSTR_DIR", Path("/fake/instructions")),
        ):
            handler.set_current_set("42154-1")

        assert handler.instructions_path == Path("/fake/instructions/42154")

    def test_creates_instruction_getter(self, handler):
        """Should instantiate an InstructionGetter with the clean set number."""
        with patch("backend.handlers.instruction_handler.InstructionGetter") as MockGetter:
            handler.set_current_set("75192-1")

        MockGetter.assert_called_once_with("75192")


# ── InstructionHandler – existing_instructions ────────────────────────────────


class TestExistingInstructions:
    """Tests for InstructionHandler.existing_instructions().

    Verifies that PDF detection returns the correct files or None.
    """

    def test_returns_files_when_pdfs_exist(self, handler, tmp_path):
        """Should return a list of PDF files when instructions are present."""
        pdf = tmp_path / "42154_1.pdf"
        pdf.write_bytes(b"fake pdf")
        handler.instructions_path = tmp_path

        result = handler.existing_instructions()

        assert result is not None
        assert len(result) == 1
        assert result[0].name == "42154_1.pdf"

    def test_returns_none_when_no_pdfs(self, handler, tmp_path):
        """Should return None when no PDF files are found in the instructions folder."""
        handler.instructions_path = tmp_path

        result = handler.existing_instructions()

        assert result is None


# ── InstructionHandler – set_callback ─────────────────────────────────────────


class TestSetCallback:
    """Tests for InstructionHandler.set_callback().

    Verifies that progress messages are correctly forwarded to the UI thread
    using wx.CallAfter, and that nothing breaks when no callback is set.
    """

    def test_calls_wx_call_after_when_callback_set(self, handler):
        """Should call wx.CallAfter with the callback and message when registered."""
        mock_callback = MagicMock()
        handler.progress_callback = mock_callback

        with patch("backend.handlers.instruction_handler.wx.CallAfter") as mock_call_after:
            handler.set_callback("Scanning page 1")

        mock_call_after.assert_called_once_with(mock_callback, "Scanning page 1")

    def test_does_nothing_when_no_callback(self, handler):
        """Should not raise or call wx.CallAfter when no callback is registered."""
        handler.progress_callback = None

        with patch("backend.handlers.instruction_handler.wx.CallAfter") as mock_call_after:
            handler.set_callback("Scanning page 1")

        mock_call_after.assert_not_called()


# ── BricklinkPartImageGetter ──────────────────────────────────────────────────


class TestBricklinkPartImageGetter:
    """Tests for BricklinkPartImageGetter.get_url() and get_destination_path().

    Verifies URL construction using the color mapping and the alternative
    digits-only fallback for part numbers with non-numeric characters.

    BricklinkPartImageGetter loads color_mapping as a class attribute at import
    time, so patch.object cannot override it after the class is defined. Instead
    we directly mutate the class attribute inside a pytest fixture and restore
    the original mapping after each test.
    """

    FAKE_COLOR_MAPPING = {
        "1": {"ext_ids": [11]},  # Rebrickable color 1 → BrickLink color 11
        "2": {"ext_ids": [None]},  # Rebrickable color 2 → no BrickLink mapping
    }

    @pytest.fixture(autouse=True)
    def patch_color_mapping(self):
        """Temporarily replace the class-level color mapping with a fake one.

        Saves the original mapping before each test and restores it afterwards
        so other tests are not affected.
        """
        from backend.handlers.image_getter import BricklinkPartImageGetter

        original = BricklinkPartImageGetter.color_mapping
        BricklinkPartImageGetter.color_mapping = self.FAKE_COLOR_MAPPING
        yield
        BricklinkPartImageGetter.color_mapping = original

    def _make_getter(self, rb_color_id, rb_part_num, alternative=False):
        """Instantiate BricklinkPartImageGetter with a patched PART_IMAGES_DIR."""
        from backend.handlers.image_getter import BricklinkPartImageGetter

        with patch("backend.handlers.image_getter.PART_IMAGES_DIR", Path("/fake/parts")):
            return BricklinkPartImageGetter(
                rb_url="https://cdn.rebrickable.com/fake.jpg",
                rb_color_id=rb_color_id,
                rb_part_num=rb_part_num,
                filename=f"{rb_part_num}_{rb_color_id}.jpg",
                alternative=alternative,
            )

    def test_returns_correct_bricklink_url(self):
        """Should construct a valid BrickLink image URL using the mapped color ID."""
        getter = self._make_getter(rb_color_id=1, rb_part_num="3001")

        assert getter.get_url() == "https://img.bricklink.com/ItemImage/PN/11/3001.png"

    def test_returns_digits_only_url_when_alternative(self):
        """Should strip non-numeric characters from the part number when alternative=True."""
        getter = self._make_getter(rb_color_id=1, rb_part_num="3001pr0001", alternative=True)

        assert getter.get_url() == "https://img.bricklink.com/ItemImage/PN/11/30010001.png"

    def test_returns_none_when_bricklink_color_is_none(self):
        """Should return None when the BrickLink color mapping has no valid color ID."""
        getter = self._make_getter(rb_color_id=2, rb_part_num="3001")

        assert getter.get_url() is None

    def test_returns_none_when_color_not_in_mapping(self):
        """Should return None when the Rebrickable color ID is absent from the mapping."""
        getter = self._make_getter(rb_color_id=999, rb_part_num="3001")

        assert getter.get_url() is None

    def test_destination_path_uses_rebrickable_filename(self):
        """Should save the image using the Rebrickable-based filename, not the BrickLink one.

        The filename stays consistent with the database which uses Rebrickable naming.
        """
        getter = self._make_getter(rb_color_id=1, rb_part_num="3001")

        assert getter.get_destination_path() == Path("/fake/parts/3001_1.jpg")


# ── ImageGetter.get_image (early exits) ──────────────────────────────────────


class TestImageGetterEarlyExits:
    """Tests for ImageGetter.get_image() early exit conditions.

    Verifies that no network request is made when the image already exists
    locally or when no URL is available.
    """

    def test_returns_true_when_image_already_exists(self, tmp_path):
        """Should return (True, ...) without downloading when the file already exists."""
        from backend.handlers.image_getter import PartImageGetter

        existing = tmp_path / "3001_1.jpg"
        existing.write_bytes(b"fake image")

        with (
            patch("backend.handlers.image_getter.PART_IMAGES_DIR", tmp_path),
            patch("backend.handlers.image_getter.SETS_IMAGES_DIR", tmp_path),
            patch("backend.handlers.image_getter.MINIFIGS_IMAGES_DIR", tmp_path),
        ):
            getter = PartImageGetter(rb_url="https://fake.url/img.jpg", filename="3001_1.jpg")

        success, msg = getter.get_image()

        assert success is True
        assert "already exists" in msg

    def test_returns_false_when_no_url(self, tmp_path):
        """Should return (False, ...) without making a request when URL is None."""
        from backend.handlers.image_getter import PartImageGetter

        with (
            patch("backend.handlers.image_getter.PART_IMAGES_DIR", tmp_path),
            patch("backend.handlers.image_getter.SETS_IMAGES_DIR", tmp_path),
            patch("backend.handlers.image_getter.MINIFIGS_IMAGES_DIR", tmp_path),
        ):
            getter = PartImageGetter(rb_url=None, filename="nonexistent.jpg")

        success, msg = getter.get_image()

        assert success is False
        assert "No valid url" in msg
