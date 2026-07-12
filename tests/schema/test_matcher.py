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
