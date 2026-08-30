"""Entry point for the PieceHunt application.

Parses command-line arguments, creates the directory structure
and initializes logging before starting the application.

Usage:
    python main.py
    python main.py --debug
    python main.py --version
"""

import argparse
from pathlib import Path

import settings
from frontend.wx.app import run_app
from logs.logging_config import setup_logging


def create_dir_structure() -> None:
    dirs = [v for v in vars(settings).values() if isinstance(v, Path) and not v.suffix]
    for dir in dirs:
        dir.mkdir(parents=True, exist_ok=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Piecehunt Debugger")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging to console.")
    parser.add_argument("--version", action="version", version=f"PieceHunt {settings.APP_VERSION}")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    create_dir_structure()
    setup_logging(debug_mode=args.debug)
    run_app()
