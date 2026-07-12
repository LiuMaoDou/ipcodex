from __future__ import annotations

from ipaddress import IPv4Interface, IPv4Network
from typing import Generic, Literal, TypeVar

from pydantic import BaseModel, ConfigDict, Field


T = TypeVar("T")


class Evidence(BaseModel):
    model_config = ConfigDict(frozen=True)

    line_number: int
    raw_text: str
    command_id: str | None = None


class ExplicitValue(BaseModel, Generic[T]):
    value: T | None = None
    source: Literal["explicit", "unknown"] = "unknown"
    evidence: list[Evidence] = Field(default_factory=list)


class IPv4AddressConfig(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    interface: IPv4Interface
    is_sub: bool = False
    evidence: Evidence


class InterfaceConfig(BaseModel):
    name: str
    creation_evidence: Evidence
    description: ExplicitValue[str] = Field(default_factory=ExplicitValue[str])
    admin_enabled: ExplicitValue[bool] = Field(default_factory=ExplicitValue[bool])
    layer_mode: ExplicitValue[str] = Field(default_factory=ExplicitValue[str])
    vrf_name: ExplicitValue[str] = Field(default_factory=ExplicitValue[str])
    eth_trunk_id: ExplicitValue[int] = Field(default_factory=ExplicitValue[int])
    ipv4_addresses: list[IPv4AddressConfig] = Field(default_factory=list)


class VpnInstanceConfig(BaseModel):
    name: str
    creation_evidence: Evidence
    route_distinguisher: ExplicitValue[str] = Field(default_factory=ExplicitValue[str])
    import_route_targets: list[str] = Field(default_factory=list)
    export_route_targets: list[str] = Field(default_factory=list)
    evidence: list[Evidence] = Field(default_factory=list)


class StaticRouteConfig(BaseModel):
    prefix: IPv4Network
    next_hop: str
    preference: int | None = None
    evidence: Evidence


class UnknownItem(BaseModel):
    line_number: int
    raw_text: str
    current_view: str
    reason: str


class CoverageMetrics(BaseModel):
    total_non_blank_lines: int = 0
    structurally_mapped_lines: int = 0
    command_lines: int = 0
    semantically_recognized_lines: int = 0
    structural_coverage: float = 0.0
    semantic_coverage: float = 0.0


class DeviceConfig(BaseModel):
    source_name: str
    vendor: str = "huawei"
    os: str = "vrp"
    hostname: ExplicitValue[str] = Field(default_factory=ExplicitValue[str])
    vlans: list[int] = Field(default_factory=list)
    interfaces: dict[str, InterfaceConfig] = Field(default_factory=dict)
    vpn_instances: dict[str, VpnInstanceConfig] = Field(default_factory=dict)
    static_routes: list[StaticRouteConfig] = Field(default_factory=list)
    unresolved_references: list[str] = Field(default_factory=list)
    unknown_items: list[UnknownItem] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    coverage: CoverageMetrics = Field(default_factory=CoverageMetrics)
