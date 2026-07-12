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
