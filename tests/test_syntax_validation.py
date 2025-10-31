"""Tests for syntax validation."""

from pathlib import Path
from xnlogo.compiler import parse_sources


def test_module_level_syntax_error():
    """Test that module-level syntax errors are reported."""
    path = Path("tests/data/invalid_syntax.py")
    result = parse_sources(path)

    assert result.diagnostics.has_errors()
    errors = [d for d in result.diagnostics if d.level == "error"]
    assert len(errors) > 0
    assert any("Syntax error" in d.message for d in errors)


def test_valid_syntax_no_errors():
    """Test that valid Python syntax doesn't produce syntax errors."""
    path = Path("tests/data/valid_behavior_syntax.py")
    result = parse_sources(path)

    # Should not have syntax errors
    errors = [d for d in result.diagnostics if "Syntax error" in d.message]
    assert len(errors) == 0
