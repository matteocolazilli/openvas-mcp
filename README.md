# GreenboneMCP

An MCP (Model Context Protocol) server that connects AI clients to Greenbone/OpenVAS through GMP (`python-gvm`).

## What this project is

`GreenboneMCP` exposes MCP tools for scan/report workflows in Greenbone/OpenVAS, so an assistant can:
- create and launch scans,
- monitor scan progress,
- stop scans,
- fetch reports,
- compare report deltas between runs.

The server runs on `stdio` transport and talks to `gvmd` through a Unix socket.

## Project status

This project is part of my Master's thesis and is currently a Proof of Concept (PoC).

It may be developed further only if there is clear community/user interest.

Contributions are welcome: feel free to open **Issues** and submit **Pull Requests**. (See the [Contributing](README.md#contributing) section below.)

## Tooling exposed by the server

### Scan workflow tools

These are always registered:
- `start_scan`
- `scan_status`
- `fetch_latest_report`
- `rescan_target`
- `delta_report`

### Inspection / control tools

These are always registered:
- `get_targets`
- `get_target`
- `get_tasks`
- `get_port_lists`
- `start_task`
- `stop_task`

## Project Structure

```text
src/
├── main.py                     # App entrypoint (stdio MCP server)
├── constants.py                # Default UUIDs and report format constants
├── config/
│   ├── gvm_client_config.py    # Env-based GVM client settings (GMP_USERNAME, GMP_PASSWORD, ...)
│   └── logging_config.py       # Logging configuration settings
├── core/
│   └── mcp_server.py           # MCP wiring, GVM connection, tool registration
├── services/
│   └── gvm_client.py           # Typed wrapper around python-gvm + XML parsing
├── tools/
│   ├── scan_workflow_tools.py    # High-level scan orchestration tools
│   ├── _scan_workflow_helpers.py  # Internal parsing/formatting helpers for workflow tools
│   └── inspection_control_tools.py # Inspection/control tools for existing scan state
└── models/
    └── generated/             # Auto-generated dataclasses (xsdata output)

```

## Requirements

- Docker Engine + Docker Compose plugin
- A Greenbone/OpenVAS instance with a reachable `gvmd` Unix socket
- Valid GMP credentials

## Installation

### Compatibility

This server has been tested only with Greenbone/OpenVAS deployed via containers, particularly Greenbone Community Edition with the official container setup: https://greenbone.github.io/docs/latest/22.4/container/

### Prerequisites

Ensure the official Greenbone Community Edition container setup is running by executing the following command in the directory where you have the `docker-compose.yml` for Greenbone:
  
```bash
docker compose -f <path-to-greenbone-compose>/docker-compose.yml up -d
```

**Note**: The official Greenbone compose setup uses the `gvmd_socket_vol` volume mounted at `/run/gvmd` in the containers.
With the default compose configuration, this named volume is usually available as:

`greenbone-community-edition_gvmd_socket_vol`.

In this project the same named volume is used to access the `gvmd` socket from the MCP server container.


### 1) Clone this repository

```bash
git clone https://github.com/matteocolazilli/GreenboneMCP.git
cd GreenboneMCP
```

### 2) Build this MCP image

```bash
docker build -t greenbonemcp:latest .
```

### 3) Create `.env` configuration and set configuration values

```bash
cp .env.example .env
```

Edit `.env` with your credentials and desired settings.

You can use this `.env` by passing it at runtime with `--env-file` to the `docker run` command.

The server reads configuration from the following environment variables, which if not set it falls back to defaults:

- `GMP_USERNAME`: GMP username (default: `admin`)
- `GMP_PASSWORD`: GMP password (required: no default, must be set)
- `LOG_LEVEL`: application log level (default: `INFO`)

### 4) Configure the MCP client and run the server

Configure your MCP client/agent, according to its documentation, to run the GreenboneMCP server with the following `docker run` command:

```bash
docker run 
  --rm -i 
  --env-file <path-to-your-env-file> 
  --name greenbonemcp 
  --volume greenbone-community-edition_gvmd_socket_vol:/run/gvmd 
  greenbonemcp:latest 
```

**Note**: the `--env-file` path must point to the `.env` you created in step 3.

### 5) Enjoy!

Use your MCP-compatible assistant to interact with OpenVAS through the tools exposed by this server!

## Contributing

- Open an Issue for bugs, ideas, or feature requests.
- Open a Pull Request with focused changes and a clear description.

Community contributions are welcome and encouraged.

### Tool Module Conventions

To keep tool modules maintainable:
- keep MCP tool handlers in `src/tools/*_tools.py`
- keep non-tool helper functions (parsing, formatting, output shaping) in internal helper modules such as `src/tools/_scan_workflow_helpers.py`
- use `src/services/gvm_client.py` for GMP interaction primitives and keep orchestration logic in tool handlers

### Developing New Tools

If you want to add new MCP tools (for example by wrapping additional `python-gvm` methods), you will likely need new typed models for XML responses.

This project contains models under `src/models/generated`.

#### Adding new dataclasses (current approach)

For now, when you need new dataclasses for additional GMP responses, add them manually.

Recommended workflow:
1. Collect representative XML responses for the GMP methods you want to support.
2. Use the existing models in `src/models/generated` as reference for naming, typing, and structure.
3. Create/update dataclasses manually to match the XML shape you need.

`gvm-tools` / `gvm-pyshell` are practical ways to obtain real XML response samples from your Greenbone instance.

## License

This project is licensed under **GNU GPL v3.0 or later**.

See [`LICENSE.md`](LICENSE.md) for the full license text.

## Third-Party Notices

This project includes and depends on third-party open-source software.
See [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md) for details on direct dependencies and their licenses.
