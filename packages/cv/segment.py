"""Grid segmentation helpers for structured handwriting templates."""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

import cv2
import numpy as np

from packages.common.types import BoundingBox
from packages.common.paths import TEMPLATES_DIR


V1_TEMPLATE_METADATA_PATH = TEMPLATES_DIR / "template_v1.json"
V2_TEMPLATE_METADATA_PATH = TEMPLATES_DIR / "template_v2.json"


def load_template_metadata(path: Path | None = None) -> dict:
    """Load template metadata from disk."""
    metadata_path = path or V1_TEMPLATE_METADATA_PATH

    with metadata_path.open("r", encoding="utf-8") as file:
        return json.load(file)


def select_template_metadata_path(
    metadata_path: Path | None,
    *,
    multi_page: bool,
) -> Path:
    """Select V2 metadata for page inputs and preserve the V1 single-page default."""
    if metadata_path is not None:
        return metadata_path

    return V2_TEMPLATE_METADATA_PATH if multi_page else V1_TEMPLATE_METADATA_PATH


def validate_template_input_count(
    metadata: dict,
    input_count: int,
    metadata_path: Path,
) -> None:
    """Ensure the number of input images matches the selected template metadata."""
    pages = get_template_pages(metadata)

    if input_count > 1 and len(pages) == 1:
        raise ValueError(
            f"Multiple input pages were provided ({input_count}), but selected metadata "
            f"'{metadata_path}' appears to be single-page/V1. Use "
            "--template-metadata templates/template_v2.json."
        )

    if input_count != len(pages):
        raise ValueError(
            f"Template {metadata['template_id']} requires {len(pages)} input page(s); "
            f"received {input_count}."
        )


def flatten_character_sets(character_sets: dict[str, str]) -> list[str]:
    """Flatten template character sets into one ordered character list."""
    characters: list[str] = []

    for character_group in character_sets.values():
        characters.extend(list(character_group))

    return characters


def get_template_pages(metadata: dict) -> list[dict]:
    """Return normalized page definitions for V1 or multi-page metadata."""
    if "pages" in metadata:
        return list(metadata["pages"])

    return [
        {
            "page_number": 1,
            "name": "default",
            "characters": flatten_character_sets(metadata["character_sets"]),
            "variants_per_character": metadata["variants_per_character"],
        }
    ]


def get_page_characters(metadata: dict, page: dict) -> list[str]:
    """Return the ordered characters assigned to one template page."""
    if "characters" in page:
        return list(page["characters"])

    character_groups = metadata["character_groups"]
    return flatten_character_sets(
        {group_name: character_groups[group_name] for group_name in page["character_groups"]}
    )


def iter_template_cells(metadata: dict, page_number: int | None = None) -> list[dict]:
    """Return metadata records for expected cells on one or all pages."""
    layout = metadata["layout"]
    columns = layout["columns"]
    cell_width = layout["cell_width_px"]
    cell_height = layout["cell_height_px"]
    gap_x = layout["cell_gap_x_px"]
    gap_y = layout["cell_gap_y_px"]
    margin_left = layout["margin_left_px"]
    margin_top = layout["margin_top_px"]

    pages = get_template_pages(metadata)
    if page_number is not None:
        pages = [page for page in pages if page["page_number"] == page_number]
        if not pages:
            raise ValueError(f"Unknown template page number: {page_number}")

    cells: list[dict] = []

    for page in pages:
        characters = get_page_characters(metadata, page)
        variants_per_character = page["variants_per_character"]
        cell_index = 0

        for character in characters:
            for variant_index in range(variants_per_character):
                row = cell_index // columns
                column = cell_index % columns

                x = margin_left + column * (cell_width + gap_x)
                y = margin_top + row * (cell_height + gap_y)

                bbox = BoundingBox(
                    x=x,
                    y=y,
                    width=cell_width,
                    height=cell_height,
                )

                cells.append(
                    {
                        "character": character,
                        "variant_id": variant_index + 1,
                        "page_number": page["page_number"],
                        "cell_index": cell_index,
                        "row": row,
                        "column": column,
                        "bbox": bbox,
                    }
                )

                cell_index += 1

    return cells


def crop_bbox(image: np.ndarray, bbox: BoundingBox) -> np.ndarray:
    """Crop a bounding box from an image."""
    return image[bbox.y : bbox.y + bbox.height, bbox.x : bbox.x + bbox.width]


def crop_handwriting_region(cell_image: np.ndarray, label_height_px: int) -> np.ndarray:
    """Remove the printed label area from a template cell crop."""
    return cell_image[label_height_px:, :]


def serialize_bbox(bbox: BoundingBox) -> dict[str, int]:
    """Convert a BoundingBox dataclass into a JSON-serializable dictionary."""
    return asdict(bbox)


def save_crop(crop: np.ndarray, output_path: Path) -> Path:
    """Save a non-empty image crop to disk."""
    crop_shape = getattr(crop, "shape", None)
    is_invalid = (
        crop is None
        or crop_shape is None
        or len(crop_shape) < 2
        or crop_shape[0] <= 0
        or crop_shape[1] <= 0
    )
    if is_invalid:
        raise ValueError(
            f"Cannot save empty crop to '{output_path}'; crop shape: {crop_shape!r}."
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    if not cv2.imwrite(str(output_path), crop):
        raise OSError(f"OpenCV could not save crop to '{output_path}'.")

    return output_path
