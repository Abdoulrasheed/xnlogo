"""Command-line interface for xnLogo."""

from __future__ import annotations

import time
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Sequence, Tuple

import typer  # type: ignore[import-not-found]

from xnlogo.compiler import build_artifact, parse_sources
from xnlogo.runtime.session import NetLogoSession, SessionConfig
from xnlogo.runtime.telemetry import TelemetryBuffer
from xnlogo.version import __version__

app = typer.Typer(help="Python-to-NetLogo transpiler and integration toolkit.")


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(__version__)
        raise typer.Exit()


@app.callback()
def main(
    ctx: typer.Context,
    version: Optional[bool] = typer.Option(
        None,
        "--version",
        callback=_version_callback,
        is_eager=True,
        help="Show the xnLogo version and exit.",
    ),
) -> None:
    """Initialize the CLI."""
    _ = ctx  # unused


@app.command()
def help(
    cmd: Optional[str] = typer.Argument(None, help="Command to show help for."),
) -> None:
    """Show help for xnlogo or a subcommand."""
    if cmd is None:
        typer.echo(app.get_help())
        raise typer.Exit()

    command = app.registered_commands.get(cmd)
    if command is None:
        typer.secho(f"Unknown command: {cmd}", fg=typer.colors.RED)
        raise typer.Exit(code=1)

    typer.echo(command.get_help(app))


@app.command()
def check(
    path: Path = typer.Argument(..., help="Path to Python source file or package."),
    strict: bool = typer.Option(False, "--strict", help="Treat warnings as errors."),
) -> None:
    """Run structural and semantic validation without generating NetLogo output."""
    result = parse_sources(path)

    if strict:
        result.diagnostics.promote_warnings_to_errors()

    _print_diagnostics(result.diagnostics)

    if result.diagnostics.has_errors():
        raise typer.Exit(code=1)


@app.command()
def build(
    path: Path = typer.Argument(..., help="Path to Python source file or package."),
    output_dir: Optional[Path] = typer.Option(
        None,
        "--output-dir",
        exists=True,
        file_okay=False,
        resolve_path=True,
        help="Directory for emitted artifacts.",
    ),
    fmt: str = typer.Option(
        "nlogox",
        "--format",
        case_sensitive=False,
        help="Output container (default nlogox; use nlogo for legacy tooling).",
    ),
    default_widgets: bool = typer.Option(
        True,
        "--default-widgets/--no-default-widgets",
        help="Emit default setup/go widgets in the interface metadata.",
    ),
) -> None:
    """Compile Python sources into NetLogo artifacts."""
    result, artifact_path = build_artifact(
        entry=path,
        fmt=fmt,
        output_dir=output_dir,
        default_widgets=default_widgets,
    )

    if result.diagnostics.has_errors():
        _print_diagnostics(result.diagnostics)
        raise typer.Exit(code=1)

    _print_diagnostics(result.diagnostics)

    if artifact_path is None:
        typer.secho("No artifact produced.", fg=typer.colors.YELLOW)
        raise typer.Exit(code=1)

    typer.secho(f"Artifact written to {artifact_path}", fg=typer.colors.GREEN)


@app.command()
def run(
    path: Path = typer.Argument(
        ..., help="Path to Python source file or compiled model."
    ),
    ticks: int = typer.Option(
        0, "--ticks", help="Number of ticks to execute (0 means until stop condition)."
    ),
    headless: bool = typer.Option(
        True, "--headless/--gui", help="Run NetLogo headless or with GUI."
    ),
    netlogo_home: Optional[Path] = typer.Option(
        None,
        "--netlogo-home",
        resolve_path=True,
        help="NetLogo installation directory (overrides XNLOGO_NETLOGO_HOME/NETLOGO_HOME).",
    ),
    seed: Optional[int] = typer.Option(
        None, "--seed", help="Random seed to apply before execution."
    ),
    metric: List[str] = typer.Option(
        [],
        "--metric",
        "-m",
        help="Telemetry reporter to capture. Use label=reporter to rename (e.g. density=count turtles).",
    ),
    output_dir: Optional[Path] = typer.Option(
        None,
        "--output-dir",
        file_okay=False,
        resolve_path=True,
        help="Directory where run artifacts (telemetry.json) will be written.",
    ),
    profile: bool = typer.Option(
        False, "--profile", help="Collect profile metrics during execution."
    ),
) -> None:
    """Execute the model through the NetLogo runtime."""
    # determine whether we received a Python source or prebuilt artifact
    if path.suffix in {".nlogo", ".nlogox"}:
        model_path = path
    else:
        result, artifact_path = build_artifact(path, fmt="nlogox")
        _print_diagnostics(result.diagnostics)
        if result.diagnostics.has_errors() or artifact_path is None:
            raise typer.Exit(code=1)
        model_path = artifact_path

    metric_specs = _parse_metric_specs(metric)

    session = NetLogoSession(
        SessionConfig(headless=headless, netlogo_home=netlogo_home)
    )
    telemetry = TelemetryBuffer()

    run_start = time.perf_counter() if profile else None

    run_directory = _prepare_run_directory(output_dir, model_path)
    telemetry_path = run_directory / "telemetry.json"

    with session:
        session.load_model(model_path)
        if seed is not None:
            try:
                session.command(f"random-seed {seed}")
            except (
                Exception
            ) as exc:  # pragma: no cover - depends on runtime availability
                typer.secho(f"Unable to apply seed: {exc}", fg=typer.colors.RED)
                raise typer.Exit(code=1)
        session.command("setup")

        current_tick = 0
        while True:
            session.command("go")
            try:
                current_tick = int(session.report("ticks"))
            except Exception as exc:  # pragma: no cover - runtime guard
                typer.secho(
                    f"Failed to read ticks reporter: {exc}", fg=typer.colors.RED
                )
                raise typer.Exit(code=1)

            metrics_payload = {}
            for label, reporter in metric_specs:
                try:
                    metrics_payload[label] = session.report(reporter)
                except Exception as exc:  # pragma: no cover - runtime guard
                    typer.secho(
                        f"Failed to evaluate reporter '{reporter}' ({label}): {exc}",
                        fg=typer.colors.RED,
                    )
                    raise typer.Exit(code=1)

            telemetry.record(current_tick, metrics_payload)

            if ticks and current_tick >= ticks:
                break

    telemetry.save(telemetry_path)

    message = f"Run completed for {current_tick} ticks"
    if profile and run_start is not None:
        duration = time.perf_counter() - run_start
        message += f" in {duration:.2f}s"

    typer.secho(message, fg=typer.colors.GREEN)
    typer.secho(f"Telemetry written to {telemetry_path}", fg=typer.colors.BLUE)


@app.command()
def export(
    path: Path = typer.Argument(
        ..., help="Path to a telemetry archive or run directory."
    ),
    output: Optional[Path] = typer.Option(
        None, "--output", help="Custom output file name."
    ),
    fmt: str = typer.Option(
        "csv", "--format", case_sensitive=False, help="Export format: csv or json."
    ),
    metrics: Optional[str] = typer.Option(
        None, "--metrics", help="Comma-separated list of metrics to export."
    ),
) -> None:
    """Export telemetry from a run into analysis-friendly artifacts."""
    source = _resolve_telemetry_source(path)

    try:
        buffer = TelemetryBuffer.from_json_file(source)
    except Exception as exc:  # pragma: no cover - defensive I/O guard
        typer.secho(f"Failed to load telemetry: {exc}", fg=typer.colors.RED)
        raise typer.Exit(code=1)

    if metrics:
        requested = [name.strip() for name in metrics.split(",") if name.strip()]
        buffer = buffer.select(requested)

    target_path = output or source.with_suffix(f".{fmt.lower()}")

    try:
        buffer.export(target_path, fmt=fmt)
    except ValueError as exc:
        typer.secho(str(exc), fg=typer.colors.RED)
        raise typer.Exit(code=1)

    typer.secho(f"Telemetry exported to {target_path}", fg=typer.colors.GREEN)


def _parse_metric_specs(values: Sequence[str]) -> List[Tuple[str, str]]:
    specs: List[Tuple[str, str]] = []
    for raw in values:
        item = raw.strip()
        if not item:
            continue
        if "=" in item:
            label, reporter = item.split("=", 1)
        else:
            label, reporter = item, item
        label = label.strip()
        reporter = reporter.strip()
        if not label or not reporter:
            raise typer.BadParameter(f"Invalid metric specification: '{raw}'")
        specs.append((label, reporter))
    return specs


def _prepare_run_directory(output_dir: Optional[Path], model_path: Path) -> Path:
    if output_dir is not None:
        output_dir.mkdir(parents=True, exist_ok=True)
        return output_dir

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    default_dir = model_path.parent / f"{model_path.stem}-run-{timestamp}"
    default_dir.mkdir(parents=True, exist_ok=True)
    return default_dir


def _resolve_telemetry_source(path: Path) -> Path:
    if path.is_dir():
        candidate = path / "telemetry.json"
        if not candidate.exists():
            raise typer.BadParameter("Telemetry directory must contain telemetry.json")
        return candidate

    if path.suffix == ".json" and path.exists():
        return path

    raise typer.BadParameter(
        "Telemetry path must be a telemetry directory or JSON file"
    )


def _print_diagnostics(diagnostics) -> None:
    """Pretty-print diagnostics to the console."""
    if not diagnostics:
        return

    for diag in diagnostics:
        color = typer.colors.RED if diag.level == "error" else typer.colors.YELLOW
        prefix = "ERROR" if diag.level == "error" else "WARN"
        typer.secho(f"{prefix}: {diag.message}", fg=color)
