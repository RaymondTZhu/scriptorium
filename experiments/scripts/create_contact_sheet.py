"""Create a glyph contact sheet from an extracted glyph manifest.

Example:
    python experiments/scripts/create_contact_sheet.py \
        --manifest data/glyphs/user_001/glyph_manifest.json
"""

from __future__ import annotations

import argparse
from pathlib import Path

from packages.eval.visual_report import create_glyph_contact_sheet
from packages.renderer.glyph_library import load_glyph_library


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments for contact sheet generation."""
    parser = argparse.ArgumentParser(
        description="Create a contact sheet for visually inspecting extracted glyphs."
    )

    parser.add_argument(
        "--manifest",
        required=True,
        type=Path,
        help="Path to a glyph manifest JSON file.",
    )

    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Optional output path. Defaults to glyph_contact_sheet.png next to the manifest.",
    )

    return parser.parse_args()


def main() -> None:
    """Create a contact sheet from the provided glyph manifest."""
    args = parse_args()

    output_path = args.output or args.manifest.parent / "glyph_contact_sheet.png"

    library = load_glyph_library(args.manifest)
    contact_sheet_path = create_glyph_contact_sheet(
        library=library,
        output_path=output_path,
    )

    print(f"Saved glyph contact sheet: {contact_sheet_path}")


if __name__ == "__main__":
    main()
