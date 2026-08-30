"""JSON sidecar provenance metadata for generated outputs."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from packages.common.config import ProjectConfig
from packages.common.paths import MANIFEST_DATA_DIR


def create_run_id() -> str:
    """Create a unique generation run identifier."""
    return f"run_{uuid4().hex[:12]}"


def write_generation_manifest(
    user_id: str,
    input_text: str,
    output_image_path: Path,
    run_id: str | None = None,
    manifest_dir: Path = MANIFEST_DATA_DIR,
    config: ProjectConfig | None = None,
    extra_fields: dict | None = None,
) -> Path:
    """Write a JSON sidecar manifest for a generated image.

    Args:
        user_id: Identifier for the handwriting sample owner.
        input_text: Text that was rendered.
        output_image_path: Path to the generated image.
        run_id: Optional run identifier. If omitted, one is generated.
        manifest_dir: Directory where the manifest should be written.
        config: Optional project config.
        extra_fields: Optional additional metadata to include.

    Returns:
        Path to the written manifest JSON file.
    """
    active_config = config or ProjectConfig()
    active_run_id = run_id or create_run_id()

    manifest = {
        "run_id": active_run_id,
        "user_id": user_id,
        "input_text": input_text,
        "output_image_path": str(output_image_path),
        "renderer_version": active_config.renderer_version,
        "template_version": active_config.template_version,
        "provenance_enabled": True,
        "created_at_utc": datetime.now(UTC).isoformat(),
        "notes": [
            "This image is a generated handwriting-style rendering.",
            "The output should not be represented as authentic human handwriting.",
            "Use only consented handwriting samples.",
        ],
    }

    if extra_fields:
        manifest.update(extra_fields)

    manifest_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = manifest_dir / f"{active_run_id}.json"

    with manifest_path.open("w", encoding="utf-8") as file:
        json.dump(manifest, file, indent=2)

    return manifest_path
