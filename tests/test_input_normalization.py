"""Tests for template page input normalization."""

import shutil

from PIL import Image

from experiments.scripts.run_pipeline import normalize_and_preprocess_pages
from packages.common.paths import PROJECT_ROOT, TEMPLATES_DIR
from packages.cv.preprocess import normalize_template_page
from packages.cv.segment import load_template_metadata


TEST_SCRATCH_DIR = PROJECT_ROOT / ".tmp_tests" / "input_normalization"


def reset_test_scratch_dir() -> None:
    """Create an empty project-local normalization test directory."""
    if TEST_SCRATCH_DIR.exists():
        shutil.rmtree(TEST_SCRATCH_DIR)
    TEST_SCRATCH_DIR.mkdir(parents=True, exist_ok=True)


def test_wrong_size_input_is_resized_to_metadata_dimensions() -> None:
    """An arbitrary input size should be normalized to V2 metadata dimensions."""
    reset_test_scratch_dir()
    input_path = TEST_SCRATCH_DIR / "arbitrary_page.png"
    output_path = TEST_SCRATCH_DIR / "normalized.png"
    original_size = (777, 999)
    metadata = load_template_metadata(TEMPLATES_DIR / "template_v2.json")
    expected_size = (
        metadata["page"]["width_px"],
        metadata["page"]["height_px"],
    )
    Image.new("RGB", original_size, "white").save(input_path)

    try:
        result = normalize_template_page(input_path, output_path, *expected_size)

        assert result.original_size == original_size
        assert result.expected_size == expected_size
        assert result.resized is True
        with Image.open(output_path) as image:
            assert image.size == expected_size
    finally:
        shutil.rmtree(PROJECT_ROOT / ".tmp_tests", ignore_errors=True)


def test_correct_size_input_is_copied_safely() -> None:
    """A correctly sized page should still get a separate normalized copy."""
    reset_test_scratch_dir()
    input_path = TEST_SCRATCH_DIR / "correct_page.png"
    output_path = TEST_SCRATCH_DIR / "normalized.png"
    Image.new("RGB", (170, 220), "white").save(input_path)

    try:
        result = normalize_template_page(input_path, output_path, 170, 220)

        assert result.resized is False
        assert output_path.exists()
        assert output_path != input_path
        with Image.open(output_path) as image:
            assert image.size == (170, 220)
    finally:
        shutil.rmtree(PROJECT_ROOT / ".tmp_tests", ignore_errors=True)


def test_pipeline_preprocesses_normalized_page_paths() -> None:
    """Pipeline preparation should feed metadata-sized copies into preprocessing."""
    reset_test_scratch_dir()
    input_paths = [TEST_SCRATCH_DIR / f"input_{index}.png" for index in range(1, 4)]
    normalized_paths = [
        TEST_SCRATCH_DIR / f"normalized_{index}.png" for index in range(1, 4)
    ]
    processed_paths = [
        TEST_SCRATCH_DIR / f"processed_{index}.png" for index in range(1, 4)
    ]
    for input_path in input_paths:
        Image.new("RGB", (63, 82), "white").save(input_path)

    try:
        results, extraction_paths = normalize_and_preprocess_pages(
            input_paths=input_paths,
            metadata={"page": {"width_px": 85, "height_px": 110}},
            normalized_paths=normalized_paths,
            processed_paths=processed_paths,
        )

        assert extraction_paths == processed_paths
        assert [result.output_path for result in results] == normalized_paths
        for normalized_path, processed_path in zip(
            normalized_paths,
            extraction_paths,
            strict=True,
        ):
            with Image.open(normalized_path) as normalized_image:
                assert normalized_image.size == (85, 110)
            with Image.open(processed_path) as processed_image:
                assert processed_image.size == (85, 110)
    finally:
        shutil.rmtree(PROJECT_ROOT / ".tmp_tests", ignore_errors=True)
