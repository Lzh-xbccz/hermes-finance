from __future__ import annotations

import unittest

from hermes_finance.czsc_adapter import _normalize_freqs, _resonance, extract_market_rows


def row(i: int) -> dict[str, float | int | str]:
    return {
        "ts": 1710000000 + i * 3600,
        "time_utc": "2024-03-09 16:00",
        "open": 100 + i,
        "high": 101 + i,
        "low": 99 + i,
        "close": 100.5 + i,
        "volume": 1000,
    }


class CzscAdapterTests(unittest.TestCase):
    def test_extract_standard_market_rows(self) -> None:
        data = {
            "symbol": "EURUSD",
            "ticker": "EURUSD=X",
            "hourly_10d": [row(1)],
            "agg_4h_10d": [row(2)],
            "daily_90d": [row(3)],
        }

        rows, source = extract_market_rows(data, market="forex")

        self.assertEqual(source, "EURUSD=X collector K-lines")
        self.assertEqual(len(rows["1h"]), 1)
        self.assertEqual(len(rows["4h"]), 1)
        self.assertEqual(len(rows["1d"]), 1)

    def test_futures_default_freqs_from_preset(self) -> None:
        self.assertEqual(_normalize_freqs(None, market="futures"), ["1h", "15m"])

    def test_a_share_default_freqs_from_preset(self) -> None:
        self.assertEqual(_normalize_freqs(None, market="a_share"), ["1d", "1h"])

    def test_live_broken_up_bi_penalizes_short_term_resonance(self) -> None:
        analyses = {
            "4h": {
                "last_bi": {"direction": "向上", "live_direction": "向下", "broken_by_current_price": True},
                "center": None,
                "active_signals": [],
            },
            "15m": {
                "last_bi": {"direction": "向上", "live_direction": "向下", "broken_by_current_price": True},
                "center": {"position": "下方"},
                "active_signals": [],
            },
        }

        resonance = _resonance(analyses)

        self.assertLessEqual(resonance["score"], -2)
        self.assertIn("空", resonance["verdict"])


if __name__ == "__main__":
    unittest.main()
