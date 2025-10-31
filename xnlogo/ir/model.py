"""Core IR dataclasses."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import List, Optional

from .statements import IRStatement


class SchedulePhase(Enum):
    SETUP = auto()
    TICK = auto()
    CUSTOM = auto()


@dataclass(slots=True)
class StateField:
    name: str
    type_hint: Optional[str] = None
    default: Optional[str] = None


@dataclass(slots=True)
class GlobalVar:
    name: str
    default: Optional[str] = None


@dataclass(slots=True)
class Reporter:
    name: str
    expression: str


@dataclass(slots=True)
class AgentBehavior:
    name: str
    statements: List[IRStatement] = field(default_factory=list)
    schedule_phase: SchedulePhase = SchedulePhase.TICK
    probabilistic: bool = False


@dataclass(slots=True)
class AgentSpec:
    identifier: str
    breed: Optional[str]
    state_fields: List[StateField] = field(default_factory=list)
    behaviors: List[AgentBehavior] = field(default_factory=list)


@dataclass(slots=True)
class PatchSpec:
    state_fields: List[StateField] = field(default_factory=list)


@dataclass(slots=True)
class SeedConfig:
    strategy: str = "random"
    value: Optional[int] = None


@dataclass(slots=True)
class ModelSpec:
    globals: List[GlobalVar] = field(default_factory=list)
    agents: List[AgentSpec] = field(default_factory=list)
    patches: PatchSpec = field(default_factory=PatchSpec)
    random_seed_strategy: SeedConfig = field(default_factory=SeedConfig)
    reporters: List[Reporter] = field(default_factory=list)
    widgets: List[dict] = field(default_factory=list)
