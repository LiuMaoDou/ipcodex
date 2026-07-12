from __future__ import annotations

from typing import Any
from unittest.mock import patch

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


def test_dashboard_and_static_assets_are_served(client: TestClient) -> None:
    page = client.get("/")

    assert page.status_code == 200
    assert "IPCodex" in page.text
    assert 'id="parse-form"' in page.text
    assert client.get("/static/styles.css").status_code == 200
    assert client.get("/static/app.js").status_code == 200


def test_favicon_is_served(client: TestClient) -> None:
    assert client.get("/favicon.ico").status_code == 200


def test_parse_rejects_unsupported_media_type(client: TestClient) -> None:
    response = client.post(
        "/api/parse",
        content="sysname Leaf01",
        headers={"content-type": "text/plain"},
    )

    assert response.status_code == 415
    assert response.json()["error"]["code"] == "unsupported_media_type"


def test_parse_rejects_malformed_json(client: TestClient) -> None:
    response = client.post(
        "/api/parse",
        content="{broken",
        headers={"content-type": "application/json"},
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "invalid_input"


def test_parse_rejects_multipart_without_file(client: TestClient) -> None:
    response = client.post("/api/parse", files={"other": (None, "value")})

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "missing_input"


def test_parse_failure_does_not_expose_input_or_local_path(
    client: TestClient,
    tmp_path,
) -> None:
    secret_text = "sysname PRIVATE-DEVICE"
    with patch("ipcodex.web.app._parse_text", side_effect=RuntimeError(tmp_path)):
        response = client.post(
            "/api/parse",
            json={"text": secret_text, "source_name": "private.cfg"},
        )

    payload = response.json()
    serialized = str(payload)
    assert response.status_code == 500
    assert payload["error"]["code"] == "parse_failed"
    assert secret_text not in serialized
    assert str(tmp_path) not in serialized
