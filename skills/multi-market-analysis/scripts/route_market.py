#!/usr/bin/env python3
"""Thin wrapper around the shared Hermes Finance router."""

from __future__ import annotations

import json
import os
import sys


PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from hermes_finance.routing import classify  # noqa: E402


def main() -> int:
    text = " ".join(sys.argv[1:]).strip()
    if not text:
        print(json.dumps({"market": "ambiguous", "reason": "empty input"}, ensure_ascii=False))
        return 0
    print(json.dumps(classify(text), ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
