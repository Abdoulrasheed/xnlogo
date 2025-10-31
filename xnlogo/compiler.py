"""High-level compiler orchestration."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, TYPE_CHECKING

from xnlogo.codegen.netlogo_generator import BuildOptions, NetLogoGenerator
from xnlogo.parser.ast_parser import ParsedModule, Parser
from xnlogo.semantics.checks import run_behavioral_checks, run_structural_checks
from xnlogo.semantics.diagnostics import DiagnosticBag

if TYPE_CHECKING:
    from xnlogo.ir.model import ModelSpec


@dataclass
class CompilationResult:
    model: "ModelSpec"
    diagnostics: DiagnosticBag


def gather_sources(entry: Path) -> list[Path]:
    if entry.is_dir():
        sources = sorted(p for p in entry.rglob("*.py") if p.is_file())
    else:
        sources = [entry]

    if not sources:
        raise FileNotFoundError(f"No Python sources found at {entry}")
    return sources


def parse_sources(entry: Path) -> CompilationResult:
    parser = Parser()
    sources = gather_sources(entry)
    parsed: ParsedModule = parser.parse(sources)
    model = parsed.model
    diagnostics = parsed.diagnostics
    run_structural_checks(model, diagnostics)
    run_behavioral_checks(model, diagnostics)
    return CompilationResult(model=model, diagnostics=diagnostics)


def build_artifact(
    entry: Path,
    fmt: str = "nlogox",
    output_dir: Optional[Path] = None,
    default_widgets: bool = True,
) -> tuple[CompilationResult, Optional[Path]]:
    result = parse_sources(entry)
    diagnostics = result.diagnostics

    if diagnostics.has_errors():
        return result, None

    generator = NetLogoGenerator(
        result.model,
        options=BuildOptions(format=fmt.lower(), default_widgets=default_widgets),
    )
    artifact_text = generator.emit()

    target_name = entry.stem + (".nlogox" if fmt.lower() == "nlogox" else ".nlogo")
    target_dir = output_dir or entry.parent
    target_dir.mkdir(parents=True, exist_ok=True)
    target_path = target_dir / target_name
    target_path.write_text(artifact_text, encoding="utf-8")
    return result, target_path
