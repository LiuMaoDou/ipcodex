from __future__ import annotations

import uvicorn


def run_server(*, host: str, port: int) -> None:
    uvicorn.run(
        "ipcodex.web.app:app",
        host=host,
        port=port,
        log_level="info",
    )
