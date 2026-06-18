"""Subprocess runner utilities."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

from .paths import PROJECT_ROOT


def run_python_script(script: Path, args: list[str], timeout: int = 180) -> dict[str, Any]:
    """Run a project Python script and return a structured command result."""

    cmd = [sys.executable, str(script), *args]
    env = os.environ.copy()
    env["PYTHONPATH"] = str(PROJECT_ROOT) + os.pathsep + env.get("PYTHONPATH", "")
    try:
        proc = subprocess.run(
            cmd,
            cwd=PROJECT_ROOT,
            env=env,
            text=True,
            capture_output=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as exc:
        return {
            "ok": False,
            "returncode": None,
            "command": _display_command(cmd),
            "stdout": exc.stdout or "",
            "stderr": exc.stderr or f"timeout after {timeout}s",
            "error": "timeout",
        }

    return {
        "ok": proc.returncode == 0,
        "returncode": proc.returncode,
        "command": _display_command(cmd),
        "stdout": proc.stdout,
        "stderr": proc.stderr,
        "error": None if proc.returncode == 0 else "nonzero_exit",
    }


def parse_json_output(stdout: str) -> Any | None:
    """Parse JSON script output if the whole stdout is valid JSON."""

    text = stdout.strip()
    if not text:
        return None
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None


def _display_command(cmd: list[str]) -> list[str]:
    """Return a safe, portable representation of the command."""

    if cmd:
        cmd = cmd[:]
        cmd[0] = Path(cmd[0]).name
    return cmd
