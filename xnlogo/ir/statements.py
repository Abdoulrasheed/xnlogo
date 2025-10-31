"""IR statement definitions."""

from __future__ import annotations

from enum import Enum


class StatementKind(str, Enum):
    """Kinds of IR statements."""

    RAW = "raw"


class IRStatement:
    """Base representation of an executable statement in the IR."""

    __slots__ = ("kind",)

    def __init__(self, kind: StatementKind) -> None:
        self.kind = kind


class RawStatement(IRStatement):
    """Represents a raw source snippet carried through to code generation."""

    __slots__ = ("source",)

    def __init__(self, source: str) -> None:
        IRStatement.__init__(self, StatementKind.RAW)
        self.source = source
