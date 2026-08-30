"""PDF report generator for PieceHunt.

Generates a missing parts report as a styled PDF using reportlab.
"""

import logging
from datetime import datetime
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    Image,
    KeepTogether,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

from settings import EMAIL_TEMPLATES_DIR, PDF_REPORTS_DIR, NO_IMAGE_FOUND_60x60

logger = logging.getLogger(__name__)

# --- Colors ---
COLOR_PRIMARY = colors.HexColor("#1a1a2e")
COLOR_HEADER_BG = colors.HexColor("#16213e")
COLOR_ROW_ALT = colors.HexColor("#f5f5f5")
COLOR_WHITE = colors.white
COLOR_LIGHT_GRAY = colors.HexColor("#dddddd")

LOGO_PATH = EMAIL_TEMPLATES_DIR / "piecehunt_logo3.png"
IMG_SIZE = 12 * mm
PAGE_WIDTH, PAGE_HEIGHT = A4
MARGIN = 15 * mm


def _build_styles() -> dict:
    """Builds and returns all paragraph styles used in the report.

    Returns:
        A dict mapping style name to ParagraphStyle.
    """
    base = getSampleStyleSheet()

    return {
        "title": ParagraphStyle(
            "title",
            parent=base["Title"],
            fontSize=22,
            textColor=COLOR_PRIMARY,
            spaceAfter=2 * mm,
            fontName="Helvetica-Bold",
        ),
        "subtitle": ParagraphStyle(
            "subtitle",
            parent=base["Normal"],
            fontSize=10,
            textColor=colors.HexColor("#555555"),
            spaceAfter=6 * mm,
            fontName="Helvetica",
        ),
        "color_header": ParagraphStyle(
            "color_header",
            parent=base["Normal"],
            fontSize=11,
            textColor=COLOR_WHITE,
            fontName="Helvetica-Bold",
            leftIndent=3 * mm,
        ),
        "part_detail": ParagraphStyle(
            "part_detail",
            parent=base["Normal"],
            fontSize=8,
            textColor=colors.HexColor("#444444"),
            fontName="Helvetica",
        ),
        "part_bold": ParagraphStyle(
            "part_bold",
            parent=base["Normal"],
            fontSize=8,
            textColor=COLOR_PRIMARY,
            fontName="Helvetica-Bold",
        ),
    }


def _make_header_footer(canvas, doc, username: str):
    """Draws the page header with logo and footer with page number.

    Args:
        canvas: The reportlab canvas object.
        doc: The document template.
        username: The username to display in the footer.
    """
    canvas.saveState()

    # Header line
    canvas.setFillColor(COLOR_PRIMARY)
    canvas.rect(MARGIN, PAGE_HEIGHT - 18 * mm, PAGE_WIDTH - 2 * MARGIN, 0.5, fill=1)

    # Logo in header
    if LOGO_PATH.exists():
        canvas.drawImage(
            str(LOGO_PATH),
            MARGIN,
            PAGE_HEIGHT - 17 * mm,
            width=45 * mm,
            height=15 * mm,
            preserveAspectRatio=True,
            mask="auto",
        )

    # Footer
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.HexColor("#888888"))
    canvas.drawString(
        MARGIN,
        8 * mm,
        f"PieceHunt  |  {username}  |  Generated {datetime.now().strftime('%d %b %Y')}",
    )
    canvas.drawRightString(PAGE_WIDTH - MARGIN, 8 * mm, f"Page {doc.page}")

    canvas.restoreState()


def _part_image(img_path: Path) -> Image:
    """Returns a reportlab Image for the given path, falling back to default.

    Args:
        img_path: Path to the 60x60 part image.

    Returns:
        A reportlab Image object sized to IMG_SIZE x IMG_SIZE.
    """
    path = img_path if (img_path and Path(img_path).exists()) else NO_IMAGE_FOUND_60x60
    img = Image(str(path), width=IMG_SIZE, height=IMG_SIZE)
    img.hAlign = "CENTER"
    return img


def generate_missing_parts_pdf(
    report_data: list[dict],
    username: str,
    include_spares: bool = False,
) -> Path:
    """Generates a missing parts PDF report and saves it to the reports directory.

    The report is grouped by color, sorted by color name then part number.
    Each part shows a thumbnail image, part number, name, element IDs,
    set breakdown and total missing quantity.

    Args:
        report_data: List of dicts as returned by PartHandler.get_missing_parts_report_data().
        username: The username of the current user, shown in header/footer.
        include_spares: Whether spare parts were included, shown in subtitle.

    Returns:
        The Path to the generated PDF file.

    Raises:
        OSError: If the file could not be written.
    """
    PDF_REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = PDF_REPORTS_DIR / f"missing_parts_{username}_{timestamp}.pdf"

    styles = _build_styles()

    doc = BaseDocTemplate(
        str(output_path),
        pagesize=A4,
        leftMargin=MARGIN,
        rightMargin=MARGIN,
        topMargin=22 * mm,
        bottomMargin=18 * mm,
    )

    frame = Frame(
        doc.leftMargin,
        doc.bottomMargin,
        doc.width,
        doc.height,
        id="main",
    )

    doc.addPageTemplates(
        [
            PageTemplate(
                id="main",
                frames=frame,
                onPage=lambda c, d: _make_header_footer(c, d, username),
            )
        ]
    )

    story = []

    # --- Title block ---
    spares_note = "Spare parts included" if include_spares else "Spare parts excluded"
    story.append(Paragraph("Missing Parts Report", styles["title"]))
    story.append(
        Paragraph(
            f"User: {username}  |  "
            f"Generated: {datetime.now().strftime('%d %b %Y  %H:%M')}  |  "
            f"{len(report_data)} unique missing parts  |  {spares_note}",
            styles["subtitle"],
        )
    )
    story.append(Spacer(1, 4 * mm))

    if not report_data:
        story.append(Paragraph("No missing parts found. Great job!", styles["part_detail"]))
        doc.build(story)
        logger.info("Empty missing parts PDF generated: %s", output_path)
        return output_path

    # Column widths: img | part nr + name | element IDs | missing
    col_widths = [
        IMG_SIZE + 4,  # thumbnail
        doc.width * 0.38,  # part nr + name + sets
        doc.width * 0.25,  # element IDs
        doc.width * 0.17,  # missing
    ]

    # Group by color (already sorted by color then part_num)
    grouped: dict[str, list] = {}
    for part in report_data:
        grouped.setdefault(part["color"], []).append(part)

    for color_name, parts in grouped.items():
        # Color group header
        header_table = Table(
            [[Paragraph(f"  {color_name}", styles["color_header"])]],
            colWidths=[doc.width],
            rowHeights=[7 * mm],
        )
        header_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), COLOR_HEADER_BG),
                    ("LEFTPADDING", (0, 0), (-1, -1), 4),
                    ("TOPPADDING", (0, 0), (-1, -1), 1),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ]
            )
        )

        # Column headers
        table_data = [
            [
                Paragraph("", styles["part_detail"]),
                Paragraph("<b>Part nr / Name / Sets</b>", styles["part_detail"]),
                Paragraph("<b>Element IDs</b>", styles["part_detail"]),
                Paragraph("<b>Missing</b>", styles["part_detail"]),
            ]
        ]

        for part in parts:
            # Sets breakdown
            if len(part["sets"]) > 1:
                sets_text = f"<b>Total: {part['total_missing']}</b>"
                for s in part["sets"]:
                    sets_text += f"<br/>  └ {s['set_num']} – {s['set_name']}: {s['missing']}"
            elif part["sets"]:
                s = part["sets"][0]
                sets_text = f"{s['set_num']} – {s['set_name']}"
            else:
                sets_text = ""

            element_str = ", ".join(str(e) for e in part["element_ids"]) if part["element_ids"] else "—"

            name_cell = Paragraph(
                f"<b>{part['part_num']}</b>  {part['name']}<br/>{sets_text}",
                styles["part_detail"],
            )

            row = [
                _part_image(part["img_path"]),
                name_cell,
                Paragraph(element_str, styles["part_detail"]),
                Paragraph(
                    f"<b>{part['total_missing']}</b>" if len(part["sets"]) > 1 else str(part["total_missing"]),
                    styles["part_detail"],
                ),
            ]
            table_data.append(row)

        parts_table = Table(
            table_data,
            colWidths=col_widths,
            repeatRows=1,
        )
        row_count = len(table_data)
        parts_table.setStyle(
            TableStyle(
                [
                    # Header row
                    ("BACKGROUND", (0, 0), (-1, 0), COLOR_LIGHT_GRAY),
                    ("FONTSIZE", (0, 0), (-1, -1), 8),
                    # Alternating rows
                    ("ROWBACKGROUNDS", (0, 1), (-1, row_count - 1), [COLOR_WHITE, COLOR_ROW_ALT]),
                    # Grid
                    ("GRID", (0, 0), (-1, -1), 0.25, COLOR_LIGHT_GRAY),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("ALIGN", (0, 0), (0, -1), "CENTER"),  # center thumbnails
                    ("ALIGN", (3, 0), (3, -1), "RIGHT"),  # right-align missing col
                    ("TOPPADDING", (0, 0), (-1, -1), 3),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                    ("LEFTPADDING", (0, 0), (-1, -1), 4),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ]
            )
        )

        story.append(KeepTogether([header_table, parts_table]))
        story.append(Spacer(1, 4 * mm))

    doc.build(story)
    logger.info("Missing parts PDF generated: %s", output_path.name)
    return output_path
