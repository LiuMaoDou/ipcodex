from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class ParameterSpec(BaseModel):
    model_config = ConfigDict(frozen=True)

    name: str
    type: str
    required: bool = True


class ViewSpec(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str
    enter_pattern: str | None = None
    allowed_parents: tuple[str, ...] = ()
    closes_on_hash: bool = True


class CommandSpec(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str
    views: tuple[str, ...]
    pattern: str
    parameters: tuple[ParameterSpec, ...] = ()
    semantic_handler: str | None = None


class SchemaBundle(BaseModel):
    model_config = ConfigDict(frozen=True)

    vendor: str
    os: str
    schema_version: str
    views: dict[str, ViewSpec] = Field(default_factory=dict)
    commands: dict[str, CommandSpec] = Field(default_factory=dict)
