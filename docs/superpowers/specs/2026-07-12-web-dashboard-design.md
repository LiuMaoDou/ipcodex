# IPCodex Local Web Dashboard Design

## Goal

Add a local-only web interface to IPCodex for parsing Huawei VRP configuration
files and inspecting the typed result. The interface must reuse the existing
parser, keep uploaded configuration data on the local machine, and preserve the
existing CLI behavior.

## Scope

The first web release supports one active parse result at a time. Users can
upload a `.cfg` or `.txt` file, drag a file onto the page, or paste configuration
text. The application does not store configuration history, use a database, or
make external network requests.

## Architecture

FastAPI serves both the browser application and a same-origin parse API. The API
calls the existing source preprocessing, CST, schema matching, and semantic
model pipeline. It returns the existing `ParseResult` JSON contract rather than
introducing a second web-specific result model.

The frontend uses repository-owned HTML, CSS, and JavaScript served as static
package assets. It has no Node build step. This keeps installation aligned with
the Python package and makes `ipcodex web` sufficient to start the application.

The existing `ipcodex parse` command remains unchanged. A new command starts
the web server:

```bash
ipcodex web --host 127.0.0.1 --port 8000
```

The default host is loopback-only. Remote binding remains an explicit operator
choice through `--host`.

## HTTP Interface

`GET /` returns the dashboard shell and its static assets.

`POST /api/parse` accepts one of these inputs:

- multipart upload in a `file` field;
- JSON with `text` and an optional `source_name`.

The endpoint rejects requests that provide neither form, empty configuration,
invalid UTF-8 input, and files above the configured upload limit. Successful
responses serialize `ParseResult` in JSON mode. Error responses contain a short
stable error code and a user-facing message, without stack traces or absolute
paths.

## Information Architecture

The selected layout is a navigation-style operations dashboard. A dark fixed
sidebar contains:

1. New Parse
2. Device Overview
3. Interfaces
4. VPN Instances
5. Static Routes
6. Unknown Commands
7. Raw JSON

Before parsing, only New Parse is active. After a successful parse, Device
Overview becomes active and the result sections become available. There is no
marketing or landing page.

## Screens and Components

### New Parse

The input view contains a drag-and-drop target, file picker, and configuration
text editor. The selected filename and byte size are shown near the input. The
primary Parse Configuration action is disabled for empty input. Parsing state
is visible in the action without resizing the layout.

Errors appear beside the input and do not clear configuration text. Successful
parsing moves the user to Device Overview.

### Device Overview

The overview presents hostname, interface count, VLAN count, VPN instance
count, static route count, structural coverage, semantic coverage, and any
unresolved references. Metrics use compact operational panels and a coverage
bar rather than decorative card grids.

### Detail Views

Interfaces, VPN instances, static routes, and unknown commands use dense,
scannable tables. Interface rows can expand to show IPv4 addresses, VRF,
Eth-Trunk membership, explicit values, and source evidence. Unknown commands
show line number, current view, reason, and raw text. Unresolved references are
also surfaced as a persistent warning in the overview.

### Raw JSON

The JSON view uses a monospace formatted viewer with Copy and Download icon
actions. Downloaded JSON uses deterministic serialization and a filename based
on the source name.

## Visual System

The visual direction is a restrained network operations tool: charcoal
navigation, white work surface, neutral gray dividers, green for successful
coverage, amber for unknown commands, and red only for errors. Controls use
compact spacing, square-to-small radii, Lucide-style line icons, and legible
system typography. Tables and labels prioritize scanning over decoration.

Desktop uses a persistent sidebar. On narrow screens the sidebar becomes a
menu drawer, input controls stack, and tables scroll horizontally. Text and
controls must not overlap at supported viewport sizes.

## State and Data Flow

The browser owns four transient states: current input, parse status, current
result, and active section. No state is persisted after a refresh.

The flow is:

1. User supplies a file or pasted text.
2. Frontend validates that content is present and submits it to `/api/parse`.
3. FastAPI validates input and invokes the existing parser pipeline.
4. The API returns `ParseResult` or a structured error.
5. Frontend stores the result in memory, renders the overview, and enables
   result navigation.

## Error Handling and Security

The server limits upload size and decodes files as UTF-8. It returns controlled
4xx responses for invalid input and a generic 500 response for unexpected
errors. Server logs may retain diagnostic details, but responses never include
stack traces, absolute paths, or file contents.

The default server listens only on `127.0.0.1`. The page has no analytics,
remote fonts, CDNs, or external API calls. Uploaded content is not written to
disk except for short-lived internal handling if required by the framework.

## Testing and Acceptance

Backend tests cover text parsing, multipart upload, empty input, invalid UTF-8,
oversized input, and controlled parser errors. CLI tests verify that the new
`web` command delegates to the server without changing `parse` behavior.

Rendered browser verification covers:

- initial page load with no console errors;
- pasted sample configuration through successful parsing;
- navigation among overview, interfaces, unknown commands, and JSON;
- JSON copy or download behavior;
- visible validation and recovery from empty input;
- desktop and mobile layout without overlap or clipping.

All existing parser tests must continue to pass. The web feature is accepted
when a user can start it with `ipcodex web`, parse the primary golden sample,
inspect the dashboard sections, and download the same semantic result exposed
by the CLI.
