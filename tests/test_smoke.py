"""Smoke tests for core Scriptorium imports and configuration."""

from packages.common import PROJECT_ROOT, ProjectConfig, ensure_project_dirs
from packages.common.types import BoundingBox


def test_project_root_exists() -> None:
    """The project root path should exist."""
    assert PROJECT_ROOT.exists()


def test_project_config_defaults() -> None:
    """Default project config should expose expected safety defaults."""
    config = ProjectConfig()

    assert config.project_name == "scriptorium"
    assert config.visible_watermark_enabled is True
    assert config.metadata_provenance_enabled is True


def test_bounding_box_fields() -> None:
    """BoundingBox should store image-region geometry."""
    bbox = BoundingBox(x=1, y=2, width=3, height=4)

    assert bbox.x == 1
    assert bbox.y == 2
    assert bbox.width == 3
    assert bbox.height == 4


def test_ensure_project_dirs_runs() -> None:
    """Project directory creation helper should run without error."""
    ensure_project_dirs()
