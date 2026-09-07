"""Tests for multi-page full-character template metadata and generation."""

import json
import shutil
from pathlib import Path

import pytest
from PIL import Image, ImageDraw

from experiments.scripts.create_template import TEMPLATE_METADATA_PATH, generate_template_pages
from packages.common.paths import PROJECT_ROOT, TEMPLATES_DIR
from packages.cv.glyph_extract import extract_glyphs_from_template_pages, make_safe_character_name
from packages.cv.segment import (
    get_template_pages,
    iter_template_cells,
    load_template_metadata,
    select_template_metadata_path,
    validate_template_input_count,
)


TEST_SCRATCH_DIR = PROJECT_ROOT / ".tmp_tests" / "template_v2"


def load_v2_metadata() -> dict:
    """Load V2 metadata for focused structural checks."""
    with (TEMPLATES_DIR / "template_v2.json").open("r", encoding="utf-8") as file:
        return json.load(file)


def test_v2_defaults_are_selected_for_template_pages() -> None:
    """Template generation and multi-page input should select V2 by default."""
    expected_path = TEMPLATES_DIR / "template_v2.json"

    assert TEMPLATE_METADATA_PATH == expected_path
    assert select_template_metadata_path(None, multi_page=True) == expected_path


def test_multiple_pages_reject_v1_metadata_with_clear_error() -> None:
    """Multiple page inputs should fail early when V1 metadata is selected."""
    metadata_path = TEMPLATES_DIR / "template_v1.json"
    metadata = load_template_metadata(metadata_path)

    with pytest.raises(ValueError, match="single-page/V1.*template_v2.json"):
        validate_template_input_count(metadata, 3, metadata_path)


def test_explicit_v1_single_page_remains_valid() -> None:
    """The explicit legacy V1 path should continue accepting one input image."""
    metadata_path = select_template_metadata_path(None, multi_page=False)
    metadata = load_template_metadata(metadata_path)

    assert metadata_path == TEMPLATES_DIR / "template_v1.json"
    validate_template_input_count(metadata, 1, metadata_path)


def test_template_v2_contains_full_character_groups() -> None:
    """V2 should include lowercase, uppercase, digits, punctuation, and symbols."""
    metadata = load_v2_metadata()
    groups = metadata["character_groups"]

    assert metadata["template_id"] == "template_v2"
    assert metadata["page_count"] == 3
    assert groups["lowercase"] == "abcdefghijklmnopqrstuvwxyz"
    assert groups["uppercase"] == "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    assert groups["digits"] == "0123456789"
    assert set(".,!?:;'\"-_()[]/\\") <= set(groups["punctuation"])
    assert set("@#$%&*+=<>") <= set(groups["symbols"])


def test_template_v2_pages_fit_and_v1_remains_supported() -> None:
    """Every V2 page should fit, while V1 still yields its original 78 cells."""
    metadata = load_v2_metadata()
    page_width = metadata["page"]["width_px"]
    page_height = metadata["page"]["height_px"]

    for page in get_template_pages(metadata):
        cells = iter_template_cells(metadata, page_number=page["page_number"])
        assert cells
        assert max(cell["bbox"].x + cell["bbox"].width for cell in cells) <= page_width
        assert max(cell["bbox"].y + cell["bbox"].height for cell in cells) <= page_height

    with (TEMPLATES_DIR / "template_v1.json").open("r", encoding="utf-8") as file:
        v1_metadata = json.load(file)

    v1_cells = iter_template_cells(v1_metadata)
    assert len(v1_cells) == 78
    assert {cell["page_number"] for cell in v1_cells} == {1}


def test_generate_template_v2_creates_three_png_pages() -> None:
    """V2 generation should produce three valid page images."""
    if TEST_SCRATCH_DIR.exists():
        shutil.rmtree(TEST_SCRATCH_DIR)

    try:
        output_paths = generate_template_pages(
            TEMPLATES_DIR / "template_v2.json",
            TEST_SCRATCH_DIR,
        )

        assert len(output_paths) == 3
        assert all(path.exists() and path.stat().st_size > 0 for path in output_paths)

        for page_number, output_path in enumerate(output_paths, start=1):
            assert output_path.name == f"template_v2_page_{page_number}.png"
            with Image.open(output_path) as image:
                assert image.size == (1700, 2200)
                assert image.mode == "RGB"
    finally:
        shutil.rmtree(PROJECT_ROOT / ".tmp_tests", ignore_errors=True)


def test_safe_glyph_filenames_use_unicode_codepoints() -> None:
    """Letters and path-sensitive punctuation should use portable names."""
    assert make_safe_character_name("A") == "U0041"
    assert make_safe_character_name("a") == "U0061"
    assert make_safe_character_name("?") == "U003F"
    assert make_safe_character_name("/") == "U002F"
    assert make_safe_character_name("\\") == "U005C"


def test_multi_page_extraction_records_page_and_template_metadata() -> None:
    """Multi-page extraction should combine ordered pages into one manifest."""
    if TEST_SCRATCH_DIR.exists():
        shutil.rmtree(TEST_SCRATCH_DIR)

    TEST_SCRATCH_DIR.mkdir(parents=True, exist_ok=True)
    metadata = {
        "template_id": "test_v2",
        "template_version": "0.2.0",
        "page": {"width_px": 100, "height_px": 100},
        "layout": {
            "columns": 1,
            "cell_width_px": 50,
            "cell_height_px": 50,
            "cell_gap_x_px": 0,
            "cell_gap_y_px": 0,
            "margin_left_px": 10,
            "margin_top_px": 10,
            "label_height_px": 10,
        },
        "character_groups": {"lowercase": "a", "uppercase": "A"},
        "pages": [
            {
                "page_number": 1,
                "character_groups": ["lowercase"],
                "variants_per_character": 1,
            },
            {
                "page_number": 2,
                "character_groups": ["uppercase"],
                "variants_per_character": 1,
            },
        ],
    }
    metadata_path = TEST_SCRATCH_DIR / "metadata.json"
    metadata_path.write_text(json.dumps(metadata), encoding="utf-8")
    input_paths = [TEST_SCRATCH_DIR / "page_1.png", TEST_SCRATCH_DIR / "page_2.png"]

    for index, input_path in enumerate(input_paths):
        image = Image.new("L", (100, 100), "white")
        draw = ImageDraw.Draw(image)
        draw.rectangle((22 + index, 32, 29 + index, 46), fill="black")
        image.save(input_path)

    try:
        manifest_path = extract_glyphs_from_template_pages(
            input_paths=input_paths,
            user_id="test_user",
            output_dir=TEST_SCRATCH_DIR / "glyphs",
            metadata_path=metadata_path,
        )
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

        assert manifest["page_count"] == 2
        assert manifest["template_version"] == "0.2.0"
        assert manifest["glyph_count"] == 2
        assert [record["page_number"] for record in manifest["glyphs"]] == [1, 2]
        assert [record["character"] for record in manifest["glyphs"]] == ["a", "A"]
        assert all(record["has_ink"] for record in manifest["glyphs"])
        assert {Path(record["image_path"]).name for record in manifest["glyphs"]} == {
            "U0041_variant_1.png",
            "U0061_variant_1.png",
        }
    finally:
        shutil.rmtree(PROJECT_ROOT / ".tmp_tests", ignore_errors=True)
