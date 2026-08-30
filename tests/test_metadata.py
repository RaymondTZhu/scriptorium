"""Tests for generated-output traceability metadata."""

from pathlib import Path
import shutil

from packages.common.paths import PROJECT_ROOT
from packages.watermark.metadata import create_run_id, write_generation_manifest

TEST_SCRATCH_DIR = PROJECT_ROOT / ".tmp_tests" / "metadata"


def reset_test_scratch_dir() -> Path:
    """Create a clean project-local scratch directory for metadata tests."""
    if TEST_SCRATCH_DIR.exists():
        shutil.rmtree(TEST_SCRATCH_DIR)

    TEST_SCRATCH_DIR.mkdir(parents=True, exist_ok=True)
    return TEST_SCRATCH_DIR


def test_create_run_id_has_expected_prefix() -> None:
    """Run IDs should be visibly identifiable as generation runs."""
    run_id = create_run_id()

    assert run_id.startswith("run_")
    assert len(run_id) > len("run_")


def test_write_generation_manifest_creates_json_file() -> None:
    """Writing a generation manifest should create a JSON sidecar file."""
    scratch_dir = reset_test_scratch_dir()

    output_image_path = scratch_dir / "rendered.png"
    output_image_path.write_text("placeholder", encoding="utf-8")

    manifest_path = write_generation_manifest(
        user_id="user_001",
        input_text="hello world",
        output_image_path=output_image_path,
        manifest_dir=scratch_dir,
    )

    assert manifest_path.exists()
    assert manifest_path.suffix == ".json"

    shutil.rmtree(PROJECT_ROOT / ".tmp_tests", ignore_errors=True)
