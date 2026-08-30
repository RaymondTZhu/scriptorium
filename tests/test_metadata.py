"""Tests for generated-output traceability metadata."""

from pathlib import Path

from packages.watermark.metadata import create_run_id, write_generation_manifest


def test_create_run_id_has_expected_prefix() -> None:
    """Run IDs should be visibly identifiable as generation runs."""
    run_id = create_run_id()

    assert run_id.startswith("run_")
    assert len(run_id) > len("run_")


def test_write_generation_manifest_creates_json_file(tmp_path: Path) -> None:
    """Writing a generation manifest should create a JSON sidecar file."""
    output_image_path = tmp_path / "rendered.png"
    output_image_path.write_text("placeholder", encoding="utf-8")

    manifest_path = write_generation_manifest(
        user_id="user_001",
        input_text="hello world",
        output_image_path=output_image_path,
        manifest_dir=tmp_path,
    )

    assert manifest_path.exists()
    assert manifest_path.suffix == ".json"
