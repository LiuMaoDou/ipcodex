from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from ipcodex.schema.models import CommandSpec, SchemaBundle, ViewSpec


def _read_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"Schema file must contain a mapping: {path}")
    return data


def load_schema_bundle(schema_root: Path) -> SchemaBundle:
    views_data = _read_yaml(Path(schema_root) / "views.yaml")
    commands_data = _read_yaml(Path(schema_root) / "commands.yaml")

    views = {
        item["id"]: ViewSpec.model_validate(item)
        for item in views_data.get("views", [])
    }
    commands = {
        item["id"]: CommandSpec.model_validate(item)
        for item in commands_data.get("commands", [])
    }

    return SchemaBundle(
        vendor=views_data["vendor"],
        os=views_data["os"],
        schema_version=views_data["schema_version"],
        views=views,
        commands=commands,
    )
