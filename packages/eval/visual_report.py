"""Visual reporting helpers for inspecting Scriptorium outputs."""

from __future__ import annotations

import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from packages.common.images import safe_save_image
from packages.renderer.glyph_library import GlyphLibrary


def get_default_font(size: int) -> ImageFont.ImageFont:
    """Return a portable default font."""
    try:
        return ImageFont.truetype("arial.ttf", size=size)
    except OSError:
        return ImageFont.load_default()


def create_glyph_contact_sheet(
    library: GlyphLibrary,
    output_path: Path | str,
    cell_width: int = 120,
    cell_height: int = 100,
    columns: int = 6,
) -> Path:
    """Create a contact sheet image for visually inspecting extracted glyphs."""
    output_path = Path(output_path)
    glyphs = library.glyphs

    if not glyphs:
        raise ValueError("Cannot create contact sheet from an empty glyph library.")

    if len(glyphs) > 120:
        columns = max(columns, 12)
        cell_width = min(cell_width, 110)
        cell_height = min(cell_height, 85)

    label_height = 24
    rows = (len(glyphs) + columns - 1) // columns
    sheet_width = columns * cell_width
    sheet_height = rows * (cell_height + label_height)

    if sheet_width <= 0 or sheet_height <= 0:
        raise ValueError(
            "Contact sheet dimensions must be positive; "
            f"calculated size=({sheet_width}, {sheet_height})."
        )

    sheet = Image.new("RGB", (sheet_width, sheet_height), "white")
    draw = ImageDraw.Draw(sheet)
    font = get_default_font(14)

    for index, glyph in enumerate(glyphs):
        row = index // columns
        column = index % columns

        x0 = column * cell_width
        y0 = row * (cell_height + label_height)

        label = f"{glyph.character!r} v{glyph.variant_id}"

        draw.rectangle(
            (x0, y0, x0 + cell_width - 1, y0 + cell_height + label_height - 1),
            outline="black",
            width=1,
        )
        draw.text((x0 + 5, y0 + 4), label, fill="black", font=font)

        with Image.open(glyph.image_path) as source_image:
            glyph_image = source_image.convert("L")
        glyph_image.thumbnail((cell_width - 12, cell_height - 12))

        paste_x = x0 + (cell_width - glyph_image.width) // 2
        paste_y = y0 + label_height + (cell_height - glyph_image.height) // 2

        sheet.paste(glyph_image.convert("RGB"), (paste_x, paste_y))

    return safe_save_image(sheet, output_path)


def create_visual_report(
    template_image_path: Path,
    contact_sheet_path: Path,
    rendered_output_path: Path,
    generation_record_path: Path | None,
    output_path: Path,
) -> Path:
    """Combine key V1 artifacts into one vertically stacked review image."""
    max_preview_width = 960
    max_preview_height = 700
    horizontal_padding = 20
    section_gap = 24
    title_height = 112
    section_title_height = 30

    previews = [
        (
            "Template image preview",
            _load_preview(template_image_path, max_preview_width, max_preview_height),
        ),
        (
            "Glyph contact sheet preview",
            _load_preview(contact_sheet_path, max_preview_width, max_preview_height),
        ),
        (
            "Rendered output preview",
            _load_preview(rendered_output_path, max_preview_width, max_preview_height),
        ),
    ]
    generation_summary = _read_generation_summary(generation_record_path)

    section_heights = [
        section_title_height + (preview.height if preview is not None else 44)
        for _, preview in previews
    ]
    metadata_height = section_title_height + max(44, len(generation_summary) * 22)
    report_width = max_preview_width + horizontal_padding * 2
    report_height = (
        title_height
        + sum(section_heights)
        + metadata_height
        + section_gap * (len(previews) + 1)
        + horizontal_padding
    )

    report = Image.new("RGB", (report_width, report_height), "white")
    draw = ImageDraw.Draw(report)
    title_font = get_default_font(28)
    section_font = get_default_font(18)
    body_font = get_default_font(14)

    draw.text((horizontal_padding, 20), "Scriptorium V1 Visual Evaluation Report", "black", title_font)
    draw.text(
        (horizontal_padding, 62),
        "Generated/synthetic output for consent-based research and visual review.",
        "black",
        body_font,
    )

    cursor_y = title_height

    for section_title, preview in previews:
        draw.text((horizontal_padding, cursor_y), section_title, "black", section_font)
        cursor_y += section_title_height

        if preview is None:
            draw.rectangle(
                (horizontal_padding, cursor_y, report_width - horizontal_padding, cursor_y + 43),
                outline="gray",
            )
            draw.text((horizontal_padding + 10, cursor_y + 13), "Artifact not available", "gray", body_font)
            cursor_y += 44
        else:
            paste_x = (report_width - preview.width) // 2
            report.paste(preview, (paste_x, cursor_y))
            cursor_y += preview.height

        cursor_y += section_gap

    draw.text((horizontal_padding, cursor_y), "Generation record summary", "black", section_font)
    cursor_y += section_title_height

    if generation_summary:
        for line in generation_summary:
            draw.text((horizontal_padding, cursor_y), line, "black", body_font)
            cursor_y += 22
    else:
        draw.text((horizontal_padding, cursor_y + 13), "Generation record not available", "gray", body_font)

    return safe_save_image(report, output_path)


def _load_preview(image_path: Path, max_width: int, max_height: int) -> Image.Image | None:
    """Load and resize an image preview while preserving its aspect ratio."""
    if not image_path.exists():
        return None

    with Image.open(image_path) as source_image:
        preview = source_image.convert("RGB")

    preview.thumbnail((max_width, max_height))
    return preview


def _read_generation_summary(record_path: Path | None) -> list[str]:
    """Read selected generation-record fields for display in a report."""
    if record_path is None or not record_path.exists():
        return []

    try:
        with record_path.open("r", encoding="utf-8") as file:
            record = json.load(file)
    except (OSError, json.JSONDecodeError):
        return ["Generation record could not be read."]

    summary_fields = (
        ("Run ID", "run_id"),
        ("User ID", "user_id"),
        ("Created at (UTC)", "created_at_utc"),
        ("Renderer version", "renderer_version"),
        ("Template version", "template_version"),
        ("Provenance enabled", "provenance_enabled"),
    )
    return [f"{label}: {record[key]}" for label, key in summary_fields if key in record]
