# Huawei VRP Configuration Parser MVP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the first IPCodex MVP: an offline Huawei VRP `display current-configuration` parser that preserves every source line, reconstructs configuration hierarchy, validates command parameters through versioned schemas, and emits a typed JSON model plus parsing coverage and unknown-command reports.

**Architecture:** Use a four-stage pipeline: source preprocessing → lossless concrete syntax tree (CST) → schema-based command matching → typed semantic model. Huawei-specific hierarchy and parameter knowledge lives in YAML `ViewSpec` and `CommandSpec` files rather than being hard-coded into the parser. The structural parser must preserve source evidence and unknown lines; semantic parsers may be added incrementally without changing the CST.

**Tech Stack:** Python 3.12, Pydantic v2, PyYAML, standard-library `ipaddress`, `argparse`, `json`, pytest, pytest-cov.

## Global Constraints

- The MVP supports only Huawei VRP offline output from `display current-configuration`.
- The initial validated target is Huawei CloudEngine-style VRP configuration; exact model and VRP version are metadata, not hard-coded assumptions.
- Every non-empty source line must remain recoverable with original text and line number.
- Unknown commands and unknown configuration blocks must be preserved and reported; they must never be silently discarded.
- Structural parsing and semantic parsing must remain separate modules.
- Configuration facts must distinguish explicit values from inferred/default values; the MVP records only explicit configuration.
- The parser must not use an LLM to decide hierarchy, syntax, parameters, or semantics.
- The parser must not connect to live devices in this MVP.
- The parser must not perform topology restoration, reachability simulation, fault diagnosis, configuration remediation, or Neo4j ingestion in this MVP.
- The MVP semantic scope is: `sysname`, `vlan batch`, interfaces, `Eth-Trunk`, IPv4 addresses, interface-to-VRF binding, VPN instances, RD/RT, and IPv4 static routes.
- BGP, OSPF, IS-IS, BFD, EVPN, VXLAN, M-LAG, ACL, QoS, and operational-state parsing are explicitly deferred.
- Source parsing must be deterministic: identical input and schema versions must produce byte-equivalent JSON after canonical serialization.
- Python package code lives under `src/ipcodex/`; tests live under `tests/`.
- Use TDD: each implementation task starts with a failing focused test.
- Initialize Git in `IPCodex` before implementation and commit after each task.

---

## MVP Acceptance Criteria

The MVP is complete only when all of the following are true:

1. `ipcodex parse samples/huawei/ce_leaf_minimal.cfg --output build/leaf01.json` exits with status `0`.
2. The JSON contains device identity, interfaces, VLANs, VPN instances, static routes, CST metadata, unknown items, warnings, and coverage metrics.
3. All non-empty input lines are represented either as recognized structural/semantic items or as explicit unknown/separator/source records.
4. The parser correctly places nested `ipv4-family` commands under `ip vpn-instance` by combining indentation, separator indentation, current view stack, and `ViewSpec.allowed_parents`.
5. `ip address 10.0.0.1 255.255.255.252` becomes `10.0.0.1/30`.
6. `undo portswitch` produces explicit semantic value `layer_mode = "layer3"` with evidence pointing to the source line.
7. A referenced VPN instance is resolved when present and reported as an unresolved reference when absent.
8. Unknown commands do not abort the file and appear in `unknown_items` with current view, line number, and raw text.
9. Structural coverage is `1.0` for all golden fixtures.
10. Semantic coverage is calculated from command lines and is at least `0.85` for the primary golden fixture.
11. `pytest -q` passes.
12. `pytest --cov=ipcodex --cov-report=term-missing` reports at least 90% coverage for `source.py`, `schema/`, `cst/`, and the MVP semantic parsers.

---

## Planned Repository Structure

```text
IPCodex/
├── plan.md
├── README.md
├── pyproject.toml
├── src/
│   └── ipcodex/
│       ├── __init__.py
│       ├── __main__.py
│       ├── cli.py
│       ├── pipeline.py
│       ├── source.py
│       ├── cst/
│       │   ├── __init__.py
│       │   ├── models.py
│       │   └── parser.py
│       ├── schema/
│       │   ├── __init__.py
│       │   ├── loader.py
│       │   ├── matcher.py
│       │   ├── models.py
│       │   ├── types.py
│       │   └── huawei_vrp/
│       │       ├── views.yaml
│       │       └── commands.yaml
│       └── semantic/
│           ├── __init__.py
│           ├── models.py
│           ├── registry.py
│           ├── system.py
│           ├── interface.py
│           └── network.py
├── samples/
│   └── huawei/
│       ├── ce_leaf_minimal.cfg
│       └── ce_unknown_commands.cfg
└── tests/
    ├── fixtures/
    │   ├── ce_leaf_minimal.expected.json
    │   └── ce_unknown_commands.expected.json
    ├── test_cli.py
    ├── test_pipeline.py
    ├── test_source.py
    ├── cst/
    │   └── test_parser.py
    ├── schema/
    │   ├── test_loader.py
    │   ├── test_matcher.py
    │   └── test_types.py
    └── semantic/
        ├── test_interface.py
        ├── test_network.py
        └── test_system.py
```

---

## Core Data Contracts

The implementation must keep these public interfaces stable through the MVP.

```python
# src/ipcodex/source.py

def load_config(path: Path) -> "SourceDocument": ...
def preprocess_text(text: str, *, source_name: str) -> "SourceDocument": ...
```

```python
# src/ipcodex/schema/loader.py

def load_schema_bundle(schema_root: Path) -> "SchemaBundle": ...
```

```python
# src/ipcodex/cst/parser.py

def parse_cst(document: SourceDocument, schema: SchemaBundle) -> "ConfigTree": ...
```

```python
# src/ipcodex/schema/matcher.py

def match_command(node: ConfigNode, schema: SchemaBundle) -> "CommandMatch | None": ...
```

```python
# src/ipcodex/semantic/registry.py

def build_semantic_model(tree: ConfigTree, schema: SchemaBundle) -> "DeviceConfig": ...
```

```python
# src/ipcodex/pipeline.py

def parse_file(path: Path, *, schema_root: Path | None = None) -> "ParseResult": ...
```

---

### Task 1: Bootstrap the Python Package and Test Harness

**Files:**
- Create: `IPCodex/pyproject.toml`
- Create: `IPCodex/src/ipcodex/__init__.py`
- Create: `IPCodex/src/ipcodex/__main__.py`
- Create: `IPCodex/tests/test_package.py`
- Create: `IPCodex/README.md`

**Interfaces:**
- Produces package version constant `ipcodex.__version__: str`.
- Produces module entry point `python -m ipcodex` that delegates to `ipcodex.cli.main` after Task 9.

- [ ] **Step 1: Initialize the repository**

Run from `IPCodex/`:

```bash
git init
git branch -M main
```

Expected: an empty Git repository on branch `main`.

- [ ] **Step 2: Write the failing package import test**

Create `tests/test_package.py`:

```python
from ipcodex import __version__


def test_package_exposes_version() -> None:
    assert __version__ == "0.1.0"
```

- [ ] **Step 3: Create `pyproject.toml`**

```toml
[build-system]
requires = ["hatchling>=1.25"]
build-backend = "hatchling.build"

[project]
name = "ipcodex"
version = "0.1.0"
description = "Offline Huawei VRP configuration parser"
readme = "README.md"
requires-python = ">=3.12"
dependencies = [
  "pydantic>=2.8,<3",
  "PyYAML>=6.0,<7",
]

[project.optional-dependencies]
dev = [
  "pytest>=8.2,<9",
  "pytest-cov>=5,<7",
]

[project.scripts]
ipcodex = "ipcodex.cli:main"

[tool.hatch.build.targets.wheel]
packages = ["src/ipcodex"]

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-ra"

[tool.coverage.run]
source = ["ipcodex"]
branch = true
```

- [ ] **Step 4: Create the package files**

Create `src/ipcodex/__init__.py`:

```python
__version__ = "0.1.0"
```

Create `src/ipcodex/__main__.py`:

```python
from ipcodex.cli import main


if __name__ == "__main__":
    raise SystemExit(main())
```

Create a temporary `src/ipcodex/cli.py` so imports are valid before Task 9:

```python
def main() -> int:
    return 0
```

- [ ] **Step 5: Create the initial README**

Create `README.md`:

````markdown
# IPCodex

IPCodex is an offline Huawei VRP configuration parser. The first MVP parses
`display current-configuration` output into a lossless configuration tree and
a typed semantic JSON model.

## Development

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
pytest -q
```
````

- [ ] **Step 6: Install and run the test**

Run:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
pytest tests/test_package.py -v
```

Expected: `1 passed`.

- [ ] **Step 7: Commit**

```bash
git add pyproject.toml README.md src tests/test_package.py
git commit -m "chore: bootstrap ipcodex parser project"
```

---

### Task 2: Preserve and Normalize Source Configuration

**Files:**
- Create: `IPCodex/src/ipcodex/source.py`
- Create: `IPCodex/tests/test_source.py`

**Interfaces:**
- Produces `SourceLine`, `SourceDocument`, `load_config`, and `preprocess_text`.
- `SourceLine.raw_text` is immutable evidence.
- `SourceLine.normalized_text` removes terminal paging/control artifacts but does not remove indentation or `#` separators.

- [ ] **Step 1: Write failing preprocessing tests**

Create `tests/test_source.py`:

```python
from ipcodex.source import preprocess_text


def test_preprocess_preserves_line_numbers_and_indentation() -> None:
    document = preprocess_text(
        "sysname Leaf01\n#\ninterface 100GE1/0/1\n description TO-SPINE\n",
        source_name="leaf.cfg",
    )

    assert document.source_name == "leaf.cfg"
    assert [line.line_number for line in document.lines] == [1, 2, 3, 4]
    assert document.lines[3].raw_text == " description TO-SPINE"
    assert document.lines[3].normalized_text == " description TO-SPINE"
    assert document.lines[3].indentation == 1


def test_preprocess_removes_paging_artifacts_without_losing_source() -> None:
    document = preprocess_text(
        "interface 100GE1/0/1---- More ----\n description TEST\x1b[42D\n",
        source_name="leaf.cfg",
    )

    assert document.lines[0].raw_text.endswith("---- More ----")
    assert document.lines[0].normalized_text == "interface 100GE1/0/1"
    assert document.lines[1].normalized_text == " description TEST"


def test_blank_lines_are_retained_but_marked() -> None:
    document = preprocess_text("sysname Leaf01\n\n#\n", source_name="leaf.cfg")

    assert len(document.lines) == 3
    assert document.lines[1].is_blank is True
```

- [ ] **Step 2: Run the tests and verify failure**

```bash
pytest tests/test_source.py -v
```

Expected: FAIL because `ipcodex.source` does not exist.

- [ ] **Step 3: Implement immutable source models and preprocessing**

Create `src/ipcodex/source.py`:

```python
from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, ConfigDict


class SourceLine(BaseModel):
    model_config = ConfigDict(frozen=True)

    line_number: int
    raw_text: str
    normalized_text: str
    indentation: int
    is_blank: bool


class SourceDocument(BaseModel):
    model_config = ConfigDict(frozen=True)

    source_name: str
    raw_text: str
    lines: tuple[SourceLine, ...]


def _normalize_line(raw_line: str) -> str:
    return (
        raw_line.replace("---- More ----", "")
        .replace("\x1b[42D", "")
        .rstrip("\r\n")
        .rstrip()
    )


def preprocess_text(text: str, *, source_name: str) -> SourceDocument:
    lines: list[SourceLine] = []
    for line_number, raw_line in enumerate(text.splitlines(), start=1):
        normalized = _normalize_line(raw_line)
        indentation = len(normalized) - len(normalized.lstrip(" "))
        lines.append(
            SourceLine(
                line_number=line_number,
                raw_text=raw_line,
                normalized_text=normalized,
                indentation=indentation,
                is_blank=normalized.strip() == "",
            )
        )
    return SourceDocument(
        source_name=source_name,
        raw_text=text,
        lines=tuple(lines),
    )


def load_config(path: Path) -> SourceDocument:
    text = path.read_text(encoding="utf-8-sig")
    return preprocess_text(text, source_name=path.name)
```

- [ ] **Step 4: Run the focused tests**

```bash
pytest tests/test_source.py -v
```

Expected: `3 passed`.

- [ ] **Step 5: Commit**

```bash
git add src/ipcodex/source.py tests/test_source.py
git commit -m "feat: preserve and normalize vrp source lines"
```

---

### Task 3: Define and Load Huawei View and Command Schemas

**Files:**
- Create: `IPCodex/src/ipcodex/schema/__init__.py`
- Create: `IPCodex/src/ipcodex/schema/models.py`
- Create: `IPCodex/src/ipcodex/schema/loader.py`
- Create: `IPCodex/src/ipcodex/schema/huawei_vrp/views.yaml`
- Create: `IPCodex/src/ipcodex/schema/huawei_vrp/commands.yaml`
- Create: `IPCodex/tests/schema/test_loader.py`

**Interfaces:**
- Produces `ViewSpec`, `ParameterSpec`, `CommandSpec`, `SchemaBundle`, and `load_schema_bundle`.
- Schema patterns are anchored regular expressions with named capture groups.
- `ViewSpec.allowed_parents` controls hierarchy; indentation alone never authorizes a parent-child relationship.

- [ ] **Step 1: Write the failing schema loader test**

Create `tests/schema/test_loader.py`:

```python
from importlib.resources import files

from ipcodex.schema.loader import load_schema_bundle


def test_load_huawei_vrp_schema_bundle() -> None:
    schema_root = files("ipcodex.schema").joinpath("huawei_vrp")
    bundle = load_schema_bundle(schema_root)

    assert bundle.vendor == "huawei"
    assert bundle.os == "vrp"
    assert bundle.views["system"].allowed_parents == ()
    assert bundle.views["interface"].allowed_parents == ("system",)
    assert bundle.views["vpn_ipv4_family"].allowed_parents == ("vpn_instance",)
    assert bundle.commands["interface_ip_address"].views == ("interface",)
```

- [ ] **Step 2: Run the test and verify failure**

```bash
pytest tests/schema/test_loader.py -v
```

Expected: FAIL because schema models and files do not exist.

- [ ] **Step 3: Implement schema models**

Create `src/ipcodex/schema/models.py`:

```python
from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class ParameterSpec(BaseModel):
    model_config = ConfigDict(frozen=True)

    name: str
    type: str
    required: bool = True


class ViewSpec(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str
    enter_pattern: str | None = None
    allowed_parents: tuple[str, ...] = ()
    closes_on_hash: bool = True


class CommandSpec(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str
    views: tuple[str, ...]
    pattern: str
    parameters: tuple[ParameterSpec, ...] = ()
    semantic_handler: str | None = None


class SchemaBundle(BaseModel):
    model_config = ConfigDict(frozen=True)

    vendor: str
    os: str
    schema_version: str
    views: dict[str, ViewSpec] = Field(default_factory=dict)
    commands: dict[str, CommandSpec] = Field(default_factory=dict)
```

- [ ] **Step 4: Create the initial view schema**

Create `src/ipcodex/schema/huawei_vrp/views.yaml`:

```yaml
vendor: huawei
os: vrp
schema_version: "0.1.0"
views:
  - id: system
    allowed_parents: []
    closes_on_hash: false

  - id: interface
    enter_pattern: '^interface (?P<interface_name>\S+)$'
    allowed_parents: [system]
    closes_on_hash: true

  - id: vpn_instance
    enter_pattern: '^ip vpn-instance (?P<vrf_name>\S+)$'
    allowed_parents: [system]
    closes_on_hash: true

  - id: vpn_ipv4_family
    enter_pattern: '^ipv4-family$'
    allowed_parents: [vpn_instance]
    closes_on_hash: true
```

- [ ] **Step 5: Create the initial command schema**

Create `src/ipcodex/schema/huawei_vrp/commands.yaml`:

```yaml
commands:
  - id: system_sysname
    views: [system]
    pattern: '^sysname (?P<hostname>\S+)$'
    parameters:
      - {name: hostname, type: identifier}
    semantic_handler: system.sysname

  - id: system_vlan_batch
    views: [system]
    pattern: '^vlan batch (?P<vlan_expression>.+)$'
    parameters:
      - {name: vlan_expression, type: vlan_expression}
    semantic_handler: network.vlan_batch

  - id: interface_description
    views: [interface]
    pattern: '^description (?P<description>.+)$'
    parameters:
      - {name: description, type: string}
    semantic_handler: interface.description

  - id: interface_shutdown
    views: [interface]
    pattern: '^shutdown$'
    parameters: []
    semantic_handler: interface.shutdown

  - id: interface_undo_shutdown
    views: [interface]
    pattern: '^undo shutdown$'
    parameters: []
    semantic_handler: interface.undo_shutdown

  - id: interface_undo_portswitch
    views: [interface]
    pattern: '^undo portswitch$'
    parameters: []
    semantic_handler: interface.undo_portswitch

  - id: interface_ip_address
    views: [interface]
    pattern: '^ip address (?P<address>\S+) (?P<mask>\S+)(?: (?P<sub>sub))?$'
    parameters:
      - {name: address, type: ipv4_address}
      - {name: mask, type: ipv4_netmask_or_prefix}
      - {name: sub, type: boolean_token, required: false}
    semantic_handler: interface.ip_address

  - id: interface_bind_vrf
    views: [interface]
    pattern: '^ip binding vpn-instance (?P<vrf_name>\S+)$'
    parameters:
      - {name: vrf_name, type: identifier}
    semantic_handler: interface.bind_vrf

  - id: interface_eth_trunk_member
    views: [interface]
    pattern: '^eth-trunk (?P<trunk_id>\d+)$'
    parameters:
      - {name: trunk_id, type: integer}
    semantic_handler: interface.eth_trunk_member

  - id: vpn_rd
    views: [vpn_ipv4_family]
    pattern: '^route-distinguisher (?P<rd>\S+)$'
    parameters:
      - {name: rd, type: route_distinguisher}
    semantic_handler: network.vpn_rd

  - id: vpn_target
    views: [vpn_ipv4_family]
    pattern: '^vpn-target (?P<rt>\S+) (?P<direction>import-extcommunity|export-extcommunity)$'
    parameters:
      - {name: rt, type: route_target}
      - {name: direction, type: enum}
    semantic_handler: network.vpn_target

  - id: static_route_ipv4
    views: [system]
    pattern: '^ip route-static (?P<prefix>\S+) (?P<mask>\S+) (?P<next_hop>\S+)(?: preference (?P<preference>\d+))?$'
    parameters:
      - {name: prefix, type: ipv4_address}
      - {name: mask, type: ipv4_netmask_or_prefix}
      - {name: next_hop, type: ipv4_address}
      - {name: preference, type: integer, required: false}
    semantic_handler: network.static_route

  - id: system_return
    views: [system]
    pattern: '^return$'
    parameters: []
```

- [ ] **Step 6: Implement the YAML loader**

Create `src/ipcodex/schema/loader.py`:

```python
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
```

Create empty package markers:

```python
# src/ipcodex/schema/__init__.py
```

- [ ] **Step 7: Run the schema test**

```bash
pytest tests/schema/test_loader.py -v
```

Expected: `1 passed`.

- [ ] **Step 8: Commit**

```bash
git add src/ipcodex/schema tests/schema/test_loader.py
git commit -m "feat: add versioned huawei vrp command schemas"
```

---

### Task 4: Build the Lossless Hierarchical CST Parser

**Files:**
- Create: `IPCodex/src/ipcodex/cst/__init__.py`
- Create: `IPCodex/src/ipcodex/cst/models.py`
- Create: `IPCodex/src/ipcodex/cst/parser.py`
- Create: `IPCodex/tests/cst/test_parser.py`

**Interfaces:**
- Consumes `SourceDocument` and `SchemaBundle`.
- Produces `ConfigTree` with a synthetic `system` root.
- A view node stores its opening line, child nodes, and optional closing separator line.
- All source line numbers must appear in `ConfigTree.mapped_line_numbers`.

- [ ] **Step 1: Write failing hierarchy tests**

Create `tests/cst/test_parser.py`:

```python
from importlib.resources import files

from ipcodex.cst.parser import parse_cst
from ipcodex.schema.loader import load_schema_bundle
from ipcodex.source import preprocess_text


def _schema():
    root = files("ipcodex.schema").joinpath("huawei_vrp")
    return load_schema_bundle(root)


def test_parser_uses_hash_indentation_to_close_nested_views() -> None:
    document = preprocess_text(
        "ip vpn-instance VPN-A\n"
        " ipv4-family\n"
        "  route-distinguisher 65001:100\n"
        " #\n"
        "#\n",
        source_name="vpn.cfg",
    )

    tree = parse_cst(document, _schema())

    vpn = tree.root.children[0]
    ipv4_family = vpn.children[0]
    rd = ipv4_family.children[0]

    assert vpn.view_id == "vpn_instance"
    assert ipv4_family.view_id == "vpn_ipv4_family"
    assert rd.text == "route-distinguisher 65001:100"
    assert ipv4_family.closing_line_number == 4
    assert vpn.closing_line_number == 5


def test_parser_preserves_unknown_commands_in_current_view() -> None:
    document = preprocess_text(
        "interface 100GE1/0/1\n"
        " mystery command 42\n"
        "#\n",
        source_name="unknown.cfg",
    )

    tree = parse_cst(document, _schema())

    command = tree.root.children[0].children[0]
    assert command.text == "mystery command 42"
    assert command.parent_view_id == "interface"
    assert tree.mapped_line_numbers == (1, 2, 3)
```

- [ ] **Step 2: Run tests and verify failure**

```bash
pytest tests/cst/test_parser.py -v
```

Expected: FAIL because CST modules do not exist.

- [ ] **Step 3: Implement CST models**

Create `src/ipcodex/cst/models.py`:

```python
from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

from ipcodex.source import SourceLine


class NodeKind(StrEnum):
    ROOT = "root"
    VIEW = "view"
    COMMAND = "command"
    BLANK = "blank"


class ConfigNode(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    kind: NodeKind
    text: str
    raw_text: str
    line_number: int | None
    indentation: int
    view_id: str | None = None
    parent_view_id: str | None = None
    captures: dict[str, str] = Field(default_factory=dict)
    children: list["ConfigNode"] = Field(default_factory=list)
    closing_line_number: int | None = None


class ConfigTree(BaseModel):
    root: ConfigNode
    source_name: str
    source_lines: tuple[SourceLine, ...]
    mapped_line_numbers: tuple[int, ...]
    warnings: tuple[str, ...] = ()
```

- [ ] **Step 4: Implement schema-aware stack parsing**

Create `src/ipcodex/cst/parser.py`:

```python
from __future__ import annotations

import re

from ipcodex.cst.models import ConfigNode, ConfigTree, NodeKind
from ipcodex.schema.models import SchemaBundle, ViewSpec
from ipcodex.source import SourceDocument, SourceLine


def _match_view(text: str, current_view_id: str, schema: SchemaBundle):
    for view in schema.views.values():
        if view.enter_pattern is None or current_view_id not in view.allowed_parents:
            continue
        match = re.fullmatch(view.enter_pattern, text)
        if match:
            return view, match.groupdict()
    return None


def _close_for_separator(
    stack: list[ConfigNode],
    separator: SourceLine,
) -> None:
    while len(stack) > 1 and stack[-1].indentation >= separator.indentation:
        closed = stack.pop()
        closed.closing_line_number = separator.line_number


def _find_parent_index(
    stack: list[ConfigNode],
    view: ViewSpec,
    indentation: int,
) -> int:
    for index in range(len(stack) - 1, -1, -1):
        candidate = stack[index]
        candidate_view = candidate.view_id or "system"
        if candidate_view in view.allowed_parents and candidate.indentation < indentation:
            return index
    if "system" in view.allowed_parents:
        return 0
    raise ValueError(
        f"No allowed parent for view {view.id} at indentation {indentation}"
    )


def parse_cst(document: SourceDocument, schema: SchemaBundle) -> ConfigTree:
    root = ConfigNode(
        kind=NodeKind.ROOT,
        text="system",
        raw_text="",
        line_number=None,
        indentation=-1,
        view_id="system",
    )
    stack = [root]
    mapped: list[int] = []
    warnings: list[str] = []

    for source_line in document.lines:
        mapped.append(source_line.line_number)
        stripped = source_line.normalized_text.strip()

        if source_line.is_blank:
            stack[-1].children.append(
                ConfigNode(
                    kind=NodeKind.BLANK,
                    text="",
                    raw_text=source_line.raw_text,
                    line_number=source_line.line_number,
                    indentation=source_line.indentation,
                    parent_view_id=stack[-1].view_id,
                )
            )
            continue

        if stripped == "#":
            _close_for_separator(stack, source_line)
            continue

        current_view = stack[-1].view_id or "system"
        view_match = _match_view(stripped, current_view, schema)

        if view_match is None and source_line.indentation == 0:
            while len(stack) > 1:
                stack.pop()
            current_view = "system"
            view_match = _match_view(stripped, current_view, schema)

        if view_match is not None:
            view, captures = view_match
            parent_index = _find_parent_index(stack, view, source_line.indentation)
            del stack[parent_index + 1 :]
            parent = stack[-1]
            node = ConfigNode(
                kind=NodeKind.VIEW,
                text=stripped,
                raw_text=source_line.raw_text,
                line_number=source_line.line_number,
                indentation=source_line.indentation,
                view_id=view.id,
                parent_view_id=parent.view_id,
                captures=captures,
            )
            parent.children.append(node)
            stack.append(node)
            continue

        stack[-1].children.append(
            ConfigNode(
                kind=NodeKind.COMMAND,
                text=stripped,
                raw_text=source_line.raw_text,
                line_number=source_line.line_number,
                indentation=source_line.indentation,
                parent_view_id=stack[-1].view_id,
            )
        )

    return ConfigTree(
        root=root,
        source_name=document.source_name,
        source_lines=document.lines,
        mapped_line_numbers=tuple(mapped),
        warnings=tuple(warnings),
    )
```

Create package marker:

```python
# src/ipcodex/cst/__init__.py
```

- [ ] **Step 5: Run the CST tests**

```bash
pytest tests/cst/test_parser.py -v
```

Expected: `2 passed`.

- [ ] **Step 6: Commit**

```bash
git add src/ipcodex/cst tests/cst/test_parser.py
git commit -m "feat: build lossless vrp configuration tree"
```

---

### Task 5: Match Commands and Decode Typed Parameters

**Files:**
- Create: `IPCodex/src/ipcodex/schema/types.py`
- Create: `IPCodex/src/ipcodex/schema/matcher.py`
- Create: `IPCodex/tests/schema/test_types.py`
- Create: `IPCodex/tests/schema/test_matcher.py`

**Interfaces:**
- Produces `decode_parameter(type_name, value)`.
- Produces `CommandMatch` and `match_command`.
- A command can match only when its parent view is listed in `CommandSpec.views`.

- [ ] **Step 1: Write failing parameter tests**

Create `tests/schema/test_types.py`:

```python
from ipaddress import IPv4Address, IPv4Network

import pytest

from ipcodex.schema.types import decode_parameter


def test_decode_ipv4_address_and_mask() -> None:
    assert decode_parameter("ipv4_address", "10.0.0.1") == IPv4Address("10.0.0.1")
    assert decode_parameter("ipv4_netmask_or_prefix", "255.255.255.252") == 30
    assert decode_parameter("ipv4_netmask_or_prefix", "24") == 24


def test_decode_vlan_expression() -> None:
    assert decode_parameter("vlan_expression", "100 200 to 202") == (100, 200, 201, 202)


def test_reject_invalid_ipv4_mask() -> None:
    with pytest.raises(ValueError):
        decode_parameter("ipv4_netmask_or_prefix", "255.0.255.0")
```

Create `tests/schema/test_matcher.py`:

```python
from importlib.resources import files

from ipcodex.cst.models import ConfigNode, NodeKind
from ipcodex.schema.loader import load_schema_bundle
from ipcodex.schema.matcher import match_command


def _schema():
    return load_schema_bundle(files("ipcodex.schema").joinpath("huawei_vrp"))


def test_match_command_respects_current_view() -> None:
    node = ConfigNode(
        kind=NodeKind.COMMAND,
        text="ip address 10.0.0.1 255.255.255.252",
        raw_text=" ip address 10.0.0.1 255.255.255.252",
        line_number=4,
        indentation=1,
        parent_view_id="interface",
    )

    match = match_command(node, _schema())

    assert match is not None
    assert match.command_id == "interface_ip_address"
    assert str(match.parameters["address"]) == "10.0.0.1"
    assert match.parameters["mask"] == 30


def test_same_text_does_not_match_in_wrong_view() -> None:
    node = ConfigNode(
        kind=NodeKind.COMMAND,
        text="ip address 10.0.0.1 255.255.255.252",
        raw_text="ip address 10.0.0.1 255.255.255.252",
        line_number=1,
        indentation=0,
        parent_view_id="system",
    )

    assert match_command(node, _schema()) is None
```

- [ ] **Step 2: Run tests and verify failure**

```bash
pytest tests/schema/test_types.py tests/schema/test_matcher.py -v
```

Expected: FAIL because matcher and type decoder do not exist.

- [ ] **Step 3: Implement typed parameter decoding**

Create `src/ipcodex/schema/types.py`:

```python
from __future__ import annotations

from ipaddress import IPv4Address, IPv4Network
from typing import Any


def _decode_mask(value: str) -> int:
    if value.isdigit():
        prefix = int(value)
        if not 0 <= prefix <= 32:
            raise ValueError(f"Invalid IPv4 prefix length: {value}")
        return prefix
    return IPv4Network(f"0.0.0.0/{value}").prefixlen


def _decode_vlan_expression(value: str) -> tuple[int, ...]:
    tokens = value.split()
    vlans: list[int] = []
    index = 0
    while index < len(tokens):
        start = int(tokens[index])
        if index + 2 < len(tokens) and tokens[index + 1] == "to":
            end = int(tokens[index + 2])
            vlans.extend(range(start, end + 1))
            index += 3
        else:
            vlans.append(start)
            index += 1
    if any(vlan < 1 or vlan > 4094 for vlan in vlans):
        raise ValueError(f"VLAN out of range: {value}")
    return tuple(dict.fromkeys(vlans))


def decode_parameter(type_name: str, value: str | None) -> Any:
    if value is None:
        return None
    if type_name == "ipv4_address":
        return IPv4Address(value)
    if type_name == "ipv4_netmask_or_prefix":
        return _decode_mask(value)
    if type_name == "integer":
        return int(value)
    if type_name == "vlan_expression":
        return _decode_vlan_expression(value)
    if type_name == "boolean_token":
        return value is not None
    if type_name in {
        "identifier",
        "string",
        "route_distinguisher",
        "route_target",
        "enum",
    }:
        return value
    raise ValueError(f"Unsupported parameter type: {type_name}")
```

- [ ] **Step 4: Implement command matching**

Create `src/ipcodex/schema/matcher.py`:

```python
from __future__ import annotations

import re
from typing import Any

from pydantic import BaseModel, ConfigDict

from ipcodex.cst.models import ConfigNode
from ipcodex.schema.models import SchemaBundle
from ipcodex.schema.types import decode_parameter


class CommandMatch(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True, frozen=True)

    command_id: str
    semantic_handler: str | None
    parameters: dict[str, Any]


def match_command(node: ConfigNode, schema: SchemaBundle) -> CommandMatch | None:
    parent_view = node.parent_view_id or "system"
    for spec in schema.commands.values():
        if parent_view not in spec.views:
            continue
        match = re.fullmatch(spec.pattern, node.text)
        if match is None:
            continue
        captures = match.groupdict()
        parameters = {
            parameter.name: decode_parameter(
                parameter.type,
                captures.get(parameter.name),
            )
            for parameter in spec.parameters
        }
        return CommandMatch(
            command_id=spec.id,
            semantic_handler=spec.semantic_handler,
            parameters=parameters,
        )
    return None
```

- [ ] **Step 5: Run the tests**

```bash
pytest tests/schema/test_types.py tests/schema/test_matcher.py -v
```

Expected: `5 passed`.

- [ ] **Step 6: Commit**

```bash
git add src/ipcodex/schema tests/schema
git commit -m "feat: match vrp commands and decode parameters"
```

---

### Task 6: Build Device, Interface, and Evidence Semantic Models

**Files:**
- Create: `IPCodex/src/ipcodex/semantic/__init__.py`
- Create: `IPCodex/src/ipcodex/semantic/models.py`
- Create: `IPCodex/src/ipcodex/semantic/system.py`
- Create: `IPCodex/src/ipcodex/semantic/interface.py`
- Create: `IPCodex/tests/semantic/test_system.py`
- Create: `IPCodex/tests/semantic/test_interface.py`

**Interfaces:**
- Produces evidence-aware semantic models.
- Interface view capture `interface_name` creates exactly one `InterfaceConfig`.
- Explicit source precedence is last-command-wins within one configuration snapshot, while retaining all evidence records.

- [ ] **Step 1: Write failing semantic tests**

Create `tests/semantic/test_system.py`:

```python
from ipcodex.semantic.models import DeviceConfig
from ipcodex.semantic.system import apply_sysname


def test_apply_sysname_sets_explicit_hostname_with_evidence() -> None:
    device = DeviceConfig(source_name="leaf.cfg")

    apply_sysname(device, hostname="Leaf01", line_number=1, raw_text="sysname Leaf01")

    assert device.hostname.value == "Leaf01"
    assert device.hostname.source == "explicit"
    assert device.hostname.evidence[-1].line_number == 1
```

Create `tests/semantic/test_interface.py`:

```python
from ipcodex.semantic.interface import (
    apply_interface_command,
    create_interface,
)


def test_interface_commands_build_typed_state() -> None:
    interface = create_interface(
        name="100GE1/0/1",
        line_number=10,
        raw_text="interface 100GE1/0/1",
    )

    apply_interface_command(
        interface,
        handler="interface.description",
        parameters={"description": "TO-SPINE01"},
        line_number=11,
        raw_text=" description TO-SPINE01",
    )
    apply_interface_command(
        interface,
        handler="interface.undo_portswitch",
        parameters={},
        line_number=12,
        raw_text=" undo portswitch",
    )
    apply_interface_command(
        interface,
        handler="interface.ip_address",
        parameters={"address": "10.0.0.1", "mask": 30, "sub": None},
        line_number=13,
        raw_text=" ip address 10.0.0.1 255.255.255.252",
    )

    assert interface.description.value == "TO-SPINE01"
    assert interface.layer_mode.value == "layer3"
    assert str(interface.ipv4_addresses[0].interface) == "10.0.0.1/30"
```

- [ ] **Step 2: Run tests and verify failure**

```bash
pytest tests/semantic/test_system.py tests/semantic/test_interface.py -v
```

Expected: FAIL because semantic models do not exist.

- [ ] **Step 3: Implement evidence-aware semantic models**

Create `src/ipcodex/semantic/models.py`:

```python
from __future__ import annotations

from ipaddress import IPv4Interface, IPv4Network
from typing import Generic, Literal, TypeVar

from pydantic import BaseModel, ConfigDict, Field


T = TypeVar("T")


class Evidence(BaseModel):
    model_config = ConfigDict(frozen=True)

    line_number: int
    raw_text: str
    command_id: str | None = None


class ExplicitValue(BaseModel, Generic[T]):
    value: T | None = None
    source: Literal["explicit", "unknown"] = "unknown"
    evidence: list[Evidence] = Field(default_factory=list)


class IPv4AddressConfig(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    interface: IPv4Interface
    is_sub: bool = False
    evidence: Evidence


class InterfaceConfig(BaseModel):
    name: str
    creation_evidence: Evidence
    description: ExplicitValue[str] = Field(default_factory=ExplicitValue[str])
    admin_enabled: ExplicitValue[bool] = Field(default_factory=ExplicitValue[bool])
    layer_mode: ExplicitValue[str] = Field(default_factory=ExplicitValue[str])
    vrf_name: ExplicitValue[str] = Field(default_factory=ExplicitValue[str])
    eth_trunk_id: ExplicitValue[int] = Field(default_factory=ExplicitValue[int])
    ipv4_addresses: list[IPv4AddressConfig] = Field(default_factory=list)


class VpnInstanceConfig(BaseModel):
    name: str
    creation_evidence: Evidence
    route_distinguisher: ExplicitValue[str] = Field(default_factory=ExplicitValue[str])
    import_route_targets: list[str] = Field(default_factory=list)
    export_route_targets: list[str] = Field(default_factory=list)
    evidence: list[Evidence] = Field(default_factory=list)


class StaticRouteConfig(BaseModel):
    prefix: IPv4Network
    next_hop: str
    preference: int | None = None
    evidence: Evidence


class UnknownItem(BaseModel):
    line_number: int
    raw_text: str
    current_view: str
    reason: str


class CoverageMetrics(BaseModel):
    total_non_blank_lines: int = 0
    structurally_mapped_lines: int = 0
    command_lines: int = 0
    semantically_recognized_lines: int = 0
    structural_coverage: float = 0.0
    semantic_coverage: float = 0.0


class DeviceConfig(BaseModel):
    source_name: str
    vendor: str = "huawei"
    os: str = "vrp"
    hostname: ExplicitValue[str] = Field(default_factory=ExplicitValue[str])
    vlans: list[int] = Field(default_factory=list)
    interfaces: dict[str, InterfaceConfig] = Field(default_factory=dict)
    vpn_instances: dict[str, VpnInstanceConfig] = Field(default_factory=dict)
    static_routes: list[StaticRouteConfig] = Field(default_factory=list)
    unresolved_references: list[str] = Field(default_factory=list)
    unknown_items: list[UnknownItem] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    coverage: CoverageMetrics = Field(default_factory=CoverageMetrics)
```

- [ ] **Step 4: Implement explicit-value updates and sysname**

Create `src/ipcodex/semantic/system.py`:

```python
from __future__ import annotations

from typing import TypeVar

from ipcodex.semantic.models import DeviceConfig, Evidence, ExplicitValue


T = TypeVar("T")


def set_explicit(
    field: ExplicitValue[T],
    value: T,
    *,
    line_number: int,
    raw_text: str,
    command_id: str | None = None,
) -> None:
    field.value = value
    field.source = "explicit"
    field.evidence.append(
        Evidence(
            line_number=line_number,
            raw_text=raw_text,
            command_id=command_id,
        )
    )


def apply_sysname(
    device: DeviceConfig,
    *,
    hostname: str,
    line_number: int,
    raw_text: str,
) -> None:
    set_explicit(
        device.hostname,
        hostname,
        line_number=line_number,
        raw_text=raw_text,
        command_id="system_sysname",
    )
```

- [ ] **Step 5: Implement interface semantics**

Create `src/ipcodex/semantic/interface.py`:

```python
from __future__ import annotations

from ipaddress import IPv4Interface
from typing import Any

from ipcodex.semantic.models import Evidence, InterfaceConfig, IPv4AddressConfig
from ipcodex.semantic.system import set_explicit


def create_interface(
    *,
    name: str,
    line_number: int,
    raw_text: str,
) -> InterfaceConfig:
    return InterfaceConfig(
        name=name,
        creation_evidence=Evidence(line_number=line_number, raw_text=raw_text),
    )


def apply_interface_command(
    interface: InterfaceConfig,
    *,
    handler: str,
    parameters: dict[str, Any],
    line_number: int,
    raw_text: str,
) -> None:
    command_id = handler.replace(".", "_")
    common = {
        "line_number": line_number,
        "raw_text": raw_text,
        "command_id": command_id,
    }

    if handler == "interface.description":
        set_explicit(interface.description, parameters["description"], **common)
    elif handler == "interface.shutdown":
        set_explicit(interface.admin_enabled, False, **common)
    elif handler == "interface.undo_shutdown":
        set_explicit(interface.admin_enabled, True, **common)
    elif handler == "interface.undo_portswitch":
        set_explicit(interface.layer_mode, "layer3", **common)
    elif handler == "interface.bind_vrf":
        set_explicit(interface.vrf_name, parameters["vrf_name"], **common)
    elif handler == "interface.eth_trunk_member":
        set_explicit(interface.eth_trunk_id, parameters["trunk_id"], **common)
    elif handler == "interface.ip_address":
        interface.ipv4_addresses.append(
            IPv4AddressConfig(
                interface=IPv4Interface(
                    f'{parameters["address"]}/{parameters["mask"]}'
                ),
                is_sub=bool(parameters.get("sub")),
                evidence=Evidence(**common),
            )
        )
    else:
        raise ValueError(f"Unsupported interface handler: {handler}")
```

Create package marker:

```python
# src/ipcodex/semantic/__init__.py
```

- [ ] **Step 6: Run the semantic tests**

```bash
pytest tests/semantic/test_system.py tests/semantic/test_interface.py -v
```

Expected: `2 passed`.

- [ ] **Step 7: Commit**

```bash
git add src/ipcodex/semantic tests/semantic
git commit -m "feat: model device and interface configuration semantics"
```

---

### Task 7: Add VLAN, VPN Instance, RD/RT, and Static Route Semantics

**Files:**
- Create: `IPCodex/src/ipcodex/semantic/network.py`
- Create: `IPCodex/tests/semantic/test_network.py`

**Interfaces:**
- Produces `apply_vlan_batch`, `create_vpn_instance`, `apply_vpn_command`, and `apply_static_route`.
- VLAN output is sorted and deduplicated.
- RD/RT values remain strings because Huawei accepts multiple textual formats.

- [ ] **Step 1: Write failing network semantic tests**

Create `tests/semantic/test_network.py`:

```python
from ipaddress import IPv4Address

from ipcodex.semantic.models import DeviceConfig
from ipcodex.semantic.network import (
    apply_static_route,
    apply_vlan_batch,
    apply_vpn_command,
    create_vpn_instance,
)


def test_vlan_batch_is_sorted_and_deduplicated() -> None:
    device = DeviceConfig(source_name="leaf.cfg")

    apply_vlan_batch(
        device,
        vlans=(200, 100, 101, 100),
        line_number=2,
        raw_text="vlan batch 200 100 101 100",
    )

    assert device.vlans == [100, 101, 200]


def test_vpn_rd_and_route_targets_are_recorded() -> None:
    vpn = create_vpn_instance(
        name="VPN-A",
        line_number=10,
        raw_text="ip vpn-instance VPN-A",
    )

    apply_vpn_command(
        vpn,
        handler="network.vpn_rd",
        parameters={"rd": "65001:100"},
        line_number=12,
        raw_text="  route-distinguisher 65001:100",
    )
    apply_vpn_command(
        vpn,
        handler="network.vpn_target",
        parameters={"rt": "65000:100", "direction": "import-extcommunity"},
        line_number=13,
        raw_text="  vpn-target 65000:100 import-extcommunity",
    )

    assert vpn.route_distinguisher.value == "65001:100"
    assert vpn.import_route_targets == ["65000:100"]


def test_static_route_normalizes_prefix() -> None:
    device = DeviceConfig(source_name="leaf.cfg")

    apply_static_route(
        device,
        parameters={
            "prefix": IPv4Address("0.0.0.0"),
            "mask": 0,
            "next_hop": IPv4Address("10.0.0.2"),
            "preference": None,
        },
        line_number=20,
        raw_text="ip route-static 0.0.0.0 0.0.0.0 10.0.0.2",
    )

    assert str(device.static_routes[0].prefix) == "0.0.0.0/0"
    assert device.static_routes[0].next_hop == "10.0.0.2"
```

- [ ] **Step 2: Run tests and verify failure**

```bash
pytest tests/semantic/test_network.py -v
```

Expected: FAIL because `semantic.network` does not exist.

- [ ] **Step 3: Implement network semantics**

Create `src/ipcodex/semantic/network.py`:

```python
from __future__ import annotations

from ipaddress import IPv4Network
from typing import Any

from ipcodex.semantic.models import (
    DeviceConfig,
    Evidence,
    StaticRouteConfig,
    VpnInstanceConfig,
)
from ipcodex.semantic.system import set_explicit


def apply_vlan_batch(
    device: DeviceConfig,
    *,
    vlans: tuple[int, ...],
    line_number: int,
    raw_text: str,
) -> None:
    del line_number, raw_text
    device.vlans = sorted(set(device.vlans).union(vlans))


def create_vpn_instance(
    *,
    name: str,
    line_number: int,
    raw_text: str,
) -> VpnInstanceConfig:
    return VpnInstanceConfig(
        name=name,
        creation_evidence=Evidence(line_number=line_number, raw_text=raw_text),
    )


def apply_vpn_command(
    vpn: VpnInstanceConfig,
    *,
    handler: str,
    parameters: dict[str, Any],
    line_number: int,
    raw_text: str,
) -> None:
    evidence = Evidence(
        line_number=line_number,
        raw_text=raw_text,
        command_id=handler.replace(".", "_"),
    )
    vpn.evidence.append(evidence)

    if handler == "network.vpn_rd":
        set_explicit(
            vpn.route_distinguisher,
            parameters["rd"],
            line_number=line_number,
            raw_text=raw_text,
            command_id="vpn_rd",
        )
    elif handler == "network.vpn_target":
        target = parameters["rt"]
        direction = parameters["direction"]
        if direction == "import-extcommunity":
            vpn.import_route_targets = sorted(
                set(vpn.import_route_targets).union({target})
            )
        elif direction == "export-extcommunity":
            vpn.export_route_targets = sorted(
                set(vpn.export_route_targets).union({target})
            )
        else:
            raise ValueError(f"Unsupported VPN target direction: {direction}")
    else:
        raise ValueError(f"Unsupported VPN handler: {handler}")


def apply_static_route(
    device: DeviceConfig,
    *,
    parameters: dict[str, Any],
    line_number: int,
    raw_text: str,
) -> None:
    prefix = IPv4Network(
        f'{parameters["prefix"]}/{parameters["mask"]}',
        strict=False,
    )
    device.static_routes.append(
        StaticRouteConfig(
            prefix=prefix,
            next_hop=str(parameters["next_hop"]),
            preference=parameters.get("preference"),
            evidence=Evidence(
                line_number=line_number,
                raw_text=raw_text,
                command_id="static_route_ipv4",
            ),
        )
    )
```

- [ ] **Step 4: Run the tests**

```bash
pytest tests/semantic/test_network.py -v
```

Expected: `3 passed`.

- [ ] **Step 5: Commit**

```bash
git add src/ipcodex/semantic/network.py tests/semantic/test_network.py
git commit -m "feat: parse vlan vrf and static route semantics"
```

---

### Task 8: Traverse the CST, Build the Semantic Model, and Resolve References

**Files:**
- Create: `IPCodex/src/ipcodex/semantic/registry.py`
- Create: `IPCodex/tests/test_pipeline.py`
- Create: `IPCodex/samples/huawei/ce_leaf_minimal.cfg`

**Interfaces:**
- Consumes `ConfigTree` and `SchemaBundle`.
- Produces `DeviceConfig` and populates unknown items and unresolved references.
- A configuration line with a valid structure but no matching `CommandSpec` counts as structurally mapped and semantically unknown.

- [ ] **Step 1: Create the primary golden sample**

Create `samples/huawei/ce_leaf_minimal.cfg`:

```text
sysname Leaf01
#
vlan batch 100 200 to 202
#
interface Eth-Trunk10
 description TO-SERVER-A
 port link-type trunk
 port trunk allow-pass vlan 100
#
interface 100GE1/0/1
 description TO-SPINE01
 undo portswitch
 ip address 10.0.0.1 255.255.255.252
#
interface Vbdif100
 ip binding vpn-instance VPN-A
 ip address 192.168.100.1 255.255.255.0
#
ip vpn-instance VPN-A
 ipv4-family
  route-distinguisher 65001:100
  vpn-target 65000:100 export-extcommunity
  vpn-target 65000:100 import-extcommunity
 #
#
ip route-static 0.0.0.0 0.0.0.0 10.0.0.2
#
return
```

The two trunk commands are intentionally outside the semantic MVP and must appear as unknown commands without causing failure.

- [ ] **Step 2: Write the failing end-to-end semantic test**

Create `tests/test_pipeline.py`:

```python
from importlib.resources import files
from pathlib import Path

from ipcodex.cst.parser import parse_cst
from ipcodex.schema.loader import load_schema_bundle
from ipcodex.semantic.registry import build_semantic_model
from ipcodex.source import load_config


SAMPLE = Path("samples/huawei/ce_leaf_minimal.cfg")


def test_build_semantic_model_from_huawei_configuration() -> None:
    schema = load_schema_bundle(files("ipcodex.schema").joinpath("huawei_vrp"))
    tree = parse_cst(load_config(SAMPLE), schema)

    device = build_semantic_model(tree, schema)

    assert device.hostname.value == "Leaf01"
    assert device.vlans == [100, 200, 201, 202]
    assert device.interfaces["100GE1/0/1"].layer_mode.value == "layer3"
    assert device.interfaces["Vbdif100"].vrf_name.value == "VPN-A"
    assert device.vpn_instances["VPN-A"].route_distinguisher.value == "65001:100"
    assert str(device.static_routes[0].prefix) == "0.0.0.0/0"
    assert device.unresolved_references == []
    assert {item.raw_text.strip() for item in device.unknown_items} == {
        "port link-type trunk",
        "port trunk allow-pass vlan 100",
    }
    assert device.coverage.structural_coverage == 1.0
    assert device.coverage.semantic_coverage >= 0.85
```

- [ ] **Step 3: Run the test and verify failure**

```bash
pytest tests/test_pipeline.py -v
```

Expected: FAIL because semantic registry traversal does not exist.

- [ ] **Step 4: Implement semantic traversal and dispatch**

Create `src/ipcodex/semantic/registry.py`:

```python
from __future__ import annotations

from ipcodex.cst.models import ConfigNode, ConfigTree, NodeKind
from ipcodex.schema.matcher import match_command
from ipcodex.schema.models import SchemaBundle
from ipcodex.semantic.interface import apply_interface_command, create_interface
from ipcodex.semantic.models import DeviceConfig, UnknownItem
from ipcodex.semantic.network import (
    apply_static_route,
    apply_vlan_batch,
    apply_vpn_command,
    create_vpn_instance,
)
from ipcodex.semantic.system import apply_sysname


def build_semantic_model(
    tree: ConfigTree,
    schema: SchemaBundle,
) -> DeviceConfig:
    device = DeviceConfig(source_name=tree.source_name)
    command_lines = 0
    recognized_lines = 0

    def visit(node: ConfigNode, interface_name: str | None, vpn_name: str | None) -> None:
        nonlocal command_lines, recognized_lines

        if node.kind == NodeKind.VIEW and node.view_id == "interface":
            interface_name = node.captures["interface_name"]
            device.interfaces[interface_name] = create_interface(
                name=interface_name,
                line_number=node.line_number or 0,
                raw_text=node.raw_text,
            )

        if node.kind == NodeKind.VIEW and node.view_id == "vpn_instance":
            vpn_name = node.captures["vrf_name"]
            device.vpn_instances[vpn_name] = create_vpn_instance(
                name=vpn_name,
                line_number=node.line_number or 0,
                raw_text=node.raw_text,
            )

        if node.kind == NodeKind.COMMAND:
            command_lines += 1
            matched = match_command(node, schema)
            if matched is None:
                device.unknown_items.append(
                    UnknownItem(
                        line_number=node.line_number or 0,
                        raw_text=node.raw_text,
                        current_view=node.parent_view_id or "system",
                        reason="no_command_schema_match",
                    )
                )
            else:
                recognized_lines += 1
                handler = matched.semantic_handler
                parameters = matched.parameters

                if handler == "system.sysname":
                    apply_sysname(
                        device,
                        hostname=parameters["hostname"],
                        line_number=node.line_number or 0,
                        raw_text=node.raw_text,
                    )
                elif handler == "network.vlan_batch":
                    apply_vlan_batch(
                        device,
                        vlans=parameters["vlan_expression"],
                        line_number=node.line_number or 0,
                        raw_text=node.raw_text,
                    )
                elif handler and handler.startswith("interface.") and interface_name:
                    apply_interface_command(
                        device.interfaces[interface_name],
                        handler=handler,
                        parameters=parameters,
                        line_number=node.line_number or 0,
                        raw_text=node.raw_text,
                    )
                elif handler and handler.startswith("network.vpn_") and vpn_name:
                    apply_vpn_command(
                        device.vpn_instances[vpn_name],
                        handler=handler,
                        parameters=parameters,
                        line_number=node.line_number or 0,
                        raw_text=node.raw_text,
                    )
                elif handler == "network.static_route":
                    apply_static_route(
                        device,
                        parameters=parameters,
                        line_number=node.line_number or 0,
                        raw_text=node.raw_text,
                    )

        for child in node.children:
            visit(child, interface_name, vpn_name)

    visit(tree.root, None, None)

    for interface in device.interfaces.values():
        vrf_name = interface.vrf_name.value
        if vrf_name and vrf_name not in device.vpn_instances:
            device.unresolved_references.append(
                f"interface:{interface.name}->vpn_instance:{vrf_name}"
            )

    total_source_lines = len(tree.source_lines)
    total_non_blank = sum(not line.is_blank for line in tree.source_lines)
    structurally_mapped = len(tree.mapped_line_numbers)
    device.coverage.total_non_blank_lines = total_non_blank
    device.coverage.structurally_mapped_lines = structurally_mapped
    device.coverage.command_lines = command_lines
    device.coverage.semantically_recognized_lines = recognized_lines
    device.coverage.structural_coverage = (
        structurally_mapped / total_source_lines if total_source_lines else 1.0
    )
    device.coverage.semantic_coverage = (
        recognized_lines / command_lines if command_lines else 1.0
    )
    return device
```

- [ ] **Step 5: Run the integration test**

```bash
pytest tests/test_pipeline.py -v
```

Expected: `1 passed`.

- [ ] **Step 6: Add a missing-VRF reference test**

Append to `tests/test_pipeline.py`:

```python
from ipcodex.source import preprocess_text


def test_missing_vpn_instance_is_reported_as_unresolved_reference() -> None:
    schema = load_schema_bundle(files("ipcodex.schema").joinpath("huawei_vrp"))
    document = preprocess_text(
        "interface Vbdif100\n"
        " ip binding vpn-instance MISSING\n"
        "#\n",
        source_name="missing.cfg",
    )
    tree = parse_cst(document, schema)

    device = build_semantic_model(tree, schema)

    assert device.unresolved_references == [
        "interface:Vbdif100->vpn_instance:MISSING"
    ]
```

- [ ] **Step 7: Run all pipeline tests**

```bash
pytest tests/test_pipeline.py -v
```

Expected: `2 passed`.

- [ ] **Step 8: Commit**

```bash
git add src/ipcodex/semantic/registry.py samples tests/test_pipeline.py
git commit -m "feat: build semantic model and resolve configuration references"
```

---

### Task 9: Add the Public Parse Pipeline and Deterministic JSON CLI

**Files:**
- Create: `IPCodex/src/ipcodex/pipeline.py`
- Replace: `IPCodex/src/ipcodex/cli.py`
- Create: `IPCodex/tests/test_cli.py`

**Interfaces:**
- Produces `ParseResult` and `parse_file`.
- CLI command: `ipcodex parse INPUT --output OUTPUT [--schema-root PATH]`.
- JSON must be UTF-8, sorted by key, indented by two spaces, and end with a newline.

- [ ] **Step 1: Write the failing CLI test**

Create `tests/test_cli.py`:

```python
import json
from pathlib import Path

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
```

- [ ] **Step 2: Run the test and verify failure**

```bash
pytest tests/test_cli.py -v
```

Expected: FAIL because the public pipeline and CLI are not implemented.

- [ ] **Step 3: Implement the public pipeline**

Create `src/ipcodex/pipeline.py`:

```python
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
```

- [ ] **Step 4: Implement the CLI**

Replace `src/ipcodex/cli.py`:

```python
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
```

- [ ] **Step 5: Run the CLI test**

```bash
pytest tests/test_cli.py -v
```

Expected: `1 passed`.

- [ ] **Step 6: Run the CLI manually**

```bash
ipcodex parse samples/huawei/ce_leaf_minimal.cfg --output build/leaf01.json
```

Expected:

- Exit code `0`.
- `build/leaf01.json` exists.
- `device.hostname.value` is `Leaf01`.
- `device.unknown_items` contains the two unsupported trunk commands.

- [ ] **Step 7: Commit**

```bash
git add src/ipcodex/pipeline.py src/ipcodex/cli.py tests/test_cli.py
git commit -m "feat: expose vrp parser through deterministic json cli"
```

---

### Task 10: Add Golden Output Regression Tests and Parser Quality Gates

**Files:**
- Create: `IPCodex/samples/huawei/ce_unknown_commands.cfg`
- Create: `IPCodex/tests/fixtures/ce_leaf_minimal.expected.json`
- Create: `IPCodex/tests/fixtures/ce_unknown_commands.expected.json`
- Modify: `IPCodex/tests/test_pipeline.py`
- Modify: `IPCodex/README.md`

**Interfaces:**
- Golden JSON files define the contract for stable parser output.
- Regression tests compare canonical JSON rather than Pydantic object identity.

- [ ] **Step 1: Create an unknown-command resilience fixture**

Create `samples/huawei/ce_unknown_commands.cfg`:

```text
sysname Edge01
#
interface GigabitEthernet0/0/1
 description INTERNET
 undo portswitch
 ip address 203.0.113.1 255.255.255.252
 proprietary-feature enable
#
experimental top-level command
#
return
```

- [ ] **Step 2: Generate golden outputs using the implemented CLI**

Run:

```bash
ipcodex parse samples/huawei/ce_leaf_minimal.cfg --output tests/fixtures/ce_leaf_minimal.expected.json
ipcodex parse samples/huawei/ce_unknown_commands.cfg --output tests/fixtures/ce_unknown_commands.expected.json
```

Expected: both JSON files are created and contain `schema_version = "0.1.0"`.

- [ ] **Step 3: Review and normalize volatile fields**

The MVP output must not include timestamps, absolute input paths, UUIDs, random identifiers, or environment-specific values. If any appear, remove them from the implementation before accepting the golden files.

- [ ] **Step 4: Add golden regression tests**

Append to `tests/test_pipeline.py`:

```python
import json

from ipcodex.pipeline import parse_file


@pytest.mark.parametrize(
    ("config_path", "expected_path"),
    [
        (
            Path("samples/huawei/ce_leaf_minimal.cfg"),
            Path("tests/fixtures/ce_leaf_minimal.expected.json"),
        ),
        (
            Path("samples/huawei/ce_unknown_commands.cfg"),
            Path("tests/fixtures/ce_unknown_commands.expected.json"),
        ),
    ],
)
def test_parser_matches_golden_json(
    config_path: Path,
    expected_path: Path,
) -> None:
    actual = parse_file(config_path).model_dump(mode="json")
    expected = json.loads(expected_path.read_text(encoding="utf-8"))

    assert actual == expected
```

Add these imports at the top of the file:

```python
import pytest
```

- [ ] **Step 5: Add structural line-coverage assertion**

Append to `tests/test_pipeline.py`:

```python
def test_every_source_line_is_mapped_in_cst() -> None:
    result = parse_file(Path("samples/huawei/ce_leaf_minimal.cfg"))
    input_line_count = len(
        Path("samples/huawei/ce_leaf_minimal.cfg")
        .read_text(encoding="utf-8")
        .splitlines()
    )

    assert result.tree.mapped_line_numbers == tuple(range(1, input_line_count + 1))
    assert result.device.coverage.structural_coverage == 1.0
```

- [ ] **Step 6: Run all tests with coverage**

```bash
pytest -q --cov=ipcodex --cov-report=term-missing
```

Expected:

- All tests pass.
- No missing lines in core source/schema/CST modules that reduce their combined coverage below 90%.
- The primary sample semantic coverage is at least 85%.

- [ ] **Step 7: Document usage and schema-extension workflow**

Append to `README.md`:

````markdown
## Parse a Huawei VRP Configuration

```bash
ipcodex parse samples/huawei/ce_leaf_minimal.cfg --output build/leaf01.json
```

The output contains:

- a lossless configuration tree with source line evidence;
- typed semantic objects for the MVP command set;
- unknown commands with current-view context;
- unresolved object references;
- structural and semantic parsing coverage.

## Add a Huawei Command

1. Add or update a `CommandSpec` in
   `src/ipcodex/schema/huawei_vrp/commands.yaml`.
2. Add parameter decoding only when the parameter type is not already present in
   `src/ipcodex/schema/types.py`.
3. Add a focused matcher test.
4. Add a semantic handler and focused semantic test when the command changes the
   typed device model.
5. Update the appropriate golden fixture and inspect the complete JSON diff.

## Add a Huawei Configuration View

1. Add a `ViewSpec` to `src/ipcodex/schema/huawei_vrp/views.yaml`.
2. Declare every allowed parent explicitly.
3. Add a CST test covering opening, nesting, and `#`-separator closure.
4. Add a malformed-parent test proving the view is not accepted in an invalid
   context.
````

- [ ] **Step 8: Commit**

```bash
git add README.md samples tests
git commit -m "test: add golden vrp parser regression suite"
```

---

## Final Verification

Run all commands from `IPCodex/`:

```bash
source .venv/bin/activate
python -m pip install -e '.[dev]'
pytest -q --cov=ipcodex --cov-report=term-missing
rm -rf build
ipcodex parse samples/huawei/ce_leaf_minimal.cfg --output build/leaf01.json
python -m ipcodex parse samples/huawei/ce_unknown_commands.cfg --output build/unknown.json
```

Verify manually:

- `build/leaf01.json` and `build/unknown.json` are valid UTF-8 JSON.
- Both commands exit with status `0`.
- No input command line is lost.
- Unknown commands include line number, raw text, current view, and reason.
- Interface and VPN instance objects include source evidence.
- Output contains no timestamps, absolute paths, random IDs, or machine-specific data.
- A second run produces files identical to the first run.

Use `CodexPro.show_changes` to review repository status and the complete diff.

Expected: only intentionally generated `build/` output, or a clean tree after `build/` is added to `.gitignore`; no source changes should be unreviewed.

Create `.gitignore` before final commit if it does not already exist:

```text
.venv/
__pycache__/
.pytest_cache/
.coverage
htmlcov/
build/
*.pyc
```

Final commit:

```bash
git add .gitignore
git commit -m "chore: finalize huawei vrp parser mvp"
```

---

## Post-MVP Roadmap

The following work must start only after this plan's acceptance criteria pass:

1. Add product/model/VRP-version metadata and version-specific schema overlays.
2. Add Huawei CLI help and command-reference ingestion into the schema-authoring workflow.
3. Add BGP view hierarchy, peer groups, address families, and inheritance resolution.
4. Add OSPF, IS-IS, BFD, route-policy, and IP-prefix semantic models.
5. Add EVPN, VXLAN, VNI, VBDIF, NVE/VTEP, and M-LAG parsing.
6. Parse operational outputs such as `display interface`, `display lldp neighbor`, and `display bgp peer` through separate templates.
7. Build cross-device relationship restoration only after semantic models and golden regression coverage are stable.
8. Build configuration analysis rules only against the vendor-independent semantic model, never directly against raw CLI text.
