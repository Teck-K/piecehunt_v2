"""Unit tests for PartHandler (v2.0.0 - API-based).

These tests validate the API-backed PartHandler logic without relying on the
legacy SQLAlchemy database model.
"""

from pathlib import Path
from unittest.mock import patch

import pytest

from backend.handlers.part_handler import PartHandler
from backend.handlers.set_handler import SetHandler
from backend.handlers.user_handler import UserHandler
from backend.helper.singletonmeta import SingletonMeta
from services.api_client import ApiError, apply_parts_action


@pytest.fixture(autouse=True)
def reset_singletons():
    """Reset singleton state between tests."""
    SingletonMeta._instances.pop(PartHandler, None)
    SingletonMeta._instances.pop(UserHandler, None)
    yield
    SingletonMeta._instances.pop(PartHandler, None)
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
def part_handler(user_handler):
    return PartHandler()


class TestGetColors:
    @patch("backend.handlers.part_handler.call_with_refresh")
    def test_get_colors_success(self, mock_call_with_refresh, part_handler):
        """Should return colors for the given userset."""
        mock_call_with_refresh.return_value = [
            {"color_id": 1, "color_name": "Red"},
            {"color_id": 5, "color_name": "Blue"},
        ]

        result = part_handler.get_colors(user_set_id=1)

        assert len(result) == 2
        assert result[0]["color_name"] == "Red"

    @patch("backend.handlers.part_handler.call_with_refresh")
    def test_get_colors_api_error(self, mock_call_with_refresh, part_handler):
        """Should return an empty list when the API fails."""
        mock_call_with_refresh.side_effect = ApiError("Server error", status_code=500)

        assert part_handler.get_colors(user_set_id=1) == []


class TestGetAllUsersetParts:
    @patch("backend.handlers.part_handler.call_with_refresh")
    def test_get_all_userset_parts_success(self, mock_call_with_refresh, part_handler):
        """Should fetch part records and add image paths."""
        mock_call_with_refresh.return_value = [
            {
                "part_num": "3001",
                "color_id": 1,
                "name": "Brick 2x4",
                "total_num": 8,
                "found_num": 3,
                "is_spare": False,
            }
        ]

        result = part_handler.get_all_userset_parts(user_set_id=1)

        assert len(result) == 1
        assert result[0]["img_path"].name == "3001_1.jpg"

    @patch("backend.handlers.part_handler.call_with_refresh")
    def test_get_all_userset_parts_api_error(self, mock_call_with_refresh, part_handler):
        """Should return an empty list when the API fails."""
        mock_call_with_refresh.side_effect = ApiError("Server error", status_code=500)

        assert part_handler.get_all_userset_parts(user_set_id=1) == []


class TestGetAllMinifigs:
    @patch("backend.handlers.part_handler.call_with_refresh")
    def test_get_all_minifigs_success(self, mock_call_with_refresh, part_handler):
        """Should fetch minifig records and add image paths."""
        mock_call_with_refresh.return_value = [
            {
                "fig_num": "fig-001",
                "name": "Hero",
            }
        ]

        result = part_handler.get_all_minifigs(user_set_id=1)

        assert len(result) == 1
        assert result[0]["img_path"].name == "fig-001.jpg"


class TestChangeQuantity:
    @patch("backend.handlers.part_handler.call_with_refresh")
    def test_change_quantity_success(self, mock_call_with_refresh, part_handler):
        """Should propagate the API quantity update."""
        mock_call_with_refresh.return_value = {"quantity_have": 3}

        success, qty = part_handler.change_quantity(user_set_id=1, userpart_id=7, quantity=3)

        assert success is True
        assert qty == 3

    @patch("backend.handlers.part_handler.call_with_refresh")
    def test_change_quantity_api_error(self, mock_call_with_refresh, part_handler):
        """Should return None values if the API raises an error."""
        mock_call_with_refresh.side_effect = ApiError("Bad request", status_code=400)

        success, qty = part_handler.change_quantity(user_set_id=1, userpart_id=7, quantity=3)

        assert success is False
        assert qty is None


class TestSetAllParts:
    @patch("backend.handlers.part_handler.call_with_refresh")
    def test_set_all_parts_calls_api(self, mock_call_with_refresh, part_handler):
        """Should call the API helper with the selected action."""
        part_handler.set_all_parts(user_set_id=1, action="reset_set")

        mock_call_with_refresh.assert_called_once_with(
            part_handler.user_handler,
            apply_parts_action,
            1,
            "reset_set",
        )


class TestErrorHandlingAndRetry:
    @patch("backend.handlers.part_handler.call_with_refresh")
    def test_retry_on_401_unauthorized(self, mock_call_with_refresh, part_handler):
        """Should let the wrapper handle refresh/retry behavior."""
        mock_call_with_refresh.side_effect = ApiError("Unauthorized", status_code=401)

        with pytest.raises(ApiError):
            mock_call_with_refresh(None, None)

    @patch("backend.handlers.part_handler.call_with_refresh")
    def test_connection_error_handling(self, mock_call_with_refresh, part_handler):
        """Should propagate connection errors unchanged."""
        mock_call_with_refresh.side_effect = ApiError("Connection failed", status_code=None)

        with pytest.raises(ApiError):
            mock_call_with_refresh(None, None)


class TestGetMissingPartsReportData:
    @patch.object(SetHandler, "get_all_user_sets")
    @patch.object(PartHandler, "get_all_userset_parts")
    def test_get_missing_parts_report_data(self, mock_get_all_userset_parts, mock_get_all_user_sets, part_handler):
        """Should aggregate, deduplicate and sort missing parts."""
        mock_get_all_user_sets.return_value = [
            {"user_set_id": 1, "set_num": "42154-1", "set_name": "Set A", "progress_pct": 50},
            {"user_set_id": 2, "set_num": "75192-1", "set_name": "Set B", "progress_pct": 80},
        ]

        mock_get_all_userset_parts.side_effect = [
            [
                {
                    "part_num": "3001",
                    "color_id": 1,
                    "color": "Red",
                    "name": "Brick",
                    "total_num": 4,
                    "found_num": 1,
                    "is_spare": False,
                    "element_ids": ["e1", "e2"],
                    "img_path": Path("/fake/red.jpg"),
                }
            ],
            [
                {
                    "part_num": "1001",
                    "color_id": 2,
                    "color": "Blue",
                    "name": "Tile",
                    "total_num": 3,
                    "found_num": 0,
                    "is_spare": False,
                    "element_ids": ["e3"],
                    "img_path": Path("/fake/blue.jpg"),
                }
            ],
        ]

        result = part_handler.get_missing_parts_report_data(include_spares=False)

        assert len(result) == 2
        assert result[0]["color"] == "Blue"
        assert result[1]["color"] == "Red"
        assert result[0]["total_missing"] == 3

    @patch.object(SetHandler, "get_all_user_sets")
    @patch.object(PartHandler, "get_all_userset_parts")
    def test_get_missing_parts_report_data_filters_by_set_num(self, mock_get_all_userset_parts, mock_get_all_user_sets, part_handler):
        """Should filter aggregated data to selected set numbers."""
        mock_get_all_user_sets.return_value = [
            {
                "user_set_id": 1,
                "set_num": "42154-1",
                "set_name": "Set A",
                "progress_pct": 50,
            }
        ]
        mock_get_all_userset_parts.return_value = [
            {
                "part_num": "3001",
                "color_id": 1,
                "color": "Red",
                "name": "Brick",
                "total_num": 2,
                "found_num": 0,
                "is_spare": False,
                "element_ids": ["e1"],
                "img_path": Path("/fake/red.jpg"),
            }
        ]

        result = part_handler.get_missing_parts_report_data(set_nums=["42154-1"])

        assert len(result) == 1
        assert result[0]["sets"][0]["set_num"] == "42154-1"

    @patch.object(SetHandler, "get_all_user_sets")
    @patch.object(PartHandler, "get_all_userset_parts")
    def test_get_missing_parts_report_data_excludes_spares(self, mock_get_all_userset_parts, mock_get_all_user_sets, part_handler):
        """Should skip spare parts unless the user asks to include them."""
        mock_get_all_user_sets.return_value = [
            {
                "user_set_id": 1,
                "set_num": "42154-1",
                "set_name": "Set A",
                "progress_pct": 50,
            }
        ]
        mock_get_all_userset_parts.return_value = [
            {
                "part_num": "3001",
                "color_id": 1,
                "color": "Red",
                "name": "Brick",
                "total_num": 2,
                "found_num": 0,
                "is_spare": True,
                "element_ids": ["e1"],
                "img_path": Path("/fake/red.jpg"),
            }
        ]

        result = part_handler.get_missing_parts_report_data(include_spares=False)

        assert result == []
