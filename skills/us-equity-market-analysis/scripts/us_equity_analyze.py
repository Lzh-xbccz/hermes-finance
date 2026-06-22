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
    structure_basis,
    recent_key_actions as _recent_key_actions,
    structure_levels,
    shape_text,
)

FETCHER = Path(__file__).resolve().parent / "us_equity_fetch.py"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate a US equity market analysis report.")
    parser.add_argument("symbol", nargs="?", help="Ticker such as AAPL, SPY, ^GSPC")
    parser.add_argument("--input", help="Path to fetched JSON")
    return parser.parse_args()


def load_json(path: str) -> Dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def fetch_live(symbol: str) -> Dict[str, Any]:
    proc = subprocess.run(["python3", str(FETCHER), symbol, "--compact"], text=True, capture_output=True)
    if proc.returncode != 0:
        raise SystemExit(proc.stderr.strip() or proc.stdout.strip())
    return json.loads(proc.stdout)


# ── 美股专用参数（委托给 shared_ta）──
def classify_pattern(rows: List[Dict[str, Any]]) -> str:
    return _classify_pattern(rows, box_chg_pct=5, box_width_pct=12, trend_chg_pct=6, trend_recent_pct=1, recovery_pct=2)

def classify_today(rows: List[Dict[str, Any]]) -> str:
    return _classify_today(rows, continuation_ratio=0.998, bounce_ratio=1.01, breakdown_ratio=0.995)

def recent_key_actions(rows: List[Dict[str, Any]]) -> List[str]:
    return _recent_key_actions(rows, body_threshold=1.2, range_threshold=2.5)

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


def key_block_gaps(data: Dict[str, Any]) -> List[str]:
    gaps = []
    if len(data.get("daily_90d", [])) < 20 or len(data.get("agg_4h_10d", [])) < 12:
        gaps.append("技术结构")
    proxies = data.get("proxies", {})
    if not proxies.get("^VIX") or not proxies.get("^TNX"):
        gaps.append("主导力量")
    if data.get("instrument_type") == "stock" and not data.get("company_event_proxy", {}).get("events"):
        gaps.append("公司事件")
    if len([k for k, v in proxies.items() if v]) < 2:
        gaps.append("交叉验证")
    return gaps


def direction(data: Dict[str, Any]) -> str:
    daily = data["daily_90d"]
    h4 = data["agg_4h_10d"]
    if data["instrument_type"] == "index":
        if len(daily) < 20:
            return "震荡"
        return "偏多" if daily[-1]["close"] > daily[-20]["close"] else "偏空"
    if len(daily) < 20 or len(h4) < 8:
        return "观望"
    up = daily[-1]["close"] > daily[-20]["close"] and h4[-1]["low"] > h4[-3]["low"]
    down = daily[-1]["close"] < daily[-20]["close"] and h4[-1]["high"] < h4[-3]["high"]
    if up:
        return "做多"
    if down:
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


def _us_equity_dimension(reason: str) -> str:
    if reason.startswith("技术结构") or "主导手法" in reason:
        return "技术结构"
    if reason.startswith(("SPY", "QQQ")):
        return "市场/ETF"
    if reason.startswith(("VIX", "10Y")):
        return "宏观利率/情绪"
    if reason.startswith(("公司事件", "公司业务事件", "监管/诉讼")):
        return "公司事件"
    return "其他"

# ─── REMOVED: _dimensionize_votes ───
# ─── REMOVED: directional_evidence ───

def _neutral_direction(data: Dict[str, Any]) -> str:
    return "震荡" if data.get("instrument_type") == "index" else "观望"


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
    proxies = data.get("proxies", {})
    parts = []
    vix = proxies.get("^VIX", {})
    tnx = proxies.get("^TNX", {})
    spy = proxies.get("SPY", {})
    qqq = proxies.get("QQQ", {})
    if vix:
        parts.append(f"VIX {vix.get('price', 0):.2f}")
    if tnx:
        parts.append(f"10Y {tnx.get('change_pct', 0):+.2f}%")
    if spy:
        parts.append(f"SPY {spy.get('change_pct', 0):+.2f}%")
    if qqq:
        parts.append(f"QQQ {qqq.get('change_pct', 0):+.2f}%")
    return "；".join(parts)


def company_event_summary(data: Dict[str, Any]) -> str:
    if data.get("instrument_type") != "stock":
        return "ETF/指数以上游驱动为主"
    events = data.get("company_event_proxy", {}).get("events", [])
    nasdaq_state = data.get("company_event_proxy", {}).get("nasdaq_earnings_page", {})
    suffix = "；Nasdaq earnings页可用" if nasdaq_state.get("available") else "；Nasdaq earnings页暂缺"
    if not events:
        return "近期公司硬事件代理暂缺" + suffix
    return " / ".join(f"{e['type']}: {e['title']}" for e in events[:3]) + suffix


def build_report(data: Dict[str, Any]) -> str:
    daily = data["daily_90d"]
    h4 = data["agg_4h_10d"]
    h1 = data["hourly_10d"]
    votes = directional_evidence(data)
    side = None
    pattern = classify_pattern(h4) if h4 else "数据不足"
    today = classify_today(h1[-24:] if len(h1) >= 24 else h1) if h1 else "数据不足"
    actions = recent_key_actions(h4 or daily)
    structure = structure_basis(h4 or daily)
    levels = structure_levels(h4 or daily)
    support = levels["support"]
    resistance = levels["resistance"]
    last = (h1[-1]["close"] if h1 else daily[-1]["close"]) if daily else 0.0
    gaps = key_block_gaps(data)
    completeness_parts = []
    if gaps:
        completeness_parts.append("关键缺口：" + "、".join(gaps))
    if data.get("errors"):
        completeness_parts.append("抓取缺口：" + "、".join(sorted(data["errors"].keys())))
    completeness = "完整" if not completeness_parts else "；".join(completeness_parts)
    lines = [f"**分析时间（UTC）**：{data['analysis_time_utc']}"]
    if data["instrument_type"] == "index":
        lines.insert(0, f"## 📈 {data['symbol']} 指数偏向")
        lines.extend([
            f"**结论**：由 AI 综合判断",
            f"**数据完整性**：{completeness}",
            "**宏观时效性**：若处于美股常规时段外，现金指数与 ETF 联动仅作背景过滤",
            f"**主导因子**：{driver_summary(data)}",
            f"**各维度证据**：{evidence_summary_text(votes)}",
            f"**反向审计**：{counter_evidence_text(votes)}",
            "",
            "### 历史轨迹复盘",
            f"- 最近主导手法：{pattern}",
            f"- 最近关键动作：{actions[0]}",
            f"- 最近关键动作：{actions[1] if len(actions) > 1 else '无'}",
            f"- 最近关键动作：{actions[2] if len(actions) > 2 else '无'}",
            f"- 今天更像：{today}",
            "",
            "### 结构依据",
            f"- 最近结构摆点：{structure['detail']}",
            f"- 当前形态：{shape_text(pattern)}",
            f"- 量价状态：{volume_state(h4 or daily)}",
            "",
            "### 主导力量立场",
            f"- 宏观/指数代理：{driver_summary(data)}",
            "- 主导叙事：现金指数默认以风险偏好和利率环境解读",
            f"- 交叉验证：可用代理 {', '.join(sorted(k for k, v in data.get('proxies', {}).items() if v)) or '无'}",
            "",
            "### 各维度证据",
            f"- 技术面：当前价 {last:.2f}",
            "- 市场结构：用指数与 ETF 交叉看风险偏好",
            "- 主导力量：以利率、权重股和大盘广度为主",
            "- 情绪面：通过 VIX 与大盘涨跌判断",
            "- 宏观面：Fed/收益率/数据窗口优先",
            "- 交叉验证：SPY/QQQ/IWM 代理",
            "",
            "### 执行提示",
            "- 现金指数默认不给直接执行位；若要执行，请切到对应 ETF 或期货语境",
        ])
    else:
        lines.insert(0, f"## 🎯 {data['symbol']} 美股交易决策")
        emoji = "由 AI 综合判断"
        sl = tp1 = tp2 = tp3 = None
        reason = "由 AI 综合判断"
        lines.extend([
            f"### 方向：{emoji}",
            "",
            f"**一句话理由**：{reason}",
            f"**数据完整性**：{completeness}",
            "**宏观时效性**：若处于盘前/盘后，个股与ETF价格波动仅作弱确认，常规时段信号优先",
            f"**市场背景**：{driver_summary(data)}",
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
            f"- 量价状态：{volume_state(h4 or daily)}",
            "",
            "### 主导力量立场",
            f"- 宏观/市场代理：{driver_summary(data)}",
            f"- 公司事件代理：{company_event_summary(data)}",
            "- 主导叙事：公司事件、行业主线和利率敏感性",
            f"- 交叉验证：可用代理 {', '.join(sorted(k for k, v in data.get('proxies', {}).items() if v)) or '无'}",
            "",
            "### 各维度证据",
            f"- 技术面：当前价 {last:.2f}",
            "- 市场结构：看 ETF、行业轮动和盘前盘后风险",
            f"- 主导力量：公司事件、行业主线和利率敏感性；{company_event_summary(data)}",
            "- 情绪面：通过 VIX 和大盘风险偏好判断",
            "- 宏观面：Fed、收益率、美元和数据窗口",
            "- 交叉验证：SPY/QQQ/IWM 与同类资产",
            "",
            "### 💰 止盈止损计划",
        ])
        if side is None:
            lines.extend([
                "- 当前不追，等待更清晰的结构回踩/反抽",
                "- `SL/TP` 暂不建议强行给出执行位",
            ])
        else:
            lines.extend([
                "| 项目 | 价位 | 结构依据 |",
                "|------|------|---------|",
                f"| **入场** | {last:.2f} | 当前区间 + 最近结构位附近 |",
                f"| **🔴 SL** | {sl:.2f} | 锚定最近关键结构位：{'higher low 下方' if side == '做多' else 'lower high 上方'} |",
                "",
                "| 级别 | 平仓% | 触发价 | 结构依据 |",
                "|------|-------|--------|---------|",
                f"| 🟡 TP1 | 30% | {tp1:.2f} | 最近结构 {'阻力' if side == '做多' else '支撑'} |",
                f"| 🟠 TP2 | 30% | {tp2:.2f} | 下一级结构位 |",
                f"| 🟢 TP3 | 40% | {tp3:.2f} | 扩展目标 |",
            ])
        lines.extend(["", "### 移动止损"])
        if side is None:
            lines.append("- 观望阶段不设置移动止损")
        else:
            lines.extend([
                "- 到 TP1 → 移损至开仓价",
                "- 到 TP2 → 移损至 TP1",
                "- 创出新高/新低后，跟踪最近 2 根 4H 结构位",
            ])
        lines.extend(["", "### 仓位"])
        if side is None:
            lines.append("- 当前以等待为主，不建议按强方向建仓")
        else:
            lines.append("- 风险金额 ÷ |入场价 - SL| = 可开股数")
        lines.extend(["", "### 失效条件"])
        if side is None:
            lines.extend([
                "1. 等待更清晰的结构位",
                "2. 等待事件窗口过去再评估",
            ])
        elif side == "做多":
            lines.extend([
                f"1. 4H 收盘跌破 {support:.2f} 并未快速收回",
                "2. 利率与风险偏好同步转坏，破坏当前逻辑",
            ])
        else:
            lines.extend([
                f"1. 4H 收盘重新站上 {resistance:.2f}",
                "2. 大盘与行业主线同步修复，破坏空头逻辑",
            ])
        lines.extend(["", "### 禁止事项"])
        lines.extend([
            "- ❌ 忽略财报/公司 headline 风险",
            "- ❌ 把 ETF 当成没有上游驱动的普通个股",
            "- ❌ 用固定百分比代替结构止损",
        ])
    if data.get("news"):
        lines.extend(["", "### 新闻观察"])
        for item in data["news"][:4]:
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
