import json
from pathlib import Path
from unittest.mock import patch

from ipcodex.cli import main


def test_cli_parses_file_and_writes_deterministic_json(tmp_path: Path) -> None:
    output = tmp_path / "leaf.json"

    exit_code = main(
        [
            "parse",
            "samples/huawei/ce_leaf_minimal.cfg",
            "--output",
            str(output),
        ]
    )

    assert exit_code == 0
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["device"]["hostname"]["value"] == "Leaf01"
    assert payload["schema_version"] == "0.1.0"
    assert output.read_text(encoding="utf-8").endswith("\n")


def test_cli_starts_local_web_server() -> None:
    with patch("ipcodex.cli.run_server") as run_server:
        exit_code = main(["web", "--port", "8123"])

    assert exit_code == 0
    run_server.assert_called_once_with(host="127.0.0.1", port=8123)
