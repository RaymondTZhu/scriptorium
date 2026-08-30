"""Grid segmentation helpers for structured handwriting templates."""

from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
import json

import cv2
import numpy as np

from packages.common.types import BoundingBox
from packages.common.paths import TEMPLATES_DIR


def load_template_metadata(path: Path | None = None) -> dict:
    """Load template metadata from disk."""
    metadata_path = path or TEMPLATES_DIR / "template_v1.json"

    with metadata_path.open("r", encoding="utf-8") as file:
        return json.load(file)


def flatten_character_sets(character_sets: dict[str, str]) -> list[str]:
    """Flatten template character sets into one ordered character list."""
    characters: list[str] = []

    for character_group in character_sets.values():
        characters.extend(list(character_group))

    return characters


def iter_template_cells(metadata: dict) -> list[dict]:
    """Return metadata records for every expected template cell."""
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

    cells: list[dict] = []
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
    """Save an image crop to disk."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(output_path), crop)
    return output_path
