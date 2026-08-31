"""Smoke tests for visual evaluation report generation."""

import json
import shutil

from PIL import Image

from packages.common.paths import PROJECT_ROOT
from packages.eval.visual_report import create_visual_report


TEST_SCRATCH_DIR = PROJECT_ROOT / ".tmp_tests" / "visual_report"


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
