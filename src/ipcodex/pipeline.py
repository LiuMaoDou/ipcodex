from __future__ import annotations

from importlib.resources import files
from pathlib import Path

from pydantic import BaseModel

from ipcodex.cst.models import ConfigTree
from ipcodex.cst.parser import parse_cst
from ipcodex.schema.loader import load_schema_bundle
from ipcodex.semantic.models import DeviceConfig
from ipcodex.semantic.registry import build_semantic_model
from ipcodex.source import load_config


class ParseResult(BaseModel):
    schema_version: str
    device: DeviceConfig
    tree: ConfigTree


def default_schema_root() -> Path:
    return Path(files("ipcodex.schema").joinpath("huawei_vrp"))


def parse_file(
    path: Path,
    *,
    schema_root: Path | None = None,
) -> ParseResult:
    selected_schema_root = schema_root or default_schema_root()
    schema = load_schema_bundle(selected_schema_root)
    document = load_config(path)
    tree = parse_cst(document, schema)
    device = build_semantic_model(tree, schema)
    return ParseResult(
        schema_version=schema.schema_version,
        device=device,
        tree=tree,
    )
