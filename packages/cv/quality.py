"""Simple image quality helpers for extracted glyph crops."""

from __future__ import annotations

import numpy as np
from PIL import Image

from packages.common.types import BoundingBox


def _to_grayscale_array(image: np.ndarray | Image.Image) -> np.ndarray:
    """Return a two-dimensional grayscale view of an image array."""
    if isinstance(image, Image.Image):
        return np.asarray(image.convert("L"))
    if image.ndim == 3:
        return image.mean(axis=2)
    return image


def detect_ink_bounding_box(
    image: np.ndarray | Image.Image,
    dark_threshold: int = 200,
    padding: int = 4,
    edge_margin: int = 4,
) -> BoundingBox | None:
    """Return a padded bounding box around dark ink pixels.

    A small edge margin prevents the known template cell border from being
    classified as handwriting. The returned coordinates are relative to the
    supplied crop.
    """
    gray_image = _to_grayscale_array(image)
    if gray_image.size == 0:
        return None

    height, width = gray_image.shape
    safe_margin = max(0, min(edge_margin, width // 2, height // 2))
    interior = gray_image[
        safe_margin : height - safe_margin,
        safe_margin : width - safe_margin,
    ]

    dark_y, dark_x = np.where(interior < dark_threshold)
    if dark_x.size == 0 or dark_y.size == 0:
        return None

    min_x = max(safe_margin, int(dark_x.min()) + safe_margin - max(0, padding))
    min_y = max(safe_margin, int(dark_y.min()) + safe_margin - max(0, padding))
    max_x = min(width - safe_margin, int(dark_x.max()) + safe_margin + max(0, padding) + 1)
    max_y = min(height - safe_margin, int(dark_y.max()) + safe_margin + max(0, padding) + 1)

    return BoundingBox(
        x=min_x,
        y=min_y,
        width=max_x - min_x,
        height=max_y - min_y,
    )


def trim_to_ink_bounding_box(
    image: np.ndarray | Image.Image,
    dark_threshold: int = 200,
    padding: int = 4,
    edge_margin: int = 4,
) -> tuple[np.ndarray, BoundingBox | None]:
    """Trim an image to padded ink bounds, preserving blank crops safely."""
    gray_image = _to_grayscale_array(image)
    ink_bbox = detect_ink_bounding_box(
        gray_image,
        dark_threshold=dark_threshold,
        padding=padding,
        edge_margin=edge_margin,
    )
    if ink_bbox is None:
        return gray_image.copy(), None

    trimmed = gray_image[
        ink_bbox.y : ink_bbox.y + ink_bbox.height,
        ink_bbox.x : ink_bbox.x + ink_bbox.width,
    ]
    return trimmed, ink_bbox


def estimate_dark_pixel_ratio(image: np.ndarray, dark_threshold: int = 200) -> float:
    """Estimate the fraction of pixels that are dark enough to contain ink.

    This is a simple proxy metric. It is not a perfect handwriting detector,
    but it helps identify completely empty or nearly empty crops.
    """
    if image.size == 0:
        return 0.0

    image = _to_grayscale_array(image)

    dark_pixels = image < dark_threshold
    return float(dark_pixels.sum() / dark_pixels.size)


def is_probably_empty(image: np.ndarray, min_dark_ratio: float = 0.002) -> bool:
    """Return True when a crop appears to contain almost no dark pixels."""
    return estimate_dark_pixel_ratio(image) < min_dark_ratio


def score_crop_quality(image: np.ndarray) -> dict[str, float | bool]:
    """Return basic quality information for a glyph crop."""
    dark_ratio = estimate_dark_pixel_ratio(image)
    has_ink = detect_ink_bounding_box(image) is not None

    return {
        "dark_pixel_ratio": dark_ratio,
        "probably_empty": not has_ink,
        "has_ink": has_ink,
    }
