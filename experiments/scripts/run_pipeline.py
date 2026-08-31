"""Run the complete V1 Scriptorium pipeline.

Example:
    python experiments/scripts/run_pipeline.py \
        --input templates/template_v1.png \
        --text "hello world" \
        --user-id user_001
"""

from __future__ import annotations

import argparse
from dataclasses import asdict
from pathlib import Path

from packages.common.paths import (
    GLYPH_DATA_DIR,
    OUTPUT_DATA_DIR,
    PROCESSED_DATA_DIR,
    ensure_project_dirs,
)
from packages.cv.glyph_extract import extract_glyphs_from_template
from packages.cv.preprocess import preprocess_image
from packages.eval.visual_report import create_glyph_contact_sheet, create_visual_report
from packages.renderer.glyph_library import load_glyph_library
from packages.renderer.layout import RendererVariationConfig, RenderSettings
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
        "--skip-visual-report",
        action="store_true",
        help="Skip automatic visual evaluation report generation.",
    )

    return parser.parse_args()


def main() -> None:
    """Run the complete V1 local pipeline."""
    args = parse_args()
    ensure_project_dirs()

    run_id = create_run_id()
    variation = RendererVariationConfig(
        seed=args.seed,
        x_jitter_px=max(0, args.x_jitter_px),
        y_jitter_px=max(0, args.y_jitter_px),
        scale_jitter=max(0.0, args.scale_jitter),
        spacing_jitter_px=max(0, args.spacing_jitter_px),
        line_spacing_jitter_px=max(0, args.line_spacing_jitter_px),
    )

    processed_path = PROCESSED_DATA_DIR / f"{run_id}_binary.png"
    glyph_output_dir = GLYPH_DATA_DIR / args.user_id
    contact_sheet_path = glyph_output_dir / "glyph_contact_sheet.png"
    rendered_output_path = OUTPUT_DATA_DIR / f"{run_id}_rendered_text.png"
    visual_report_path = OUTPUT_DATA_DIR / "visual_report.png"

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
        variation=variation,
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
            "renderer_config": asdict(variation),
        },
    )

    report_created = False
    required_report_artifacts = (
        args.input,
        contact_sheet_path,
        output_path,
        provenance_manifest_path,
    )

    if not args.skip_visual_report and all(path.exists() for path in required_report_artifacts):
        create_visual_report(
            template_image_path=args.input,
            contact_sheet_path=contact_sheet_path,
            rendered_output_path=output_path,
            generation_record_path=provenance_manifest_path,
            output_path=visual_report_path,
        )
        report_created = True

    print(f"Saved processed image: {processed_path}")
    print(f"Saved glyph manifest: {glyph_manifest_path}")
    print(f"Saved contact sheet: {contact_sheet_path}")
    print(f"Saved rendered output: {output_path}")
    print(f"Saved provenance manifest: {provenance_manifest_path}")
    if report_created:
        print(f"Saved visual evaluation report: {visual_report_path}")


if __name__ == "__main__":
    main()
