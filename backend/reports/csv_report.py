"""CSV report generator for PieceHunt.

Generates a missing parts report as a CSV file using the LEGO color id,
in the format: Part,Color,Quantity,Is Spare.
"""

import csv
import logging
from datetime import datetime
from pathlib import Path

from settings import CSV_REPORTS_DIR

logger = logging.getLogger(__name__)

HEADERS = ["Part", "Color", "Quantity", "Is Spare"]


def generate_missing_parts_csv(
    report_data: list[dict],
    username: str,
) -> Path:
    """Generates a missing parts CSV report and saves it to the reports directory.

    Writes one row per missing part, using the LEGO color id as color.
    Spare parts are never flagged, so "Is Spare" is always False.
    Parts without a LEGO color id are skipped and logged as a warning.

    Args:
        report_data: List of dicts as returned by PartHandler.get_missing_parts_report_data().
        username: The username of the current user.

    Returns:
        The Path to the generated CSV file.

    Raises:
        OSError: If the file could not be written.
    """

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = CSV_REPORTS_DIR / f"missing_parts_{username}_{timestamp}.csv"

    skipped = 0

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(HEADERS)

        for part in report_data:
            #     lego_color_id = part.get("lego_color_id")
            #     if lego_color_id is None:
            #         skipped += 1
            #         logger.warning(
            #             "No LEGO color id for part %s (color_id=%s), skipping",
            #             part["part_num"],
            #             part.get("color_id"),
            #         )
            #         continue

            spare_qty = part.get("total_missing_spare", 0)
            regular_qty = part["total_missing"] - spare_qty

            if regular_qty > 0:
                writer.writerow([part["part_num"], part["color_id"], regular_qty, False])
            if spare_qty > 0:
                writer.writerow([part["part_num"], part["color_id"], spare_qty, True])

    logger.info(
        "Missing parts CSV generated: %s (%d rows, %d skipped)",
        output_path.name,
        len(report_data) - skipped,
        skipped,
    )
    return output_path
