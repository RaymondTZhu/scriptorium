"""Create a visual evaluation report from V1 pipeline artifacts."""

from __future__ import annotations

import argparse
from pathlib import Path

from packages.common.paths import GLYPH_DATA_DIR, OUTPUT_DATA_DIR, TEMPLATES_DIR
from packages.eval.visual_report import create_visual_report


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments for visual report generation."""
    parser = argparse.ArgumentParser(
        description="Combine V1 artifacts into a visual evaluation report."
    )
    parser.add_argument(
        "--template-image",
        type=Path,
        default=TEMPLATES_DIR / "template_v1.png",
        help="Path to the handwriting template image.",
    )
    parser.add_argument(
        "--contact-sheet",
        type=Path,
        default=GLYPH_DATA_DIR / "user_001" / "glyph_contact_sheet.png",
        help="Path to the glyph contact sheet image.",
    )
    parser.add_argument(
        "--rendered-output",
        type=Path,
        default=OUTPUT_DATA_DIR / "rendered_text.png",
        help="Path to the rendered output image.",
    )
    parser.add_argument(
        "--generation-record",
        type=Path,
        default=None,
        help="Optional path to a JSON generation record.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=OUTPUT_DATA_DIR / "visual_report.png",
        help="Path where the visual report image should be saved.",
    )
    return parser.parse_args()


def main() -> None:
    """Create a visual report from command-line arguments."""
    args = parse_args()
    report_path = create_visual_report(
        template_image_path=args.template_image,
        contact_sheet_path=args.contact_sheet,
        rendered_output_path=args.rendered_output,
        generation_record_path=args.generation_record,
        output_path=args.output,
    )
    print(f"Saved visual evaluation report: {report_path}")


if __name__ == "__main__":
    main()
