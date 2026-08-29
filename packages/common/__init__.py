"""Shared utilities and data models for Scriptorium."""

from packages.common.config import ProjectConfig
from packages.common.paths import (
    DATA_DIR,
    DOCS_DIR,
    EXPERIMENT_RESULTS_DIR,
    EXPERIMENT_SCRIPTS_DIR,
    EXPERIMENTS_DIR,
    GLYPH_DATA_DIR,
    MANIFEST_DATA_DIR,
    OUTPUT_DATA_DIR,
    PROCESSED_DATA_DIR,
    PROJECT_ROOT,
    RAW_DATA_DIR,
    TEMPLATES_DIR,
    ensure_project_dirs,
)
from packages.common.types import BoundingBox, GenerationManifest, GlyphRecord

__all__ = [
    "BoundingBox",
    "DATA_DIR",
    "DOCS_DIR",
    "EXPERIMENT_RESULTS_DIR",
    "EXPERIMENT_SCRIPTS_DIR",
    "EXPERIMENTS_DIR",
    "GLYPH_DATA_DIR",
    "GenerationManifest",
    "GlyphRecord",
    "MANIFEST_DATA_DIR",
    "OUTPUT_DATA_DIR",
    "PROCESSED_DATA_DIR",
    "PROJECT_ROOT",
    "ProjectConfig",
    "RAW_DATA_DIR",
    "TEMPLATES_DIR",
    "ensure_project_dirs",
]
