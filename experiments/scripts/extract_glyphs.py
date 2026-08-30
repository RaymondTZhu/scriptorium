"""Extract glyph crops from a structured handwriting template image.

Example:
    python experiments/scripts/extract_glyphs.py \
        --input templates/template_v1.png \
        --user-id user_001
"""

from __future__ import annotations

import argparse
from pathlib import Path

from packages.common.paths import GLYPH_DATA_DIR, ensure_project_dirs
from packages.cv.glyph_extract import extract_glyphs_from_template


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments for glyph extraction."""
    parser = argparse.ArgumentParser(
        description="Extract glyph crops from a structured handwriting template image."
    )

    parser.add_argument(
        "--input",
        required=True,
        type=Path,
        help="Path to the completed handwriting template image.",
    )

    parser.add_argument(
        "--user-id",
        default="user_001",
        help="Identifier for the handwriting sample owner.",
    )

    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Optional output directory. Defaults to data/glyphs/<user-id>.",
    )

    return parser.parse_args()


def main() -> None:
    """Run glyph extraction from the command line."""
    args = parse_args()
    ensure_project_dirs()

    output_dir = args.output_dir or GLYPH_DATA_DIR / args.user_id

    manifest_path = extract_glyphs_from_template(
        input_path=args.input,
        user_id=args.user_id,
        output_dir=output_dir,
    )

    print(f"Saved glyph manifest: {manifest_path}")


if __name__ == "__main__":
    main()
