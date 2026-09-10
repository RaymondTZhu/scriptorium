"""Run the complete Scriptorium pipeline.

Example:
    python experiments/scripts/run_pipeline.py \
        --input-page templates/template_v2_page_1.png \
        --input-page templates/template_v2_page_2.png \
        --input-page templates/template_v2_page_3.png \
        --text "Hello, World! 123" \
        --user-id user_001
"""

from __future__ import annotations

import argparse
import shutil
from dataclasses import asdict
from pathlib import Path

from packages.common.paths import (
    GLYPH_DATA_DIR,
    OUTPUT_DATA_DIR,
    PROCESSED_DATA_DIR,
    TEMPLATES_DIR,
    ensure_project_dirs,
    sanitize_path_component,
)
from packages.cv.glyph_extract import extract_glyphs_from_template_pages
from packages.cv.preprocess import (
    PageNormalizationResult,
    normalize_template_page,
    preprocess_image,
)
from packages.cv.segment import (
    load_template_metadata,
    select_template_metadata_path,
    validate_template_input_count,
)
from packages.eval.visual_report import create_glyph_contact_sheet, create_visual_report
from packages.generation import select_text_for_rendering, text_generation_metadata
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

    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument(
        "--input",
        type=Path,
        help="Path to one completed V1 handwriting template image.",
    )

    input_group.add_argument(
        "--input-page",
        action="append",
        type=Path,
        help="Completed V2 page path; repeat once for each page in order.",
    )

    parser.add_argument(
        "--template-metadata",
        type=Path,
        default=None,
        help=(
            "Template metadata JSON. Defaults to template_v2.json for "
            "--input-page and template_v1.json for legacy --input."
        ),
    )

    parser.add_argument(
        "--text",
        help="Text to render directly. Cannot be combined with --prompt.",
    )

    parser.add_argument(
        "--prompt",
        help="Prompt used to generate text. Cannot be combined with --text.",
    )

    parser.add_argument(
        "--text-provider",
        choices=("local", "openai"),
        default="local",
        help="Prompt-to-text provider. Defaults to the deterministic local provider.",
    )

    parser.add_argument(
        "--text-model",
        default=None,
        help="Optional text-generation model. OpenAI defaults to gpt-5.5.",
    )

    parser.add_argument(
        "--max-generated-chars",
        type=int,
        default=500,
        help="Maximum generated text length; longer provider output is truncated.",
    )

    parser.add_argument(
        "--user-id",
        default="user_001",
        help="Identifier for the handwriting sample owner.",
    )

    parser.add_argument(
        "--page-width",
        type=int,
        default=1200,
        help="Rendered page width in pixels.",
    )

    parser.add_argument(
        "--max-line-width",
        type=int,
        default=1080,
        help="Maximum text width before word wrapping.",
    )

    parser.add_argument(
        "--margin-px",
        type=int,
        default=60,
        help="Rendered page margin in pixels.",
    )

    parser.add_argument(
        "--line-spacing-px",
        type=int,
        default=95,
        help="Vertical advance between rendered lines.",
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


def normalize_and_preprocess_pages(
    input_paths: list[Path],
    metadata: dict,
    normalized_paths: list[Path],
    processed_paths: list[Path],
) -> tuple[list[PageNormalizationResult], list[Path]]:
    """Normalize template pages before creating extraction-ready images."""
    expected_width = metadata["page"]["width_px"]
    expected_height = metadata["page"]["height_px"]
    results: list[PageNormalizationResult] = []

    for input_path, normalized_path, processed_path in zip(
        input_paths,
        normalized_paths,
        processed_paths,
        strict=True,
    ):
        result = normalize_template_page(
            input_path=input_path,
            output_path=normalized_path,
            expected_width=expected_width,
            expected_height=expected_height,
        )
        results.append(result)
        preprocess_image(input_path=normalized_path, output_path=processed_path)

    return results, processed_paths


def print_normalization_diagnostic(result: PageNormalizationResult) -> None:
    """Print the source and destination geometry for one template page."""
    print(
        "Template page normalization: "
        f"input={result.input_path}, original_size={result.original_size}, "
        f"expected_size={result.expected_size}, resized={result.resized}, "
        f"output={result.output_path}"
    )


def main() -> None:
    """Run the complete V1 local pipeline."""
    args = parse_args()
    ensure_project_dirs()

    text_result = select_text_for_rendering(
        text=args.text,
        prompt=args.prompt,
        provider=args.text_provider,
        model=args.text_model,
        max_chars=args.max_generated_chars,
    )
    final_text = text_result.generated_text
    if text_result.prompt:
        print(f"Generated text: {final_text}")

    run_id = create_run_id()
    input_paths = args.input_page or [args.input]
    metadata_path = select_template_metadata_path(
        args.template_metadata,
        multi_page=bool(args.input_page),
    )
    metadata = load_template_metadata(metadata_path)
    validate_template_input_count(metadata, len(input_paths), metadata_path)

    try:
        display_metadata_path = metadata_path.relative_to(TEMPLATES_DIR.parent)
    except ValueError:
        display_metadata_path = metadata_path
    print(f"Using template metadata: {display_metadata_path}")
    variation = RendererVariationConfig(
        seed=args.seed,
        x_jitter_px=max(0, args.x_jitter_px),
        y_jitter_px=max(0, args.y_jitter_px),
        scale_jitter=max(0.0, args.scale_jitter),
        spacing_jitter_px=max(0, args.spacing_jitter_px),
        line_spacing_jitter_px=max(0, args.line_spacing_jitter_px),
    )
    render_settings = RenderSettings(
        canvas_width=args.page_width,
        max_line_width=args.max_line_width,
        margin_left=args.margin_px,
        margin_top=args.margin_px,
        margin_bottom=args.margin_px,
        line_height=args.line_spacing_px,
    )

    if len(input_paths) == 1:
        normalized_paths = [PROCESSED_DATA_DIR / f"{run_id}_normalized.png"]
        processed_paths = [PROCESSED_DATA_DIR / f"{run_id}_binary.png"]
    else:
        normalized_paths = [
            PROCESSED_DATA_DIR / f"{run_id}_page_{index}_normalized.png"
            for index in range(1, len(input_paths) + 1)
        ]
        processed_paths = [
            PROCESSED_DATA_DIR / f"{run_id}_page_{index}_binary.png"
            for index in range(1, len(input_paths) + 1)
        ]
    glyph_output_dir = GLYPH_DATA_DIR / sanitize_path_component(args.user_id)
    contact_sheet_path = glyph_output_dir / "glyph_contact_sheet.png"
    rendered_output_path = OUTPUT_DATA_DIR / f"{run_id}_rendered_text.png"
    latest_rendered_output_path = OUTPUT_DATA_DIR / "rendered_text.png"
    visual_report_path = OUTPUT_DATA_DIR / "visual_report.png"

    normalization_results, processed_paths = normalize_and_preprocess_pages(
        input_paths=input_paths,
        metadata=metadata,
        normalized_paths=normalized_paths,
        processed_paths=processed_paths,
    )
    for result in normalization_results:
        print_normalization_diagnostic(result)

    glyph_manifest_path = extract_glyphs_from_template_pages(
        input_paths=processed_paths,
        user_id=args.user_id,
        output_dir=glyph_output_dir,
        metadata_path=metadata_path,
    )

    library = load_glyph_library(glyph_manifest_path)

    create_glyph_contact_sheet(
        library=library,
        output_path=contact_sheet_path,
    )

    output_path = render_text_to_image(
        text=final_text,
        library=library,
        output_path=rendered_output_path,
        settings=render_settings,
        variation=variation,
    )

    output_path = add_visible_provenance_footer(output_path)
    shutil.copy2(output_path, latest_rendered_output_path)

    provenance_manifest_path = write_generation_manifest(
        user_id=args.user_id,
        input_text=final_text,
        output_image_path=output_path,
        run_id=run_id,
        extra_fields={
            "pipeline": "v1",
            "input_image_path": str(input_paths[0]) if len(input_paths) == 1 else None,
            "input_image_paths": [str(path) for path in input_paths],
            "normalized_image_paths": [str(path) for path in normalized_paths],
            "processed_image_path": (
                str(processed_paths[0]) if len(processed_paths) == 1 else None
            ),
            "processed_image_paths": [str(path) for path in processed_paths],
            "glyph_manifest_path": str(glyph_manifest_path),
            "contact_sheet_path": str(contact_sheet_path),
            "visible_provenance_enabled": True,
            "renderer_config": {
                **asdict(variation),
                "page_width": render_settings.canvas_width,
                "max_line_width": render_settings.max_line_width,
                "margin_px": args.margin_px,
                "line_spacing_px": render_settings.line_height,
            },
            **text_generation_metadata(text_result, args.max_generated_chars),
        },
    )

    report_created = False
    required_report_artifacts = (
        normalized_paths[0],
        contact_sheet_path,
        latest_rendered_output_path,
        provenance_manifest_path,
    )

    if not args.skip_visual_report and all(path.exists() for path in required_report_artifacts):
        create_visual_report(
            template_image_path=normalized_paths[0],
            contact_sheet_path=contact_sheet_path,
            rendered_output_path=latest_rendered_output_path,
            generation_record_path=provenance_manifest_path,
            output_path=visual_report_path,
        )
        report_created = True

    for processed_path in processed_paths:
        print(f"Saved processed image: {processed_path}")
    print(f"Saved glyph manifest: {glyph_manifest_path}")
    print(f"Saved contact sheet: {contact_sheet_path}")
    print(f"Saved rendered output: {output_path}")
    print(f"Saved latest rendered output: {latest_rendered_output_path}")
    print(f"Saved provenance manifest: {provenance_manifest_path}")
    if report_created:
        print(f"Saved visual evaluation report: {visual_report_path}")


if __name__ == "__main__":
    main()
