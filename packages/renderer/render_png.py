"""PNG renderer for composing text from extracted glyph images."""

from __future__ import annotations

import random
from pathlib import Path

from PIL import Image, ImageDraw

from packages.renderer.glyph_library import GlyphLibrary
from packages.renderer.layout import RenderSettings
from packages.renderer.perturb import jitter_int


def render_text_to_image(
    text: str,
    library: GlyphLibrary,
    output_path: Path,
    settings: RenderSettings | None = None,
    seed: int = 7,
) -> Path:
    """Render text into a PNG image using extracted glyph variants."""
    active_settings = settings or RenderSettings()
    rng = random.Random(seed)

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
            cursor_y += active_settings.line_height
            continue

        if character == " ":
            cursor_x += active_settings.word_spacing
            continue

        if cursor_x > active_settings.canvas_width - active_settings.margin_left:
            cursor_x = active_settings.margin_left
            cursor_y += active_settings.line_height

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
            cursor_x += active_settings.placeholder_width + active_settings.character_spacing
            continue

        glyph_record = library.sample_variant(character, rng=rng)
        glyph_image = Image.open(glyph_record.image_path).convert("L")
        glyph_image.thumbnail((active_settings.glyph_height, active_settings.glyph_height))

        paste_y = jitter_int(
            base_value=cursor_y,
            max_abs_jitter=active_settings.baseline_jitter_px,
            rng=rng,
        )

        canvas.paste(glyph_image.convert("RGB"), (cursor_x, paste_y))

        cursor_x += glyph_image.width + active_settings.character_spacing

    output_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(output_path)

    return output_path


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
