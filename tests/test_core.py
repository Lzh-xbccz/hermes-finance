from __future__ import annotations

import unittest

from hermes_finance.routing import classify, normalize_market
from hermes_finance.service import crypto_pair_symbol, route_market


class RoutingTests(unittest.TestCase):
    def test_crypto_route(self) -> None:
        self.assertEqual(classify("BTC")["market"], "crypto")

    def test_a_share_route(self) -> None:
        self.assertEqual(classify("600519")["market"], "a_share")

    def test_forex_route(self) -> None:
        self.assertEqual(classify("EURUSD")["market"], "forex")

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


if __name__ == "__main__":
    unittest.main()
