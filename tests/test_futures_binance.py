from __future__ import annotations

import importlib.util
from pathlib import Path
from unittest import mock
import unittest


ROOT = Path(__file__).resolve().parents[1]
FETCH_PATH = ROOT / "skills" / "futures-market-analysis" / "scripts" / "futures_fetch.py"
ANALYZE_PATH = ROOT / "skills" / "futures-market-analysis" / "scripts" / "futures_analyze.py"
CHART_PATH = ROOT / "skills" / "futures-market-analysis" / "scripts" / "market_structure_chart.py"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


futures_fetch = load_module("futures_fetch_test", FETCH_PATH)
futures_analyze = load_module("futures_analyze_test", ANALYZE_PATH)
futures_chart = load_module("futures_market_structure_chart_test", CHART_PATH)


def kline(ts_ms: int, open_: str, high: str, low: str, close: str) -> list[object]:
    return [ts_ms, open_, high, low, close, "100", ts_ms + 1, "7400000", 1000]


class BinanceTradFiTests(unittest.TestCase):
    def test_fetch_binance_tradfi_perp_normalizes_summary_and_klines(self) -> None:
        def fake_fetch(path: str, params=None, retries: int = 3):
            symbol = (params or {}).get("symbol")
            if path == "/fapi/v1/exchangeInfo":
                return {
                    "symbols": [
                        {
                            "symbol": "CLUSDT",
                            "baseAsset": "CL",
                            "quoteAsset": "USDT",
                            "contractType": "TRADIFI_PERPETUAL",
                            "underlyingType": "COMMODITY",
                            "underlyingSubType": ["TradFi"],
                            "status": "TRADING",
                        }
                    ]
                }
            self.assertEqual(symbol, "CLUSDT")
            if path == "/fapi/v1/ticker/24hr":
                return {"lastPrice": "74.26", "priceChangePercent": "-0.90", "highPrice": "79.02", "lowPrice": "73.46", "quoteVolume": "673800000"}
            if path == "/fapi/v1/premiumIndex":
                return {"markPrice": "74.29", "indexPrice": "74.25"}
            if path == "/fapi/v1/openInterest":
                return {"openInterest": "1822570.96"}
            if path == "/fapi/v1/fundingRate":
                return [{"fundingTime": 1710000000000, "fundingRate": "0.000001", "markPrice": "74.2"}]
            if path == "/futures/data/openInterestHist":
                return [
                    {"timestamp": 1710000000000, "sumOpenInterest": "1800000", "sumOpenInterestValue": "133000000"},
                    {"timestamp": 1710000300000, "sumOpenInterest": "1822570.96", "sumOpenInterestValue": "135000000"},
                ]
            if path == "/futures/data/topLongShortAccountRatio":
                return [{"timestamp": 1710000000000, "longAccount": "0.80", "shortAccount": "0.20", "longShortRatio": "4.0"}]
            if path == "/futures/data/topLongShortPositionRatio":
                return [{"timestamp": 1710000000000, "longAccount": "0.75", "shortAccount": "0.25", "longShortRatio": "3.0"}]
            if path == "/fapi/v1/klines":
                return [kline(1710000000000, "74", "75", "73", "74.5")]
            raise AssertionError(path)

        with mock.patch.object(futures_fetch, "fetch_binance_json", side_effect=fake_fetch):
            data = futures_fetch.fetch_binance_tradfi_perp("CL")

        self.assertTrue(data["available"])
        self.assertEqual(data["symbol"], "CLUSDT")
        self.assertEqual(data["summary"]["last_price"], 74.26)
        self.assertGreater(data["summary"]["open_interest_60m_change_pct"], 0)
        self.assertEqual(data["summary"]["klines"], {"15m": 1, "1h": 1, "4h": 1, "1d": 1})

    def test_report_prefers_binance_tradfi_kline_layer(self) -> None:
        rows = [kline(1710000000000 + i * 3600000, "100", "102", "99", str(100 + i * 0.1)) for i in range(260)]
        normalized = futures_fetch.normalize_binance_kline_rows(rows)
        data = {
            "analysis_time_utc": "2026-06-18 00:00",
            "symbol": "CL",
            "ticker": "CL=F",
            "binance_tradfi_symbol": "CLUSDT",
            "daily_90d": [],
            "agg_4h_10d": [],
            "hourly_10d": [],
            "proxies": {"^OVX": {"price": 50.0}, "DX-Y.NYB": {"change_pct": 0.1}},
            "structured_drivers": {
                "binance_tradfi_perp": {
                    "available": True,
                    "symbol": "CLUSDT",
                    "summary": {
                        "last_price": 74.26,
                        "price_change_pct_24h": -0.9,
                        "high_24h": 79.02,
                        "low_24h": 73.46,
                        "quote_volume_24h": 673800000,
                        "mark_price": 74.29,
                        "index_price": 74.25,
                        "open_interest": 1822570.96,
                        "open_interest_60m_change_pct": 1.25,
                        "latest_funding_rate": 0.000001,
                        "latest_top_account_long_short_ratio": 4.0,
                        "latest_top_position_long_short_ratio": 3.0,
                    },
                    "klines": {"15m": normalized[-200:], "1h": normalized, "4h": normalized[-180:], "1d": normalized[-120:]},
                }
            },
            "source_status": {"binance_tradfi_perp": "ok"},
            "errors": {},
            "news": [],
        }

        report = futures_analyze.build_report(data)

        self.assertIn("Binance CLUSDT TradFi Perp K线", report)
        self.assertIn("Binance TradFi 永续", report)
        self.assertIn("CLUSDT", report)

    def test_futures_market_structure_chart_truncates_broken_channel_without_volume_background(self) -> None:
        rows = []
        highs = {25: 100.0, 38: 94.0, 52: 88.0, 64: 80.0, 70: 79.0}
        lows = {23: 95.0, 36: 88.0, 50: 82.0, 62: 74.0, 66: 72.0}
        for i in range(76):
            base = 99 - i * 0.35
            low = lows.get(i, base - 1.0)
            high = highs.get(i, base + 1.0)
            if i >= 67:
                low = 74 + (i - 67) * 0.45
                high = low + 2.4
            close = low + (high - low) * 0.55
            if i >= 70:
                close = high - 0.3
            rows.append({
                "ts": 1710000000 + i * 14400,
                "time_utc": f"2026-06-{(i // 6) + 1:02d} {(i % 6) * 4:02d}:00",
                "open": close - 0.2,
                "high": high,
                "low": low,
                "close": close,
                "volume": 1000 + i,
            })

        payload = futures_chart.build_futures_structure_payload("CL", rows, "CLUSDT")
        html = futures_chart.render_futures_structure_html(payload)

        self.assertEqual(payload["architecture"]["kind"], "下降通道")
        self.assertIn("上破", payload["architecture"]["position"])
        self.assertIsNotNone(payload["architecture"]["break_idx"])
        self.assertEqual(payload["lines"]["upper"][-1]["time"], rows[payload["architecture"]["break_idx"]]["ts"])
        self.assertNotIn("addHistogramSeries", html)
        self.assertIn("无成交量背景", html)

    def test_futures_market_structure_chart_labels_breakdown_as_breakdown_not_breakout(self) -> None:
        rows = []
        highs = {25: 90.0, 38: 96.0, 52: 103.0, 64: 110.0}
        lows = {23: 80.0, 36: 86.0, 50: 93.0, 62: 100.0}
        for i in range(76):
            base = 82 + i * 0.35
            low = lows.get(i, base - 1.0)
            high = highs.get(i, base + 1.0)
            if i >= 67:
                high = 101 - (i - 67) * 0.45
                low = high - 2.4
            close = low + (high - low) * 0.45
            if i >= 70:
                close = low + 0.3
            rows.append({
                "ts": 1710000000 + i * 14400,
                "time_utc": f"2026-06-{(i // 6) + 1:02d} {(i % 6) * 4:02d}:00",
                "open": close + 0.2,
                "high": high,
                "low": low,
                "close": close,
                "volume": 1000 + i,
            })

        payload = futures_chart.build_futures_structure_payload("CL", rows, "CLUSDT")
        html = futures_chart.render_futures_structure_html(payload)

        self.assertEqual(payload["architecture"]["kind"], "上升通道")
        self.assertIn("下破", payload["architecture"]["position"])
        self.assertIn("下破后反抽高点", html)
        self.assertIn("下破后低点", html)
        self.assertNotIn("突破后高点", html)
        self.assertNotIn("突破后回踩低点", html)


if __name__ == "__main__":
    unittest.main()
