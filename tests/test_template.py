"""Tests for V1 handwriting template metadata."""

import json

from packages.common.paths import TEMPLATES_DIR


def test_template_metadata_exists() -> None:
    """The V1 template metadata file should exist."""
    assert (TEMPLATES_DIR / "template_v1.json").exists()


def test_template_metadata_is_lowercase_v1() -> None:
    """V1 should use lowercase-only metadata so the template fits one page."""
    with (TEMPLATES_DIR / "template_v1.json").open("r", encoding="utf-8") as file:
        metadata = json.load(file)

    assert metadata["template_id"] == "template_v1"
    assert metadata["template_version"] == "0.1.0"
    assert metadata["character_sets"] == {
        "lowercase": "abcdefghijklmnopqrstuvwxyz",
    }
    assert metadata["variants_per_character"] == 3
    assert metadata["layout"]["columns"] > 0
