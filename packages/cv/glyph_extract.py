"""Glyph extraction from structured handwriting template cells."""

from __future__ import annotations

import json
from pathlib import Path

import cv2

from packages.common.paths import GLYPH_DATA_DIR
from packages.cv.quality import score_crop_quality, trim_to_ink_bounding_box
from packages.cv.segment import (
    crop_bbox,
    crop_handwriting_region,
    iter_template_cells,
    load_template_metadata,
    save_crop,
    serialize_bbox,
)


def extract_glyphs_from_template(
    input_path: Path,
    user_id: str,
    output_dir: Path | None = None,
    metadata_path: Path | None = None,
) -> Path:
    """Extract handwriting-region crops from all expected template cells.

    Args:
        input_path: Path to the completed or blank template image.
        user_id: Identifier for the sample owner.
        output_dir: Optional output directory. Defaults to `data/glyphs/<user_id>`.
        metadata_path: Optional template metadata path.

    Returns:
        Path to the written glyph manifest JSON file.
    """
    metadata = load_template_metadata(metadata_path)
    layout = metadata["layout"]
    label_height = layout["label_height_px"]

    image = cv2.imread(str(input_path), cv2.IMREAD_GRAYSCALE)

    if image is None:
        raise FileNotFoundError(f"Could not load input image: {input_path}")

    user_output_dir = output_dir or GLYPH_DATA_DIR / user_id
    user_output_dir.mkdir(parents=True, exist_ok=True)

    records: list[dict] = []

    for cell in iter_template_cells(metadata):
        character = cell["character"]
        variant_id = cell["variant_id"]
        bbox = cell["bbox"]

        full_cell_crop = crop_bbox(image, bbox)
        handwriting_crop = crop_handwriting_region(full_cell_crop, label_height)
        trimmed_crop, ink_bbox = trim_to_ink_bounding_box(handwriting_crop)
        quality = score_crop_quality(handwriting_crop)

        safe_character = make_safe_character_name(character)
        crop_filename = f"{safe_character}_variant_{variant_id}.png"
        crop_path = user_output_dir / crop_filename

        save_crop(trimmed_crop, crop_path)

        records.append(
            {
                "user_id": user_id,
                "character": character,
                "variant_id": variant_id,
                "image_path": str(crop_path),
                "cell_bbox": serialize_bbox(bbox),
                "original_bbox": serialize_bbox(bbox),
                "ink_bbox": serialize_bbox(ink_bbox) if ink_bbox is not None else None,
                "width": int(trimmed_crop.shape[1]),
                "height": int(trimmed_crop.shape[0]),
                "has_ink": quality["has_ink"],
                "quality": quality,
            }
        )

    manifest = {
        "user_id": user_id,
        "template_id": metadata["template_id"],
        "template_version": metadata["template_version"],
        "source_image": str(input_path),
        "glyph_count": len(records),
        "glyphs": records,
    }

    manifest_path = user_output_dir / "glyph_manifest.json"

    with manifest_path.open("w", encoding="utf-8") as file:
        json.dump(manifest, file, indent=2)

    return manifest_path


def make_safe_character_name(character: str) -> str:
    """Convert a character into a filesystem-safe name."""
    special_names = {
        ".": "period",
        ",": "comma",
        "!": "exclamation",
        "?": "question",
        ";": "semicolon",
        ":": "colon",
        "'": "apostrophe",
        '"': "quote",
        "-": "dash",
        "(": "left_paren",
        ")": "right_paren",
        " ": "space",
    }

    if character in special_names:
        return special_names[character]

    if character.isupper():
        return f"upper_{character.lower()}"

    if character.islower() or character.isdigit():
        return character

    return f"char_{ord(character)}"
