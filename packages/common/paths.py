"""Project path helpers for Scriptorium.

This module centralizes important filesystem paths so the rest of the
project does not need to hard-code relative paths repeatedly.
"""

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
