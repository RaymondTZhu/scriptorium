"""Run the complete V1 Scriptorium pipeline.

Example:
    python experiments/scripts/run_pipeline.py \
        --input templates/template_v1.png \
        --text "hello world" \
        --user-id user_001
"""

from __future__ import annotations

import argparse
from pathlib import Path

from packages.common.paths import (
    GLYPH_DATA_DIR,
    OUTPUT_DATA_DIR,
    PROCESSED_DATA_DIR,
    ensure_project_dirs,
)
from packages.cv.glyph_extract import extract_glyphs_from_template
from packages.cv.preprocess import preprocess_image
from packages.eval.visual_report import create_glyph_contact_sheet
from packages.renderer.glyph_library import load_glyph_library
from packages.renderer.layout import RenderSettings
from packages.renderer.render_png import render_text_to_image
from packages.watermark.metadata import create_run_id, write_generation_manifest
from packages.watermark.visible import add_visible_provenance_footer


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments for the V1 pipeline."""
    parser = argparse.ArgumentParser(
        description="Run preprocessing, glyph extraction, rendering, and provenance export."
    )

    parser.add_argument(
        "--input",
        required=True,
        type=Path,
        help="Path to a completed handwriting template image.",
    )

    parser.add_argument(
        "--text",
        required=True,
        help="Text to render with extracted glyphs.",
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
        help="Random seed for reproducible rendering.",
    )

    return parser.parse_args()


def main() -> None:
    """Run the complete V1 local pipeline."""
    args = parse_args()
    ensure_project_dirs()

    run_id = create_run_id()

    processed_path = PROCESSED_DATA_DIR / f"{run_id}_binary.png"
    glyph_output_dir = GLYPH_DATA_DIR / args.user_id
    contact_sheet_path = glyph_output_dir / "glyph_contact_sheet.png"
    rendered_output_path = OUTPUT_DATA_DIR / f"{run_id}_rendered_text.png"

    preprocess_image(
        input_path=args.input,
        output_path=processed_path,
    )

    glyph_manifest_path = extract_glyphs_from_template(
        input_path=processed_path,
        user_id=args.user_id,
        output_dir=glyph_output_dir,
    )

    library = load_glyph_library(glyph_manifest_path)

    create_glyph_contact_sheet(
        library=library,
        output_path=contact_sheet_path,
    )

    output_path = render_text_to_image(
        text=args.text,
        library=library,
        output_path=rendered_output_path,
        settings=RenderSettings(),
        seed=args.seed,
    )

    output_path = add_visible_provenance_footer(output_path)

    provenance_manifest_path = write_generation_manifest(
        user_id=args.user_id,
        input_text=args.text,
        output_image_path=output_path,
        run_id=run_id,
        extra_fields={
            "pipeline": "v1",
            "input_image_path": str(args.input),
            "processed_image_path": str(processed_path),
            "glyph_manifest_path": str(glyph_manifest_path),
            "contact_sheet_path": str(contact_sheet_path),
            "visible_provenance_enabled": True,
        },
    )

    print(f"Saved processed image: {processed_path}")
    print(f"Saved glyph manifest: {glyph_manifest_path}")
    print(f"Saved contact sheet: {contact_sheet_path}")
    print(f"Saved rendered output: {output_path}")
    print(f"Saved provenance manifest: {provenance_manifest_path}")


if __name__ == "__main__":
    main()
