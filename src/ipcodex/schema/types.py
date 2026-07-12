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
