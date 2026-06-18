"""Shared Python API for Hermes Finance.

The package is intentionally thin: market collectors remain in the existing
scripts, while this layer gives CLI, Skills, and MCP one stable interface.
"""

from __future__ import annotations

from .routing import classify, normalize_market
from .service import analyze_market, czsc_analyze, fetch_market_data, route_market

__all__ = [
    "analyze_market",
    "classify",
    "czsc_analyze",
    "fetch_market_data",
    "normalize_market",
    "route_market",
]
