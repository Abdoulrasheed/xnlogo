"""runtime api for agent-based modeling.

transpiles python agent definitions to netlogo and executes via runtime.
"""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Callable, Type, TypeVar

T = TypeVar("T")


def agent(
    cls: Type[T] | None = None, **kwargs
) -> Type[T] | Callable[[Type[T]], Type[T]]:
    """decorator for agent classes."""

    def decorator(cls: Type[T]) -> Type[T]:
        cls._xnlogo_agent = True  # type: ignore
        cls._xnlogo_kwargs = kwargs  # type: ignore
        return cls

    if cls is None:
        return decorator
    else:
        return decorator(cls)


def run(source_file: Path | str, steps: int = 100, headless: bool = True) -> None:
    """compile and execute python model in netlogo."""
    from xnlogo.compiler import build_artifact
    from xnlogo.runtime.session import NetLogoSession, SessionConfig

    source_path = Path(source_file)
    if not source_path.exists():
        raise FileNotFoundError(f"Source file not found: {source_path}")

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        result, artifact_path = build_artifact(
            source_path, fmt="nlogox", output_dir=tmp_path
        )

        if result.diagnostics.has_errors():
            for diag in result.diagnostics.errors:
                print(f"Error: {diag.message}")
            raise RuntimeError("Compilation failed. See errors above.")

        if artifact_path is None:
            raise RuntimeError("Failed to generate NetLogo artifact")

        config = SessionConfig(headless=headless)
        with NetLogoSession(config) as session:
            session.load_model(artifact_path)
            session.command("setup")
            session.repeat("go", steps)

            try:
                tick_count = session.report("ticks")
                turtle_count = session.report("count turtles")
                print(
                    f"Simulation completed: {tick_count} ticks, {turtle_count} turtles"
                )
            except Exception:
                pass

