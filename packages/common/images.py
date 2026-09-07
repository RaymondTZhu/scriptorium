"""Shared helpers for saving generated Pillow images safely."""

from __future__ import annotations

import os
from pathlib import Path

from PIL import Image


def safe_save_image(image: Image.Image, output_path: Path | str) -> Path:
    """Atomically save a non-empty image through a same-directory temporary file."""
    final_path = Path(output_path)
    temp_path = final_path.with_name(f"{final_path.stem}.tmp{final_path.suffix}")
    image_size = image.size
    image_mode = image.mode

    if image.width <= 0 or image.height <= 0:
        raise ValueError(
            f"Cannot save image with non-positive size {image_size} to {final_path!r}."
        )

    try:
        final_path.parent.mkdir(parents=True, exist_ok=True)
        if temp_path.exists():
            temp_path.unlink()

        image_to_save = image if image.mode == "RGB" else image.convert("RGB")
        image_to_save.save(temp_path)
        os.replace(temp_path, final_path)
    except (OSError, ValueError) as error:
        try:
            if temp_path.exists():
                temp_path.unlink()
        except OSError:
            pass

        resolved_path = final_path.resolve(strict=False)
        resolved_parent = final_path.parent.resolve(strict=False)
        raise OSError(
            "Could not safely save generated image: "
            f"output_path={final_path!r}, resolved_path={str(resolved_path)!r}, "
            f"parent={str(resolved_parent)!r}, parent_exists={final_path.parent.exists()}, "
            f"image_size={image_size}, image_mode={image_mode!r}, error={error}"
        ) from error

    return final_path
