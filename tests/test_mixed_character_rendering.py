"""Tests for loading and rendering mixed V2 character groups."""

import json
import shutil

from PIL import Image, ImageDraw

from packages.common.paths import PROJECT_ROOT
from packages.renderer.layout import RendererVariationConfig, RenderSettings
from packages.renderer.glyph_library import load_glyph_library
from packages.renderer.render_png import render_text_to_image


TEST_SCRATCH_DIR = PROJECT_ROOT / ".tmp_tests" / "mixed_rendering"


def test_library_loads_and_renders_mixed_v2_text() -> None:
    """Uppercase, lowercase, digits, and punctuation should render from a V2 manifest."""
    if TEST_SCRATCH_DIR.exists():
        shutil.rmtree(TEST_SCRATCH_DIR)

    TEST_SCRATCH_DIR.mkdir(parents=True, exist_ok=True)
    text = "Hello, World! 123"
    records = []

    for index, character in enumerate(dict.fromkeys(text.replace(" ", ""))):
        image_path = TEST_SCRATCH_DIR / f"U{ord(character):04X}.png"
        image = Image.new("L", (18, 32), "white")
        draw = ImageDraw.Draw(image)
        draw.line((3 + index % 8, 4, 12, 27), fill="black", width=3)
        image.save(image_path)
        records.append(
            {
                "user_id": "test_user",
                "character": character,
                "variant_id": 1,
                "page_number": 1,
                "template_version": "0.2.0",
                "image_path": str(image_path),
                "width": image.width,
                "height": image.height,
                "has_ink": True,
            }
        )

    manifest_path = TEST_SCRATCH_DIR / "glyph_manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "template_version": "0.2.0",
                "glyphs": records,
            }
        ),
        encoding="utf-8",
    )

    try:
        library = load_glyph_library(manifest_path)
        assert all(library.has_character(character) for character in set(text) - {" "})

        output_path = TEST_SCRATCH_DIR / "mixed.png"
        render_text_to_image(
            text=text + "~",
            library=library,
            output_path=output_path,
            settings=RenderSettings(canvas_width=900, canvas_height=180),
            variation=RendererVariationConfig(seed=42),
        )

        assert output_path.exists()
        assert output_path.stat().st_size > 0
        with Image.open(output_path) as rendered:
            assert rendered.width == 900
            assert rendered.height >= 180
    finally:
        shutil.rmtree(PROJECT_ROOT / ".tmp_tests", ignore_errors=True)
