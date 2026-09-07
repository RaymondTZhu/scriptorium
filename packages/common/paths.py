"""Project path helpers for Scriptorium.

This module centralizes important filesystem paths so the rest of the
project does not need to hard-code relative paths repeatedly.
"""

import re
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
GLYPH_DATA_DIR = DATA_DIR / "glyphs"
OUTPUT_DATA_DIR = DATA_DIR / "outputs"
MANIFEST_DATA_DIR = DATA_DIR / "manifests"

DOCS_DIR = PROJECT_ROOT / "docs"
TEMPLATES_DIR = PROJECT_ROOT / "templates"
EXPERIMENTS_DIR = PROJECT_ROOT / "experiments"
EXPERIMENT_SCRIPTS_DIR = EXPERIMENTS_DIR / "scripts"
EXPERIMENT_RESULTS_DIR = EXPERIMENTS_DIR / "results"


def sanitize_path_component(value: str, fallback: str = "user") -> str:
    """Return a Windows-safe folder name for a user-provided path component."""
    sanitized = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", value).strip(" .")
    if not sanitized:
        sanitized = fallback

    windows_reserved_names = {"CON", "PRN", "AUX", "NUL"}
    windows_reserved_names.update(f"COM{number}" for number in range(1, 10))
    windows_reserved_names.update(f"LPT{number}" for number in range(1, 10))
    if sanitized.upper() in windows_reserved_names:
        sanitized = f"{sanitized}_"

    return sanitized


def ensure_project_dirs() -> None:
    """Create local project data directories if they do not already exist.

    The repository tracks empty data folders with `.gitkeep` files, but this
    helper makes scripts more robust if folders are deleted locally or if a
    user starts from a fresh checkout.
    """
    for path in [
        RAW_DATA_DIR,
        PROCESSED_DATA_DIR,
        GLYPH_DATA_DIR,
        OUTPUT_DATA_DIR,
        MANIFEST_DATA_DIR,
        EXPERIMENT_RESULTS_DIR,
    ]:
        path.mkdir(parents=True, exist_ok=True)
