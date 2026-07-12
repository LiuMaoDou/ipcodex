from __future__ import annotations

import re
from typing import Any

from pydantic import BaseModel, ConfigDict

from ipcodex.cst.models import ConfigNode
from ipcodex.schema.models import SchemaBundle
from ipcodex.schema.types import decode_parameter


class CommandMatch(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True, frozen=True)

    command_id: str
    semantic_handler: str | None
    parameters: dict[str, Any]


def match_command(node: ConfigNode, schema: SchemaBundle) -> CommandMatch | None:
    parent_view = node.parent_view_id or "system"
    for spec in schema.commands.values():
        if parent_view not in spec.views:
            continue
        match = re.fullmatch(spec.pattern, node.text)
        if match is None:
            continue
        captures = match.groupdict()
        parameters = {
            parameter.name: decode_parameter(
                parameter.type,
                captures.get(parameter.name),
            )
            for parameter in spec.parameters
        }
        return CommandMatch(
            command_id=spec.id,
            semantic_handler=spec.semantic_handler,
            parameters=parameters,
        )
    return None
