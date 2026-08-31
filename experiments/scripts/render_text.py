"""Render text using an extracted glyph manifest.

Example:
    python experiments/scripts/render_text.py \
        --manifest data/glyphs/user_001/glyph_manifest.json \
        --text "hello world"
"""

from __future__ import annotations

import argparse
from dataclasses import asdict
from pathlib import Path

from packages.common.paths import OUTPUT_DATA_DIR, ensure_project_dirs
from packages.renderer.glyph_library import load_glyph_library
from packages.renderer.layout import RendererVariationConfig, RenderSettings
from packages.renderer.render_png import render_text_to_image
from packages.watermark.metadata import create_run_id, write_generation_manifest
from packages.watermark.visible import add_visible_provenance_footer


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
        "--user-id",
        default="user_001",
        help="Identifier for the handwriting sample owner.",
    )

    parser.add_argument(
        "--seed",
        type=int,
        default=7,
        help="Random seed for reproducible glyph selection and variation.",
    )

    parser.add_argument(
        "--x-jitter-px",
        type=int,
        default=2,
        help="Maximum horizontal glyph-position jitter in pixels.",
    )

    parser.add_argument(
        "--y-jitter-px",
        type=int,
        default=3,
        help="Maximum baseline jitter in pixels.",
    )

    parser.add_argument(
        "--scale-jitter",
        type=float,
        default=0.04,
        help="Maximum proportional glyph-scale jitter.",
    )

    parser.add_argument(
        "--spacing-jitter-px",
        type=int,
        default=2,
        help="Maximum inter-glyph spacing jitter in pixels.",
    )

    parser.add_argument(
        "--line-spacing-jitter-px",
        type=int,
        default=0,
        help="Maximum line-spacing jitter in pixels.",
    )

    parser.add_argument(
        "--disable-visible-provenance",
        action="store_true",
        help="Disable visible footer labeling. JSON manifest is still written.",
    )

    return parser.parse_args()


def main() -> None:
    """Render text from the command line."""
    args = parse_args()
    ensure_project_dirs()

    library = load_glyph_library(args.manifest)
    settings = RenderSettings()
    variation = RendererVariationConfig(
        seed=args.seed,
        x_jitter_px=max(0, args.x_jitter_px),
        y_jitter_px=max(0, args.y_jitter_px),
        scale_jitter=max(0.0, args.scale_jitter),
        spacing_jitter_px=max(0, args.spacing_jitter_px),
        line_spacing_jitter_px=max(0, args.line_spacing_jitter_px),
    )
    run_id = create_run_id()

    output_path = render_text_to_image(
        text=args.text,
        library=library,
        output_path=args.output,
        settings=settings,
        variation=variation,
    )

    if not args.disable_visible_provenance:
        output_path = add_visible_provenance_footer(output_path)

    manifest_path = write_generation_manifest(
        user_id=args.user_id,
        input_text=args.text,
        output_image_path=output_path,
        run_id=run_id,
        extra_fields={
            "glyph_manifest_path": str(args.manifest),
            "visible_provenance_enabled": not args.disable_visible_provenance,
            "renderer_config": asdict(variation),
        },
    )

    print(f"Saved rendered text image: {output_path}")
    print(f"Saved provenance manifest: {manifest_path}")


if __name__ == "__main__":
    main()
