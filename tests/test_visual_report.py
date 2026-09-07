"""Smoke tests for visual evaluation report generation."""

import json
import shutil

from PIL import Image

from packages.common.paths import PROJECT_ROOT, sanitize_path_component
from packages.common.types import GlyphRecord
from packages.eval.visual_report import create_glyph_contact_sheet, create_visual_report
from packages.renderer.glyph_library import GlyphLibrary


TEST_SCRATCH_DIR = PROJECT_ROOT / ".tmp_tests" / "visual_report"


def test_create_glyph_contact_sheet_writes_normal_path() -> None:
    """A contact sheet should save into a project-local glyph output folder."""
    if TEST_SCRATCH_DIR.exists():
        shutil.rmtree(TEST_SCRATCH_DIR)

    glyph_dir = TEST_SCRATCH_DIR / "glyphs" / sanitize_path_component("test/user")
    glyph_path = glyph_dir / "glyph.png"
    output_path = glyph_dir / "glyph_contact_sheet.png"
    glyph_dir.mkdir(parents=True, exist_ok=True)
    Image.new("L", (20, 30), "white").save(glyph_path)
    library = GlyphLibrary(
        [
            GlyphRecord(
                user_id="test/user",
                character="a",
                variant_id=1,
                image_path=glyph_path,
            )
        ]
    )

    try:
        result = create_glyph_contact_sheet(library, output_path)

        assert result == output_path
        assert output_path.exists()
        assert output_path.stat().st_size > 0
        assert output_path.parent.name == "test_user"
    finally:
        shutil.rmtree(PROJECT_ROOT / ".tmp_tests", ignore_errors=True)


def test_create_visual_report_writes_nonempty_png() -> None:
    """A report should combine synthetic artifacts into a nonempty PNG file."""
    if TEST_SCRATCH_DIR.exists():
        shutil.rmtree(TEST_SCRATCH_DIR)

    TEST_SCRATCH_DIR.mkdir(parents=True, exist_ok=True)
    template_path = TEST_SCRATCH_DIR / "template.png"
    contact_sheet_path = TEST_SCRATCH_DIR / "contact_sheet.png"
    rendered_output_path = TEST_SCRATCH_DIR / "rendered.png"
    generation_record_path = TEST_SCRATCH_DIR / "generation.json"
    report_path = TEST_SCRATCH_DIR / "visual_report.png"

    Image.new("RGB", (320, 220), "white").save(template_path)
    Image.new("RGB", (300, 180), "lightgray").save(contact_sheet_path)
    Image.new("RGB", (280, 120), "white").save(rendered_output_path)
    generation_record_path.write_text(
        json.dumps(
            {
                "run_id": "run_test",
                "user_id": "test_user",
                "renderer_version": "0.1.0",
                "template_version": "0.1.0",
                "provenance_enabled": True,
            }
        ),
        encoding="utf-8",
    )

    try:
        result = create_visual_report(
            template_image_path=template_path,
            contact_sheet_path=contact_sheet_path,
            rendered_output_path=rendered_output_path,
            generation_record_path=generation_record_path,
            output_path=report_path,
        )

        assert result == report_path
        assert report_path.exists()
        assert report_path.stat().st_size > 0
    finally:
        shutil.rmtree(PROJECT_ROOT / ".tmp_tests", ignore_errors=True)
