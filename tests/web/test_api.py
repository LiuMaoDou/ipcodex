from __future__ import annotations

from typing import Any

import pytest
from fastapi.testclient import TestClient

from ipcodex.web.app import create_app


@pytest.fixture
def client() -> TestClient:
    return TestClient(create_app(max_upload_bytes=64))


def test_parse_json_configuration_returns_existing_parse_result(
    client: TestClient,
) -> None:
    response = client.post(
        "/api/parse",
        json={"text": "sysname Leaf01\n#\nreturn\n", "source_name": "leaf.cfg"},
    )

    assert response.status_code == 200
    assert response.json()["device"]["hostname"]["value"] == "Leaf01"


def test_parse_multipart_configuration(client: TestClient) -> None:
    response = client.post(
        "/api/parse",
        files={
            "file": (
                "edge.cfg",
                b"sysname Edge01\n#\nreturn\n",
                "text/plain",
            )
        },
    )

    assert response.status_code == 200
    assert response.json()["device"]["source_name"] == "edge.cfg"


@pytest.mark.parametrize(
    ("request_kwargs", "status", "code"),
    [
        ({"json": {"text": "", "source_name": "empty.cfg"}}, 422, "empty_config"),
        (
            {"files": {"file": ("bad.cfg", b"\xff", "text/plain")}},
            422,
            "invalid_encoding",
        ),
        (
            {"files": {"file": ("large.cfg", b"x" * 65, "text/plain")}},
            413,
            "upload_too_large",
        ),
    ],
)
def test_parse_rejects_invalid_input(
    client: TestClient,
    request_kwargs: dict[str, Any],
    status: int,
    code: str,
) -> None:
    response = client.post("/api/parse", **request_kwargs)

    assert response.status_code == status
    assert response.json()["error"]["code"] == code
