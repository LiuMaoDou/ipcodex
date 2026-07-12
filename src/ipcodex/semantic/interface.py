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
