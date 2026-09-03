"""Tests for tight glyph crops and blank-safe library loading."""

import json
import shutil

import numpy as np
from PIL import Image

from packages.common.paths import PROJECT_ROOT
from packages.cv.quality import detect_ink_bounding_box, trim_to_ink_bounding_box
from packages.renderer.glyph_library import load_glyph_library


TEST_SCRATCH_DIR = PROJECT_ROOT / ".tmp_tests" / "glyph_trimming"


def test_detect_ink_bounding_box_is_tight_and_padded() -> None:
    """Ink detection should exclude large white margins and include padding."""
    crop = np.full((100, 120), 255, dtype=np.uint8)
    crop[30:50, 40:60] = 0

    bbox = detect_ink_bounding_box(crop, padding=3, edge_margin=0)

    assert bbox is not None
    assert (bbox.x, bbox.y, bbox.width, bbox.height) == (37, 27, 26, 26)

    trimmed, trimmed_bbox = trim_to_ink_bounding_box(
        Image.fromarray(crop),
        padding=3,
        edge_margin=0,
    )
    assert trimmed_bbox == bbox
    assert trimmed.shape == (26, 26)


def test_blank_crop_falls_back_without_crashing() -> None:
    """A blank crop should retain its image and report no ink bounds."""
    blank = np.full((50, 80), 255, dtype=np.uint8)

    trimmed, bbox = trim_to_ink_bounding_box(blank)

    assert bbox is None
    assert trimmed.shape == blank.shape
    assert np.array_equal(trimmed, blank)


def test_glyph_library_excludes_explicitly_blank_variants() -> None:
    """Blank manifest records should remain inspectable but not renderable."""
    if TEST_SCRATCH_DIR.exists():
        shutil.rmtree(TEST_SCRATCH_DIR)

    TEST_SCRATCH_DIR.mkdir(parents=True, exist_ok=True)
    manifest_path = TEST_SCRATCH_DIR / "glyph_manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "glyphs": [
                    {
                        "user_id": "test_user",
                        "character": "a",
                        "variant_id": 1,
                        "image_path": "blank.png",
                        "has_ink": False,
                    },
                    {
                        "user_id": "test_user",
                        "character": "b",
                        "variant_id": 1,
                        "image_path": "b.png",
                        "cell_bbox": {"x": 1, "y": 2, "width": 240, "height": 92},
                    },
                ]
            }
        ),
        encoding="utf-8",
    )

    try:
        library = load_glyph_library(manifest_path)

        assert len(library.glyphs) == 2
        assert not library.has_character("a")
        assert library.has_character("b")
        assert library.get_variants("b")[0].has_ink is True
    finally:
        shutil.rmtree(PROJECT_ROOT / ".tmp_tests", ignore_errors=True)
