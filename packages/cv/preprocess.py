"""Basic image preprocessing utilities for Scriptorium.

This module contains the first computer vision stage of the V1 pipeline:
loading an image, converting it to grayscale, and producing a thresholded
binary image for later template segmentation and glyph extraction.
"""

from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np


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
