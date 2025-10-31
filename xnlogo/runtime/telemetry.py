"""Telemetry capture and export utilities."""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List


@dataclass(slots=True)
class TelemetryRecord:
    tick: int
    metrics: Dict[str, Any]


@dataclass
class TelemetryBuffer:
    """Collects telemetry samples during a NetLogo run."""

    records: List[TelemetryRecord] = field(default_factory=list)

    def record(self, tick: int, metrics: Dict[str, Any]) -> None:
        self.records.append(TelemetryRecord(tick=tick, metrics=dict(metrics)))

    def to_json(self) -> str:
        return json.dumps(
            [{"tick": record.tick, **record.metrics} for record in self.records],
            indent=2,
        )

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(self.to_json(), encoding="utf-8")

    def export(self, path: Path, fmt: str = "json") -> None:
        fmt = fmt.lower()
        if fmt == "json":
            self.save(path)
        elif fmt == "csv":
            self._export_csv(path)
        else:
            raise ValueError(f"Unsupported telemetry export format: {fmt}")

    def select(self, metric_names: Iterable[str]) -> "TelemetryBuffer":
        requested = {name for name in metric_names if name}
        if not requested:
            return self

        filtered = TelemetryBuffer()
        for record in self.records:
            filtered_metrics = {
                k: v for k, v in record.metrics.items() if k in requested
            }
            filtered.record(record.tick, filtered_metrics)
        return filtered

    @classmethod
    def from_json_file(cls, path: Path) -> "TelemetryBuffer":
        raw = path.read_text(encoding="utf-8")
        data = json.loads(raw)
        buffer = cls()
        for row in data:
            tick = int(row.get("tick", 0))
            metrics = {k: v for k, v in row.items() if k != "tick"}
            buffer.record(tick, metrics)
        return buffer

    def _export_csv(self, path: Path) -> None:
        if not self.records:
            path.write_text("", encoding="utf-8")
            return

        fieldnames = sorted(
            {key for record in self.records for key in record.metrics.keys()}
        )
        fieldnames.insert(0, "tick")

        with path.open("w", encoding="utf-8", newline="") as fh:
            writer = csv.DictWriter(fh, fieldnames=fieldnames)
            writer.writeheader()
            for record in self.records:
                row = {"tick": record.tick, **record.metrics}
                writer.writerow(row)
