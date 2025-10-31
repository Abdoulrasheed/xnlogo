from pathlib import Path

import pytest

from xnlogo.compiler import build_artifact, gather_sources, parse_sources


def test_gather_sources_returns_files(tmp_path: Path) -> None:
    src_dir = tmp_path / "pkg"
    src_dir.mkdir()
    file_a = src_dir / "a.py"
    file_a.write_text("print('hello')\n", encoding="utf-8")

    sources = gather_sources(src_dir)

    assert sources == [file_a]


def test_parse_sources_produces_model(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    sample = Path(__file__).parent / "data" / "sample_model.py"
    target = tmp_path / "model.py"
    target.write_text(sample.read_text(encoding="utf-8"), encoding="utf-8")

    result = parse_sources(target)

    assert not result.diagnostics.has_errors()
    assert result.model.agents


def test_build_artifact_writes_nlogox(tmp_path: Path) -> None:
    sample = Path(__file__).parent / "data" / "sample_model.py"
    target = tmp_path / "model.py"
    target.write_text(sample.read_text(encoding="utf-8"), encoding="utf-8")

    result, artifact_path = build_artifact(target, fmt="nlogox")

    assert artifact_path is not None
    contents = artifact_path.read_text(encoding="utf-8")

    assert "<model" in contents
    assert "Rabbit" in contents
