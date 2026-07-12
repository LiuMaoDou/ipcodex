import json
from importlib.resources import files
from pathlib import Path

import pytest

from ipcodex.cst.parser import parse_cst
from ipcodex.pipeline import parse_file
from ipcodex.schema.loader import load_schema_bundle
from ipcodex.semantic.registry import build_semantic_model
from ipcodex.source import load_config, preprocess_text


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


def test_every_source_line_is_mapped_in_cst() -> None:
    result = parse_file(Path("samples/huawei/ce_leaf_minimal.cfg"))
    input_line_count = len(
        Path("samples/huawei/ce_leaf_minimal.cfg")
        .read_text(encoding="utf-8")
        .splitlines()
    )

    assert result.tree.mapped_line_numbers == tuple(range(1, input_line_count + 1))
    assert result.device.coverage.structural_coverage == 1.0
