import json
import logging
from collections import defaultdict

import wx

from backend.handlers.set_handler import SetHandler
from backend.handlers.user_handler import UserHandler
from backend.helper import resize_with_wx
from backend.helper.singletonmeta import SingletonMeta
from services.api_client import (
    ApiError,
    apply_parts_action,
    get_userset_colors,
    get_userset_minifigs,
    get_userset_parts,
    update_part_quantity,
)
from services.api_retry import call_with_refresh
from settings import COLOR_MAPPERS_DIR, PART_IMAGES_DIR, MINIFIGS_IMAGES_DIR_150x150, PART_IMAGES_DIR_60x60

logger = logging.getLogger(__name__)
with open(COLOR_MAPPERS_DIR / "color_mapping_lego.json", encoding="utf-8") as f:
    _RAW_COLOR_MAP = json.load(f)


def _build_lego_color_map(raw: dict) -> dict:
    result = {}
    for color_id, info in raw.items():
        ext_ids = info.get("ext_ids") or []
        ext_descrs = info.get("ext_descrs") or []

        if not ext_ids:
            continue

        first_names = ext_descrs[0] if ext_descrs else []
        result[int(color_id)] = {
            "lego_color_id": ext_ids[0],
            "lego_color": first_names[0] if first_names else None,
        }
    return result


LEGO_COLOR_MAP = _build_lego_color_map(_RAW_COLOR_MAP)


class PartHandler(metaclass=SingletonMeta):
    """Handles all part-related operations for a user's set.

    All database access now goes through the Piecehunt API. This class only
    handles local concerns: resolving image paths and image display checks.
    """

    def __init__(self):
        self.user_handler = UserHandler()

    def _token(self) -> str:
        return self.user_handler.auth_session.access_token

    def get_colors(self, user_set_id: int) -> list[dict]:
        """Distinct colors used across a user's set.

        Args:
            user_set_id: The ID of the UserSets record (was: a userset object).
        """
        try:
            return call_with_refresh(self.user_handler, get_userset_colors, user_set_id)
        except ApiError as e:
            logger.error("Failed to fetch colors for userset %s: %s", user_set_id, e)
            return []

    def get_all_userset_parts(self, user_set_id: int) -> list[dict]:
        """Retrieves all parts for a user's set with their progress and metadata.

        Args:
            user_set_id: The ID of the UserSets record (was: a userset object).

        Returns:
            A list of dicts containing part details, progress and image paths.
        """
        try:
            parts = call_with_refresh(self.user_handler, get_userset_parts, user_set_id)
        except ApiError as e:
            logger.error("Failed to fetch parts for userset %s: %s", user_set_id, e)
            return []

        for part in parts:
            part["img_path"] = PART_IMAGES_DIR_60x60 / f"{part['part_num']}_{part['color_id']}.jpg"

        logger.debug("Loaded %d parts for userset: %s", len(parts), user_set_id)
        return parts

    def get_all_minifigs(self, user_set_id: int) -> list[dict]:
        """Retrieves all minifigures for a user's set with their metadata.

        Args:
            user_set_id: The ID of the UserSets record (was: a userset object).

        Returns:
            A list of dicts containing minifigure details and image paths.
        """
        try:
            minifigs = call_with_refresh(self.user_handler, get_userset_minifigs, user_set_id)
        except ApiError as e:
            logger.error("Failed to fetch minifigs for userset %s: %s", user_set_id, e)
            return []

        for minifig in minifigs:
            minifig["img_path"] = MINIFIGS_IMAGES_DIR_150x150 / f"{minifig['fig_num']}.jpg"

        return minifigs

    def change_quantity(self, user_set_id: int, userpart_id: int, quantity: int):
        """Updates the found quantity for a single part.

        Automatically refreshes the access token and retries once if it had
        expired, so users don't lose in-progress work during a long session.

        Args:
            user_set_id: The ID of the UserSets record this part belongs to.
            userpart_id: The ID of the UserSetParts record to update.
            quantity: The new absolute found quantity.

        Returns:
            A tuple of (True, new quantity) on success, (False, None) on failure.
        """
        try:
            result = call_with_refresh(self.user_handler, update_part_quantity, user_set_id, userpart_id, quantity)
        except ApiError as e:
            logger.error("Failed to change quantity for userpart %s to %s: %s", userpart_id, quantity, e)
            return False, None

        return True, result["quantity_have"]

    def set_all_parts(self, user_set_id: int, action: str):
        """Sets all parts in a set to completed or resets them to zero.

        Args:
            user_set_id: The ID of the UserSets record.
            action: Either 'reset_set' or 'complete_set'.
        """
        try:
            call_with_refresh(self.user_handler, apply_parts_action, user_set_id, action)
        except ApiError as e:
            logger.error("Failed to set all parts for userset %s (%s): %s", user_set_id, action, e)

    def get_missing_parts_report_data(
        self,
        include_spares: bool = False,
        set_nums: list[str] | None = None,
    ) -> list[dict]:
        """Aggregates missing parts across selected sets for the current user.

        Groups missing parts by part_num and color_id. If the same part is
        missing in multiple sets, the sets are listed individually with their
        respective missing quantities, alongside a total.

        Args:
            include_spares: Whether to include spare parts in the report.
            set_nums: Optional list of set_num strings to filter on.
                If None or empty, all incomplete sets are included.

        Returns:
            A list of dicts sorted by color name then part_num (see original
            docstring for the exact dict shape).
        """
        set_handler = SetHandler()
        all_user_sets = set_handler.get_all_user_sets(include_spares=include_spares)

        if set_nums:
            user_sets = [s for s in all_user_sets if s["set_num"] in set_nums]
        else:
            user_sets = [s for s in all_user_sets if s["progress_pct"] < 100]

        aggregated = defaultdict(
            lambda: {
                "part_num": None,
                "name": None,
                "color": None,
                "lego_color": None,
                "color_id": None,
                "lego_color_id": None,
                "element_ids": [],
                "img_path": None,
                "total_missing": 0,
                "total_missing_spare": 0,
                "sets": [],
            }
        )

        for user_set in user_sets:
            parts = self.get_all_userset_parts(user_set["user_set_id"])

            for part in parts:
                if not include_spares and part["is_spare"]:
                    continue

                missing = part["total_num"] - part["found_num"]
                if missing <= 0:
                    continue

                key = (part["part_num"], part["color_id"])
                entry = aggregated[key]
                lego = LEGO_COLOR_MAP.get(part["color_id"], {})

                entry["part_num"] = part["part_num"]
                entry["name"] = part["name"]
                entry["color"] = part["color"]
                entry["color_id"] = part["color_id"]
                entry["img_path"] = part["img_path"]
                entry["lego_color"] = lego.get("lego_color")
                entry["lego_color_id"] = lego.get("lego_color_id")

                for eid in part["element_ids"]:
                    if eid not in entry["element_ids"]:
                        entry["element_ids"].append(eid)

                entry["total_missing"] += missing
                if part["is_spare"]:
                    entry["total_missing_spare"] += missing
                entry["sets"].append(
                    {
                        "set_num": user_set["set_num"],
                        "set_name": user_set["set_name"],
                        "missing": missing,
                    }
                )

        result = sorted(aggregated.values(), key=lambda x: (x["color"].lower(), x["part_num"]))

        logger.debug(
            "Missing parts report data: %d unique parts for user: %s",
            len(result),
            self.user_handler.auth_session.email,
        )
        return result

    def image_too_large_to_display(self, img_path, max_w, max_h):
        """Saves a temporary image file to be used to display an image that is too large.

        Returns:
            (True, temp_path) if the image is too large, else (False, None).
        """
        temp_image_path = PART_IMAGES_DIR / "temp_image.jpg"
        img = wx.Image(str(img_path), wx.BITMAP_TYPE_ANY)
        w, h = img.GetWidth(), img.GetHeight()
        if w > max_w or h > max_h:
            resize_with_wx.resize_image(img_path, temp_image_path, max_w, max_h)
            return True, temp_image_path
        return False, None
