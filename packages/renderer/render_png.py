"""PNG renderer for composing text from extracted glyph images."""

from __future__ import annotations

import random
from pathlib import Path

from PIL import Image, ImageDraw

from packages.common.images import safe_save_image
from packages.renderer.glyph_library import GlyphLibrary
from packages.renderer.layout import RendererVariationConfig, RenderSettings
from packages.renderer.perturb import jitter_int, jitter_scale


def render_text_to_image(
    text: str,
    library: GlyphLibrary,
    output_path: Path,
    settings: RenderSettings | None = None,
    seed: int | None = 7,
    variation: RendererVariationConfig | None = None,
) -> Path:
    """Render text into a PNG image using extracted glyph variants."""
    active_settings = settings or RenderSettings()
    active_variation = variation or RendererVariationConfig(seed=seed)
    rng = random.Random(active_variation.seed)

    canvas = Image.new(
        "RGB",
        (active_settings.canvas_width, active_settings.canvas_height),
        "white",
    )
    draw = ImageDraw.Draw(canvas)

    cursor_x = active_settings.margin_left
    cursor_y = active_settings.margin_top

    for character in text:
        if character == "\n":
            cursor_x = active_settings.margin_left
            cursor_y += _line_advance(active_settings, active_variation, rng)
            continue

        if character == " ":
            cursor_x += active_settings.word_spacing
            continue

        if cursor_x > active_settings.canvas_width - active_settings.margin_left:
            cursor_x = active_settings.margin_left
            cursor_y += _line_advance(active_settings, active_variation, rng)

        if cursor_y > active_settings.canvas_height - active_settings.margin_top:
            break

        if not library.has_character(character):
            draw_unsupported_character_placeholder(
                draw=draw,
                x=cursor_x,
                y=cursor_y,
                width=active_settings.placeholder_width,
                height=active_settings.glyph_height,
            )
            cursor_x += _glyph_advance(
                active_settings.placeholder_width,
                active_settings,
                active_variation,
                rng,
            )
            continue

        glyph_record = library.sample_variant(character, rng=rng)
        with Image.open(glyph_record.image_path) as source_image:
            glyph_image = source_image.convert("L")

        scale = jitter_scale(active_variation.scale_jitter, rng)
        target_height = max(1, round(active_settings.glyph_height * scale))
        glyph_image.thumbnail((target_height, target_height))

        paste_x = max(
            0,
            jitter_int(
                base_value=cursor_x,
                max_abs_jitter=active_variation.x_jitter_px,
                rng=rng,
            ),
        )

        paste_y = jitter_int(
            base_value=cursor_y,
            max_abs_jitter=active_variation.y_jitter_px,
            rng=rng,
        )

        canvas.paste(glyph_image.convert("RGB"), (paste_x, paste_y))

        cursor_x += _glyph_advance(
            glyph_image.width,
            active_settings,
            active_variation,
            rng,
        )

    return safe_save_image(canvas, output_path)


def _glyph_advance(
    glyph_width: int,
    settings: RenderSettings,
    variation: RendererVariationConfig,
    rng: random.Random,
) -> int:
    """Return a positive horizontal cursor advance for one glyph."""
    spacing = jitter_int(
        base_value=settings.character_spacing,
        max_abs_jitter=variation.spacing_jitter_px,
        rng=rng,
    )
    return glyph_width + max(0, spacing)


def _line_advance(
    settings: RenderSettings,
    variation: RendererVariationConfig,
    rng: random.Random,
) -> int:
    """Return a positive line-height advance."""
    return max(
        1,
        jitter_int(
            base_value=settings.line_height,
            max_abs_jitter=variation.line_spacing_jitter_px,
            rng=rng,
        ),
    )


def draw_unsupported_character_placeholder(
    draw: ImageDraw.ImageDraw,
    x: int,
    y: int,
    width: int,
    height: int,
) -> None:
    """Draw a visible placeholder box for unsupported characters."""
    draw.rectangle((x, y, x + width, y + height), outline="black", width=1)
    draw.line((x, y, x + width, y + height), fill="black", width=1)
    draw.line((x + width, y, x, y + height), fill="black", width=1)
