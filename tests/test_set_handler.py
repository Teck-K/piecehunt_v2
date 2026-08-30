"""Unit tests for SetHandler (v2.0.0 - API-based).

These tests validate the API-backed SetHandler behavior and local image helpers
without depending on the old SQLAlchemy database model.
"""

from unittest.mock import patch

import pytest

from backend.handlers.set_handler import SetHandler
from backend.handlers.user_handler import UserHandler
from backend.helper.singletonmeta import SingletonMeta
from services.api_client import ApiError


@pytest.fixture(autouse=True)
def reset_singletons():
    """Reset singleton state between tests."""
    SingletonMeta._instances.pop(SetHandler, None)
    SingletonMeta._instances.pop(UserHandler, None)
    yield
    SingletonMeta._instances.pop(SetHandler, None)
    SingletonMeta._instances.pop(UserHandler, None)


@pytest.fixture
def user_handler():
    handler = UserHandler()
    handler.set_auth_session(
        user_id="user-123",
        access_token="token-abc",
        refresh_token="refresh-xyz",
        email="user@example.com",
    )
    return handler


@pytest.fixture
def set_handler(user_handler):
    return SetHandler()


class TestSetExists:
    def test_requires_login(self, set_handler):
        """Should reject set existence checks when not logged in."""
        set_handler.user_handler.clear_auth_session()

        ok, msg = set_handler.set_exists("42154")

        assert ok is False
        assert msg == "Not logged in"

    @patch("backend.handlers.set_handler.call_with_refresh")
    def test_set_exists_success(self, mock_call_with_refresh, set_handler):
        """Should store the resolved set and return success."""
        mock_call_with_refresh.return_value = {
            "already_added": False,
            "set": {"set_num": "42154", "name": "Test Set"},
        }

        ok, msg = set_handler.set_exists("42154")

        assert ok is True
        assert msg == "Set added"
        assert set_handler.set_num == "42154"
        assert set_handler.normalized_set_num == "42154-1"

    @patch("backend.handlers.set_handler.call_with_refresh")
    def test_set_exists_when_already_added(self, mock_call_with_refresh, set_handler):
        """Should reject sets already attached to the user."""
        mock_call_with_refresh.return_value = {
            "already_added": True,
            "set": {"set_num": "42154", "name": "Test Set"},
        }

        ok, msg = set_handler.set_exists("42154")

        assert ok is False
        assert "already added" in msg.lower()


class TestAddSet:
    @patch("backend.handlers.set_handler.Thread")
    @patch("backend.handlers.set_handler.SetImageGetter")
    @patch("backend.handlers.set_handler.call_with_refresh")
    def test_add_set_success(self, mock_call_with_refresh, mock_set_image_getter, mock_thread, set_handler):
        """Should add a set and return success for the API-backed flow."""
        set_handler.set_num = "42154"
        set_handler.normalized_set_num = "42154-1"
        mock_call_with_refresh.return_value = {
            "parts": [],
            "minifigs": [],
            "set_img_url": "https://example.com/set.jpg",
        }
        mock_set_image_getter.return_value.get_image.return_value = (True, "saved")

        ok, msg = set_handler.add_set()

        assert ok is True
        assert msg == "Set and Image saved"
        mock_thread.assert_called_once()

    @patch("backend.handlers.set_handler.call_with_refresh")
    def test_add_set_api_error(self, mock_call_with_refresh, set_handler):
        """Should surface API errors from the server."""
        set_handler.set_num = "42154"
        set_handler.normalized_set_num = "42154-1"
        mock_call_with_refresh.side_effect = ApiError("Set not found", status_code=404)

        ok, msg = set_handler.add_set()

        assert ok is False
        assert "Set not found" in msg


class TestGetAllUserSets:
    @patch("backend.handlers.set_handler.call_with_refresh")
    def test_get_all_user_sets_adds_image_paths(self, mock_call_with_refresh, set_handler):
        """Should append image paths for each set returned by the API."""
        mock_call_with_refresh.return_value = [
            {"set_num": "42154", "user_set_id": 1, "set_name": "Test Set"},
            {"set_num": "75192", "user_set_id": 2, "set_name": "Another Set"},
        ]

        result = set_handler.get_all_user_sets(include_spares=True)

        assert len(result) == 2
        assert result[0]["img_path"].name == "42154.jpg"
        assert result[1]["img_path"].name == "75192.jpg"


class TestDownloadPartImages:
    def test_raises_connection_error_when_offline(self, set_handler):
        """Should fail fast when the internet connection is unavailable."""
        with patch("backend.handlers.set_handler.is_connected", return_value=False):
            with pytest.raises(ConnectionError, match="No Internet Connection"):
                set_handler.download_part_images([{"part_num": "3001", "color_id": 1, "img_url": "https://example.com/3001.jpg"}])

    def test_skips_existing_images(self, set_handler, tmp_path):
        """Should skip parts whose image already exists in the local cache."""
        part = {"part_num": "3001", "color_id": 1, "img_url": "https://example.com/3001.jpg"}
        existing_file = tmp_path / "3001_1.jpg"
        existing_file.write_bytes(b"existing")

        with (
            patch("backend.handlers.set_handler.is_connected", return_value=True),
            patch("backend.handlers.set_handler.PART_IMAGES_DIR", tmp_path),
            patch.object(set_handler, "download_single_image") as mock_download,
        ):
            set_handler.download_part_images([part])

        mock_download.assert_not_called()


class TestRescale:
    def test_invalid_image_type_logs_error(self, set_handler):
        """Should ignore unsupported image types."""
        with patch("backend.handlers.set_handler.resize_image") as mock_resize:
            set_handler.rescale(image_type="invalid", filename="test.jpg")

        mock_resize.assert_not_called()

    def test_no_filename_logs_warning(self, set_handler):
        """Should ignore empty filenames gracefully."""
        with patch("backend.handlers.set_handler.resize_image") as mock_resize:
            set_handler.rescale(image_type="set", filename=None)

        mock_resize.assert_not_called()
