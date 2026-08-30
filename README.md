# PieceHunt

[![License: Custom (Non-Commercial)](https://img.shields.io/badge/License-Custom%20Non--Commercial-blue.svg)](LICENSE)

PieceHunt is a desktop application for LEGO collectors who want to rebuild complete sets from a mixed pile of bricks. The app helps you organize your owned sets, track the parts you have found, inspect missing parts, download official building instructions, and identify stickered pages inside instruction booklets.

This project is currently built as a native desktop app with wxPython and uses a remote PieceHunt API for account management, set data, and user progress.

## Why this project exists

When a LEGO collection is mixed together, it becomes difficult to know which bricks belong to which set and which parts are still missing. PieceHunt solves that by:

- letting users add sets they own
- tracking progress per set and per part
- showing which parts are still missing
- downloading instructions for a selected set
- scanning instruction pages for stickered parts with YOLO

## Current status

The project is in active desktop-app development and is being used as a focused LEGO sorting and inventory tool. The current version in the project metadata is v2.0.0.

## Main features

- User registration and login through the PieceHunt API
- Set management: add, inspect, and track set progress
- Part tracking per set, including quantity updates and color filtering
- Missing parts reporting, including PDF/Excel export and optional email delivery
- Instruction download for LEGO set PDFs
- Sticker detection in instruction pages using YOLO
- Local caching of set, minifig, and part images for faster offline browsing
- Native desktop interface using wxPython

## Tech stack

- Python 3.14+
- wxPython for the desktop UI
- httpx for API communication
- BeautifulSoup for LEGO instruction page scraping
- PyMuPDF (fitz) for PDF page extraction
- Ultralytics YOLO for sticker detection
- Pillow and wx image resizing for local asset preparation
- reportlab and openpyxl for report generation
- python-dotenv for environment setup
- uv for dependency management and project execution

## Project structure

```text
piecehunt/
├── main.py                  # app entry point
├── settings.py              # app paths and settings
├── pyproject.toml           # project metadata and dependencies
├── README.md                # project documentation
├── assets/                  # app icons and placeholder images
├── backend/
│   ├── handlers/            # user, set, part and instruction logic
│   ├── reports/             # PDF/Excel report generation helpers
│   ├── email_service/       # email templates and supporting files
│   └── helper/              # utilities like resize and singleton helpers
├── data/
│   ├── database_data/       # local cached data and backups
│   ├── instructions/        # downloaded LEGO instruction PDFs
│   ├── parts/               # downloaded part images
│   ├── minifigs/            # minifig images
│   ├── sets/                # set images
│   └── yolo/                # model and false-positive image storage
├── frontend/
│   └── wx/                  # wxPython UI screens and panels
├── logs/                    # runtime logs
├── models/
│   └── best.pt              # YOLO model used for sticker detection
├── services/
│   ├── api_client.py        # REST calls to the PieceHunt API
│   ├── api_retry.py         # token refresh retry logic
│   ├── auth.py              # login/register result helpers
│   ├── auth_session.py      # stored auth session data
│   ├── feedback.py          # bug/issue reporting to the API
│   └── ...
├── tests/                   # automated tests for handlers and logic
└── scripts/                 # utility scripts
```

## Runtime architecture

The current architecture is split between the local desktop app and the remote API layer:

- `frontend/wx/` contains all screens, menus, panels, and dialogs
- `backend/handlers/` contains the domain logic for users, sets, parts, and instructions
- `services/` wraps the remote REST API calls, authentication, and retry behavior
- `data/` stores downloaded images, instructions, generated reports, and local cache assets
- `models/best.pt` is used by the sticker detection pipeline

## Requirements

- Python 3.14 or newer
- uv installed
- Internet access for initial set/data loading and instruction downloads

## Quick start

1. Clone the repository:

```bash
git clone <repo-url>
cd piecehunt
```

2. Install dependencies:

```bash
uv sync
```


3. Run the app:

```bash
uv run main.py
```

4. Optional debug mode:

```bash
uv run main.py --debug
```

5. Check the version:

```bash
uv run main.py --version
```

## Key user workflow

### 1. Sign in or register

The app starts on a welcome screen. Users can log in or create an account through the API-backed authentication flow.

### 2. Add a LEGO set

Once signed in, the user can add one or more sets. The app fetches the set data and downloads the relevant local images for:

- the set cover image
- the included part images
- minifig images
- resized local thumbnails for the UI

### 3. Track progress

Each set shows the progress percentage and its current status. Users can update quantities as they find LEGO pieces and mark missing parts as completed.

### 4. Inspect missing parts

The app can generate a missing-parts overview for one or more sets and export it as PDF or Excel, with optional email delivery.

### 5. Download instructions

For an active set, the app fetches instruction PDFs from the official LEGO site. The system stores them under `data/instructions/<set_number>/`.

### 6. Detect stickered pages

Instruction pages are converted to images and processed with a YOLO model. Detected stickered pages are saved so users can review them in a custom image viewer.

## Data and local cache

The application creates and uses a local data storage structure under `data/`:

- `data/parts/images` for part images
- `data/minifigs/images` for minifig images
- `data/sets/images` for set images
- `data/instructions` for downloaded LEGO PDFs and sticker results
- `data/reports` for generated Excel and PDF files
- `data/yolo` for model-related files and false positive tracking


## Development notes

- `main.py` is the application entry point and creates required directories before startup.
- `settings.py` defines the project paths and default API endpoint.
- `services/api_client.py` is the main REST interface for the app.
- `backend/handlers/` houses the logic used by the wx panels and dialogs.
- `tests/` covers the key handler behaviors and expected application logic.

## Useful commands

```bash
# run the app
uv run main.py

# run debug mode
uv run main.py --debug

# run the test suite
uv run pytest

# format/lint check
uv run ruff check .
```

## Notes

- This project is a personal desktop utility and not a general-purpose LEGO database package.
- The product depends on the hosted PieceHunt API for account and set data.


## License

PieceHunt is provided under a custom non-commercial license. See [LICENSE](LICENSE) for full details.

**Summary:**
- ✅ **Free for non-commercial use** (personal, educational, non-profit)
- ✅ **Personal modifications allowed** (must remain private)
- ❌ **Commercial use requires permission** (contact for licensing)
- ❌ **Redistribution without permission not allowed**

For commercial licensing inquiries, please contact the copyright holder.
