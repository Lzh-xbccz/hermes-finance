from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def ohlc_rows(count: int, *, start: float = 100.0, step: float = 1.0) -> list[dict[str, float | int | str]]:
    rows = []
    for i in range(count):
        close = start + i * step
        rows.append({
            "ts": 1710000000 + i * 3600,
            "time_utc": f"2026-06-{(i % 28) + 1:02d} 00:00",
            "open": close - step * 0.2,
            "high": close + 1.0,
            "low": close - 1.0,
            "close": close,
            "volume": 1000 + i,
        })
    return rows


class DirectionGateTests(unittest.TestCase):
    def test_futures_requires_multidimension_confirmation(self) -> None:
        mod = load_module(
            "futures_analyze_gate",
            ROOT / "skills" / "futures-market-analysis" / "scripts" / "futures_analyze.py",
        )
        rows = ohlc_rows(40, step=1.0)
        data = {
            "symbol": "GC",
            "proxies": {
                "DX-Y.NYB": {"change_pct": 0.7},
                "^TNX": {"change_pct": 0.8},
            },
            "structured_drivers": {},
        }

        self.assertEqual(mod.direction_from_evidence(data, rows, rows), "观望")

    def test_forex_usd_pair_does_not_follow_technical_only(self) -> None:
        mod = load_module(
            "forex_analyze_gate",
            ROOT / "skills" / "forex-market-analysis" / "scripts" / "forex_analyze.py",
        )
        rows = ohlc_rows(40, step=0.001)
        data = {
            "symbol": "EURUSD",
            "daily_90d": rows,
            "agg_4h_10d": rows,
            "hourly_10d": rows,
            "proxies": {
                "DX-Y.NYB": {"change_pct": 0.5},
                "^TNX": {"change_pct": 0.6},
                "^VIX": {"change_pct": 0.0},
            },
            "structured_drivers": {"rates": {"diff_signal": "🟢 USD利差优势 +1.0%"}},
            "upcoming_macro_events": [],
        }

        self.assertEqual(mod.direction_from_evidence(data), "观望")

    def test_us_equity_stock_requires_event_confirmation(self) -> None:
        mod = load_module(
            "us_equity_analyze_gate",
            ROOT / "skills" / "us-equity-market-analysis" / "scripts" / "us_equity_analyze.py",
        )
        rows = ohlc_rows(40, step=1.0)
        data = {
            "symbol": "AAPL",
            "instrument_type": "stock",
            "daily_90d": rows,
            "agg_4h_10d": rows,
            "hourly_10d": rows,
            "proxies": {
                "^VIX": {"price": 15.0, "change_pct": -1.0},
                "^TNX": {"change_pct": 0.0},
                "SPY": {"change_pct": 0.6},
                "QQQ": {"change_pct": 0.7},
            },
            "company_event_proxy": {"events": []},
        }

        self.assertEqual(mod.direction_from_evidence(data), "观望")

    def test_us_equity_index_degrades_to_range_not_watch(self) -> None:
        mod = load_module(
            "us_equity_analyze_index_gate",
            ROOT / "skills" / "us-equity-market-analysis" / "scripts" / "us_equity_analyze.py",
        )
        rows = ohlc_rows(40, step=1.0)
        data = {
            "symbol": "^GSPC",
            "instrument_type": "index",
            "daily_90d": rows,
            "agg_4h_10d": rows,
            "hourly_10d": rows,
            "proxies": {
                "^VIX": {"price": 15.0, "change_pct": 0.0},
                "^TNX": {"change_pct": 0.0},
                "SPY": {"change_pct": 0.1},
                "QQQ": {"change_pct": 0.1},
            },
        }

        self.assertEqual(mod.direction_from_evidence(data), "震荡")

    def test_forex_high_impact_event_window_uses_numeric_hours(self) -> None:
        mod = load_module(
            "forex_analyze_event_gate",
            ROOT / "skills" / "forex-market-analysis" / "scripts" / "forex_analyze.py",
        )
        rows = ohlc_rows(40, step=0.001)
        data = {
            "symbol": "EURUSD",
            "daily_90d": rows,
            "agg_4h_10d": rows,
            "hourly_10d": rows,
            "proxies": {
                "DX-Y.NYB": {"change_pct": -0.5},
                "^TNX": {"change_pct": -0.6},
                "^VIX": {"change_pct": -6.0},
            },
            "structured_drivers": {"rates": {"diff_signal": "🔴 USD利差劣势 -1.0%"}},
            "upcoming_macro_events": [
                {"impact": "High", "delta_hours": "+2.5h"},
            ],
        }

        votes = mod.directional_evidence(data)
        self.assertEqual(votes["veto"], [])


if __name__ == "__main__":
    unittest.main()
