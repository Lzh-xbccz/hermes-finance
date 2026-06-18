from __future__ import annotations

import importlib.util
from pathlib import Path
import types
from unittest import mock
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ScriptRegressionTests(unittest.TestCase):
    def test_czsc_parse_args_returns_signals_flag(self) -> None:
        class FakeFreq:
            F1 = types.SimpleNamespace(value=1)
            F5 = types.SimpleNamespace(value=5)
            F15 = types.SimpleNamespace(value=15)
            F30 = types.SimpleNamespace(value=30)
            F60 = types.SimpleNamespace(value=60)
            F120 = types.SimpleNamespace(value=120)
            F240 = types.SimpleNamespace(value=240)
            D = types.SimpleNamespace(value=1440)
            W = types.SimpleNamespace(value=10080)

        fake_czsc = types.ModuleType("czsc")
        fake_czsc.CZSC = object
        fake_czsc.RawBar = object
        fake_czsc.Freq = FakeFreq
        fake_czsc.format_standard_kline = lambda *args, **kwargs: []
        fake_connector = types.ModuleType("czsc.connectors.ccxt_connector")
        fake_connector.get_raw_bars = lambda *args, **kwargs: []
        fake_signals = types.ModuleType("czsc._native.signals")
        fake_signals.call_signal = lambda *args, **kwargs: []

        modules = {
            "czsc": fake_czsc,
            "czsc.connectors": types.ModuleType("czsc.connectors"),
            "czsc.connectors.ccxt_connector": fake_connector,
            "czsc._native": types.ModuleType("czsc._native"),
            "czsc._native.signals": fake_signals,
        }
        with mock.patch.dict(sys.modules, modules):
            module = load_module("czsc_analyze_regression", ROOT / "scripts" / "czsc_analyze.py")

            with mock.patch.object(sys, "argv", ["czsc_analyze.py", "BTCUSDT", "--signals", "--report"]):
                symbol, freqs, do_chart, do_signals, do_report = module.parse_args()

        self.assertEqual(symbol, "BTCUSDT")
        self.assertEqual(freqs, ["4h", "15m"])
        self.assertFalse(do_chart)
        self.assertTrue(do_signals)
        self.assertTrue(do_report)

    def test_a_share_remote_command_uses_single_env_prefix(self) -> None:
        module = load_module(
            "a_share_fetch_regression",
            ROOT / "skills" / "a-share-market-analysis" / "scripts" / "a_share_fetch.py",
        )

        completed = mock.Mock(returncode=0, stdout="{}", stderr="")
        with mock.patch.object(module, "_load_remote_script", return_value="print('ok')"):
            with mock.patch.object(module.subprocess, "run", return_value=completed) as run:
                module.run_remote("ash-remote", ["all"], "600519")

        cmd = run.call_args.args[0]
        self.assertEqual(
            cmd,
            [
                "ssh",
                "-o",
                "BatchMode=yes",
                "ash-remote",
                "env",
                "A_SHARE_SECTIONS=all",
                "A_SHARE_STOCK=600519",
                "python3",
                "-",
            ],
        )

    def test_parse_sectors_keeps_non_yi_flow_values(self) -> None:
        module = load_module(
            "a_share_data_regression",
            ROOT / "skills" / "a-share-market-analysis" / "scripts" / "a_share_data.py",
        )

        result = module.parse_sectors([
            {"board": "示例行业", "netBuy": "1.5%", "totalVol": "2500万"},
        ])

        self.assertEqual(result["top_gainers"][0]["net_flow_yi"], 2500.0)


if __name__ == "__main__":
    unittest.main()
