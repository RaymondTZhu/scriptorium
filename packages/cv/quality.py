"""Simple image quality helpers for extracted glyph crops."""

from __future__ import annotations

import numpy as np


def estimate_dark_pixel_ratio(image: np.ndarray, dark_threshold: int = 200) -> float:
    """Estimate the fraction of pixels that are dark enough to contain ink.

    This is a simple proxy metric. It is not a perfect handwriting detector,
    but it helps identify completely empty or nearly empty crops.
    """
    if image.size == 0:
        return 0.0

    if image.ndim == 3:
        image = image.mean(axis=2)

    dark_pixels = image < dark_threshold
    return float(dark_pixels.sum() / dark_pixels.size)


def is_probably_empty(image: np.ndarray, min_dark_ratio: float = 0.002) -> bool:
    """Return True when a crop appears to contain almost no dark pixels."""
    return estimate_dark_pixel_ratio(image) < min_dark_ratio


def score_crop_quality(image: np.ndarray) -> dict[str, float | bool]:
    """Return basic quality information for a glyph crop."""
    dark_ratio = estimate_dark_pixel_ratio(image)

    return {
        "dark_pixel_ratio": dark_ratio,
        "probably_empty": dark_ratio < 0.002,
    }
