# IPCodex Local Web Dashboard Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a local FastAPI dashboard that parses one Huawei VRP configuration at a time and presents the existing `ParseResult` as an operations-focused navigation interface.

**Architecture:** A new `ipcodex.web` package owns the FastAPI application and repository-packaged static assets. The API accepts JSON text or a multipart file, validates it without persisting content, and invokes the existing in-memory parsing pipeline. The existing CLI gains an `ipcodex web` subcommand that starts Uvicorn on loopback by default.

**Tech Stack:** Python 3.12, FastAPI, Uvicorn, Pydantic v2, pytest, FastAPI TestClient, HTML5, CSS, vanilla JavaScript, inline SVG icons.

## Global Constraints

- Keep `ipcodex parse INPUT --output OUTPUT [--schema-root PATH]` unchanged.
- Default web binding is `127.0.0.1:8000`; remote binding requires an explicit `--host` value.
- Do not persist uploaded configuration, parse history, or parse results.
- Do not use a database, analytics, CDN, remote font, or external API.
- Accept `.cfg` and `.txt` files and pasted UTF-8 configuration text.
- Reject empty input, invalid UTF-8, and request bodies above 2 MiB with structured errors.
- API errors contain `error.code` and `error.message`, never stack traces, absolute paths, or configuration contents.
- Reuse the existing `ParseResult` contract and parser stages.
- Frontend code is repository-owned static HTML, CSS, and JavaScript with no Node build step.
- The selected UI is the navigation-style dashboard with compact tables and transient in-memory state.
- Run all existing tests after every task and commit each completed task separately.

---

### Task 1: Add the In-Memory Parse API

**Files:**
- Modify: `pyproject.toml`
- Create: `src/ipcodex/web/__init__.py`
- Create: `src/ipcodex/web/app.py`
- Create: `tests/web/test_api.py`

**Interfaces:**
- Consumes: `preprocess_text(text: str, *, source_name: str)`, `parse_cst`, `load_schema_bundle`, and `build_semantic_model`.
- Produces: `create_app(*, max_upload_bytes: int = 2 * 1024 * 1024) -> FastAPI` and module-level `app`.
- `POST /api/parse` accepts JSON `{ "text": str, "source_name": str | null }` or multipart field `file`.

- [x] **Step 1: Add FastAPI test dependencies and write failing API tests**

Add runtime dependencies to `pyproject.toml`:

```toml
"fastapi>=0.115,<1",
"python-multipart>=0.0.20,<1",
"uvicorn>=0.34,<1",
```

Add the following dev dependency:

```toml
"httpx>=0.28,<1",
```

Create `tests/web/test_api.py` with tests that use `TestClient(create_app(max_upload_bytes=64))` and assert:

```python
def test_parse_json_configuration_returns_existing_parse_result() -> None:
    response = client.post(
        "/api/parse",
        json={"text": "sysname Leaf01\n#\nreturn\n", "source_name": "leaf.cfg"},
    )
    assert response.status_code == 200
    assert response.json()["device"]["hostname"]["value"] == "Leaf01"


def test_parse_multipart_configuration() -> None:
    response = client.post(
        "/api/parse",
        files={"file": ("edge.cfg", b"sysname Edge01\n#\nreturn\n", "text/plain")},
    )
    assert response.status_code == 200
    assert response.json()["device"]["source_name"] == "edge.cfg"


@pytest.mark.parametrize(
    ("request_kwargs", "status", "code"),
    [
        ({"json": {"text": "", "source_name": "empty.cfg"}}, 422, "empty_config"),
        ({"files": {"file": ("bad.cfg", b"\xff", "text/plain")}}, 422, "invalid_encoding"),
        ({"files": {"file": ("large.cfg", b"x" * 65, "text/plain")}}, 413, "upload_too_large"),
    ],
)
def test_parse_rejects_invalid_input(request_kwargs, status, code) -> None:
    response = client.post("/api/parse", **request_kwargs)
    assert response.status_code == status
    assert response.json()["error"]["code"] == code
```

- [x] **Step 2: Run the API tests and verify the red state**

Run:

```bash
python -m pip install -e '.[dev]'
pytest tests/web/test_api.py -v
```

Expected: collection fails because `ipcodex.web.app` does not exist.

- [x] **Step 3: Implement request validation and in-memory parsing**

Create `src/ipcodex/web/app.py` with:

```python
from importlib.resources import files

from fastapi import FastAPI, Request, UploadFile
from fastapi.responses import JSONResponse

from ipcodex.cst.parser import parse_cst
from ipcodex.schema.loader import load_schema_bundle
from ipcodex.semantic.registry import build_semantic_model
from ipcodex.source import preprocess_text


def _error(status_code: int, code: str, message: str) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={"error": {"code": code, "message": message}},
    )


def _parse_text(text: str, source_name: str) -> dict:
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

    @application.post("/api/parse")
    async def parse_configuration(request: Request):
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
            text = payload.get("text", "") if isinstance(payload, dict) else ""
            source_name = payload.get("source_name") or "pasted.cfg" if isinstance(payload, dict) else "pasted.cfg"
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
```

Create an empty `src/ipcodex/web/__init__.py`.

- [x] **Step 4: Run focused and full tests**

Run:

```bash
pytest tests/web/test_api.py -v
pytest -q
```

Expected: all API tests and the existing suite pass.

- [x] **Step 5: Review and commit**

```bash
git diff
git add pyproject.toml src/ipcodex/web/__init__.py src/ipcodex/web/app.py tests/web/test_api.py
git commit -m "feat: add local configuration parse api"
```

---

### Task 2: Add the Web Server CLI Command

**Files:**
- Modify: `src/ipcodex/cli.py`
- Create: `src/ipcodex/web/server.py`
- Modify: `tests/test_cli.py`

**Interfaces:**
- Produces: `run_server(*, host: str, port: int) -> None`.
- Adds: `ipcodex web [--host HOST] [--port PORT]` with defaults `127.0.0.1` and `8000`.

- [x] **Step 1: Write a failing CLI delegation test**

Use `unittest.mock.patch("ipcodex.cli.run_server")` and assert:

```python
def test_cli_starts_local_web_server() -> None:
    with patch("ipcodex.cli.run_server") as run_server:
        exit_code = main(["web", "--port", "8123"])
    assert exit_code == 0
    run_server.assert_called_once_with(host="127.0.0.1", port=8123)
```

- [x] **Step 2: Run the test and verify failure**

Run: `pytest tests/test_cli.py::test_cli_starts_local_web_server -v`

Expected: FAIL because the `web` subcommand and `run_server` do not exist.

- [x] **Step 3: Implement Uvicorn delegation and CLI arguments**

Create `src/ipcodex/web/server.py`:

```python
import uvicorn


def run_server(*, host: str, port: int) -> None:
    uvicorn.run("ipcodex.web.app:app", host=host, port=port, log_level="info")
```

Extend `_build_parser()` with a `web` subparser containing `--host` and `--port`.
Import `run_server` in `cli.py` and add:

```python
if args.command == "web":
    run_server(host=args.host, port=args.port)
    return 0
```

- [x] **Step 4: Run focused and full tests**

Run:

```bash
pytest tests/test_cli.py -v
pytest -q
```

Expected: all CLI and existing tests pass.

- [x] **Step 5: Review and commit**

```bash
git diff
git add src/ipcodex/cli.py src/ipcodex/web/server.py tests/test_cli.py
git commit -m "feat: start web dashboard from cli"
```

---

### Task 3: Build the Navigation Dashboard

**Files:**
- Create: `src/ipcodex/web/static/index.html`
- Create: `src/ipcodex/web/static/styles.css`
- Create: `src/ipcodex/web/static/app.js`
- Modify: `src/ipcodex/web/app.py`
- Modify: `tests/web/test_api.py`

**Interfaces:**
- `GET /` returns `index.html`.
- `GET /static/styles.css` and `GET /static/app.js` return packaged assets.
- Frontend state is `{ inputText, sourceName, status, result, activeSection }` and is never persisted.

- [x] **Step 1: Produce and approve the complete visual concept**

Generate a full desktop dashboard concept for the accepted navigation layout,
including New Parse, Device Overview, dense tables, warning state, and Raw JSON.
Extract exact layout, color, typography, spacing, icon, and responsive tokens into
the implementation notes before editing frontend files.

- [x] **Step 2: Write failing static asset tests**

Add tests asserting:

```python
def test_dashboard_and_static_assets_are_served() -> None:
    page = client.get("/")
    assert page.status_code == 200
    assert "IPCodex" in page.text
    assert 'id="parse-form"' in page.text
    assert client.get("/static/styles.css").status_code == 200
    assert client.get("/static/app.js").status_code == 200
```

- [x] **Step 3: Run the static tests and verify failure**

Run: `pytest tests/web/test_api.py::test_dashboard_and_static_assets_are_served -v`

Expected: FAIL with 404 for `/` or static assets.

- [x] **Step 4: Serve packaged static assets**

Resolve `files("ipcodex.web").joinpath("static")`, mount it at `/static`, and
return `index.html` from `GET /` with `FileResponse`. Ensure Hatch includes the
HTML, CSS, and JavaScript in the wheel.

- [x] **Step 5: Implement the dashboard shell and parse input flow**

Build semantic HTML with:

- persistent desktop sidebar and mobile menu button;
- navigation buttons for all seven approved sections;
- drag-and-drop file target, hidden file input, text editor, metadata row, error region, and stable-size parse button;
- content panels for overview, interfaces, VPN instances, static routes, unknown commands, and raw JSON;
- icon-only Copy and Download buttons with accessible labels and tooltips.

Implement JavaScript that submits multipart data when a file is selected and
JSON when text is pasted, retains the input on failure, stores one result in
memory, switches to overview on success, renders compact tables, expands
interface evidence rows, copies JSON, downloads deterministic JSON, and manages
the mobile drawer.

- [x] **Step 6: Implement the responsive visual system**

Use the accepted charcoal, white, neutral gray, green, amber, and red palette.
Keep radii at 8px or less, use fixed icon-button dimensions, make data tables
horizontally scrollable, keep the sidebar persistent above 900px, and use an
overlay drawer below 900px. Add visible focus states and respect
`prefers-reduced-motion`.

- [x] **Step 7: Run API tests, full tests, and wheel inspection**

Run:

```bash
pytest tests/web/test_api.py -v
pytest -q
uv build
unzip -l dist/ipcodex-0.1.0-py3-none-any.whl | rg 'ipcodex/web/static'
```

Expected: all tests pass and all three static assets appear in the wheel.

- [x] **Step 8: Review and commit**

```bash
git diff
git add src/ipcodex/web tests/web/test_api.py
git commit -m "feat: add local parser dashboard"
```

---

### Task 4: Complete Browser QA and Documentation

**Files:**
- Modify: `README.md`
- Modify: `tests/web/test_api.py`
- Modify frontend files only when QA reveals a defect.

**Interfaces:**
- Documents `ipcodex web`, local URL, input options, privacy behavior, and stop procedure.
- Verifies the complete browser flow against the accepted concept.

- [x] **Step 1: Add API resilience tests**

Add tests for unsupported content type, missing multipart file, and an injected
parser exception. Assert stable status codes and verify response JSON contains
no current working directory or configuration text.

- [x] **Step 2: Run the new tests and fix only demonstrated defects**

Run: `pytest tests/web/test_api.py -v`

Expected: all resilience tests pass after any required minimal correction.

- [x] **Step 3: Document local web usage**

Add to `README.md`:

```markdown
## Local Web Dashboard

```bash
source .venv/bin/activate
ipcodex web
```

Open `http://127.0.0.1:8000`. Upload a Huawei VRP `.cfg`/`.txt` file or paste
configuration text. IPCodex processes the configuration locally and does not
retain it after refresh. Press `Ctrl+C` in the terminal to stop the server.
```

- [x] **Step 4: Start the app and run Browser QA**

Start `ipcodex web --port 8000`, then use the Browser plugin for:

1. page identity, nonblank DOM, no framework overlay, and console health;
2. paste the primary sample and submit;
3. verify overview values `Leaf01`, 3 interfaces, 4 VLANs, 1 VPN, 1 route;
4. navigate to Interfaces, Unknown Commands, and Raw JSON;
5. exercise Copy or Download and verify the result;
6. submit empty input and verify visible recoverable validation;
7. capture desktop and mobile screenshots and inspect for clipping or overlap.

- [x] **Step 5: Compare concept and implementation**

Use `view_image` on the accepted concept and latest desktop/mobile screenshots.
Record at least five comparison points: layout, typography, palette, navigation,
table density, responsive drawer, and interaction state. Fix every material
mismatch and rerun Browser QA.

- [x] **Step 6: Run final verification**

Run:

```bash
python -m pip install -e '.[dev]'
pytest -q --cov=ipcodex --cov-report=term-missing
ipcodex parse samples/huawei/ce_leaf_minimal.cfg --output build/leaf01.json
```

Expected: the complete suite passes, coverage remains at least 90%, and the
existing CLI output remains valid.

- [x] **Step 7: Review, commit, and push**

```bash
git diff
git status --short
git add README.md tests/web/test_api.py src/ipcodex/web
git commit -m "docs: document local web dashboard"
git push origin main
```
