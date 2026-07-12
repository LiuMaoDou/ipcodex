from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

from ipcodex.pipeline import parse_file


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="ipcodex")
    subparsers = parser.add_subparsers(dest="command", required=True)

    parse_parser = subparsers.add_parser("parse")
    parse_parser.add_argument("input", type=Path)
    parse_parser.add_argument("--output", type=Path, required=True)
    parse_parser.add_argument("--schema-root", type=Path)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)

    if args.command == "parse":
        result = parse_file(args.input, schema_root=args.schema_root)
        payload = result.model_dump(mode="json")
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        return 0

    raise AssertionError(f"Unhandled command: {args.command}")
