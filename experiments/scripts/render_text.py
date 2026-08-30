"""Render text using an extracted glyph manifest.

Example:
    python experiments/scripts/render_text.py \
        --manifest data/glyphs/user_001/glyph_manifest.json \
        --text "hello world"
"""

from __future__ import annotations

import argparse
from pathlib import Path

from packages.common.paths import OUTPUT_DATA_DIR, ensure_project_dirs
from packages.renderer.glyph_library import load_glyph_library
from packages.renderer.layout import RenderSettings
from packages.renderer.render_png import render_text_to_image


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments for text rendering."""
    parser = argparse.ArgumentParser(
        description="Render typed text using extracted handwriting glyphs."
    )

    parser.add_argument(
        "--manifest",
        required=True,
        type=Path,
        help="Path to a glyph manifest JSON file.",
    )

    parser.add_argument(
        "--text",
        required=True,
        help="Text to render. V1 works best with lowercase letters and spaces.",
    )

    parser.add_argument(
        "--output",
        type=Path,
        default=OUTPUT_DATA_DIR / "rendered_text.png",
        help="Path where the rendered image should be saved.",
    )

    parser.add_argument(
        "--seed",
        type=int,
        default=7,
        help="Random seed for reproducible glyph variant sampling.",
    )

    return parser.parse_args()


def main() -> None:
    """Render text from the command line."""
    args = parse_args()
    ensure_project_dirs()

    library = load_glyph_library(args.manifest)
    settings = RenderSettings()

    output_path = render_text_to_image(
        text=args.text,
        library=library,
        output_path=args.output,
        settings=settings,
        seed=args.seed,
    )

    print(f"Saved rendered text image: {output_path}")


if __name__ == "__main__":
    main()
