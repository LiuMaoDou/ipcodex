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
