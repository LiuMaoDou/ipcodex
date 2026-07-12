from __future__ import annotations

from importlib.resources import files
from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.datastructures import UploadFile

from ipcodex.cst.parser import parse_cst
from ipcodex.schema.loader import load_schema_bundle
from ipcodex.semantic.registry import build_semantic_model
from ipcodex.source import preprocess_text


def _error(status_code: int, code: str, message: str) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={"error": {"code": code, "message": message}},
    )


def _parse_text(text: str, source_name: str) -> dict[str, Any]:
    schema = load_schema_bundle(files("ipcodex.schema").joinpath("huawei_vrp"))
    tree = parse_cst(preprocess_text(text, source_name=source_name), schema)
    device = build_semantic_model(tree, schema)
    return {
        "schema_version": schema.schema_version,
        "device": device.model_dump(mode="json"),
        "tree": tree.model_dump(mode="json"),
    }


def create_app(*, max_upload_bytes: int = 2 * 1024 * 1024) -> FastAPI:
    application = FastAPI(title="IPCodex", docs_url=None, redoc_url=None)

    @application.post("/api/parse", response_model=None)
    async def parse_configuration(request: Request) -> dict[str, Any] | JSONResponse:
        content_type = request.headers.get("content-type", "")

        if content_type.startswith("multipart/form-data"):
            form = await request.form()
            upload = form.get("file")
            if not isinstance(upload, UploadFile):
                return _error(422, "missing_input", "Select a configuration file.")
            content = await upload.read(max_upload_bytes + 1)
            if len(content) > max_upload_bytes:
                return _error(413, "upload_too_large", "Configuration exceeds 2 MiB.")
            try:
                text = content.decode("utf-8-sig")
            except UnicodeDecodeError:
                return _error(422, "invalid_encoding", "Configuration must be UTF-8.")
            source_name = upload.filename or "uploaded.cfg"
        elif content_type.startswith("application/json"):
            payload = await request.json()
            if not isinstance(payload, dict):
                return _error(422, "missing_input", "Paste configuration text.")
            text = payload.get("text", "")
            source_name = payload.get("source_name") or "pasted.cfg"
            if not isinstance(text, str) or not isinstance(source_name, str):
                return _error(422, "invalid_input", "Configuration input is invalid.")
            if len(text.encode("utf-8")) > max_upload_bytes:
                return _error(413, "upload_too_large", "Configuration exceeds 2 MiB.")
        else:
            return _error(415, "unsupported_media_type", "Use JSON or multipart upload.")

        if not text.strip():
            return _error(422, "empty_config", "Configuration cannot be empty.")

        try:
            return _parse_text(text, source_name)
        except Exception:
            return _error(500, "parse_failed", "The configuration could not be parsed.")

    return application


app = create_app()
