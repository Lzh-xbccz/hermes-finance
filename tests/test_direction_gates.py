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


def channel_rows(
    count: int,
    *,
    start_low: float,
    low_step: float,
    width: float,
    close_position: float = 0.65,
) -> list[dict[str, float | int | str]]:
    rows = []
    for i in range(count):
        base = start_low + i * low_step
        high_boost = 5.0 if i % 6 == 2 else 0.0
        low_boost = -5.0 if i % 6 == 5 else 0.0
        low = base + low_boost
        high = base + width + high_boost
        close = low + (high - low) * close_position
        rows.append({
            "ts": 1710000000 + i * 3600,
            "time_utc": f"2026-06-{(i % 28) + 1:02d} 00:00",
            "open": close - 0.1,
            "high": high,
            "low": low,
            "close": close,
            "volume": 1000 + i,
        })
    return rows


def rising_channel_then_pullback_rows() -> list[dict[str, float | int | str]]:
    rows = channel_rows(96, start_low=100, low_step=1.0, width=10, close_position=0.55)
    for i in range(72, 96):
        base = 172 - (i - 72) * 0.75
        high_boost = 5.0 if i % 6 == 2 else 0.0
        low_boost = -5.0 if i % 6 == 5 else 0.0
        low = base + low_boost
        high = base + 10 + high_boost
        close = low + (high - low) * 0.45
        rows[i].update({
            "open": close + 0.1,
            "high": high,
            "low": low,
            "close": close,
        })
    return rows


def rising_channel_from_capitulation_low_rows() -> list[dict[str, float | int | str]]:
    rows = []
    lows = {
        36: 250.0,
        44: 336.0,
        56: 414.0,
        68: 422.0,
        80: 440.0,
    }
    highs = {
        40: 460.0,
        52: 470.0,
        60: 500.0,
        72: 544.0,
        84: 477.0,
    }
    for i in range(88):
        base_low = 390 + i * 0.8
        low = lows.get(i, base_low)
        high = highs.get(i, low + 12)
        if high <= low:
            high = low + 12
        close = low + (high - low) * 0.58
        rows.append({
            "ts": 1717545600 + i * 14400,
            "time_utc": f"2026-06-{(i // 6) + 5:02d} {(i % 6) * 4:02d}:00",
            "open": close - 0.3,
            "high": high,
            "low": low,
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

    def test_forex_related_usd_rates_count_as_one_dimension(self) -> None:
        mod = load_module(
            "forex_analyze_dimension_gate",
            ROOT / "skills" / "forex-market-analysis" / "scripts" / "forex_analyze.py",
        )
        rows = ohlc_rows(40, step=0.001)
        data = {
            "symbol": "USDJPY",
            "daily_90d": rows,
            "agg_4h_10d": rows,
            "hourly_10d": rows,
            "proxies": {
                "DX-Y.NYB": {"change_pct": 0.6},
                "^TNX": {"change_pct": 0.8},
                "^VIX": {"change_pct": 0.0},
            },
            "structured_drivers": {"rates": {"diff_signal": "🟢 USD利差优势 +1.0%"}},
            "upcoming_macro_events": [],
        }

        votes = mod.directional_evidence(data)
        self.assertEqual(len(votes["做多"]), 2)
        self.assertEqual(mod.direction_from_evidence(data, votes), "观望")

    def test_forex_cftc_quote_currency_maps_against_pair(self) -> None:
        mod = load_module(
            "forex_analyze_cftc_pair_mapping",
            ROOT / "skills" / "forex-market-analysis" / "scripts" / "forex_analyze.py",
        )
        rows = ohlc_rows(40, step=0.0)
        data = {
            "symbol": "USDJPY",
            "daily_90d": rows,
            "agg_4h_10d": rows,
            "hourly_10d": rows,
            "proxies": {
                "DX-Y.NYB": {"change_pct": 0.0},
                "^TNX": {"change_pct": 0.0},
                "^VIX": {"change_pct": 0.0},
            },
            "structured_drivers": {"cftc": {"position_signal": "🟢 一致看多"}},
            "upcoming_macro_events": [],
        }

        votes = mod.directional_evidence(data)
        self.assertEqual(votes["做多"], [])
        self.assertEqual(len(votes["做空"]), 1)
        self.assertIn("CFTC/仓位", votes["做空"][0])

    def test_us_equity_market_etfs_count_as_one_dimension(self) -> None:
        mod = load_module(
            "us_equity_analyze_dimension_gate",
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
                "^VIX": {"price": 15.0, "change_pct": 0.0},
                "^TNX": {"change_pct": 0.0},
                "SPY": {"change_pct": 0.8},
                "QQQ": {"change_pct": 0.9},
            },
            "company_event_proxy": {"events": [
                {"type": "business_proxy", "title": "Apple product launch"},
            ]},
        }

        votes = mod.directional_evidence(data)
        self.assertEqual(len(votes["做多"]), 3)
        self.assertEqual(mod.direction_from_evidence(data, votes), "做多")
        self.assertEqual(sum("市场/ETF" in item for item in votes["做多"]), 1)
        self.assertEqual(sum("公司事件" in item for item in votes["做多"]), 1)

    def test_futures_technical_pattern_is_one_dimension(self) -> None:
        mod = load_module(
            "futures_analyze_dimension_gate",
            ROOT / "skills" / "futures-market-analysis" / "scripts" / "futures_analyze.py",
        )
        rows = ohlc_rows(40, step=1.0)
        data = {
            "symbol": "HG",
            "proxies": {
                "DX-Y.NYB": {"change_pct": -0.6},
            },
            "structured_drivers": {},
        }

        votes = mod.directional_evidence(data, rows, rows)
        self.assertEqual(len(votes["做多"]), 2)
        self.assertEqual(mod.direction_from_evidence(data, rows, rows, votes), "观望")

    def test_futures_fundamental_headlines_are_one_dimension(self) -> None:
        mod = load_module(
            "futures_analyze_fundamental_dimension",
            ROOT / "skills" / "futures-market-analysis" / "scripts" / "futures_analyze.py",
        )
        rows = ohlc_rows(40, step=0.0)
        data = {
            "symbol": "CL",
            "proxies": {
                "DX-Y.NYB": {"change_pct": 0.0},
                "^OVX": {"price": 35.0, "change_pct": 0.0},
            },
            "structured_drivers": {"eia": {"available": True}},
            "news": [
                {"title": "Oil rises as inventory draw points to tighter supply"},
                {"title": "Crude gains after OPEC cut fuels supply fears"},
            ],
        }

        votes = mod.directional_evidence(data, rows, rows)
        self.assertEqual(len(votes["做多"]), 1)
        self.assertIn("供需/库存/事件", votes["做多"][0])
        self.assertEqual(mod.direction_from_evidence(data, rows, rows, votes), "观望")

    def test_futures_eia_availability_without_inventory_delta_is_neutral(self) -> None:
        mod = load_module(
            "futures_analyze_eia_neutral",
            ROOT / "skills" / "futures-market-analysis" / "scripts" / "futures_analyze.py",
        )
        rows = ohlc_rows(40, step=0.0)
        data = {
            "symbol": "CL",
            "proxies": {
                "DX-Y.NYB": {"change_pct": 0.0},
                "^OVX": {"price": 35.0, "change_pct": 0.0},
            },
            "structured_drivers": {"eia": {"available": True}},
            "news": [],
        }

        votes = mod.directional_evidence(data, rows, rows)
        self.assertEqual(votes["做多"], [])
        self.assertEqual(votes["做空"], [])
        self.assertTrue(any("EIA页面可用" in item for item in votes["neutral"]))

    def test_crypto_contract_signals_count_as_one_dimension(self) -> None:
        mod = load_module(
            "crypto_fetch_direction_gate",
            ROOT / "skills" / "crypto-market-analysis" / "scripts" / "fetch_data.py",
        )
        rows = ohlc_rows(40, step=0.0)
        data = {
            "daily": rows,
            "h4": rows,
            "contracts": {
                "price_change_pct_24h": 2.0,
                "oi_60m_change_pct": 0.8,
                "latest_long_short_ratio": 1.6,
                "latest_funding_rate": 0.00005,
            },
            "macro": {},
            "sentiment": {},
        }

        votes = mod.directional_evidence(data)
        self.assertEqual(len(votes["做多"]), 1)
        self.assertIn("合约结构", votes["做多"][0])
        self.assertEqual(mod.direction_from_evidence(votes), "观望")

    def test_crypto_macro_proxies_count_as_one_dimension(self) -> None:
        mod = load_module(
            "crypto_fetch_macro_dimension_gate",
            ROOT / "skills" / "crypto-market-analysis" / "scripts" / "fetch_data.py",
        )
        rows = ohlc_rows(40, step=0.0)
        data = {
            "daily": rows,
            "h4": rows,
            "contracts": {
                "price_change_pct_24h": 0.0,
                "oi_60m_change_pct": 0.0,
                "latest_long_short_ratio": 1.0,
                "latest_funding_rate": 0.0,
            },
            "macro": {
                "spy_5d_change_pct": 2.0,
                "vix_price": 12.0,
                "dxy_change_pct": -0.8,
                "asset_5d_change_pct": 5.0,
            },
            "sentiment": {},
        }

        votes = mod.directional_evidence(data)
        self.assertEqual(len(votes["做多"]), 1)
        self.assertIn("宏观/风险偏好", votes["做多"][0])
        self.assertEqual(mod.direction_from_evidence(votes), "观望")

    def test_crypto_news_events_count_as_one_dimension(self) -> None:
        mod = load_module(
            "crypto_fetch_news_dimension_gate",
            ROOT / "skills" / "crypto-market-analysis" / "scripts" / "fetch_data.py",
        )
        rows = ohlc_rows(40, step=0.0)
        data = {
            "daily": rows,
            "h4": rows,
            "contracts": {
                "price_change_pct_24h": 0.0,
                "oi_60m_change_pct": 0.0,
                "latest_long_short_ratio": 1.0,
                "latest_funding_rate": 0.0,
            },
            "news": {
                "bullish": [
                    {"title": "Spot bitcoin ETF inflows return"},
                    {"title": "Institutional demand lifts bitcoin"},
                ],
                "bearish": [],
            },
            "macro": {},
            "sentiment": {},
        }

        votes = mod.directional_evidence(data)
        self.assertEqual(len(votes["做多"]), 1)
        self.assertIn("新闻/事件基本面", votes["做多"][0])
        self.assertEqual(mod.direction_from_evidence(votes), "观望")

    def test_crypto_mixed_news_events_are_neutral(self) -> None:
        mod = load_module(
            "crypto_fetch_mixed_news_gate",
            ROOT / "skills" / "crypto-market-analysis" / "scripts" / "fetch_data.py",
        )
        rows = ohlc_rows(40, step=0.0)
        data = {
            "daily": rows,
            "h4": rows,
            "contracts": {
                "price_change_pct_24h": 0.0,
                "oi_60m_change_pct": 0.0,
                "latest_long_short_ratio": 1.0,
                "latest_funding_rate": 0.0,
            },
            "news": {
                "bullish": [{"title": "Bitcoin ETF inflow improves"}],
                "bearish": [{"title": "Crypto exchange hack hits sentiment"}],
            },
            "macro": {},
            "sentiment": {},
        }

        votes = mod.directional_evidence(data)
        self.assertEqual(votes["做多"], [])
        self.assertEqual(votes["做空"], [])
        self.assertTrue(any("新闻/事件多空混合" in item for item in votes["neutral"]))

    def test_crypto_extreme_funding_blocks_long_direction(self) -> None:
        mod = load_module(
            "crypto_fetch_funding_veto",
            ROOT / "skills" / "crypto-market-analysis" / "scripts" / "fetch_data.py",
        )
        rows = ohlc_rows(40, step=1.0)
        data = {
            "daily": rows,
            "h4": rows,
            "contracts": {
                "price_change_pct_24h": 2.0,
                "oi_60m_change_pct": 0.8,
                "latest_long_short_ratio": 1.4,
                "latest_funding_rate": 0.0005,
            },
            "macro": {
                "spy_5d_change_pct": 2.0,
                "vix_price": 12.0,
                "dxy_change_pct": -0.8,
                "asset_5d_change_pct": 5.0,
            },
            "news": {
                "bullish": [{"title": "Spot bitcoin ETF inflows return"}],
                "bearish": [],
            },
            "sentiment": {"fear_greed": 30},
            "options": {"put_call_ratio": 0.6},
        }

        votes = mod.directional_evidence(data)
        self.assertGreaterEqual(len(votes["做多"]), 3)
        self.assertTrue(votes["veto_long"])
        self.assertEqual(mod.direction_from_evidence(votes), "观望")

    def test_crypto_requires_core_dimensions(self) -> None:
        mod = load_module(
            "crypto_fetch_core_dimension_gate",
            ROOT / "skills" / "crypto-market-analysis" / "scripts" / "fetch_data.py",
        )
        rows = ohlc_rows(40, step=1.0)
        data = {
            "daily": rows,
            "h4": rows,
            "macro": {
                "spy_5d_change_pct": 2.0,
                "vix_price": 12.0,
                "dxy_change_pct": -0.8,
                "asset_5d_change_pct": 5.0,
            },
            "sentiment": {"fear_greed": 30},
            "options": {"put_call_ratio": 0.6},
        }

        votes = mod.directional_evidence(data)
        self.assertIn("合约结构", votes["missing"])
        self.assertEqual(mod.direction_from_evidence(votes), "观望")

    def test_crypto_technical_neutral_is_not_missing_when_4h_pattern_votes(self) -> None:
        mod = load_module(
            "crypto_fetch_technical_neutral_gate",
            ROOT / "skills" / "crypto-market-analysis" / "scripts" / "fetch_data.py",
        )
        rows = []
        for i in range(40):
            close = 100 + (i % 5 - 2)
            rows.append({
                "ts": 1710000000 + i * 3600,
                "time_utc": f"2026-06-{(i % 28) + 1:02d} 00:00",
                "open": close,
                "high": 110 if i % 7 == 0 else close + 1,
                "low": 90 if i % 9 == 0 or i >= 37 else close - 1,
                "close": close,
                "volume": 1000,
            })
        data = {
            "daily": rows,
            "h4": rows,
            "contracts": {
                "price_change_pct_24h": 0.0,
                "oi_60m_change_pct": 0.0,
                "latest_long_short_ratio": 1.0,
                "latest_funding_rate": 0.0,
            },
            "macro": {},
            "sentiment": {},
        }

        votes = mod.directional_evidence(data)
        self.assertNotIn("技术结构", votes["missing"])
        self.assertTrue(any("技术结构=震荡/无方向优势" in item for item in votes["neutral"]))

    def test_crypto_market_architecture_detects_rising_channel(self) -> None:
        mod = load_module(
            "crypto_fetch_market_architecture",
            ROOT / "skills" / "crypto-market-analysis" / "scripts" / "fetch_data.py",
        )
        rows = channel_rows(48, start_low=100, low_step=0.8, width=8, close_position=0.82)

        arch = mod._crypto_market_architecture(rows)

        self.assertEqual(arch["kind"], "上升通道")
        self.assertEqual(arch["stance"], "做多")
        self.assertIn("市场架构=上升通道", arch["reason"])

    def test_crypto_market_architecture_returns_drawable_lines(self) -> None:
        mod = load_module(
            "crypto_fetch_market_architecture_lines",
            ROOT / "skills" / "crypto-market-analysis" / "scripts" / "fetch_data.py",
        )
        rows = channel_rows(48, start_low=100, low_step=0.8, width=8, close_position=0.82)

        arch = mod._crypto_market_architecture(rows)

        self.assertGreaterEqual(len(arch["upper_line"]["points"]), 2)
        self.assertGreaterEqual(len(arch["lower_line"]["points"]), 2)
        self.assertGreaterEqual(len(arch["upper_line"]["anchors"]), 2)
        self.assertGreaterEqual(len(arch["lower_line"]["anchors"]), 2)
        self.assertGreater(arch["upper_breakout"], arch["upper"])
        self.assertLess(arch["lower_breakdown"], arch["lower"])
        self.assertTrue(any(item["step"] == "轨道" for item in arch["logic"]))

    def test_crypto_market_architecture_keeps_parent_rising_channel_during_pullback(self) -> None:
        mod = load_module(
            "crypto_fetch_market_architecture_pullback",
            ROOT / "skills" / "crypto-market-analysis" / "scripts" / "fetch_data.py",
        )
        rows = rising_channel_then_pullback_rows()

        arch = mod._crypto_market_architecture(rows)

        self.assertEqual(arch["kind"], "上升通道")
        self.assertIn("最近4组摆点=下降通道", "；".join(item["detail"] for item in arch["logic"]))
        self.assertEqual(arch["upper_line"]["points"][0]["idx"], arch["upper_line"]["anchors"][0]["idx"])
        self.assertEqual(arch["lower_line"]["points"][0]["idx"], arch["lower_line"]["anchors"][0]["idx"])

    def test_crypto_market_architecture_prefers_foundation_low_trendline(self) -> None:
        mod = load_module(
            "crypto_fetch_market_architecture_foundation",
            ROOT / "skills" / "crypto-market-analysis" / "scripts" / "fetch_data.py",
        )
        rows = rising_channel_from_capitulation_low_rows()

        arch = mod._crypto_market_architecture(rows)

        self.assertEqual(arch["kind"], "上升通道")
        self.assertEqual(arch["structure_mode"], "底部趋势线")
        self.assertEqual(arch["lower_line"]["anchors"][0]["idx"], 36)
        self.assertEqual(arch["lower_line"]["points"][0]["idx"], 36)
        self.assertIn("底部趋势线", "；".join(item["detail"] for item in arch["logic"]))

    def test_crypto_market_architecture_foundation_upper_uses_main_high_chain(self) -> None:
        mod = load_module(
            "crypto_fetch_market_architecture_upper_chain",
            ROOT / "skills" / "crypto-market-analysis" / "scripts" / "fetch_data.py",
        )
        rows = rising_channel_from_capitulation_low_rows()

        arch = mod._crypto_market_architecture(rows)

        self.assertEqual(arch["structure_mode"], "底部趋势线")
        self.assertEqual([p["idx"] for p in arch["upper_line"]["anchors"]], [40, 72])
        self.assertNotIn(84, [p["idx"] for p in arch["upper_line"]["anchors"]])
        self.assertTrue(any("跳过回调 lower high" in item["detail"] for item in arch["logic"]))

    def test_crypto_market_architecture_keeps_conflicting_recent_structure_as_subtrend(self) -> None:
        mod = load_module(
            "crypto_fetch_market_architecture_subtrend",
            ROOT / "skills" / "crypto-market-analysis" / "scripts" / "fetch_data.py",
        )
        rows = rising_channel_then_pullback_rows()

        arch = mod._crypto_market_architecture(rows)

        self.assertEqual(arch["kind"], "上升通道")
        self.assertEqual(arch["sub_structure"]["kind"], "下降通道")
        self.assertGreaterEqual(len(arch["sub_structure"]["upper_line"]["points"]), 2)
        self.assertGreaterEqual(len(arch["sub_structure"]["lower_line"]["points"]), 2)
        self.assertTrue(any(item["step"] == "子趋势" for item in arch["logic"]))

    def test_crypto_market_architecture_falling_upper_uses_lower_high_chain(self) -> None:
        mod = load_module(
            "crypto_fetch_market_architecture_lower_high_chain",
            ROOT / "skills" / "crypto-market-analysis" / "scripts" / "fetch_data.py",
        )
        rows = channel_rows(96, start_low=100, low_step=0.6, width=12, close_position=0.55)
        highs = {60: 190.0, 68: 184.0, 82: 171.0}
        lows = {58: 142.0, 70: 146.0, 84: 150.0}
        for i in range(56, 96):
            base = 148 + (i - 56) * 0.1
            low = lows.get(i, base)
            high = highs.get(i, low + 8)
            close = low + (high - low) * 0.55
            rows[i].update({"open": close - 0.1, "high": high, "low": low, "close": close})

        arch = mod._crypto_market_architecture(rows)

        if arch["kind"] in {"下降通道", "收敛三角/楔形"}:
            self.assertEqual([p["idx"] for p in arch["upper_line"]["anchors"]], [60, 68, 82])

    def test_crypto_market_architecture_envelope_keeps_outer_rails(self) -> None:
        mod = load_module(
            "crypto_fetch_market_architecture_envelope",
            ROOT / "skills" / "crypto-market-analysis" / "scripts" / "fetch_data.py",
        )
        highs = [
            {"idx": 0, "price": 100.0},
            {"idx": 5, "price": 90.0},
            {"idx": 10, "price": 80.0},
        ]
        lows = [
            {"idx": 0, "price": 50.0},
            {"idx": 5, "price": 58.0},
            {"idx": 10, "price": 66.0},
        ]

        upper = mod._architecture_envelope_line(highs, 10, "upper", 0)
        lower = mod._architecture_envelope_line(lows, 10, "lower", 0)

        self.assertEqual([p["idx"] for p in upper["anchors"]], [0, 10])
        self.assertEqual([p["idx"] for p in lower["anchors"]], [0, 10])
        self.assertEqual(len(upper["points"]), 2)
        self.assertEqual(len(lower["points"]), 2)

    def test_crypto_market_architecture_parent_upper_extends_after_peak(self) -> None:
        mod = load_module(
            "crypto_fetch_market_architecture_peak_extension",
            ROOT / "skills" / "crypto-market-analysis" / "scripts" / "fetch_data.py",
        )
        highs = [
            {"idx": 0, "price": 100.0},
            {"idx": 5, "price": 120.0},
            {"idx": 10, "price": 112.0},
            {"idx": 15, "price": 105.0},
        ]

        parent = mod._architecture_envelope_line(highs, 18, "upper", 0, role="parent", direction_slope=2.0)
        subtrend = mod._architecture_envelope_line(highs, 18, "upper", 0, role="subtrend")

        self.assertEqual([p["idx"] for p in parent["anchors"]], [0, 5])
        self.assertEqual([p["idx"] for p in parent["points"]], [0, 18])
        self.assertGreater(parent["points"][-1]["price"], parent["anchors"][-1]["price"])
        self.assertEqual([p["idx"] for p in subtrend["anchors"]], [5, 15])
        self.assertLess(subtrend["points"][-1]["price"], subtrend["anchors"][-1]["price"])

    def test_crypto_market_architecture_is_one_technical_dimension(self) -> None:
        mod = load_module(
            "crypto_fetch_market_architecture_dimension",
            ROOT / "skills" / "crypto-market-analysis" / "scripts" / "fetch_data.py",
        )
        rows = channel_rows(48, start_low=100, low_step=1.0, width=8, close_position=0.82)
        data = {
            "daily": rows,
            "h4": rows,
            "contracts": {
                "price_change_pct_24h": 0.0,
                "oi_60m_change_pct": 0.0,
                "latest_long_short_ratio": 1.0,
                "latest_funding_rate": 0.0,
            },
            "macro": {},
            "sentiment": {},
        }

        votes = mod.directional_evidence(data)

        self.assertEqual(len(votes["做多"]), 1)
        self.assertIn("技术结构", votes["做多"][0])
        self.assertIn("市场架构=上升通道", votes["做多"][0])

    def test_market_structure_chart_payload_and_html(self) -> None:
        mod = load_module(
            "crypto_market_structure_chart",
            ROOT / "skills" / "crypto-market-analysis" / "scripts" / "market_structure_chart.py",
        )
        rows = channel_rows(48, start_low=100, low_step=0.8, width=8, close_position=0.82)

        payload = mod.build_market_structure_payload("btc", rows)
        html = mod.render_market_structure_html(payload)

        self.assertEqual(payload["symbol"], "BTCUSDT")
        self.assertEqual(payload["architecture"]["kind"], "上升通道")
        self.assertGreaterEqual(len(payload["lines"]["upper"]), 2)
        self.assertGreaterEqual(len(payload["lines"]["lower"]), 2)
        self.assertIn("subUpper", payload["lines"])
        self.assertIn("subLower", payload["lines"])
        self.assertIn("LightweightCharts", html)
        self.assertIn("上升通道", html)
        self.assertIn("上轨 / 阻力", html)


if __name__ == "__main__":
    unittest.main()
