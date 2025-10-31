"""CLI export command tests."""

import json

from xnlogo.cli.commands import export


def test_export_json_to_csv(tmp_path):
    telemetry = [
        {"tick": 1, "population": 10, "energy": 3.2},
        {"tick": 2, "population": 11, "energy": 3.4},
    ]
    telemetry_path = tmp_path / "telemetry.json"
    telemetry_path.write_text(json.dumps(telemetry), encoding="utf-8")

    output_csv = tmp_path / "out.csv"

    export(path=telemetry_path, output=output_csv, fmt="csv", metrics="energy")

    content = output_csv.read_text(encoding="utf-8").strip().splitlines()
    assert content[0] == "tick,energy"
    assert content[1] == "1,3.2"
