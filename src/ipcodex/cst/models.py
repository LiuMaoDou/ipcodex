from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

from ipcodex.source import SourceLine


class NodeKind(StrEnum):
    ROOT = "root"
    VIEW = "view"
    COMMAND = "command"
    BLANK = "blank"


class ConfigNode(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    kind: NodeKind
    text: str
    raw_text: str
    line_number: int | None
    indentation: int
    view_id: str | None = None
    parent_view_id: str | None = None
    captures: dict[str, str] = Field(default_factory=dict)
    children: list["ConfigNode"] = Field(default_factory=list)
    closing_line_number: int | None = None


class ConfigTree(BaseModel):
    root: ConfigNode
    source_name: str
    source_lines: tuple[SourceLine, ...]
    mapped_line_numbers: tuple[int, ...]
    warnings: tuple[str, ...] = ()
