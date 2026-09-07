"""Basic image preprocessing utilities for Scriptorium.

This module contains the first computer vision stage of the V1 pipeline:
loading an image, converting it to grayscale, and producing a thresholded
binary image for later template segmentation and glyph extraction.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

from packages.common.images import safe_save_image


@dataclass(frozen=True)
class PageNormalizationResult:
    """Details about one normalized template page."""

    input_path: Path
    output_path: Path
    original_size: tuple[int, int]
    expected_size: tuple[int, int]
    resized: bool


def normalize_template_page(
    input_path: Path,
    output_path: Path,
    expected_width: int,
    expected_height: int,
) -> PageNormalizationResult:
    """Copy or resize a template page to its metadata-defined dimensions."""
    expected_size = (expected_width, expected_height)

    with Image.open(input_path) as source_image:
        original_size = source_image.size
        if original_size == expected_size:
            normalized_image = source_image.copy()
        else:
            normalized_image = source_image.resize(
                expected_size,
                resample=Image.Resampling.LANCZOS,
            )

    safe_save_image(normalized_image, output_path)

    return PageNormalizationResult(
        input_path=input_path,
        output_path=output_path,
        original_size=original_size,
        expected_size=expected_size,
        resized=original_size != expected_size,
    )


def load_image(image_path: Path) -> np.ndarray:
    """Load an image from disk using OpenCV.

    OpenCV loads color images in BGR channel order by default.

    Args:
        image_path: Path to the input image.

    Returns:
        Loaded image as a NumPy array.

    Raises:
        FileNotFoundError: If OpenCV cannot load the image.
    """
    image = cv2.imread(str(image_path))

    if image is None:
        raise FileNotFoundError(f"Could not load image: {image_path}")

    return image


def to_grayscale(image: np.ndarray) -> np.ndarray:
    """Convert a BGR image to grayscale.

    Args:
        image: Input image in OpenCV BGR format.

    Returns:
        Grayscale image as a two-dimensional NumPy array.
    """
    return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)


def apply_light_blur(gray_image: np.ndarray) -> np.ndarray:
    """Apply a small Gaussian blur before thresholding.

    A light blur reduces small image noise that can interfere with thresholding.
    """
    return cv2.GaussianBlur(gray_image, (5, 5), 0)


def adaptive_threshold(gray_image: np.ndarray) -> np.ndarray:
    """Convert a grayscale image to a binary image.

    Output convention:
    - dark handwriting/template pixels remain dark
    - light background pixels become white
    """
    blurred = apply_light_blur(gray_image)

    return cv2.adaptiveThreshold(
        blurred,
        maxValue=255,
        adaptiveMethod=cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        thresholdType=cv2.THRESH_BINARY,
        blockSize=31,
        C=11,
    )


def preprocess_image(input_path: Path, output_path: Path) -> Path:
    """Run the basic preprocessing pipeline and save the binary image.

    Args:
        input_path: Path to the source handwriting template image.
        output_path: Path where the processed binary image should be saved.

    Returns:
        Path to the saved binary image.
    """
    image = load_image(input_path)
    gray = to_grayscale(image)
    binary = adaptive_threshold(gray)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(output_path), binary)

    return output_path
