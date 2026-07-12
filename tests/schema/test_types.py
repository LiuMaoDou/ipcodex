from ipaddress import IPv4Address

import pytest

from ipcodex.schema.types import decode_parameter


def test_decode_ipv4_address_and_mask() -> None:
    assert decode_parameter("ipv4_address", "10.0.0.1") == IPv4Address("10.0.0.1")
    assert decode_parameter("ipv4_netmask_or_prefix", "255.255.255.252") == 30
    assert decode_parameter("ipv4_netmask_or_prefix", "24") == 24


def test_decode_vlan_expression() -> None:
    assert decode_parameter("vlan_expression", "100 200 to 202") == (
        100,
        200,
        201,
        202,
    )


def test_reject_invalid_ipv4_mask() -> None:
    with pytest.raises(ValueError):
        decode_parameter("ipv4_netmask_or_prefix", "255.0.255.0")
