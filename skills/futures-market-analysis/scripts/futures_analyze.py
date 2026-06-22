#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys as _sys
from pathlib import Path
from typing import Any, Dict, List

_sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "scripts"))
from shared_ta import (
    classify_pattern as _classify_pattern,
    classify_today as _classify_today,
    find_swings,
    structure_basis,
    recent_key_actions as _recent_key_actions,
    structure_levels,
    shape_text,
)

FETCHER = Path(__file__).resolve().parent / "futures_fetch.py"
BINANCE_TRADFI_EXPECTED = {"CL", "BZ", "GC", "SI", "HG", "NG", "PL", "PA"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate a futures market analysis report.")
    parser.add_argument("symbol", nargs="?", help="Futures symbol such as CL, GC, ES")
    parser.add_argument("--input", help="Path to previously fetched JSON")
    return parser.parse_args()


def load_json(path: str) -> Dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def fetch_live(symbol: str) -> Dict[str, Any]:
    proc = subprocess.run(["python3", str(FETCHER), symbol, "--compact"], text=True, capture_output=True)
    if proc.returncode != 0:
        raise SystemExit(proc.stderr.strip() or proc.stdout.strip())
    return json.loads(proc.stdout)


# ── 期货专用参数（委托给 shared_ta）──
def classify_pattern(rows: List[Dict[str, Any]]) -> str:
    return _classify_pattern(rows, box_chg_pct=4, box_width_pct=10, trend_chg_pct=5, trend_recent_pct=1, recovery_pct=2)

def classify_today(rows: List[Dict[str, Any]]) -> str:
    return _classify_today(rows, continuation_ratio=0.998, bounce_ratio=1.01, breakdown_ratio=0.995)

def recent_key_actions(rows: List[Dict[str, Any]]) -> List[str]:
    return _recent_key_actions(rows, body_threshold=1.0, range_threshold=2.0)

# find_swings / structure_basis / shape_text / structure_levels → 直接使用 shared_ta 版本


def volume_state(rows: List[Dict[str, Any]]) -> str:
    if len(rows) < 10:
        return "量能样本不足"
    recent = sum(r["volume"] for r in rows[-5:]) / 5
    prev = sum(r["volume"] for r in rows[-10:-5]) / 5
    latest_close = rows[-1]["close"]
    prev_close = rows[-2]["close"]
    if prev <= 0:
        return "成交量代理不足"
    ratio = recent / prev
    if latest_close > prev_close and ratio > 1.1:
        return f"上涨放量（近5根/前5根量比 {ratio:.2f}）→ 健康"
    if latest_close < prev_close and ratio > 1.1:
        return f"下跌放量（近5根/前5根量比 {ratio:.2f}）→ 危险"
    if ratio < 0.8:
        return f"缩量整理（近5根/前5根量比 {ratio:.2f}）"
    return f"量能中性（近5根/前5根量比 {ratio:.2f}）"


def binance_tradfi_block(data: Dict[str, Any]) -> Dict[str, Any]:
    block = data.get("structured_drivers", {}).get("binance_tradfi_perp", {})
    return block if isinstance(block, dict) else {}


def binance_tradfi_available(data: Dict[str, Any]) -> bool:
    block = binance_tradfi_block(data)
    return bool(block.get("available") and block.get("klines"))


def analysis_rows(data: Dict[str, Any]) -> Dict[str, Any]:
    block = binance_tradfi_block(data)
    klines = block.get("klines", {}) if block.get("available") else {}
    has_binance_core = bool(klines.get("1h") and klines.get("4h") and klines.get("1d"))
    if has_binance_core:
        return {
            "daily": klines["1d"],
            "h4": klines["4h"],
            "h1": klines["1h"],
            "source": f"Binance {block.get('symbol', '')} TradFi Perp K线",
            "uses_binance": True,
        }
    return {
        "daily": data.get("daily_90d", []),
        "h4": data.get("agg_4h_10d", []),
        "h1": data.get("hourly_10d", []),
        "source": f"{data.get('ticker', data.get('symbol', '近月代理'))} 近月代理K线",
        "uses_binance": False,
    }


def fmt_number(value: Any, digits: int = 2) -> str:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return "n/a"
    if abs(number) >= 1_000_000_000:
        return f"{number / 1_000_000_000:.{digits}f}B"
    if abs(number) >= 1_000_000:
        return f"{number / 1_000_000:.{digits}f}M"
    if abs(number) >= 1_000:
        return f"{number:,.{digits}f}"
    return f"{number:.{digits}f}"


def fmt_pct(value: Any, digits: int = 2) -> str:
    try:
        return f"{float(value):+.{digits}f}%"
    except (TypeError, ValueError):
        return "n/a"


def fmt_rate(value: Any, digits: int = 4) -> str:
    try:
        return f"{float(value) * 100:+.{digits}f}%"
    except (TypeError, ValueError):
        return "n/a"


def binance_tradfi_summary(data: Dict[str, Any]) -> str:
    block = binance_tradfi_block(data)
    if not block:
        return "Binance TradFi 永续未配置"
    symbol = block.get("symbol", data.get("binance_tradfi_symbol", ""))
    if not block.get("available"):
        return f"Binance {symbol or 'TradFi'} 永续未返回可用数据"
    summary = block.get("summary", {})
    return (
        f"Binance {symbol}: last {fmt_number(summary.get('last_price'))}, "
        f"mark/index {fmt_number(summary.get('mark_price'))}/{fmt_number(summary.get('index_price'))}, "
        f"24h {fmt_pct(summary.get('price_change_pct_24h'))}, "
        f"range {fmt_number(summary.get('low_24h'))}-{fmt_number(summary.get('high_24h'))}, "
        f"quoteVol {fmt_number(summary.get('quote_volume_24h'))}, "
        f"OI {fmt_number(summary.get('open_interest'))} ({fmt_pct(summary.get('open_interest_60m_change_pct'))}/60m), "
        f"funding {fmt_rate(summary.get('latest_funding_rate'))}, "
        f"top acct L/S {fmt_number(summary.get('latest_top_account_long_short_ratio'))}, "
        f"top pos L/S {fmt_number(summary.get('latest_top_position_long_short_ratio'))}"
    )


def market_structure_text(data: Dict[str, Any], row_basis: Dict[str, Any]) -> str:
    block = binance_tradfi_block(data)
    if row_basis.get("uses_binance") and block.get("available"):
        return (
            f"以 Binance {block.get('symbol')} TradFi 永续作为可执行K线/资金费率/OI层；"
            f"{data.get('ticker')} 近月代理、CFTC/EIA/OVX/DXY 用于传统期货供需与宏观验证"
        )
    return "以传统近月代理观察，注意单合约/近月替代限制"


def key_block_gaps(data: Dict[str, Any]) -> List[str]:
    gaps = []
    rows = analysis_rows(data)
    daily = rows["daily"]
    h4 = rows["h4"]
    h1 = rows["h1"]
    if len(daily) < 20 or len(h4) < 12 or len(h1) < 24:
        gaps.append("技术结构")
    symbol = data["symbol"]
    if symbol in BINANCE_TRADFI_EXPECTED and not binance_tradfi_available(data):
        gaps.append("Binance TradFi Perp")
    proxies = data.get("proxies", {})
    required_map = {
        "CL": ["^OVX", "DX-Y.NYB"],
        "BZ": ["^OVX", "DX-Y.NYB"],
        "GC": ["^TNX", "DX-Y.NYB"],
        "SI": ["^TNX", "DX-Y.NYB"],
        "HG": ["DX-Y.NYB"],
        "NG": ["^VIX"],
        "PL": ["^TNX", "DX-Y.NYB"],
        "PA": ["^TNX", "DX-Y.NYB"],
        "ES": ["^VIX", "^TNX"],
        "NQ": ["^VIX", "^TNX"],
        "YM": ["^VIX", "^TNX"],
        "RTY": ["^VIX", "^TNX"],
    }
    required = required_map.get(symbol, [])
    if required and any(not proxies.get(name) for name in required):
        gaps.append("主导力量")
    if len([k for k, v in proxies.items() if v]) < 2:
        gaps.append("交叉验证")
    return gaps


def price_bias(daily: List[Dict[str, Any]], hourly4: List[Dict[str, Any]]) -> str:
    if len(daily) < 20 or len(hourly4) < 8:
        return "观望"
    daily_up = daily[-1]["close"] > daily[-20]["close"]
    hl = hourly4[-1]["low"] > hourly4[-3]["low"]
    lh = hourly4[-1]["high"] < hourly4[-3]["high"]
    if daily_up and hl:
        return "做多"
    if (not daily_up) and lh:
        return "做空"
    return "观望"


def _proxy_change(data: Dict[str, Any], name: str) -> float | None:
    value = data.get("proxies", {}).get(name, {}).get("change_pct")
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _proxy_price(data: Dict[str, Any], name: str) -> float | None:
    value = data.get("proxies", {}).get(name, {}).get("price")
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _futures_dimension(reason: str) -> str:
    if reason.startswith("技术结构") or "主导手法" in reason:
        return "技术结构"
    if reason.startswith(("DXY", "美债收益率", "10Y")):
        return "宏观/利率美元"
    if reason.startswith(("OVX", "VIX")):
        return "波动率/情绪"
    if reason.startswith("可执行永续"):
        return "可执行合约层"
    if reason.startswith(("供需/库存", "地缘/OPEC", "天气/库存", "中国需求/库存")):
        return "供需/库存/事件"
    if reason.startswith("CFTC"):
        return "CFTC/仓位"
    return "其他"


def _headline_signal(symbol: str, title: str) -> str | None:
    text = title.lower()
    energy_bullish = [
        "inventory draw",
        "inventories draw",
        "stockpile draw",
        "stockpiles draw",
        "drawdown",
        "supply disruption",
        "supply risk",
        "supply fears",
        "sanctions",
        "opec cut",
        "output cut",
        "geopolitical tension",
        "middle east tension",
    ]
    energy_bearish = [
        "inventory build",
        "inventories build",
        "stockpile build",
        "stockpiles build",
        "surplus",
        "oversupply",
        "output hike",
        "output increase",
        "demand weak",
        "demand worries",
        "ceasefire",
    ]
    gas_bullish = [
        "storage draw",
        "inventory draw",
        "cold weather",
        "heat wave",
        "lng exports rise",
        "supply disruption",
    ]
    gas_bearish = [
        "storage build",
        "inventory build",
        "mild weather",
        "production rises",
        "production hits record",
        "oversupply",
    ]
    copper_bullish = [
        "china stimulus",
        "china demand",
        "mine disruption",
        "supply disruption",
        "inventory draw",
        "stockpile draw",
    ]
    copper_bearish = [
        "china demand weak",
        "demand concerns",
        "inventory build",
        "stockpile build",
        "surplus",
        "tariff",
    ]
    precious_bullish = [
        "safe-haven demand",
        "geopolitical tension",
        "rate cut bets",
        "dollar weakens",
    ]
    precious_bearish = [
        "dollar strengthens",
        "yields rise",
        "rate hike bets",
        "safe-haven demand fades",
    ]

    if symbol in {"CL", "BZ"}:
        bullish, bearish = energy_bullish, energy_bearish
    elif symbol == "NG":
        bullish, bearish = gas_bullish, gas_bearish
    elif symbol == "HG":
        bullish, bearish = copper_bullish, copper_bearish
    elif symbol in {"GC", "SI", "PL", "PA"}:
        bullish, bearish = precious_bullish, precious_bearish
    else:
        return None

    has_bullish = any(token in text for token in bullish)
    has_bearish = any(token in text for token in bearish)
    if has_bullish and not has_bearish:
        return "做多"
    if has_bearish and not has_bullish:
        return "做空"
    if has_bullish and has_bearish:
        return "neutral"
    return None

# ─── REMOVED: _dimensionize_votes ───
# ─── REMOVED: directional_evidence ───

def evidence_summary_text(data: Dict[str, Any]) -> str:
    """输出原始数据摘要，不做证据分类。"""
    return f"原始数据已采集，包含 {len(data)} 个字段；详情见 JSON 输出"

def counter_evidence_text(data: Dict[str, Any]) -> str:
    """列出数据可用性，不做反向判断。"""
    missing = [k for k, v in data.items() if v is None or v == []]
    if missing:
        return f"数据可用性：完整；缺失项：{', '.join(missing)}"
    return "数据可用性：完整"

def driver_summary(data: Dict[str, Any]) -> str:
    symbol = data["symbol"]
    proxies = data.get("proxies", {})
    parts = []
    if symbol == "CL":
        ovx = proxies.get("^OVX", {})
        dxy = proxies.get("DX-Y.NYB", {})
        if ovx:
            parts.append(f"OVX {ovx.get('price', 0):.2f}")
        if dxy:
            parts.append(f"DXY {dxy.get('change_pct', 0):+.2f}%")
        if binance_tradfi_available(data):
            parts.append(f"{binance_tradfi_block(data).get('symbol')} 可执行永续层")
        parts.append("关注地缘/OPEC+/库存")
    elif symbol == "BZ":
        ovx = proxies.get("^OVX", {})
        dxy = proxies.get("DX-Y.NYB", {})
        if ovx:
            parts.append(f"OVX {ovx.get('price', 0):.2f}")
        if dxy:
            parts.append(f"DXY {dxy.get('change_pct', 0):+.2f}%")
        if binance_tradfi_available(data):
            parts.append(f"{binance_tradfi_block(data).get('symbol')} 可执行永续层")
        parts.append("关注地缘/OPEC+/Brent-WTI价差")
    elif symbol in {"GC", "SI"}:
        tnx = proxies.get("^TNX", {})
        dxy = proxies.get("DX-Y.NYB", {})
        if tnx:
            parts.append(f"10Y {tnx.get('change_pct', 0):+.2f}%")
        if dxy:
            parts.append(f"DXY {dxy.get('change_pct', 0):+.2f}%")
        if binance_tradfi_available(data):
            parts.append(f"{binance_tradfi_block(data).get('symbol')} 可执行永续层")
        parts.append("关注利率与避险")
    elif symbol in {"HG", "NG", "PL", "PA"}:
        dxy = proxies.get("DX-Y.NYB", {})
        tnx = proxies.get("^TNX", {})
        vix = proxies.get("^VIX", {})
        if dxy:
            parts.append(f"DXY {dxy.get('change_pct', 0):+.2f}%")
        if tnx:
            parts.append(f"10Y {tnx.get('change_pct', 0):+.2f}%")
        if vix:
            parts.append(f"VIX {vix.get('price', 0):.2f}")
        if binance_tradfi_available(data):
            parts.append(f"{binance_tradfi_block(data).get('symbol')} 可执行永续层")
        parts.append("关注供需、美元与风险偏好")
    else:
        vix = proxies.get("^VIX", {})
        tnx = proxies.get("^TNX", {})
        if vix:
            parts.append(f"VIX {vix.get('price', 0):.2f}")
        if tnx:
            parts.append(f"10Y {tnx.get('change_pct', 0):+.2f}%")
        parts.append("关注宏观数据与风险偏好")
    return "；".join(parts)


def cftc_summary(data: Dict[str, Any]) -> str:
    """CFTC 持仓摘要 — 支持 CSV 结构化数据 + HTML fallback"""
    cftc = data.get("structured_drivers", {}).get("cftc", {})
    if not cftc or not cftc.get("found"):
        return "CFTC 持仓摘要暂缺"
    method = cftc.get("method", "unknown")
    
    # 非商业持仓（投机）— CSV 新字段
    nc_long = cftc.get("non_commercial_long")
    nc_short = cftc.get("non_commercial_short")
    nc_net = cftc.get("non_commercial_net")
    
    # 商业持仓（套保）
    c_long = cftc.get("commercial_long")
    c_short = cftc.get("commercial_short")
    c_net = cftc.get("commercial_net")
    
    # 仓位信号
    signal = cftc.get("position_signal", "")
    
    parts = []
    if nc_long and nc_short:
        nc_net_val = nc_net if nc_net else nc_long - nc_short
        parts.append(f"投机: 多 {nc_long:,} / 空 {nc_short:,} (净 {nc_net_val:+,})")
    if c_long and c_short:
        c_net_val = c_net if c_net else c_long - c_short
        parts.append(f"套保: 多 {c_long:,} / 空 {c_short:,} (净 {c_net_val:+,})")
    if signal:
        parts.append(signal)
    
    oi = cftc.get("open_interest")
    if oi:
        parts.append(f"总持仓: {oi:,}")
    report_date = cftc.get("report_date", "")
    if report_date:
        parts.append(f"报告日: {report_date}")
    
    if not parts:
        if method == "html_fallback":
            return "CFTC 周报原始摘录可用，但数值未结构化归类"
        return "CFTC 摘要可用但未归类"
    
    return "CFTC(\"{}\") — {}".format(
        cftc.get("market", "?"),
        " | ".join(parts)
    )


def structure_levels(rows: List[Dict[str, Any]]) -> Dict[str, float]:
    recent = rows[-8:] if len(rows) >= 8 else rows
    lows = [r["low"] for r in recent]
    highs = [r["high"] for r in recent]
    return {"support": min(lows), "resistance": max(highs)}


def build_report(data: Dict[str, Any]) -> str:
    row_basis = analysis_rows(data)
    daily = row_basis["daily"]
    h4 = row_basis["h4"]
    h1 = row_basis["h1"]
    if not daily and not h4 and not h1:
        gaps = key_block_gaps(data)
        completeness_parts = ["关键缺口：" + "、".join(gaps or ["技术结构"])]
        if data.get("errors"):
            completeness_parts.append("抓取缺口：" + "、".join(sorted(data["errors"].keys())))
        lines = [
            f"## 🎯 {data['symbol']} 期货交易决策",
            "",
            f"**分析时间（UTC）**：{data['analysis_time_utc']}",
            "### 方向：⚪ 观望",
            "",
            "**一句话理由**：K线主源与传统近月代理均不可用，无法锚定结构位",
            f"**数据完整性**：{';'.join(completeness_parts)}",
            f"**K线主源**：{row_basis['source']}",
            f"**主导驱动**：{driver_summary(data)}",
            "",
            "### 主导力量立场",
            f"- Binance TradFi 永续：{binance_tradfi_summary(data)}",
            f"- CFTC 摘要：{cftc_summary(data)}",
            f"- 交叉验证：可用代理 {', '.join(sorted(k for k, v in data.get('proxies', {}).items() if v)) or '无'}",
            "",
            "### 💰 止盈止损计划",
            "- 当前不追价，等待 K 线主源恢复后再评估",
            "- `SL/TP` 暂不建议强行给出执行位",
            "",
            "### 免责声明",
            "以上分析基于公开数据，不构成投资建议。",
        ]
        return "\n".join(lines)
    votes = directional_evidence(data, daily, h4)
    direction = None
    pattern = classify_pattern(h4)
    today = classify_today(h1[-24:] if len(h1) >= 24 else h1)
    actions = recent_key_actions(h4)
    structure = structure_basis(h4)
    levels = structure_levels(h4)
    support = levels["support"]
    resistance = levels["resistance"]
    last = h1[-1]["close"] if h1 else daily[-1]["close"]
    gaps = key_block_gaps(data)
    if direction == "做多":
        sl = support * 0.997
        tp1 = resistance
        tp2 = resistance * 1.015
        tp3 = resistance * 1.03
        reason = "4H 结构给出 higher low 倾向，且短线未破关键低点"
    elif direction == "做空":
        sl = resistance * 1.003
        tp1 = support
        tp2 = support * 0.985
        tp3 = support * 0.97
        reason = "4H 结构给出 lower high 倾向，且反弹未能抬高关键高点"
    else:
        sl = tp1 = tp2 = tp3 = None
        reason = "结构与驱动未形成足够一致性" if not gaps and structure["stance"] != "结构模糊" else "关键结构或关键数据不够清晰，按规则降级为观望"
    news = data.get("news", [])[:4]
    completeness_parts = []
    if gaps:
        completeness_parts.append("关键缺口：" + "、".join(gaps))
    if data.get("errors"):
        completeness_parts.append("抓取缺口：" + "、".join(sorted(data["errors"].keys())))
    completeness = "完整" if not completeness_parts else "；".join(completeness_parts)
    lines = [
        f"## 🎯 {data['symbol']} 期货交易决策",
        "",
        f"**分析时间（UTC）**：{data['analysis_time_utc']}",
        f"### 方向：由 AI 综合判断",
        "",
        f"**一句话理由**：{reason}",
        f"**数据完整性**：{completeness}",
        "**宏观时效性**：24h 期货/代理市场按抓取时点视作近实时，重大事件窗口需额外降权技术面",
        f"**K线主源**：{row_basis['source']}",
        f"**主导驱动**：{driver_summary(data)}",
        f"**各维度证据**：{evidence_summary_text(votes)}",
        f"**反向审计**：{counter_evidence_text(votes)}",
        "",
        "### 历史轨迹复盘",
        f"- 最近 `30D 4H` 主导手法：{pattern}",
        f"- 最近关键动作：{actions[0]}",
        f"- 最近关键动作：{actions[1] if len(actions) > 1 else '无'}",
        f"- 最近关键动作：{actions[2] if len(actions) > 2 else '无'}",
        f"- 今天更像：{today}",
        "",
        "### 结构依据",
        f"- 最近结构摆点：{structure['detail']}",
        f"- 当前形态：{shape_text(pattern)}",
        f"- 量价状态：{volume_state(h4)}",
        "",
        "### 主导力量立场",
        f"- 主导力量代理：{driver_summary(data)}",
        f"- Binance TradFi 永续：{binance_tradfi_summary(data)}",
        f"- CFTC 摘要：{cftc_summary(data)}",
        f"- 情绪代理：{'OVX/VIX 未见异常缺口' if any(k in data.get('proxies', {}) for k in ['^OVX', '^VIX']) else '波动率代理不足'}",
        f"- 交叉验证：可用代理 {', '.join(sorted(k for k, v in data.get('proxies', {}).items() if v)) or '无'}",
        "",
        "### 各维度证据",
        f"- 技术面：当前价 {last:.2f}，4H 结构与最近摆点决定方向",
        f"- 市场结构：{market_structure_text(data, row_basis)}",
        f"- 主导力量：{driver_summary(data)}；{cftc_summary(data)}",
        "- 情绪面：通过波动率代理和 headline 风险判断",
        f"- 宏观面：重大事件前技术权重下降；{'EIA 周报来源可用' if data.get('structured_drivers', {}).get('eia', {}).get('available') else 'EIA 结构化块暂缺'}",
        "- 交叉验证：通过 DXY / VIX / TNX / ETF 代理做确认",
        "",
        "### 💰 止盈止损计划",
    ]
    if direction is None:
        lines.extend([
            "- 当前不追价，等待更清晰的结构回踩或反抽",
            "- `SL/TP` 暂不建议强行给出执行位",
        ])
    else:
        lines.extend([
            "| 项目 | 价位 | 结构依据 |",
            "|------|------|---------|",
            f"| **入场** | {last:.2f} | 当前区间 + 最近结构位附近 |",
            f"| **🔴 SL** | {sl:.2f} | 锚定最近关键结构位：{'higher low 下方' if direction == '做多' else 'lower high 上方'} |",
            "",
            "| 级别 | 平仓% | 触发价 | 结构依据 |",
            "|------|-------|--------|---------|",
            f"| 🟡 TP1 | 30% | {tp1:.2f} | 最近结构 {'阻力' if direction == '做多' else '支撑'} |",
            f"| 🟠 TP2 | 30% | {tp2:.2f} | 下一级结构位 |",
            f"| 🟢 TP3 | 40% | {tp3:.2f} | 扩展目标 |",
        ])
    lines.extend(["", "### 移动止损"])
    if direction is None:
        lines.append("- 观望阶段不设置移动止损")
    else:
        lines.extend([
            "- 到 TP1 → 移损至开仓价",
            "- 到 TP2 → 移损至 TP1",
            "- 创出新高/新低后，跟踪最近 2 根 4H 结构位",
        ])
    lines.extend(["", "### 仓位"])
    if direction is None:
        lines.append("- 当前以等待为主，不建议按强方向建仓")
    else:
        lines.append("- 风险金额 ÷ (|入场价 - SL| × 合约乘数) = 可开仓位；需代入具体合约乘数")
    lines.extend(["", "### 失效条件"])
    if direction == "做多":
        lines.extend([
            f"1. 4H 收盘跌破 {support:.2f} 一带并未快速收回",
            "2. 事件面出现与当前方向相反的重大升级",
        ])
    elif direction == "做空":
        lines.extend([
            f"1. 4H 收盘重新站上 {resistance:.2f} 一带",
            "2. 风险代理与 headline 同时转向支持反弹",
        ])
    else:
        lines.extend([
            "1. 等待 4H 结构重新给出更清晰的 higher low 或 lower high",
            "2. 等待重大事件窗口过去后再评估",
        ])
    lines.extend(["", "### 禁止事项"])
    lines.extend([
        "- ❌ 在重大事件前追单",
        "- ❌ 用固定百分比代替结构止损",
        "- ❌ 把近月代理价格当成精确合约执行价而不说明假设",
    ])
    if news:
        lines.extend(["", "### 新闻观察"])
        for item in news:
            lines.append(f"- {item['title']} | {item['source']}")
    lines.extend(["", "### 免责声明", "以上分析基于公开数据，不构成投资建议。"])
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    if args.input:
        data = load_json(args.input)
    else:
        if not args.symbol:
            raise SystemExit("symbol is required unless --input is provided")
        data = fetch_live(args.symbol)
    print(build_report(data))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
