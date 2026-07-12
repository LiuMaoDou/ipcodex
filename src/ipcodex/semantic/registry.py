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
