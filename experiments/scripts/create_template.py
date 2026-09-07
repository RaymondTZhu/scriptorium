"""Generate structured handwriting capture template images.

V1 produces one lowercase page. V2 produces separate pages for lowercase,
uppercase, and digits/punctuation/symbols.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from packages.common.images import safe_save_image
from packages.common.paths import PROJECT_ROOT, TEMPLATES_DIR


TEMPLATE_METADATA_PATH = TEMPLATES_DIR / "template_v2.json"


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


def draw_header(
    draw: ImageDraw.ImageDraw,
    metadata: dict,
    page_number: int = 1,
    page_count: int = 1,
) -> None:
    """Draw the title and consent/provenance notice."""
    title_font = get_default_font(34)
    body_font = get_default_font(18)

    notice = metadata["provenance_notice"]

    draw.text((100, 70), "Scriptorium Handwriting Capture Template", fill="black", font=title_font)
    draw.text(
        (100, 125),
        (
            f"Template: {metadata['template_id']} | Version: {metadata['template_version']} "
            f"| Page: {page_number}/{page_count}"
        ),
        fill="black",
        font=body_font,
    )
    draw.text((100, 165), notice["title"], fill="black", font=body_font)
    draw.text((100, 195), notice["body"], fill="black", font=body_font)
    if metadata.get("instructions"):
        draw.text((100, 225), metadata["instructions"], fill="black", font=body_font)


def draw_template_cells(
    draw: ImageDraw.ImageDraw,
    metadata: dict,
    characters: list[str] | None = None,
    variants_per_character: int | None = None,
) -> None:
    """Draw labeled handwriting cells based on template metadata."""
    layout = metadata["layout"]
    active_characters = characters or flatten_character_sets(metadata["character_sets"])
    active_variants = variants_per_character or metadata["variants_per_character"]

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

    for character in active_characters:
        for variant_index in range(active_variants):
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

    return safe_save_image(image, output_path)


def generate_template_pages(metadata_path: Path, output_dir: Path = TEMPLATES_DIR) -> list[Path]:
    """Generate all PNG pages described by a template metadata file."""
    metadata = load_template_metadata(metadata_path)
    pages = metadata.get("pages")

    if not pages:
        output_path = output_dir / f"{metadata['template_id']}.png"
        return [generate_template_image(metadata_path, output_path)]

    page = metadata["page"]
    output_paths: list[Path] = []

    for page_definition in pages:
        page_number = page_definition["page_number"]
        characters = _page_characters(metadata, page_definition)
        image = Image.new("RGB", (page["width_px"], page["height_px"]), "white")
        draw = ImageDraw.Draw(image)

        draw_header(draw, metadata, page_number=page_number, page_count=len(pages))
        draw_template_cells(
            draw,
            metadata,
            characters=characters,
            variants_per_character=page_definition["variants_per_character"],
        )

        output_path = output_dir / f"{metadata['template_id']}_page_{page_number}.png"
        output_paths.append(safe_save_image(image, output_path))

    return output_paths


def _page_characters(metadata: dict, page_definition: dict) -> list[str]:
    """Flatten the character groups assigned to one metadata page."""
    groups = metadata["character_groups"]
    return flatten_character_sets(
        {name: groups[name] for name in page_definition["character_groups"]}
    )


def parse_args() -> argparse.Namespace:
    """Parse template generation arguments."""
    parser = argparse.ArgumentParser(description="Generate handwriting capture template pages.")
    parser.add_argument(
        "--template-metadata",
        type=Path,
        default=TEMPLATE_METADATA_PATH,
        help="Template metadata JSON. Defaults to template_v2.json.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=TEMPLATES_DIR,
        help="Directory for generated template PNG pages.",
    )
    return parser.parse_args()


def main() -> None:
    """Generate the configured template image pages."""
    args = parse_args()
    output_paths = generate_template_pages(args.template_metadata, args.output_dir)

    for output_path in output_paths:
        try:
            display_path = output_path.relative_to(PROJECT_ROOT)
        except ValueError:
            display_path = output_path
        print(f"Generated template image: {display_path}")


if __name__ == "__main__":
    main()
