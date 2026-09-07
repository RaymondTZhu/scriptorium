"""Glyph library loading utilities.

The glyph library is the bridge between computer vision extraction and future
handwritten-style rendering. It loads extracted glyph metadata from a manifest
and provides convenient character-based lookup.
"""

from __future__ import annotations

import json
import random
from collections import defaultdict
from pathlib import Path

from packages.common.types import BoundingBox, GlyphRecord


class GlyphLibrary:
    """In-memory collection of extracted glyph records grouped by character."""

    def __init__(self, glyphs: list[GlyphRecord]) -> None:
        """Create a glyph library from a list of glyph records."""
        self.glyphs = glyphs
        self._by_character: dict[str, list[GlyphRecord]] = defaultdict(list)

        for glyph in glyphs:
            if glyph.has_ink:
                self._by_character[glyph.character].append(glyph)

    def characters(self) -> list[str]:
        """Return all characters available in this glyph library."""
        return sorted(self._by_character.keys())

    def get_variants(self, character: str) -> list[GlyphRecord]:
        """Return all glyph variants for a character."""
        return list(self._by_character.get(character, []))

    def has_character(self, character: str) -> bool:
        """Return True if this library contains at least one glyph for a character."""
        return bool(self.get_variants(character))

    def sample_variant(self, character: str, rng: random.Random | None = None) -> GlyphRecord:
        """Sample one glyph variant for a character.

        Raises:
            KeyError: If the requested character is unavailable.
        """
        variants = self.get_variants(character)

        if not variants:
            raise KeyError(f"No glyph variants found for character: {character!r}")

        random_source = rng or random
        return random_source.choice(variants)


def load_glyph_library(manifest_path: Path) -> GlyphLibrary:
    """Load a glyph library from a glyph manifest JSON file."""
    with manifest_path.open("r", encoding="utf-8") as file:
        manifest = json.load(file)

    glyphs: list[GlyphRecord] = []

    for record in manifest["glyphs"]:
        bbox_data = record.get("cell_bbox")
        original_bbox_data = record.get("original_bbox", bbox_data)
        quality = record.get("quality", {})

        glyphs.append(
            GlyphRecord(
                user_id=record["user_id"],
                character=record["character"],
                variant_id=record["variant_id"],
                image_path=Path(record["image_path"]),
                bbox=_deserialize_bbox(bbox_data),
                quality_score=quality.get("dark_pixel_ratio"),
                original_bbox=_deserialize_bbox(original_bbox_data),
                ink_bbox=_deserialize_bbox(record.get("ink_bbox")),
                width=record.get("width"),
                height=record.get("height"),
                has_ink=record.get("has_ink", not quality.get("probably_empty", False)),
                page_number=record.get("page_number", 1),
                template_version=record.get("template_version", manifest.get("template_version")),
            )
        )

    return GlyphLibrary(glyphs)


def _deserialize_bbox(data: dict | None) -> BoundingBox | None:
    """Create a bounding box from manifest data when present."""
    if data is None:
        return None

    return BoundingBox(
        x=data["x"],
        y=data["y"],
        width=data["width"],
        height=data["height"],
    )
