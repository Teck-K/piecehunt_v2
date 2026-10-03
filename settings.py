"""Application settings and path configuration for PieceHunt."""

import tomllib
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).parent

try:
    APP_VERSION = version("piecehunt")
except PackageNotFoundError:
    with open(PROJECT_ROOT / "pyproject.toml", "rb") as f:
        APP_VERSION = tomllib.load(f)["project"]["version"]

load_dotenv(PROJECT_ROOT / ".env")
API_BASE_URL = "https://api.piecehunt.app"


LOGS_DIR = PROJECT_ROOT / "logs"
DATA_DIR = PROJECT_ROOT / "data"
DATABASE_DATA_DIR = DATA_DIR / "database_data"
OLD_DATABASE_DIR = DATABASE_DATA_DIR / "old_database_data"
PARTS_DIR = DATA_DIR / "parts"
PART_IMAGES_DIR = PARTS_DIR / "images"
PART_IMAGES_DIR_60x60 = PART_IMAGES_DIR / "60x60"
MINIFIGS_DIR = DATA_DIR / "minifigs"
MINIFIGS_IMAGES_DIR = MINIFIGS_DIR / "images"
MINIFIGS_IMAGES_DIR_150x150 = MINIFIGS_IMAGES_DIR / "150x150"
SETS_DIR = DATA_DIR / "sets"
SETS_IMAGES_DIR = SETS_DIR / "images"
SETS_IMAGES_DIR_160x120 = SETS_IMAGES_DIR / "160x120"

INSTR_DIR = DATA_DIR / "instructions"
CSV_DIR = DATA_DIR / "new_lego_data"

YOLO_DIR = DATA_DIR / "yolo"
FALSE_POSITIVE_DIR = YOLO_DIR / "false_positives"

PDF_REPORTS_DIR = DATA_DIR / "reports" / "pdf"
EXCEL_REPORTS_DIR = DATA_DIR / "reports" / "excel"

BACKEND_DIR = PROJECT_ROOT / "backend"
BACKEND_HANDLERS_DIR = BACKEND_DIR / "handlers"
COLOR_MAPPERS_DIR = BACKEND_DIR / "color_mappers"

REPORTS_DIR = BACKEND_DIR / "reports"

EMAIL_SERVICE_DIR = BACKEND_DIR / "email_service"
EMAIL_TEMPLATES_DIR = EMAIL_SERVICE_DIR / "templates"

ASSETS_DIR = PROJECT_ROOT / "assets"
APP_IMAGES_DIR = ASSETS_DIR / "app_images"
BG_IMAGES_DIR = APP_IMAGES_DIR / "bg_images"

MODELS_DIR = PROJECT_ROOT / "models"

NO_IMAGE_FOUND = APP_IMAGES_DIR / "no_image_found" / "no_image_found_large.jpg"
NO_IMAGE_FOUND_60x60 = APP_IMAGES_DIR / "no_image_found" / "no_image_found_60x60.jpg"
NO_IMAGE_FOUND_150x150 = APP_IMAGES_DIR / "no_image_found" / "no_image_found_150x150.jpg"
NO_IMAGE_FOUND_160x120 = APP_IMAGES_DIR / "no_image_found" / "no_image_found_160x120.jpg"

YOLO_MODEL = MODELS_DIR / "best.pt"
