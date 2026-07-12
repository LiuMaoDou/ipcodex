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
