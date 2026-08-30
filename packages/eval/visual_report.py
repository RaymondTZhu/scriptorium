"""Visual reporting helpers for inspecting Scriptorium outputs."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from packages.renderer.glyph_library import GlyphLibrary


def get_default_font(size: int) -> ImageFont.ImageFont:
    """Return a portable default font."""
    try:
        return ImageFont.truetype("arial.ttf", size=size)
    except OSError:
        return ImageFont.load_default()


def create_glyph_contact_sheet(
    library: GlyphLibrary,
    output_path: Path,
    cell_width: int = 120,
    cell_height: int = 100,
    columns: int = 6,
) -> Path:
    """Create a contact sheet image for visually inspecting extracted glyphs."""
    glyphs = library.glyphs

    if not glyphs:
        raise ValueError("Cannot create contact sheet from an empty glyph library.")

    label_height = 24
    rows = (len(glyphs) + columns - 1) // columns
    sheet_width = columns * cell_width
    sheet_height = rows * (cell_height + label_height)

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

        glyph_image = Image.open(glyph.image_path).convert("L")
        glyph_image.thumbnail((cell_width - 12, cell_height - 12))

        paste_x = x0 + (cell_width - glyph_image.width) // 2
        paste_y = y0 + label_height + (cell_height - glyph_image.height) // 2

        sheet.paste(glyph_image.convert("RGB"), (paste_x, paste_y))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(output_path)

    return output_path
