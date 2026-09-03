"""Smoke tests for deterministic renderer variation controls."""

import shutil

from PIL import Image, ImageDraw

from packages.common.paths import PROJECT_ROOT
from packages.common.types import BoundingBox, GlyphRecord
from packages.renderer.glyph_library import GlyphLibrary
from packages.renderer.layout import RendererVariationConfig, RenderSettings
from packages.renderer.render_png import render_text_to_image


TEST_SCRATCH_DIR = PROJECT_ROOT / ".tmp_tests" / "renderer"


def create_test_library() -> GlyphLibrary:
    """Create a small synthetic glyph library in project-local scratch space."""
    if TEST_SCRATCH_DIR.exists():
        shutil.rmtree(TEST_SCRATCH_DIR)

    TEST_SCRATCH_DIR.mkdir(parents=True, exist_ok=True)
    glyphs: list[GlyphRecord] = []

    for variant_id, line_x in enumerate((8, 16, 24), start=1):
        image_path = TEST_SCRATCH_DIR / f"a_variant_{variant_id}.png"
        image = Image.new("L", (32, 64), "white")
        draw = ImageDraw.Draw(image)
        draw.line((line_x, 8, line_x, 56), fill="black", width=4)
        image.save(image_path)
        glyphs.append(
            GlyphRecord(
                user_id="test_user",
                character="a",
                variant_id=variant_id,
                image_path=image_path,
            )
        )

    return GlyphLibrary(glyphs)


def render_with_seed(library: GlyphLibrary, seed: int, filename: str) -> bytes:
    """Render synthetic text and return the resulting PNG bytes."""
    output_path = TEST_SCRATCH_DIR / filename
    variation = RendererVariationConfig(
        seed=seed,
        x_jitter_px=2,
        y_jitter_px=3,
        scale_jitter=0.04,
        spacing_jitter_px=2,
    )

    render_text_to_image(
        text="aaaaaaaaaaaa",
        library=library,
        output_path=output_path,
        settings=RenderSettings(canvas_width=800, canvas_height=180),
        variation=variation,
    )
    return output_path.read_bytes()


def test_renderer_is_deterministic_for_same_seed() -> None:
    """The same glyphs, text, and seed should produce identical PNG bytes."""
    library = create_test_library()

    try:
        first = render_with_seed(library, seed=17, filename="first.png")
        second = render_with_seed(library, seed=17, filename="second.png")

        assert first == second
    finally:
        shutil.rmtree(PROJECT_ROOT / ".tmp_tests", ignore_errors=True)


def test_renderer_changes_for_different_seeds() -> None:
    """Different seeds should change variant selection or placement."""
    library = create_test_library()

    try:
        first = render_with_seed(library, seed=17, filename="first.png")
        second = render_with_seed(library, seed=23, filename="second.png")

        assert first != second
    finally:
        shutil.rmtree(PROJECT_ROOT / ".tmp_tests", ignore_errors=True)


def test_trimmed_width_controls_character_spacing() -> None:
    """A large original cell must not inflate spacing for a narrow glyph asset."""
    if TEST_SCRATCH_DIR.exists():
        shutil.rmtree(TEST_SCRATCH_DIR)

    TEST_SCRATCH_DIR.mkdir(parents=True, exist_ok=True)
    image_path = TEST_SCRATCH_DIR / "narrow.png"
    Image.new("L", (8, 20), "black").save(image_path)
    library = GlyphLibrary(
        [
            GlyphRecord(
                user_id="test_user",
                character="a",
                variant_id=1,
                image_path=image_path,
                original_bbox=BoundingBox(x=0, y=0, width=240, height=92),
                width=8,
                height=20,
                has_ink=True,
            )
        ]
    )
    output_path = TEST_SCRATCH_DIR / "narrow_render.png"

    try:
        render_text_to_image(
            text="aa",
            library=library,
            output_path=output_path,
            settings=RenderSettings(
                canvas_width=200,
                canvas_height=80,
                margin_left=10,
                margin_top=10,
                glyph_height=20,
                character_spacing=4,
            ),
            variation=RendererVariationConfig(
                seed=1,
                x_jitter_px=0,
                y_jitter_px=0,
                scale_jitter=0,
                spacing_jitter_px=0,
            ),
        )

        with Image.open(output_path) as rendered:
            ink_bounds = rendered.convert("L").point(lambda value: 255 - value).getbbox()

        assert ink_bounds is not None
        assert ink_bounds[2] <= 30
    finally:
        shutil.rmtree(PROJECT_ROOT / ".tmp_tests", ignore_errors=True)
