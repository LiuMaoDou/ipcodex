from __future__ import annotations

from typing import TypeVar

from ipcodex.semantic.models import DeviceConfig, Evidence, ExplicitValue


T = TypeVar("T")


def set_explicit(
    field: ExplicitValue[T],
    value: T,
    *,
    line_number: int,
    raw_text: str,
    command_id: str | None = None,
) -> None:
    field.value = value
    field.source = "explicit"
    field.evidence.append(
        Evidence(
            line_number=line_number,
            raw_text=raw_text,
            command_id=command_id,
        )
    )


def apply_sysname(
    device: DeviceConfig,
    *,
    hostname: str,
    line_number: int,
    raw_text: str,
) -> None:
    set_explicit(
        device.hostname,
        hostname,
        line_number=line_number,
        raw_text=raw_text,
        command_id="system_sysname",
    )
