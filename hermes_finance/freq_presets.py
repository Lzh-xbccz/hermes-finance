"""
交易频段预设 — 所有市场共用。
安装时 AI 会询问用户选择，配置写入 TRADING_MODE 环境变量或 .env 文件。

三档预设：
  short  = 短线（1H + 15min）— 日内交易，持仓数小时
  medium = 中线（1D + 4H）  — 波段交易，持仓数天
  long   = 长线（1W + 1D）  — 趋势交易，持仓数周

用法：
  from hermes_finance.freq_presets import FREQ_PRESETS, get_freqs, TRADING_MODE

  freqs = get_freqs("crypto")  # → ['1h', '15m'] (根据 TRADING_MODE)
"""

import os

# ── 各频段定义 ──
FREQ_SHORT = ("short", "短线 (1H+15min) — 日内交易，持仓数小时")
FREQ_MEDIUM = ("medium", "中线 (1D+4H) — 波段交易，持仓数天")
FREQ_LONG = ("long", "长线 (1W+1D) — 趋势交易，持仓数周")

ALL_MODES = [FREQ_SHORT, FREQ_MEDIUM, FREQ_LONG]

# ── 各市场在不同频段下的对应用期 ──
FREQ_PRESETS: dict[str, dict[str, list[str]]] = {
    "short": {
        "crypto":    ["1h", "15m"],
        "futures":   ["1h", "15m"],
        "forex":     ["1h", "15m"],
        "us_equity": ["1h", "15m"],
        "a_share":   ["1d", "1h"],   # A股 T+1，最细也得到日线
    },
    "medium": {
        "crypto":    ["1d", "4h"],
        "futures":   ["1d", "4h"],
        "forex":     ["1d", "4h"],
        "us_equity": ["1d", "4h"],
        "a_share":   ["1d", "4h"],
    },
    "long": {
        "crypto":    ["1w", "1d"],
        "futures":   ["1w", "1d"],
        "forex":     ["1w", "1d"],
        "us_equity": ["1w", "1d"],
        "a_share":   ["1w", "1d"],
    },
}

# ── 当前模式（环境变量 > 默认短线）──
TRADING_MODE = os.environ.get("HERMES_TRADING_MODE", "short")
if TRADING_MODE not in FREQ_PRESETS:
    TRADING_MODE = "short"


def get_freqs(market: str) -> list[str]:
    """返回当前交易频段下指定市场的默认缠论周期。"""
    return FREQ_PRESETS.get(TRADING_MODE, FREQ_PRESETS["short"]).get(market, ["1h", "15m"])


def get_mode_label() -> str:
    """返回当前交易频段的显示名称。"""
    for mode_id, label in ALL_MODES:
        if mode_id == TRADING_MODE:
            return label
    return FREQ_SHORT[1]
