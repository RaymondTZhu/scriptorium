"""Visible provenance labeling for generated handwriting-style images."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from packages.common.images import safe_save_image

def get_default_font(size: int) -> ImageFont.ImageFont:
    """Return a portable default font."""
    try:
        return ImageFont.truetype("arial.ttf", size=size)
    except OSError:
        return ImageFont.load_default()


def add_visible_provenance_footer(
    image_path: Path,
    output_path: Path | None = None,
    label: str = "Generated handwriting-style rendering | Scriptorium",
) -> Path:
    """Add a visible provenance footer to an image.

    Args:
        image_path: Path to the source image.
        output_path: Optional path for the labeled image. If omitted, the
            source image is overwritten.
        label: Footer text to draw.

    Returns:
        Path to the saved labeled image.
    """
    save_path = output_path or image_path

    image = Image.open(image_path).convert("RGB")
    footer_height = 38

    labeled_image = Image.new(
        "RGB",
        (image.width, image.height + footer_height),
        "white",
    )
    labeled_image.paste(image, (0, 0))

    draw = ImageDraw.Draw(labeled_image)
    font = get_default_font(14)

    footer_y = image.height
    draw.rectangle(
        (0, footer_y, labeled_image.width, labeled_image.height),
        fill="white",
        outline="black",
    )
    draw.text((12, footer_y + 11), label, fill="black", font=font)

    return safe_save_image(labeled_image, save_path)
