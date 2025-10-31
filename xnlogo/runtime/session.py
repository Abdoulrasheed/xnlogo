"""Session management for NetLogo integration."""

from __future__ import annotations

import contextlib
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, List, Optional, Sequence, Tuple

_HEADLESS_CLASS: Any | None = None
_ACTIVE_NETLOGO_HOME: Optional[Path] = None


@dataclass(slots=True)
class SessionConfig:
    """Configuration for NetLogo runtime sessions."""

    netlogo_home: Optional[Path] = None
    headless: bool = True
    jvm_path: Optional[Path] = None
    classpath_extra: Sequence[Path] = ()
    java_options: Sequence[str] = ()
    extensions_dir: Optional[Path] = None
    models_dir: Optional[Path] = None
    docs_dir: Optional[Path] = None


class NetLogoSession:
    """Manage lifecycle for NetLogo interactions using JPype and the NetLogo Headless API."""

    def __init__(self, config: SessionConfig | None = None) -> None:
        self.config = config or SessionConfig()
        self._workspace: Any | None = None

    def __enter__(self) -> "NetLogoSession":
        self.open()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    # Lifecycle ---------------------------------------------------------------

    def open(self) -> None:
        if self._workspace is not None:
            return

        headless_cls = _ensure_headless_workspace(self.config)
        self._workspace = headless_cls.newInstance()

    def close(self) -> None:
        if self._workspace is None:
            return
        with contextlib.suppress(Exception):  # pragma: no cover - best effort cleanup
            self._workspace.dispose()
        self._workspace = None

    # Actions -----------------------------------------------------------------

    def load_model(self, path: Path) -> None:
        workspace = self._require_workspace()
        workspace.open(str(path))

    def command(self, command: str) -> None:
        workspace = self._require_workspace()
        workspace.command(command)

    def report(self, reporter: str) -> Any:
        workspace = self._require_workspace()
        return workspace.report(reporter)

    def repeat(self, command: str, ticks: int) -> None:
        for _ in range(ticks):
            self.command(command)

    # Internal helpers --------------------------------------------------------

    def _require_workspace(self) -> Any:
        if self._workspace is None:
            raise RuntimeError("Session not open")
        return self._workspace


def open_session(config: SessionConfig | None = None) -> NetLogoSession:
    return NetLogoSession(config=config)


def _ensure_headless_workspace(config: SessionConfig) -> Any:
    global _HEADLESS_CLASS
    if _HEADLESS_CLASS is not None:
        return _HEADLESS_CLASS

    jpype = _import_jpype()

    _ensure_jvm_started(jpype, config)

    from org.nlogo.headless import HeadlessWorkspace  # type: ignore[attr-defined]

    _HEADLESS_CLASS = HeadlessWorkspace
    return HeadlessWorkspace


def _import_jpype():
    try:  # pragma: no cover - import guard
        import jpype  # type: ignore[import-not-found]
        import jpype.imports  # type: ignore[import-not-found]  # noqa: F401 - side effect enabling Java package imports
    except ImportError as exc:  # pragma: no cover - dependency guard
        raise RuntimeError(
            "JPype is not installed. Install xnlogo[runtime] or add jpype1 to your environment."
        ) from exc
    return jpype


def _ensure_jvm_started(jpype_module, config: SessionConfig) -> Path:
    global _ACTIVE_NETLOGO_HOME
    if jpype_module.isJVMStarted():
        if _ACTIVE_NETLOGO_HOME is None:
            raise RuntimeError(
                "JVM is already started but NetLogo home was not recorded."
            )
        return _ACTIVE_NETLOGO_HOME

    netlogo_home = _resolve_netlogo_home(config)
    os.environ.setdefault("NETLOGO_HOME", str(netlogo_home))
    os.environ.setdefault("XNLOGO_NETLOGO_HOME", str(netlogo_home))
    classpath = _build_classpath(netlogo_home, config.classpath_extra)
    java_args = list(config.java_options) + _default_java_args(netlogo_home, config)

    kwargs = {
        "classpath": classpath,
        "convertStrings": True,
        "ignoreUnrecognized": True,
    }

    jvm_path = str(config.jvm_path) if config.jvm_path else None
    if jvm_path:
        jpype_module.startJVM(jvm_path, *java_args, **kwargs)
    else:
        jpype_module.startJVM(*java_args, **kwargs)

    _ACTIVE_NETLOGO_HOME = netlogo_home
    return netlogo_home


def _resolve_netlogo_home(config: SessionConfig) -> Path:
    candidates: Iterable[Path]

    if config.netlogo_home is not None:
        candidates = [config.netlogo_home]
    else:
        env_candidates: List[str] = []
        for env_var in (
            "XNLOGO_NETLOGO_HOME",
            "NETLOGO_HOME",
            "PYNETLOGO_NETLOGO_HOME",
        ):
            value = os.environ.get(env_var)
            if value:
                env_candidates.append(value)
        default_mac = Path("/Applications/NetLogo 7.0.0")
        if default_mac.exists():
            env_candidates.append(str(default_mac))
        candidates = [Path(path) for path in env_candidates]

    for base in candidates:
        home = base.expanduser().resolve()
        try:
            _discover_app_dir(home)
        except RuntimeError:
            continue
        return home

    raise RuntimeError(
        "Unable to locate NetLogo installation. Provide SessionConfig.netlogo_home or set NETLOGO_HOME "
        "to the directory containing NetLogo (the folder or .app bundle with the bundled jars)."
    )


def _build_classpath(netlogo_home: Path, extras: Sequence[Path]) -> List[str]:
    app_dir = _discover_app_dir(netlogo_home)

    jars = sorted(str(path) for path in app_dir.glob("*.jar"))
    jars.extend(str(Path(extra)) for extra in extras)
    if not jars:
        raise RuntimeError(f"No NetLogo jars found in {app_dir}")
    return jars


def _default_java_args(netlogo_home: Path, config: SessionConfig) -> List[str]:
    args: List[str] = []
    extensions_dir = _resolve_resource_dir(
        netlogo_home,
        config.extensions_dir,
        (
            ("extensions",),
            ("app", "extensions"),
            ("Contents", "Java", "extensions"),
            ("Contents", "Resources", "extensions"),
            ("Contents", "Resources", "app", "extensions"),
        ),
    )
    models_dir = _resolve_resource_dir(
        netlogo_home,
        config.models_dir,
        (
            ("models",),
            ("app", "models"),
            ("Contents", "Java", "models"),
            ("Contents", "Resources", "models"),
            ("Contents", "Resources", "app", "models"),
        ),
    )
    docs_dir = _resolve_resource_dir(
        netlogo_home,
        config.docs_dir,
        (
            ("docs",),
            ("app", "docs"),
            ("Contents", "Java", "docs"),
            ("Contents", "Resources", "docs"),
            ("Contents", "Resources", "app", "docs"),
        ),
    )

    args.extend(
        [
            f"-Dnetlogo.extensions.dir={extensions_dir}",
            f"-Dnetlogo.models.dir={models_dir}",
            f"-Dnetlogo.docs.dir={docs_dir}",
            f"-Dorg.nlogo.preferHeadless={'true' if config.headless else 'false'}",
        ]
    )

    natives_dir = _resolve_resource_dir(
        netlogo_home,
        None,
        (
            ("natives",),
            ("app", "natives"),
            ("Contents", "Resources", "natives"),
            ("Contents", "Resources", "app", "natives"),
            ("Contents", "Java", "natives"),
        ),
        allow_missing=True,
    )
    if natives_dir is not None and natives_dir.exists():
        native_paths = [entry for entry in natives_dir.iterdir() if entry.is_dir()]
        native_target = native_paths[0] if native_paths else natives_dir
        args.append(f"-Djava.library.path={native_target}")

    module_exports = [
        "--add-exports=java.base/java.lang=ALL-UNNAMED",
        "--add-exports=java.desktop/sun.awt=ALL-UNNAMED",
        "--add-exports=java.desktop/sun.java2d=ALL-UNNAMED",
        "--add-exports=java.desktop/com.apple.laf=ALL-UNNAMED",
    ]
    args.extend(module_exports)
    return args


def _discover_app_dir(netlogo_home: Path) -> Path:
    candidates = [
        netlogo_home / "app",
        netlogo_home / "Contents" / "Java",
        netlogo_home / "Contents" / "Resources" / "app",
        netlogo_home / "Java",
    ]

    for candidate in candidates:
        if candidate.exists():
            return candidate

    raise RuntimeError(
        f"Unable to find NetLogo jars under '{netlogo_home}'. Expected to locate an 'app' or 'Contents/Java' directory."
    )


def _resolve_resource_dir(
    netlogo_home: Path,
    override: Optional[Path],
    relative_candidates: Tuple[Tuple[str, ...], ...],
    *,
    allow_missing: bool = False,
) -> Optional[Path]:
    if override is not None:
        return override.expanduser().resolve()

    for parts in relative_candidates:
        candidate = netlogo_home.joinpath(*parts).resolve()
        if candidate.exists():
            return candidate

    if allow_missing:
        return None

    # even if the directory is absent, return the first candidate path
    # so that user-visible errors point to the expected location
    default_parts = relative_candidates[0]
    return netlogo_home.joinpath(*default_parts).resolve()
