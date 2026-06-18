#!/usr/bin/env python3
"""Portable launcher for the Hermes Finance MCP server.

AI clients often start MCP servers from different working directories. This
launcher resolves the repository root from its own location, then starts the
server with a stable PYTHONPATH and cwd.
"""

from __future__ import annotations

import os
import runpy
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)
os.environ["PYTHONPATH"] = str(ROOT) + os.pathsep + os.environ.get("PYTHONPATH", "")

runpy.run_path(str(ROOT / "hermes_finance_mcp" / "server.py"), run_name="__main__")
