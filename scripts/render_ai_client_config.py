#!/usr/bin/env python3
"""Render Hermes Finance MCP configuration for common AI clients."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LAUNCHER = ROOT / "bin" / "hermes_finance_mcp.py"


def stdio_server(abs_paths: bool = True) -> dict:
    root = str(ROOT) if abs_paths else "."
    launcher = str(LAUNCHER) if abs_paths else "bin/hermes_finance_mcp.py"
    return {
        "command": "python3",
        "args": [launcher],
        "env": {"PYTHONPATH": root},
    }


def render_json(client: str) -> str:
    server = stdio_server(abs_paths=True)
    if client in {"claude-code", "claude-desktop", "cursor", "cline", "windsurf", "roo", "amp", "universal"}:
        if client == "cline":
            server = {**server, "disabled": False, "autoApprove": []}
        if client == "roo":
            server = {**server, "disabled": False, "alwaysAllow": []}
        if client == "claude-code":
            server = {**server, "timeout": 600000}
        return json.dumps({"mcpServers": {"hermes-finance": server}}, indent=2)
    if client == "vscode":
        return json.dumps(
            {
                "servers": {
                    "hermesFinance": {
                        "type": "stdio",
                        "command": "python3",
                        "args": [str(LAUNCHER)],
                        "cwd": str(ROOT),
                        "env": {"PYTHONPATH": str(ROOT)},
                    }
                }
            },
            indent=2,
        )
    if client == "gemini":
        return json.dumps(
            {
                "mcpServers": {
                    "hermes_finance": {
                        "command": "python3",
                        "args": [str(LAUNCHER)],
                        "cwd": str(ROOT),
                        "env": {"PYTHONPATH": str(ROOT)},
                        "timeout": 600000,
                        "trust": False,
                    }
                }
            },
            indent=2,
        )
    if client == "zed":
        return json.dumps({"context_servers": {"hermes-finance": server}}, indent=2)
    raise ValueError(f"unsupported JSON client: {client}")


def render_toml() -> str:
    return f"""[mcp_servers.hermes_finance]
command = "python3"
args = ["{LAUNCHER}"]
cwd = "{ROOT}"
startup_timeout_sec = 20
tool_timeout_sec = 240
enabled = true
default_tools_approval_mode = "prompt"
"""


def render_yaml() -> str:
    return f"""name: Hermes Finance
version: 1.0.0
schema: v1
mcpServers:
  - name: Hermes Finance
    command: python3
    args:
      - {LAUNCHER}
    cwd: {ROOT}
    env:
      PYTHONPATH: {ROOT}
    connectionTimeout: 20000
"""


def main() -> int:
    parser = argparse.ArgumentParser(description="Render AI client MCP config for Hermes Finance.")
    parser.add_argument(
        "client",
        choices=[
            "universal",
            "claude-code",
            "claude-desktop",
            "cursor",
            "vscode",
            "windsurf",
            "cline",
            "roo",
            "gemini",
            "continue",
            "codex",
            "zed",
            "amp",
        ],
    )
    parser.add_argument("--out", help="Optional path to write the rendered config.")
    args = parser.parse_args()

    if args.client == "codex":
        content = render_toml()
    elif args.client == "continue":
        content = render_yaml()
    else:
        content = render_json(args.client) + "\n"

    if args.out:
        Path(args.out).expanduser().write_text(content, encoding="utf-8")
    else:
        print(content, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
