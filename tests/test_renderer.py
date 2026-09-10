"""Smoke tests for deterministic renderer variation controls."""

import shutil

from PIL import Image, ImageDraw

from packages.common.paths import PROJECT_ROOT
from packages.common.types import BoundingBox, GlyphRecord
from packages.renderer.glyph_library import GlyphLibrary
from packages.renderer.layout import RendererVariationConfig, RenderSettings
from packages.renderer.render_png import plan_text_layout, render_text_to_image


TEST_SCRATCH_DIR = PROJECT_ROOT / ".tmp_tests" / "renderer"


def layout_settings(max_line_width: int = 140) -> RenderSettings:
    """Return compact settings for deterministic wrapping tests."""
    return RenderSettings(
        canvas_width=180,
        max_line_width=max_line_width,
        margin_left=20,
        margin_top=20,
        margin_bottom=20,
        line_height=50,
        glyph_height=32,
        character_spacing=4,
        word_spacing=16,
        footer_spacing=8,
    )


def no_variation(seed: int = 1) -> RendererVariationConfig:
    """Return a seeded configuration with placement jitter disabled."""
    return RendererVariationConfig(
        seed=seed,
        x_jitter_px=0,
        y_jitter_px=0,
        scale_jitter=0,
        spacing_jitter_px=0,
        line_spacing_jitter_px=0,
    )


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


def test_long_text_wraps_and_grows_canvas_height() -> None:
    """Additional wrapped lines should increase the rendered image height."""
    library = create_test_library()
    short_path = TEST_SCRATCH_DIR / "short.png"
    long_path = TEST_SCRATCH_DIR / "long.png"

    try:
        render_text_to_image(
            "aa",
            library,
            short_path,
            settings=layout_settings(),
            variation=no_variation(),
        )
        render_text_to_image(
            "aa aa aa aa aa aa",
            library,
            long_path,
            settings=layout_settings(),
            variation=no_variation(),
        )

        with Image.open(short_path) as short_image, Image.open(long_path) as long_image:
            assert long_image.height > short_image.height
    finally:
        shutil.rmtree(PROJECT_ROOT / ".tmp_tests", ignore_errors=True)


def test_normal_word_moves_intact_to_next_line() -> None:
    """A fitting word should wrap as a unit rather than split between lines."""
    library = create_test_library()

    try:
        layout = plan_text_layout(
            "aa aaa",
            library,
            settings=layout_settings(max_line_width=90),
            variation=no_variation(),
        )
        line_indices = [glyph.line_index for glyph in layout.glyphs]

        assert line_indices[:2] == [0, 0]
        assert line_indices[2:] == [1, 1, 1]
    finally:
        shutil.rmtree(PROJECT_ROOT / ".tmp_tests", ignore_errors=True)


def test_oversized_word_uses_character_level_wrapping() -> None:
    """A word wider than a full line may split at character boundaries."""
    library = create_test_library()

    try:
        layout = plan_text_layout(
            "aaaaaaaa",
            library,
            settings=layout_settings(max_line_width=70),
            variation=no_variation(),
        )

        assert layout.line_count > 1
        assert len({glyph.line_index for glyph in layout.glyphs}) > 1
    finally:
        shutil.rmtree(PROJECT_ROOT / ".tmp_tests", ignore_errors=True)


def test_explicit_newline_is_preserved() -> None:
    """A newline should force the following word onto the next line."""
    library = create_test_library()

    try:
        layout = plan_text_layout(
            "aa\naa",
            library,
            settings=layout_settings(),
            variation=no_variation(),
        )

        assert [glyph.line_index for glyph in layout.glyphs] == [0, 0, 1, 1]
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
