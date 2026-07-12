from ipcodex.semantic.models import DeviceConfig
from ipcodex.semantic.system import apply_sysname


def test_apply_sysname_sets_explicit_hostname_with_evidence() -> None:
    device = DeviceConfig(source_name="leaf.cfg")

    apply_sysname(device, hostname="Leaf01", line_number=1, raw_text="sysname Leaf01")

    assert device.hostname.value == "Leaf01"
    assert device.hostname.source == "explicit"
    assert device.hostname.evidence[-1].line_number == 1
