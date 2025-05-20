# CalDAV MCP Server

A MicroChannel Protocol (MCP) server for CalDAV integration, allowing calendar synchronization with Claude desktop.

## Features

- Calendar events synchronization via CalDAV
- Custom URL with username/password authentication
- Easy installation in Claude desktop

## Installation

```bash
poetry install
```

## Development

```bash
poetry install
poetry run pytest
```

## Usage

Start the server:
```bash
poetry run caldav-mcp
```

Install in Claude desktop:
```bash
poetry run python -m caldav_mcp.install
```
