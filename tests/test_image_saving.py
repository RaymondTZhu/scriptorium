"""Tests for safe generated-image saving."""

import shutil

import pytest
from PIL import Image

from packages.common.images import safe_save_image
from packages.common.paths import PROJECT_ROOT


TEST_SCRATCH_DIR = PROJECT_ROOT / ".tmp_tests" / "image_saving"


def reset_test_scratch_dir() -> None:
    """Create a clean project-local image-saving directory."""
    if TEST_SCRATCH_DIR.exists():
        shutil.rmtree(TEST_SCRATCH_DIR)
    TEST_SCRATCH_DIR.mkdir(parents=True, exist_ok=True)


def test_safe_save_image_creates_parents_and_returns_final_path() -> None:
    """Saving should create missing parents and return the requested path."""
    reset_test_scratch_dir()
    output_path = TEST_SCRATCH_DIR / "nested" / "generated.png"

    try:
        result = safe_save_image(Image.new("L", (12, 8), 128), output_path)

        assert result == output_path
        assert output_path.exists()
        assert output_path.stat().st_size > 0
        with Image.open(output_path) as saved_image:
            assert saved_image.mode == "RGB"
            assert saved_image.size == (12, 8)
    finally:
        shutil.rmtree(PROJECT_ROOT / ".tmp_tests", ignore_errors=True)


def test_safe_save_image_atomically_overwrites_existing_image() -> None:
    """A later save should replace the complete existing image."""
    reset_test_scratch_dir()
    output_path = TEST_SCRATCH_DIR / "generated.png"

    try:
        safe_save_image(Image.new("RGB", (5, 6), "red"), output_path)
        safe_save_image(Image.new("RGB", (9, 7), "blue"), output_path)

        with Image.open(output_path) as saved_image:
            assert saved_image.size == (9, 7)
            assert saved_image.getpixel((0, 0)) == (0, 0, 255)
        assert not (TEST_SCRATCH_DIR / "generated.tmp.png").exists()
    finally:
        shutil.rmtree(PROJECT_ROOT / ".tmp_tests", ignore_errors=True)


def test_safe_save_image_rejects_zero_sized_image() -> None:
    """A zero-sized generated image should fail before filesystem writing."""
    reset_test_scratch_dir()
    output_path = TEST_SCRATCH_DIR / "empty.png"

    try:
        with pytest.raises(ValueError, match="non-positive size"):
            safe_save_image(Image.new("RGB", (0, 4)), output_path)

        assert not output_path.exists()
    finally:
        shutil.rmtree(PROJECT_ROOT / ".tmp_tests", ignore_errors=True)
