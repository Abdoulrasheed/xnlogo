"""Tests to validate that generated NetLogo code is syntactically valid."""

from pathlib import Path
from xml.etree import ElementTree as ET

import pytest

from xnlogo.compiler import build_artifact


def extract_netlogo_code(nlogox_path: Path) -> str:
    """Extract the NetLogo code section from a .nlogox file."""
    tree = ET.parse(nlogox_path)
    root = tree.getroot()
    code_elem = root.find("code")
    if code_elem is not None and code_elem.text:
        return code_elem.text
    return ""


def validate_netlogo_syntax(code: str) -> list[str]:
    """
    Basic syntax validation for NetLogo code.

    Returns list of validation errors (empty list = valid).
    This is a simple heuristic check, not a full parser.
    """
    errors = []

    # Check balanced brackets
    bracket_stack = []
    for i, char in enumerate(code):
        if char == "[":
            bracket_stack.append(("[", i))
        elif char == "]":
            if not bracket_stack:
                errors.append(f"Unmatched closing bracket at position {i}")
            else:
                bracket_stack.pop()

    if bracket_stack:
        errors.append(f"Unclosed bracket at position {bracket_stack[-1][1]}")

    # Check balanced parentheses
    paren_stack = []
    for i, char in enumerate(code):
        if char == "(":
            paren_stack.append(("(", i))
        elif char == ")":
            if not paren_stack:
                errors.append(f"Unmatched closing parenthesis at position {i}")
            else:
                paren_stack.pop()

    if paren_stack:
        errors.append(f"Unclosed parenthesis at position {paren_stack[-1][1]}")

    # Check for Python syntax leaks (common mistakes)
    python_keywords = ["self.", "def ", "class ", "import ", "from "]
    for keyword in python_keywords:
        if keyword in code:
            errors.append(
                f"Python syntax detected: '{keyword}' found in generated NetLogo code"
            )

    # Check for Python operators that don't exist in NetLogo
    if " == " in code:
        errors.append("Python equality operator '==' found (NetLogo uses '=')")

    if "**" in code and "^" not in code:
        # Allow ** if it's actually being used for power, check context
        lines_with_power = [line for line in code.split("\n") if "**" in line]
        if any("**" in line and "^" not in line for line in lines_with_power):
            errors.append("Python power operator '**' found (NetLogo uses '^')")

    return errors


@pytest.fixture
def test_data_dir() -> Path:
    """Path to test data directory."""
    return Path(__file__).parent / "data"


@pytest.fixture
def golden_dir() -> Path:
    """Path to golden reference files."""
    return Path(__file__).parent / "data" / "golden"


def test_simple_agent_validity(tmp_path: Path, test_data_dir: Path) -> None:
    """Validate that simple_agent.py generates syntactically valid NetLogo."""
    source = test_data_dir / "simple_agent.py"
    result, output_file = build_artifact(source, fmt="nlogox", output_dir=tmp_path)

    assert output_file is not None
    code = extract_netlogo_code(output_file)
    errors = validate_netlogo_syntax(code)

    assert not errors, "NetLogo syntax errors:\n" + "\n".join(errors)


def test_agent_with_conditionals_validity(tmp_path: Path, test_data_dir: Path) -> None:
    """Validate that agent_with_conditionals.py generates valid NetLogo."""
    source = test_data_dir / "agent_with_conditionals.py"
    result, output_file = build_artifact(source, fmt="nlogox", output_dir=tmp_path)

    assert output_file is not None
    code = extract_netlogo_code(output_file)
    errors = validate_netlogo_syntax(code)

    assert not errors, "NetLogo syntax errors:\n" + "\n".join(errors)


def test_multi_breed_validity(tmp_path: Path, test_data_dir: Path) -> None:
    """Validate that multi_breed.py generates valid NetLogo."""
    source = test_data_dir / "multi_breed.py"
    result, output_file = build_artifact(source, fmt="nlogox", output_dir=tmp_path)

    assert output_file is not None
    code = extract_netlogo_code(output_file)
    errors = validate_netlogo_syntax(code)

    assert not errors, "NetLogo syntax errors:\n" + "\n".join(errors)


def test_complex_agent_validity(tmp_path: Path, test_data_dir: Path) -> None:
    """Validate that complex_agent.py generates valid NetLogo."""
    source = test_data_dir / "complex_agent.py"
    result, output_file = build_artifact(source, fmt="nlogox", output_dir=tmp_path)

    assert output_file is not None
    code = extract_netlogo_code(output_file)
    errors = validate_netlogo_syntax(code)

    assert not errors, "NetLogo syntax errors:\n" + "\n".join(errors)


def test_agent_with_loops_validity(tmp_path: Path, test_data_dir: Path) -> None:
    """Validate that agent_with_loops.py generates valid NetLogo."""
    source = test_data_dir / "agent_with_loops.py"
    result, output_file = build_artifact(source, fmt="nlogox", output_dir=tmp_path)

    assert output_file is not None
    code = extract_netlogo_code(output_file)
    errors = validate_netlogo_syntax(code)

    assert not errors, "NetLogo syntax errors:\n" + "\n".join(errors)


def test_golden_files_are_valid(golden_dir: Path) -> None:
    """Validate that all golden reference files contain valid NetLogo syntax."""
    golden_files = list(golden_dir.glob("*.nlogox"))
    assert golden_files, "No golden files found"

    all_errors = {}
    for golden_file in golden_files:
        code = extract_netlogo_code(golden_file)
        errors = validate_netlogo_syntax(code)
        if errors:
            all_errors[golden_file.name] = errors

    if all_errors:
        error_msg = "NetLogo syntax errors in golden files:\n"
        for filename, errors in all_errors.items():
            error_msg += f"\n{filename}:\n" + "\n".join(f"  - {e}" for e in errors)
        pytest.fail(error_msg)
