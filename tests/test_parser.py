from pathlib import Path

from xnlogo.parser.ast_parser import Parser


def test_parser_handles_missing_file(tmp_path: Path) -> None:
    parser = Parser()
    result = parser.parse([tmp_path / "missing.py"])
    assert len(result.diagnostics) >= 1
