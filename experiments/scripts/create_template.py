"""Generate the V1 handwriting capture template image.

This script reads `templates/template_v1.json` and creates a blank PNG
template that can be filled in with consented handwriting samples.
"""

from __future__ import annotations

import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from packages.common.paths import PROJECT_ROOT, TEMPLATES_DIR


TEMPLATE_METADATA_PATH = TEMPLATES_DIR / "template_v1.json"
TEMPLATE_IMAGE_PATH = TEMPLATES_DIR / "template_v1.png"


def load_template_metadata(path: Path) -> dict:
    """Load template metadata from a JSON file."""
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def flatten_character_sets(character_sets: dict[str, str]) -> list[str]:
    """Flatten configured character sets into a single ordered character list."""
    characters: list[str] = []

    for character_group in character_sets.values():
        characters.extend(list(character_group))

    return characters


def get_default_font(size: int) -> ImageFont.ImageFont:
    """Return a default Pillow font.

    Pillow's built-in default font keeps this script portable because it does
    not depend on a system-specific font file being available.
    """
    try:
        return ImageFont.truetype("arial.ttf", size=size)
    except OSError:
        return ImageFont.load_default()


def draw_header(draw: ImageDraw.ImageDraw, metadata: dict) -> None:
    """Draw the title and consent/provenance notice."""
    title_font = get_default_font(34)
    body_font = get_default_font(18)

    notice = metadata["provenance_notice"]

    draw.text((100, 70), "Scriptorium Handwriting Capture Template", fill="black", font=title_font)
    draw.text(
        (100, 125),
        f"Template: {metadata['template_id']} | Version: {metadata['template_version']}",
        fill="black",
        font=body_font,
    )
    draw.text((100, 165), notice["title"], fill="black", font=body_font)
    draw.text((100, 195), notice["body"], fill="black", font=body_font)


def draw_template_cells(draw: ImageDraw.ImageDraw, metadata: dict) -> None:
    """Draw labeled handwriting cells based on template metadata."""
    layout = metadata["layout"]
    characters = flatten_character_sets(metadata["character_sets"])
    variants_per_character = metadata["variants_per_character"]

    columns = layout["columns"]
    cell_width = layout["cell_width_px"]
    cell_height = layout["cell_height_px"]
    gap_x = layout["cell_gap_x_px"]
    gap_y = layout["cell_gap_y_px"]
    margin_left = layout["margin_left_px"]
    margin_top = layout["margin_top_px"]
    label_height = layout["label_height_px"]

    label_font = get_default_font(16)

    cell_index = 0

    for character in characters:
        for variant_index in range(variants_per_character):
            row = cell_index // columns
            column = cell_index % columns

            x0 = margin_left + column * (cell_width + gap_x)
            y0 = margin_top + row * (cell_height + gap_y)
            x1 = x0 + cell_width
            y1 = y0 + cell_height

            label = f"{repr(character)} variant {variant_index + 1}"

            draw.rectangle((x0, y0, x1, y1), outline="black", width=2)
            draw.line((x0, y0 + label_height, x1, y0 + label_height), fill="black", width=1)
            draw.text((x0 + 8, y0 + 6), label, fill="black", font=label_font)

            cell_index += 1


def generate_template_image(metadata_path: Path, output_path: Path) -> Path:
    """Generate a blank handwriting capture template image."""
    metadata = load_template_metadata(metadata_path)
    page = metadata["page"]

    image = Image.new("RGB", (page["width_px"], page["height_px"]), "white")
    draw = ImageDraw.Draw(image)

    draw_header(draw, metadata)
    draw_template_cells(draw, metadata)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(output_path)

    return output_path


def main() -> None:
    """Generate the configured template image."""
    output_path = generate_template_image(
        metadata_path=TEMPLATE_METADATA_PATH,
        output_path=TEMPLATE_IMAGE_PATH,
    )

    relative_output_path = output_path.relative_to(PROJECT_ROOT)
    print(f"Generated template image: {relative_output_path}")


if __name__ == "__main__":
    main()
