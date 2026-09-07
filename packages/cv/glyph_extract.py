"""Glyph extraction from structured handwriting template cells."""

from __future__ import annotations

import json
import warnings
from pathlib import Path

import cv2

from packages.common.paths import GLYPH_DATA_DIR, sanitize_path_component
from packages.common.types import BoundingBox
from packages.cv.quality import score_crop_quality, trim_to_ink_bounding_box
from packages.cv.segment import (
    crop_handwriting_region,
    get_template_pages,
    iter_template_cells,
    load_template_metadata,
    save_crop,
    select_template_metadata_path,
    serialize_bbox,
    validate_template_input_count,
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
    return extract_glyphs_from_template_pages(
        input_paths=[input_path],
        user_id=user_id,
        output_dir=output_dir,
        metadata_path=metadata_path,
    )


def extract_glyphs_from_template_pages(
    input_paths: list[Path],
    user_id: str,
    output_dir: Path | None = None,
    metadata_path: Path | None = None,
) -> Path:
    """Extract glyphs from one V1 page or an ordered set of V2 pages."""
    active_metadata_path = select_template_metadata_path(
        metadata_path,
        multi_page=len(input_paths) > 1,
    )
    metadata = load_template_metadata(active_metadata_path)
    layout = metadata["layout"]
    label_height = layout["label_height_px"]
    pages = get_template_pages(metadata)

    validate_template_input_count(metadata, len(input_paths), active_metadata_path)

    user_output_dir = output_dir or GLYPH_DATA_DIR / sanitize_path_component(user_id)
    user_output_dir.mkdir(parents=True, exist_ok=True)

    records: list[dict] = []

    for input_path, page in zip(input_paths, pages, strict=True):
        page_number = page["page_number"]
        image = cv2.imread(str(input_path), cv2.IMREAD_GRAYSCALE)

        if image is None:
            raise FileNotFoundError(f"Could not load input image: {input_path}")

        for cell in iter_template_cells(metadata, page_number=page_number):
            character = cell["character"]
            variant_id = cell["variant_id"]
            bbox = cell["bbox"]

            safe_character = make_safe_character_name(character)
            crop_filename = f"{safe_character}_variant_{variant_id}.png"
            crop_path = user_output_dir / crop_filename

            clamped_bbox = clamp_bbox_to_image(bbox, image.shape)
            if clamped_bbox.width <= 0 or clamped_bbox.height <= 0:
                _warn_invalid_crop(
                    page_number=page_number,
                    character=character,
                    variant_id=variant_id,
                    original_bbox=bbox,
                    clamped_bbox=clamped_bbox,
                    image_shape=image.shape,
                )
                records.append(
                    _blank_glyph_record(
                        user_id=user_id,
                        character=character,
                        variant_id=variant_id,
                        page_number=page_number,
                        template_version=metadata["template_version"],
                        crop_path=crop_path,
                        original_bbox=bbox,
                        clamped_bbox=clamped_bbox,
                    )
                )
                continue

            full_cell_crop = image[
                clamped_bbox.y : clamped_bbox.y + clamped_bbox.height,
                clamped_bbox.x : clamped_bbox.x + clamped_bbox.width,
            ]
            handwriting_crop = crop_handwriting_region(full_cell_crop, label_height)
            if handwriting_crop.shape[0] <= 0 or handwriting_crop.shape[1] <= 0:
                _warn_invalid_crop(
                    page_number=page_number,
                    character=character,
                    variant_id=variant_id,
                    original_bbox=bbox,
                    clamped_bbox=clamped_bbox,
                    image_shape=image.shape,
                )
                records.append(
                    _blank_glyph_record(
                        user_id=user_id,
                        character=character,
                        variant_id=variant_id,
                        page_number=page_number,
                        template_version=metadata["template_version"],
                        crop_path=crop_path,
                        original_bbox=bbox,
                        clamped_bbox=clamped_bbox,
                    )
                )
                continue

            trimmed_crop, ink_bbox = trim_to_ink_bounding_box(handwriting_crop)
            quality = score_crop_quality(handwriting_crop)

            save_crop(trimmed_crop, crop_path)

            records.append(
                {
                    "user_id": user_id,
                    "character": character,
                    "variant_id": variant_id,
                    "page_number": page_number,
                    "template_version": metadata["template_version"],
                    "image_path": str(crop_path),
                    "cell_bbox": serialize_bbox(bbox),
                    "original_bbox": serialize_bbox(bbox),
                    "clamped_bbox": serialize_bbox(clamped_bbox),
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
        "source_image": str(input_paths[0]) if len(input_paths) == 1 else None,
        "source_images": [str(path) for path in input_paths],
        "page_count": len(pages),
        "glyph_count": len(records),
        "glyphs": records,
    }

    manifest_path = user_output_dir / "glyph_manifest.json"

    with manifest_path.open("w", encoding="utf-8") as file:
        json.dump(manifest, file, indent=2)

    return manifest_path


def clamp_bbox_to_image(
    bbox: BoundingBox,
    image_shape: tuple[int, ...],
) -> BoundingBox:
    """Clamp a bounding box to an image, retaining zero-sized invalid bounds."""
    image_height, image_width = image_shape[:2]
    x1 = min(max(bbox.x, 0), image_width)
    y1 = min(max(bbox.y, 0), image_height)
    x2 = min(max(bbox.x + bbox.width, 0), image_width)
    y2 = min(max(bbox.y + bbox.height, 0), image_height)

    return BoundingBox(
        x=x1,
        y=y1,
        width=max(0, x2 - x1),
        height=max(0, y2 - y1),
    )


def _warn_invalid_crop(
    *,
    page_number: int,
    character: str,
    variant_id: int,
    original_bbox: BoundingBox,
    clamped_bbox: BoundingBox,
    image_shape: tuple[int, ...],
) -> None:
    """Warn that one invalid glyph crop is being retained as a blank record."""
    warnings.warn(
        "Skipping invalid glyph crop: "
        f"page={page_number}, character={character!r}, variant={variant_id}, "
        f"original_bbox={serialize_bbox(original_bbox)}, "
        f"clamped_bbox={serialize_bbox(clamped_bbox)}, image_shape={image_shape}.",
        RuntimeWarning,
        stacklevel=2,
    )


def _blank_glyph_record(
    *,
    user_id: str,
    character: str,
    variant_id: int,
    page_number: int,
    template_version: str,
    crop_path: Path,
    original_bbox: BoundingBox,
    clamped_bbox: BoundingBox,
) -> dict:
    """Create a non-renderable manifest record for an invalid glyph cell."""
    return {
        "user_id": user_id,
        "character": character,
        "variant_id": variant_id,
        "page_number": page_number,
        "template_version": template_version,
        "image_path": str(crop_path),
        "cell_bbox": serialize_bbox(original_bbox),
        "original_bbox": serialize_bbox(original_bbox),
        "clamped_bbox": serialize_bbox(clamped_bbox),
        "ink_bbox": None,
        "width": 0,
        "height": 0,
        "has_ink": False,
        "quality": {
            "dark_pixel_ratio": 0.0,
            "probably_empty": True,
            "has_ink": False,
        },
    }


def make_safe_character_name(character: str) -> str:
    """Convert one character into a portable Unicode-codepoint filename stem."""
    if len(character) != 1:
        raise ValueError("Glyph filenames require exactly one character.")

    return f"U{ord(character):04X}"
