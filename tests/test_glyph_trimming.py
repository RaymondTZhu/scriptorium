"""Tests for tight glyph crops and blank-safe library loading."""

import json
import shutil
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from packages.common.paths import PROJECT_ROOT
from packages.cv.glyph_extract import extract_glyphs_from_template_pages
from packages.cv.quality import detect_ink_bounding_box, trim_to_ink_bounding_box
from packages.cv.segment import save_crop
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


def test_save_crop_rejects_empty_images_with_clear_error() -> None:
    """Empty image arrays should raise ValueError before OpenCV is called."""
    output_path = TEST_SCRATCH_DIR / "empty.png"

    with pytest.raises(ValueError, match=r"empty\.png.*\(0, 10\)"):
        save_crop(np.empty((0, 10), dtype=np.uint8), output_path)


def test_extraction_records_out_of_bounds_cells_as_blank() -> None:
    """A cell outside the supplied image should not crash extraction."""
    if TEST_SCRATCH_DIR.exists():
        shutil.rmtree(TEST_SCRATCH_DIR)

    TEST_SCRATCH_DIR.mkdir(parents=True, exist_ok=True)
    image_path = TEST_SCRATCH_DIR / "small.png"
    Image.new("L", (40, 40), "white").save(image_path)
    metadata_path = TEST_SCRATCH_DIR / "metadata.json"
    metadata_path.write_text(
        json.dumps(
            {
                "template_id": "out_of_bounds_test",
                "template_version": "0.0.1",
                "page": {"width_px": 100, "height_px": 100},
                "layout": {
                    "columns": 1,
                    "cell_width_px": 20,
                    "cell_height_px": 20,
                    "cell_gap_x_px": 0,
                    "cell_gap_y_px": 0,
                    "margin_left_px": 60,
                    "margin_top_px": 60,
                    "label_height_px": 5,
                },
                "character_sets": {"lowercase": "a"},
                "variants_per_character": 1,
            }
        ),
        encoding="utf-8",
    )

    try:
        with pytest.warns(RuntimeWarning, match="page=1.*character='a'.*image_shape"):
            manifest_path = extract_glyphs_from_template_pages(
                input_paths=[image_path],
                user_id="test_user",
                output_dir=TEST_SCRATCH_DIR / "glyphs",
                metadata_path=metadata_path,
            )

        record = json.loads(manifest_path.read_text(encoding="utf-8"))["glyphs"][0]
        assert record["has_ink"] is False
        assert record["width"] == 0
        assert record["height"] == 0
        assert record["clamped_bbox"]["width"] == 0
        assert not Path(record["image_path"]).exists()
    finally:
        shutil.rmtree(PROJECT_ROOT / ".tmp_tests", ignore_errors=True)


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
