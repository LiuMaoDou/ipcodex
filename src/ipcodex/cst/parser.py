from __future__ import annotations

import re

from ipcodex.cst.models import ConfigNode, ConfigTree, NodeKind
from ipcodex.schema.models import SchemaBundle, ViewSpec
from ipcodex.source import SourceDocument, SourceLine


def _match_view(text: str, current_view_id: str, schema: SchemaBundle):
    for view in schema.views.values():
        if view.enter_pattern is None or current_view_id not in view.allowed_parents:
            continue
        match = re.fullmatch(view.enter_pattern, text)
        if match:
            return view, match.groupdict()
    return None


def _close_for_separator(
    stack: list[ConfigNode],
    separator: SourceLine,
) -> None:
    while len(stack) > 1 and stack[-1].indentation >= separator.indentation:
        closed = stack.pop()
        closed.closing_line_number = separator.line_number


def _find_parent_index(
    stack: list[ConfigNode],
    view: ViewSpec,
    indentation: int,
) -> int:
    for index in range(len(stack) - 1, -1, -1):
        candidate = stack[index]
        candidate_view = candidate.view_id or "system"
        if candidate_view in view.allowed_parents and candidate.indentation < indentation:
            return index
    if "system" in view.allowed_parents:
        return 0
    raise ValueError(
        f"No allowed parent for view {view.id} at indentation {indentation}"
    )


def parse_cst(document: SourceDocument, schema: SchemaBundle) -> ConfigTree:
    root = ConfigNode(
        kind=NodeKind.ROOT,
        text="system",
        raw_text="",
        line_number=None,
        indentation=-1,
        view_id="system",
    )
    stack = [root]
    mapped: list[int] = []
    warnings: list[str] = []

    for source_line in document.lines:
        mapped.append(source_line.line_number)
        stripped = source_line.normalized_text.strip()

        if source_line.is_blank:
            stack[-1].children.append(
                ConfigNode(
                    kind=NodeKind.BLANK,
                    text="",
                    raw_text=source_line.raw_text,
                    line_number=source_line.line_number,
                    indentation=source_line.indentation,
                    parent_view_id=stack[-1].view_id,
                )
            )
            continue

        if stripped == "#":
            _close_for_separator(stack, source_line)
            continue

        current_view = stack[-1].view_id or "system"
        view_match = _match_view(stripped, current_view, schema)

        if view_match is None and source_line.indentation == 0:
            while len(stack) > 1:
                stack.pop()
            current_view = "system"
            view_match = _match_view(stripped, current_view, schema)

        if view_match is not None:
            view, captures = view_match
            parent_index = _find_parent_index(stack, view, source_line.indentation)
            del stack[parent_index + 1 :]
            parent = stack[-1]
            node = ConfigNode(
                kind=NodeKind.VIEW,
                text=stripped,
                raw_text=source_line.raw_text,
                line_number=source_line.line_number,
                indentation=source_line.indentation,
                view_id=view.id,
                parent_view_id=parent.view_id,
                captures=captures,
            )
            parent.children.append(node)
            stack.append(node)
            continue

        stack[-1].children.append(
            ConfigNode(
                kind=NodeKind.COMMAND,
                text=stripped,
                raw_text=source_line.raw_text,
                line_number=source_line.line_number,
                indentation=source_line.indentation,
                parent_view_id=stack[-1].view_id,
            )
        )

    return ConfigTree(
        root=root,
        source_name=document.source_name,
        source_lines=document.lines,
        mapped_line_numbers=tuple(mapped),
        warnings=tuple(warnings),
    )
