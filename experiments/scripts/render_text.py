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
from packages.generation import select_text_for_rendering, text_generation_metadata
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
        "--output",
        type=Path,
        default=OUTPUT_DATA_DIR / "rendered_text.png",
        help="Path where the rendered image should be saved.",
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
        help="Page margin in pixels.",
    )

    parser.add_argument(
        "--line-spacing-px",
        type=int,
        default=95,
        help="Vertical advance between rendered lines.",
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

    library = load_glyph_library(args.manifest)
    settings = RenderSettings(
        canvas_width=args.page_width,
        max_line_width=args.max_line_width,
        margin_left=args.margin_px,
        margin_top=args.margin_px,
        margin_bottom=args.margin_px,
        line_height=args.line_spacing_px,
    )
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
        text=final_text,
        library=library,
        output_path=args.output,
        settings=settings,
        variation=variation,
    )

    if not args.disable_visible_provenance:
        output_path = add_visible_provenance_footer(output_path)

    manifest_path = write_generation_manifest(
        user_id=args.user_id,
        input_text=final_text,
        output_image_path=output_path,
        run_id=run_id,
        extra_fields={
            "glyph_manifest_path": str(args.manifest),
            "visible_provenance_enabled": not args.disable_visible_provenance,
            "renderer_config": {
                **asdict(variation),
                "page_width": settings.canvas_width,
                "max_line_width": settings.max_line_width,
                "margin_px": args.margin_px,
                "line_spacing_px": settings.line_height,
            },
            **text_generation_metadata(text_result, args.max_generated_chars),
        },
    )

    print(f"Saved rendered text image: {output_path}")
    print(f"Saved provenance manifest: {manifest_path}")


if __name__ == "__main__":
    main()
