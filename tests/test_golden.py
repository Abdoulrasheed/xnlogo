"""Golden file comparison tests for .nlogox generation."""

import difflib
from pathlib import Path
from xml.etree import ElementTree as ET

import pytest

from xnlogo.compiler import build_artifact


def normalize_xml(xml_str: str) -> str:
    """Normalize XML for comparison by parsing and pretty-printing."""
    try:
        root = ET.fromstring(xml_str)
        ET.indent(root, space="  ")
        return ET.tostring(root, encoding="unicode")
    except ET.ParseError:
        return xml_str


def compare_nlogox(actual_path: Path, expected_path: Path) -> tuple[bool, str]:
    """
    Compare two .nlogox files, returning (matches, diff_text).

    Normalizes XML before comparison to avoid whitespace differences.
    """
    actual_text = actual_path.read_text(encoding="utf-8")
    expected_text = expected_path.read_text(encoding="utf-8")

    actual_normalized = normalize_xml(actual_text)
    expected_normalized = normalize_xml(expected_text)

    if actual_normalized == expected_normalized:
        return True, ""

    diff = difflib.unified_diff(
        expected_normalized.splitlines(keepends=True),
        actual_normalized.splitlines(keepends=True),
        fromfile=str(expected_path),
        tofile=str(actual_path),
        lineterm="",
    )
    return False, "".join(diff)


@pytest.fixture
def golden_dir() -> Path:
    """Path to golden reference files."""
    return Path(__file__).parent / "data" / "golden"


@pytest.fixture
def test_data_dir() -> Path:
    """Path to test data directory."""
    return Path(__file__).parent / "data"


def test_simple_agent_golden(
    tmp_path: Path, test_data_dir: Path, golden_dir: Path
) -> None:
    """Test that simple_agent.py compiles to match the golden .nlogox file."""
    source = test_data_dir / "simple_agent.py"
    golden_file = golden_dir / "simple_agent.nlogox"

    # Build the model
    result, output_file = build_artifact(
        source, fmt="nlogox", output_dir=tmp_path, default_widgets=True
    )

    # Check for compilation errors
    errors = [d for d in result.diagnostics if d.level == "error"]
    assert not errors, f"Compilation errors: {[e.message for e in errors]}"
    assert output_file is not None, "Build failed to produce output file"

    # Compare against golden file
    matches, diff = compare_nlogox(output_file, golden_file)

    if not matches:
        pytest.fail(f"Generated .nlogox does not match golden file:\n{diff}")


def test_agent_with_conditionals_golden(
    tmp_path: Path, test_data_dir: Path, golden_dir: Path
) -> None:
    """Test that agent_with_conditionals.py with if/else statements compiles correctly."""
    source = test_data_dir / "agent_with_conditionals.py"
    golden_file = golden_dir / "agent_with_conditionals.nlogox"

    result, output_file = build_artifact(
        source, fmt="nlogox", output_dir=tmp_path, default_widgets=True
    )

    errors = [d for d in result.diagnostics if d.level == "error"]
    assert not errors, f"Compilation errors: {[e.message for e in errors]}"
    assert output_file is not None, "Build failed to produce output file"

    matches, diff = compare_nlogox(output_file, golden_file)

    if not matches:
        pytest.fail(f"Generated .nlogox does not match golden file:\n{diff}")


def test_multi_breed_golden(
    tmp_path: Path, test_data_dir: Path, golden_dir: Path
) -> None:
    """Test that multi_breed.py with multiple breeds compiles correctly."""
    source = test_data_dir / "multi_breed.py"
    golden_file = golden_dir / "multi_breed.nlogox"

    result, output_file = build_artifact(
        source, fmt="nlogox", output_dir=tmp_path, default_widgets=True
    )

    errors = [d for d in result.diagnostics if d.level == "error"]
    assert not errors, f"Compilation errors: {[e.message for e in errors]}"
    assert output_file is not None, "Build failed to produce output file"

    matches, diff = compare_nlogox(output_file, golden_file)

    if not matches:
        pytest.fail(f"Generated .nlogox does not match golden file:\n{diff}")


def test_complex_agent_golden(
    tmp_path: Path, test_data_dir: Path, golden_dir: Path
) -> None:
    """Test that complex_agent.py with advanced features compiles correctly."""
    source = test_data_dir / "complex_agent.py"
    golden_file = golden_dir / "complex_agent.nlogox"

    result, output_file = build_artifact(
        source, fmt="nlogox", output_dir=tmp_path, default_widgets=True
    )

    errors = [d for d in result.diagnostics if d.level == "error"]
    assert not errors, f"Compilation errors: {[e.message for e in errors]}"
    assert output_file is not None, "Build failed to produce output file"

    matches, diff = compare_nlogox(output_file, golden_file)

    if not matches:
        pytest.fail(f"Generated .nlogox does not match golden file:\n{diff}")
