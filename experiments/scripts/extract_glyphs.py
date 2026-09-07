"""Extract glyph crops from a structured handwriting template image.

Example:
    python experiments/scripts/extract_glyphs.py \
        --input-page templates/template_v2_page_1.png \
        --input-page templates/template_v2_page_2.png \
        --input-page templates/template_v2_page_3.png \
        --user-id user_001
"""

from __future__ import annotations

import argparse
from pathlib import Path

from packages.common.paths import (
    GLYPH_DATA_DIR,
    PROCESSED_DATA_DIR,
    TEMPLATES_DIR,
    ensure_project_dirs,
    sanitize_path_component,
)
from packages.cv.glyph_extract import extract_glyphs_from_template_pages
from packages.cv.preprocess import normalize_template_page
from packages.cv.segment import (
    load_template_metadata,
    select_template_metadata_path,
    validate_template_input_count,
)


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments for glyph extraction."""
    parser = argparse.ArgumentParser(
        description="Extract glyph crops from a structured handwriting template image."
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

    output_dir = args.output_dir or GLYPH_DATA_DIR / sanitize_path_component(args.user_id)
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

    expected_width = metadata["page"]["width_px"]
    expected_height = metadata["page"]["height_px"]
    normalized_paths: list[Path] = []
    for page_number, input_path in enumerate(input_paths, start=1):
        normalized_path = (
            PROCESSED_DATA_DIR / f"extract_page_{page_number}_{input_path.stem}_normalized.png"
        )
        result = normalize_template_page(
            input_path=input_path,
            output_path=normalized_path,
            expected_width=expected_width,
            expected_height=expected_height,
        )
        normalized_paths.append(normalized_path)
        print(
            "Template page normalization: "
            f"input={result.input_path}, original_size={result.original_size}, "
            f"expected_size={result.expected_size}, resized={result.resized}, "
            f"output={result.output_path}"
        )

    manifest_path = extract_glyphs_from_template_pages(
        input_paths=normalized_paths,
        user_id=args.user_id,
        output_dir=output_dir,
        metadata_path=metadata_path,
    )

    print(f"Saved glyph manifest: {manifest_path}")


if __name__ == "__main__":
    main()
