"""Diagnostic collection utilities."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Iterator, List


@dataclass(slots=True)
class Diagnostic:
    """Represents a compiler diagnostic message."""

    message: str
    level: str = "error"


class DiagnosticBag:
    """Collect diagnostic messages across compiler stages."""

    def __init__(self) -> None:
        self._items: List[Diagnostic] = []

    def error(self, message: str) -> None:
        self._items.append(Diagnostic(message=message, level="error"))

    def warning(self, message: str) -> None:
        self._items.append(Diagnostic(message=message, level="warning"))

    def extend(self, diagnostics: Iterable[Diagnostic]) -> None:
        self._items.extend(diagnostics)

    def __iter__(self) -> Iterator[Diagnostic]:
        return iter(self._items)

    def __len__(self) -> int:  # pragma: no cover - trivial
        return len(self._items)

    def has_errors(self) -> bool:
        return any(item.level == "error" for item in self._items)

    def promote_warnings_to_errors(self) -> None:
        for item in self._items:
            if item.level == "warning":
                item.level = "error"
