from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, ConfigDict


class SourceLine(BaseModel):
    model_config = ConfigDict(frozen=True)

    line_number: int
    raw_text: str
    normalized_text: str
    indentation: int
    is_blank: bool


class SourceDocument(BaseModel):
    model_config = ConfigDict(frozen=True)

    source_name: str
    raw_text: str
    lines: tuple[SourceLine, ...]


def _normalize_line(raw_line: str) -> str:
    return (
        raw_line.replace("---- More ----", "")
        .replace("\x1b[42D", "")
        .rstrip("\r\n")
        .rstrip()
    )


def preprocess_text(text: str, *, source_name: str) -> SourceDocument:
    lines: list[SourceLine] = []
    for line_number, raw_line in enumerate(text.splitlines(), start=1):
        normalized = _normalize_line(raw_line)
        indentation = len(normalized) - len(normalized.lstrip(" "))
        lines.append(
            SourceLine(
                line_number=line_number,
                raw_text=raw_line,
                normalized_text=normalized,
                indentation=indentation,
                is_blank=normalized.strip() == "",
            )
        )
    return SourceDocument(
        source_name=source_name,
        raw_text=text,
        lines=tuple(lines),
    )


def load_config(path: Path) -> SourceDocument:
    text = path.read_text(encoding="utf-8-sig")
    return preprocess_text(text, source_name=path.name)
