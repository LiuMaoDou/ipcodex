from ipcodex.semantic.interface import (
    apply_interface_command,
    create_interface,
)


def test_interface_commands_build_typed_state() -> None:
    interface = create_interface(
        name="100GE1/0/1",
        line_number=10,
        raw_text="interface 100GE1/0/1",
    )

    apply_interface_command(
        interface,
        handler="interface.description",
        parameters={"description": "TO-SPINE01"},
        line_number=11,
        raw_text=" description TO-SPINE01",
    )
    apply_interface_command(
        interface,
        handler="interface.undo_portswitch",
        parameters={},
        line_number=12,
        raw_text=" undo portswitch",
    )
    apply_interface_command(
        interface,
        handler="interface.ip_address",
        parameters={"address": "10.0.0.1", "mask": 30, "sub": None},
        line_number=13,
        raw_text=" ip address 10.0.0.1 255.255.255.252",
    )

    assert interface.description.value == "TO-SPINE01"
    assert interface.layer_mode.value == "layer3"
    assert str(interface.ipv4_addresses[0].interface) == "10.0.0.1/30"
