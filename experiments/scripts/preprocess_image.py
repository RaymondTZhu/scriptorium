"""Run basic preprocessing on a handwriting template image.

Example:
    python experiments/scripts/preprocess_image.py \
        --input templates/template_v2_page_1.png \
        --output data/processed/template_v2_page_1_binary.png
"""

from __future__ import annotations

import argparse
from pathlib import Path

from packages.common.paths import PROCESSED_DATA_DIR, ensure_project_dirs
from packages.cv.preprocess import preprocess_image


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments for the preprocessing script."""
    parser = argparse.ArgumentParser(
        description="Preprocess a handwriting template image into a binary image."
    )

    parser.add_argument(
        "--input",
        required=True,
        type=Path,
        help="Path to the input handwriting template image.",
    )

    parser.add_argument(
        "--output",
        default=PROCESSED_DATA_DIR / "binary.png",
        type=Path,
        help="Path where the processed binary image should be saved.",
    )

    return parser.parse_args()


def main() -> None:
    """Run image preprocessing from the command line."""
    args = parse_args()
    ensure_project_dirs()

    output_path = preprocess_image(
        input_path=args.input,
        output_path=args.output,
    )

    print(f"Saved preprocessed image: {output_path}")


if __name__ == "__main__":
    main()
