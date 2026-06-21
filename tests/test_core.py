from __future__ import annotations

from unittest import mock
import unittest

from hermes_finance.routing import classify, normalize_market
from hermes_finance.formatters.markdown import format_market_result
from hermes_finance.service import analyze_market, crypto_pair_symbol, futures_symbol, route_market


class RoutingTests(unittest.TestCase):
    def test_crypto_route(self) -> None:
        self.assertEqual(classify("BTC")["market"], "crypto")

    def test_a_share_route(self) -> None:
        self.assertEqual(classify("600519")["market"], "a_share")

    def test_forex_route(self) -> None:
        self.assertEqual(classify("EURUSD")["market"], "forex")

    def test_binance_tradfi_perp_routes_to_futures_before_crypto(self) -> None:
        result = classify("CLUSDT")
        self.assertEqual(result["market"], "futures")
        self.assertIn("Binance TradFi", result["reason"])

    def test_market_aliases(self) -> None:
        self.assertEqual(normalize_market("a-share"), "a_share")
        self.assertEqual(normalize_market("us-equity"), "us_equity")

    def test_route_market_shape(self) -> None:
        result = route_market("AAPL")
        self.assertEqual(result["market"], "us_equity")
        self.assertEqual(result["input"], "AAPL")


class ServiceTests(unittest.TestCase):
    def test_crypto_pair_symbol(self) -> None:
        self.assertEqual(crypto_pair_symbol("bitcoin"), "BTCUSDT")
        self.assertEqual(crypto_pair_symbol("ETHUSDT"), "ETHUSDT")

    def test_futures_symbol_aliases_binance_tradfi_perps(self) -> None:
        self.assertEqual(futures_symbol("CLUSDT"), "CL")
        self.assertEqual(futures_symbol("XAUUSDT"), "GC")
        self.assertEqual(futures_symbol("COPPERUSDT"), "HG")

    @mock.patch("hermes_finance.service.fetch_market_data")
    @mock.patch("hermes_finance.service.czsc_analyze")
    def test_crypto_analyze_runs_czsc_by_default(self, mock_czsc, mock_fetch) -> None:
        mock_fetch.return_value = {
            "ok": True,
            "market": "crypto",
            "symbol": "BTC",
            "collector": "collector.py",
            "data": None,
            "output_text": "collector evidence",
            "stderr": "",
        }
        mock_czsc.return_value = {
            "ok": True,
            "report_text": "czsc evidence",
        }
        result = analyze_market("crypto", "BTC")
        mock_czsc.assert_called_once()
        self.assertEqual(mock_czsc.call_args.args[0], "BTCUSDT")
        self.assertIn("Crypto Analysis Contract", result["markdown"])

    @mock.patch("hermes_finance.service.fetch_market_data")
    @mock.patch("hermes_finance.service.analyze_market_klines")
    def test_futures_analyze_runs_collector_kline_czsc_by_default(self, mock_czsc, mock_fetch) -> None:
        mock_fetch.return_value = {
            "ok": True,
            "market": "futures",
            "symbol": "CL",
            "collector": "collector.py",
            "data": {"symbol": "CL", "source_status": {"binance_tradfi_perp": "ok"}},
            "output_text": "",
            "stderr": "",
        }
        mock_czsc.return_value = {
            "ok": True,
            "mode": "collector_klines",
            "report_text": "futures czsc evidence",
        }
        result = analyze_market("futures", "CL")
        mock_czsc.assert_called_once()
        self.assertEqual(mock_czsc.call_args.kwargs["market"], "futures")
        self.assertIn("Eight-Dimension Analysis Contract", result["markdown"])


class FormatterTests(unittest.TestCase):
    def test_crypto_markdown_requires_eight_dimension_contract(self) -> None:
        result = {
            "market": "crypto",
            "symbol": "BTC",
            "fetch": {
                "ok": True,
                "collector": "skills/crypto-market-analysis/scripts/fetch_data.py",
                "data": None,
                "output_text": "collector evidence",
                "stderr": "",
            },
            "czsc": {"ok": True, "report_text": "czsc evidence"},
            "notes": [],
        }
        markdown = format_market_result(result)
        self.assertIn("## Crypto Analysis Contract", markdown)
        self.assertIn("各维度证据", markdown)
        self.assertIn("反向审计", markdown)
        self.assertIn("缠论确认", markdown)
        self.assertIn("八维深挖", markdown)
        self.assertIn("Do not compress", markdown)

    def test_futures_markdown_requires_eight_dimension_contract(self) -> None:
        result = {
            "market": "futures",
            "symbol": "CL",
            "fetch": {
                "ok": True,
                "collector": "skills/futures-market-analysis/scripts/futures_fetch.py",
                "data": {"symbol": "CL", "source_status": {"binance_tradfi_perp": "ok"}},
                "output_text": "",
                "stderr": "",
            },
            "czsc": {"ok": True, "mode": "collector_klines", "report_text": "czsc evidence"},
            "notes": [],
        }
        markdown = format_market_result(result)
        self.assertIn("## Eight-Dimension Analysis Contract", markdown)
        self.assertIn("可执行合约层/OI/资金费率", markdown)
        self.assertIn("各维度证据", markdown)
        self.assertIn("反向审计", markdown)
        self.assertIn("缠论确认", markdown)
        self.assertIn("CZSC score", markdown)
        self.assertIn("synthesize the collected evidence", markdown)
        self.assertIn("CZSC Report", markdown)


if __name__ == "__main__":
    unittest.main()
