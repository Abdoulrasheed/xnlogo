"""Tests for telemetry helpers."""


def test_telemetry_buffer_roundtrip(tmp_path):
    from xnlogo.runtime.telemetry import TelemetryBuffer

    buffer = TelemetryBuffer()
    buffer.record(1, {"population": 10})
    buffer.record(2, {"population": 12, "energy": 3.5})

    json_path = tmp_path / "telemetry.json"
    buffer.save(json_path)

    loaded = TelemetryBuffer.from_json_file(json_path)
    assert len(loaded.records) == 2
    assert loaded.records[1].metrics["energy"] == 3.5

    filtered = loaded.select(["energy"])
    assert filtered.records[0].metrics == {}
    assert filtered.records[1].metrics == {"energy": 3.5}

    csv_path = tmp_path / "telemetry.csv"
    loaded.export(csv_path, fmt="csv")
    content = csv_path.read_text(encoding="utf-8").strip().splitlines()
    assert content[0] == "tick,energy,population"
    assert content[1].startswith("1,")
