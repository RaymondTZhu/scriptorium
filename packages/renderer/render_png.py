"""PNG renderer with word wrapping and dynamic canvas sizing."""

from __future__ import annotations

import random
import re
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageDraw

from packages.common.images import safe_save_image
from packages.renderer.glyph_library import GlyphLibrary
from packages.renderer.layout import RendererVariationConfig, RenderSettings
from packages.renderer.perturb import jitter_int, jitter_scale


@dataclass(frozen=True)
class PlacedGlyph:
    """One glyph or placeholder positioned on the final canvas."""

    character: str
    x: int
    y: int
    width: int
    height: int
    line_index: int
    image: Image.Image | None


@dataclass(frozen=True)
class RenderLayout:
    """Computed glyph positions and dynamic output dimensions."""

    glyphs: list[PlacedGlyph]
    width: int
    height: int
    line_count: int


@dataclass(frozen=True)
class _GlyphPlan:
    """Seeded glyph measurements before absolute placement."""

    character: str
    width: int
    height: int
    advance: int
    x_jitter: int
    y_jitter: int
    image: Image.Image | None


def render_text_to_image(
    text: str,
    library: GlyphLibrary,
    output_path: Path,
    settings: RenderSettings | None = None,
    seed: int | None = 7,
    variation: RendererVariationConfig | None = None,
) -> Path:
    """Lay out and render text into a dynamically sized PNG image."""
    active_settings = settings or RenderSettings()
    active_variation = variation or RendererVariationConfig(seed=seed)
    layout = plan_text_layout(text, library, active_settings, active_variation)

    canvas = Image.new("RGB", (layout.width, layout.height), "white")
    draw = ImageDraw.Draw(canvas)

    for glyph in layout.glyphs:
        if glyph.image is None:
            draw_unsupported_character_placeholder(
                draw=draw,
                x=glyph.x,
                y=glyph.y,
                width=glyph.width,
                height=glyph.height,
            )
        else:
            canvas.paste(glyph.image.convert("RGB"), (glyph.x, glyph.y))

    return safe_save_image(canvas, output_path)


def plan_text_layout(
    text: str,
    library: GlyphLibrary,
    settings: RenderSettings | None = None,
    variation: RendererVariationConfig | None = None,
) -> RenderLayout:
    """Plan seeded word wrapping and calculate the required canvas height."""
    active_settings = settings or RenderSettings()
    active_variation = variation or RendererVariationConfig()
    rng = random.Random(active_variation.seed)

    page_width = active_settings.canvas_width
    available_width = page_width - (2 * active_settings.margin_left)
    if page_width <= 0 or available_width <= 0:
        raise ValueError("Page width must be larger than twice the horizontal margin.")

    max_line_width = active_settings.max_line_width or available_width
    max_line_width = min(max_line_width, available_width)
    if max_line_width <= 0:
        raise ValueError("Maximum line width must be greater than zero.")

    left = active_settings.margin_left
    right = left + max_line_width
    cursor_x = left
    cursor_y = active_settings.margin_top
    line_index = 0
    placed: list[PlacedGlyph] = []

    paragraphs = text.split("\n")
    for paragraph_index, paragraph in enumerate(paragraphs):
        words = re.findall(r"\S+", paragraph)

        for word in words:
            plans = [
                _plan_character(character, library, active_settings, active_variation, rng)
                for character in word
            ]
            word_width = _planned_word_width(plans)
            line_has_content = cursor_x > left

            if word_width <= max_line_width:
                required_width = word_width + (
                    active_settings.word_spacing if line_has_content else 0
                )
                if line_has_content and cursor_x + required_width > right:
                    cursor_x = left
                    cursor_y += _line_advance(active_settings, active_variation, rng)
                    line_index += 1
                    line_has_content = False

                if line_has_content:
                    cursor_x += active_settings.word_spacing

                cursor_x = _place_plans(
                    plans,
                    cursor_x,
                    cursor_y,
                    line_index,
                    placed,
                )
                continue

            if line_has_content:
                cursor_x = left
                cursor_y += _line_advance(active_settings, active_variation, rng)
                line_index += 1

            for plan in plans:
                glyph_width = max(plan.advance, plan.width + max(0, plan.x_jitter))
                if cursor_x > left and cursor_x + glyph_width > right:
                    cursor_x = left
                    cursor_y += _line_advance(active_settings, active_variation, rng)
                    line_index += 1
                cursor_x = _place_plans(
                    [plan],
                    cursor_x,
                    cursor_y,
                    line_index,
                    placed,
                )

        if paragraph_index < len(paragraphs) - 1:
            cursor_x = left
            cursor_y += _line_advance(active_settings, active_variation, rng)
            line_index += 1

    content_bottom = max(
        [cursor_y + active_settings.glyph_height]
        + [glyph.y + glyph.height for glyph in placed]
    )
    required_height = (
        content_bottom + active_settings.margin_bottom + active_settings.footer_spacing
    )

    return RenderLayout(
        glyphs=placed,
        width=page_width,
        height=max(1, active_settings.canvas_height, required_height),
        line_count=line_index + 1,
    )


def _plan_character(
    character: str,
    library: GlyphLibrary,
    settings: RenderSettings,
    variation: RendererVariationConfig,
    rng: random.Random,
) -> _GlyphPlan:
    """Select, size, and jitter one glyph using the local seeded RNG."""
    if not library.has_character(character):
        width = settings.placeholder_width
        image = None
    else:
        glyph_record = library.sample_variant(character, rng=rng)
        with Image.open(glyph_record.image_path) as source_image:
            image = source_image.convert("L")
        scale = jitter_scale(variation.scale_jitter, rng)
        target_height = max(1, round(settings.glyph_height * scale))
        image.thumbnail((target_height, target_height))
        width = image.width

    return _GlyphPlan(
        character=character,
        width=width,
        height=image.height if image is not None else settings.glyph_height,
        advance=_glyph_advance(width, settings, variation, rng),
        x_jitter=jitter_int(0, variation.x_jitter_px, rng),
        y_jitter=jitter_int(0, variation.y_jitter_px, rng),
        image=image,
    )


def _planned_word_width(plans: list[_GlyphPlan]) -> int:
    """Return the horizontal extent of a completely planned word."""
    cursor = 0
    right_edge = 0
    for plan in plans:
        right_edge = max(right_edge, cursor + max(0, plan.x_jitter) + plan.width)
        cursor += plan.advance
    return max(cursor, right_edge)


def _place_plans(
    plans: list[_GlyphPlan],
    cursor_x: int,
    cursor_y: int,
    line_index: int,
    placed: list[PlacedGlyph],
) -> int:
    """Place planned glyphs at absolute coordinates and return the next cursor x."""
    for plan in plans:
        placed.append(
            PlacedGlyph(
                character=plan.character,
                x=max(0, cursor_x + plan.x_jitter),
                y=max(0, cursor_y + plan.y_jitter),
                width=plan.width,
                height=plan.height,
                line_index=line_index,
                image=plan.image,
            )
        )
        cursor_x += plan.advance
    return cursor_x


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
