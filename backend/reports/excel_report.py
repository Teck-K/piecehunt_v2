"""Excel report generator for PieceHunt.

Generates a missing parts report as a styled Excel file using openpyxl.
"""

import logging
from datetime import datetime
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

from settings import EXCEL_REPORTS_DIR

logger = logging.getLogger(__name__)

# --- Styles ---
COLOR_PRIMARY = "1A1A2E"
COLOR_HEADER_BG = "16213E"
COLOR_ROW_ALT = "F5F5F5"
COLOR_WHITE = "FFFFFF"
COLOR_ACCENT = "E94560"

HEADERS = ["Color", "Part nr", "Name", "Element IDs", "Missing", "Sets"]
COL_WIDTHS = [20, 14, 40, 28, 10, 50]


def _header_font() -> Font:
    return Font(name="Calibri", bold=True, color=COLOR_WHITE, size=10)


def _header_fill() -> PatternFill:
    return PatternFill(fill_type="solid", fgColor=COLOR_HEADER_BG)


def _cell_font(bold: bool = False) -> Font:
    return Font(name="Calibri", bold=bold, size=9)


def _thin_border() -> Border:
    thin = Side(style="thin", color="DDDDDD")
    return Border(left=thin, right=thin, top=thin, bottom=thin)


def _alt_fill() -> PatternFill:
    return PatternFill(fill_type="solid", fgColor=COLOR_ROW_ALT)


def _white_fill() -> PatternFill:
    return PatternFill(fill_type="solid", fgColor=COLOR_WHITE)


def generate_missing_parts_excel(
    report_data: list[dict],
    username: str,
    include_spares: bool = False,
) -> Path:
    """Generates a missing parts Excel report and saves it to the reports directory.

    Creates a single worksheet with a flat table sorted by color then part number.
    Includes a title row, metadata row, column headers and one row per missing part.

    Args:
        report_data: List of dicts as returned by PartHandler.get_missing_parts_report_data().
        username: The username of the current user.
        include_spares: Whether spare parts were included, shown in metadata row.

    Returns:
        The Path to the generated Excel file.

    Raises:
        OSError: If the file could not be written.
    """
    EXCEL_REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = EXCEL_REPORTS_DIR / f"missing_parts_{username}_{timestamp}.xlsx"

    wb = Workbook()
    ws = wb.active
    ws.title = "Missing Parts"

    # --- Title row ---
    ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=len(HEADERS))
    title_cell = ws.cell(row=1, column=1, value="PieceHunt – Missing Parts Report")
    title_cell.font = Font(name="Calibri", bold=True, size=14, color=COLOR_PRIMARY)
    title_cell.alignment = Alignment(horizontal="left", vertical="center")
    ws.row_dimensions[1].height = 22

    # --- Metadata row ---
    spares_note = "Spare parts included" if include_spares else "Spare parts excluded"
    meta = (
        f"User: {username}  |  "
        f"Generated: {datetime.now().strftime('%d %b %Y  %H:%M')}  |  "
        f"{len(report_data)} unique missing parts  |  {spares_note}"
    )
    ws.merge_cells(start_row=2, start_column=1, end_row=2, end_column=len(HEADERS))
    meta_cell = ws.cell(row=2, column=1, value=meta)
    meta_cell.font = Font(name="Calibri", size=9, color="666666")
    meta_cell.alignment = Alignment(horizontal="left", vertical="center")
    ws.row_dimensions[2].height = 16

    ws.append([])  # empty spacer row

    # --- Column headers ---
    header_row = 4
    for col_idx, header in enumerate(HEADERS, start=1):
        cell = ws.cell(row=header_row, column=col_idx, value=header)
        cell.font = _header_font()
        cell.fill = _header_fill()
        cell.alignment = Alignment(horizontal="left", vertical="center", wrap_text=False)
        cell.border = _thin_border()
    ws.row_dimensions[header_row].height = 18

    # --- Data rows ---
    for row_idx, part in enumerate(report_data, start=header_row + 1):
        element_str = ", ".join(str(e) for e in part["element_ids"]) if part["element_ids"] else "—"

        if len(part["sets"]) > 1:
            sets_str = "  |  ".join(f"{s['set_num']} – {s['set_name']}: {s['missing']}" for s in part["sets"])
        elif part["sets"]:
            s = part["sets"][0]
            sets_str = f"{s['set_num']} – {s['set_name']}"
        else:
            sets_str = "—"

        row_values = [
            part["color"],
            part["part_num"],
            part["name"],
            element_str,
            part["total_missing"],
            sets_str,
        ]

        is_alt = (row_idx - header_row) % 2 == 0
        fill = _alt_fill() if is_alt else _white_fill()

        for col_idx, value in enumerate(row_values, start=1):
            cell = ws.cell(row=row_idx, column=col_idx, value=value)
            cell.font = _cell_font(bold=(col_idx == 5))  # bold missing count
            cell.fill = fill
            cell.border = _thin_border()
            cell.alignment = Alignment(
                horizontal="right" if col_idx == 5 else "left",
                vertical="center",
                wrap_text=(col_idx == 6),  # wrap sets column
            )
        ws.row_dimensions[row_idx].height = 15

    # --- Column widths ---
    for col_idx, width in enumerate(COL_WIDTHS, start=1):
        ws.column_dimensions[get_column_letter(col_idx)].width = width

    # --- Freeze header row ---
    ws.freeze_panes = ws.cell(row=header_row + 1, column=1)

    # --- Autofilter ---
    ws.auto_filter.ref = f"A{header_row}:{get_column_letter(len(HEADERS))}{header_row}"

    wb.save(output_path)
    logger.info("Missing parts Excel generated: %s", output_path.name)
    return output_path
