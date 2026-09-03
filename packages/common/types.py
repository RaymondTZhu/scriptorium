"""Shared data types used across Scriptorium modules.

These types are intentionally small and general. More specialized models can
be added later inside CV, renderer, watermark, API, or evaluation modules.
"""

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class BoundingBox:
    """Rectangular region in image coordinates.

    Attributes:
        x: Left coordinate of the box.
        y: Top coordinate of the box.
        width: Width of the box in pixels.
        height: Height of the box in pixels.
    """

    x: int
    y: int
    width: int
    height: int


@dataclass(frozen=True)
class GlyphRecord:
    """Metadata describing one extracted handwriting glyph."""

    user_id: str
    character: str
    variant_id: int
    image_path: Path
    bbox: BoundingBox | None = None
    quality_score: float | None = None
    original_bbox: BoundingBox | None = None
    ink_bbox: BoundingBox | None = None
    width: int | None = None
    height: int | None = None
    has_ink: bool = True


@dataclass(frozen=True)
class GenerationManifest:
    """Metadata describing one generated handwritten-style output."""

    run_id: str
    user_id: str
    input_text: str
    output_path: Path
    renderer_version: str
    template_version: str
    provenance_enabled: bool
