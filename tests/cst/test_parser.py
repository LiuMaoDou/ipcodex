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
