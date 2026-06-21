#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys as _sys
from pathlib import Path
from typing import Any, Dict, List

# 共享 TA 函数（消除与 a_share / us_equity 的重复）
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

FETCHER = Path(__file__).resolve().parent / "forex_fetch.py"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate an FX market analysis report.")
    parser.add_argument("symbol", nargs="?", help="FX symbol such as EURUSD")
    parser.add_argument("--input", help="Path to fetched JSON")
    return parser.parse_args()


def load_json(path: str) -> Dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def fetch_live(symbol: str) -> Dict[str, Any]:
    proc = subprocess.run(["python3", str(FETCHER), symbol, "--compact"], text=True, capture_output=True)
    if proc.returncode != 0:
        raise SystemExit(proc.stderr.strip() or proc.stdout.strip())
    return json.loads(proc.stdout)


# ── 外汇专用参数（委托给 shared_ta）──
def classify_pattern(rows: List[Dict[str, Any]]) -> str:
    return _classify_pattern(rows, box_chg_pct=2, box_width_pct=4, trend_chg_pct=1.5, trend_recent_pct=0.2, recovery_pct=0.5)

def classify_today(rows: List[Dict[str, Any]]) -> str:
    return _classify_today(rows, continuation_ratio=0.999, bounce_ratio=1.002, breakdown_ratio=0.999)

def recent_key_actions(rows: List[Dict[str, Any]]) -> List[str]:
    return _recent_key_actions(rows, body_threshold=0.2, range_threshold=0.35)

# find_swings / structure_basis / shape_text / structure_levels → 直接使用 shared_ta 版本（无参数差异）


def volume_state(rows: List[Dict[str, Any]]) -> str:
    if not rows:
        return "无样本"
    return "外汇无集中成交量，Yahoo 体量仅作弱代理，不单独作为执行依据"


def key_block_gaps(data: Dict[str, Any]) -> List[str]:
    gaps = []
    if len(data.get("daily_90d", [])) < 20 or len(data.get("agg_4h_10d", [])) < 12 or len(data.get("hourly_10d", [])) < 24:
        gaps.append("技术结构")
    proxies = data.get("proxies", {})
    rates = data.get("structured_drivers", {}).get("rates", {})
    dxy_ok = bool(proxies.get("DX-Y.NYB")) or bool(rates.get("dxy"))
    rates_ok = bool(rates.get("us_10y")) or bool(proxies.get("^TNX"))
    if not (dxy_ok and rates_ok):
        gaps.append("主导力量")
    if len([k for k, v in proxies.items() if v]) < 2 and not rates:
        gaps.append("交叉验证")
    return gaps


def direction(data: Dict[str, Any]) -> str:
    daily = data["daily_90d"]
    h4 = data["agg_4h_10d"]
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


def _event_delta_hours(event: Dict[str, Any]) -> float | None:
    raw = str(event.get("delta_hours", "")).removesuffix("h")
    try:
        return float(raw)
    except ValueError:
        return None


def _forex_dimension(reason: str) -> str:
    if reason.startswith("技术结构") or "主导手法" in reason:
        return "技术结构"
    if reason.startswith(("DXY", "10Y")) or "USD利差" in reason or "对手国债" in reason:
        return "美元/利差/利率"
    if reason.startswith("VIX"):
        return "风险情绪"
    if reason.startswith("CFTC"):
        return "CFTC/仓位"
    return "其他"


def _dimensionize_votes(votes: Dict[str, List[str]], classifier) -> Dict[str, List[str]]:
    buckets: Dict[str, Dict[str, List[str]]] = {}
    for side in ("做多", "做空"):
        for reason in votes.get(side, []):
            bucket = classifier(reason)
            buckets.setdefault(bucket, {"做多": [], "做空": []})[side].append(reason)

    collapsed: Dict[str, Any] = {
        "做多": [],
        "做空": [],
        "neutral": list(votes.get("neutral", [])),
        "veto": list(votes.get("veto", [])),
        "dimensions": {},
    }
    for name, sides in buckets.items():
        long_reasons = sides["做多"]
        short_reasons = sides["做空"]
        if long_reasons and not short_reasons:
            collapsed["做多"].append(f"{name}: {'；'.join(long_reasons)}")
            collapsed["dimensions"][name] = {"stance": "做多", "reasons": long_reasons}
        elif short_reasons and not long_reasons:
            collapsed["做空"].append(f"{name}: {'；'.join(short_reasons)}")
            collapsed["dimensions"][name] = {"stance": "做空", "reasons": short_reasons}
        else:
            reason = "多空内部冲突：多(" + "；".join(long_reasons) + ") / 空(" + "；".join(short_reasons) + ")"
            collapsed["neutral"].append(f"{name}: {reason}")
            collapsed["dimensions"][name] = {"stance": "中性", "reasons": long_reasons + short_reasons}
    return collapsed


def directional_evidence(data: Dict[str, Any]) -> Dict[str, List[str]]:
    """Build conservative evidence for the requested FX pair itself."""

    votes: Dict[str, List[str]] = {"做多": [], "做空": [], "veto": [], "neutral": []}
    technical = direction(data)
    if technical in {"做多", "做空"}:
        votes[technical].append(f"技术结构={technical}")

    pattern = classify_pattern(data.get("agg_4h_10d", []))
    if pattern == "趋势推进":
        votes["做多"].append("4H主导手法=趋势推进")
    elif pattern in {"冲高派发", "阴跌磨人"}:
        votes["做空"].append(f"4H主导手法={pattern}")
    elif pattern in {"箱体洗盘", "跌破回收"}:
        votes["neutral"].append(f"4H主导手法={pattern}")

    symbol = data["symbol"]
    dxy_chg = _proxy_change(data, "DX-Y.NYB")
    tnx_chg = _proxy_change(data, "^TNX")
    vix_chg = _proxy_change(data, "^VIX")
    rates = data.get("structured_drivers", {}).get("rates", {})
    diff_signal = str(rates.get("diff_signal", ""))

    usd_base = symbol.startswith("USD") or symbol == "DXY"
    usd_quote = symbol.endswith("USD") and not usd_base

    def usd_strength_vote(reason: str) -> None:
        if usd_base:
            votes["做多"].append(reason)
        elif usd_quote:
            votes["做空"].append(reason)
        else:
            votes["neutral"].append(reason)

    def usd_weakness_vote(reason: str) -> None:
        if usd_base:
            votes["做空"].append(reason)
        elif usd_quote:
            votes["做多"].append(reason)
        else:
            votes["neutral"].append(reason)

    if dxy_chg is not None:
        if dxy_chg > 0.20:
            usd_strength_vote(f"DXY走强 {dxy_chg:+.2f}%")
        elif dxy_chg < -0.20:
            usd_weakness_vote(f"DXY走弱 {dxy_chg:+.2f}%")

    if tnx_chg is not None:
        if tnx_chg > 0.30:
            usd_strength_vote(f"10Y上行 {tnx_chg:+.2f}%")
        elif tnx_chg < -0.30:
            usd_weakness_vote(f"10Y下行 {tnx_chg:+.2f}%")

    if "USD利差优势" in diff_signal:
        usd_strength_vote(diff_signal)
    elif "USD利差劣势" in diff_signal:
        usd_weakness_vote(diff_signal)

    if symbol in {"USDJPY", "USDCHF"} and vix_chg is not None:
        if vix_chg > 5:
            votes["做空"].append(f"VIX上升 {vix_chg:+.2f}% 支持避险货币")
        elif vix_chg < -5:
            votes["做多"].append(f"VIX下降 {vix_chg:+.2f}% 压低避险需求")

    if symbol in {"AUDUSD", "NZDUSD"} and vix_chg is not None:
        if vix_chg > 5:
            votes["做空"].append(f"VIX上升 {vix_chg:+.2f}% 压制风险货币")
        elif vix_chg < -5:
            votes["做多"].append(f"VIX下降 {vix_chg:+.2f}% 支撑风险货币")

    events = data.get("upcoming_macro_events") or []
    high_impact_near = []
    for event in events:
        delta = _event_delta_hours(event)
        if event.get("impact") == "High" and delta is not None and -1 <= delta <= 2:
            high_impact_near.append(event)
    if high_impact_near:
        votes["veto"].append("高影响宏观数据窗口过近，禁止硬给方向")

    cftc_signal = str(data.get("structured_drivers", {}).get("cftc", {}).get("position_signal", ""))
    if cftc_signal:
        cftc_market_is_base = usd_quote or symbol == "DXY"
        cftc_market_is_quote = usd_base and symbol != "DXY"
        if "🟢" in cftc_signal:
            if cftc_market_is_base:
                votes["做多"].append(f"CFTC {cftc_signal}")
            elif cftc_market_is_quote:
                votes["做空"].append(f"CFTC 对手货币 {cftc_signal}，压制{symbol}")
            else:
                votes["neutral"].append(f"CFTC {cftc_signal}")
        elif "🔴" in cftc_signal:
            if cftc_market_is_base:
                votes["做空"].append(f"CFTC {cftc_signal}")
            elif cftc_market_is_quote:
                votes["做多"].append(f"CFTC 对手货币 {cftc_signal}，支撑{symbol}")
            else:
                votes["neutral"].append(f"CFTC {cftc_signal}")

    return _dimensionize_votes(votes, _forex_dimension)


def evidence_summary_text(votes: Dict[str, List[str]]) -> str:
    """逐项列出各维度证据，不做方向决策。"""
    return (
        f"偏多维度 {len(votes['做多'])} 项：{'; '.join(votes['做多']) or '无'}；"
        f"偏空维度 {len(votes['做空'])} 项：{'; '.join(votes['做空']) or '无'}；"
        f"中性/缺失：{'; '.join(votes['neutral']) or '无'}；"
        f"硬性降级：{'; '.join(votes['veto']) or '无'}"
    )


def counter_evidence_text(votes: Dict[str, List[str]]) -> str:
    """列出最强反方向证据，不做方向决策。"""
    if votes['veto']:
        return '存在硬性降级项：' + '；'.join(votes['veto'])
    long_reasons = votes['做多']
    short_reasons = votes['做空']
    if long_reasons and short_reasons:
        return f"最强空头证据：{'; '.join(short_reasons)}；最强多头证据：{'; '.join(long_reasons)}"
    if long_reasons:
        return f"无同等级反证；多头证据：{'; '.join(long_reasons)}"
    if short_reasons:
        return f"无同等级反证；空头证据：{'; '.join(short_reasons)}"
    return '多空均无强证据'


def macro_summary(data: Dict[str, Any]) -> str:
    """宏观代理摘要：DXY + VIX + 利率曲线 + 利差信号"""
    proxies = data.get("proxies", {})
    rates = data.get("structured_drivers", {}).get("rates", {})
    parts = []
    dxy = rates.get("dxy") or proxies.get("DX-Y.NYB", {})
    vix = proxies.get("^VIX", {})
    if dxy:
        dxy_chg = dxy.get("change_pct", 0)
        dxy_trend = rates.get("dxy_trend", "")
        parts.append(f"DXY {dxy_chg:+.2f}%{(' '+dxy_trend) if dxy_trend else ''}")
    if vix:
        parts.append(f"VIX {vix.get('price', 0):.2f}")
    # 收益率曲线信号
    curve_signal = rates.get("curve_signal", "")
    if curve_signal:
        parts.append(f"曲线: {curve_signal}")
    # 利差信号
    diff_signal = rates.get("diff_signal", "")
    if diff_signal and diff_signal != "N/A":
        parts.append(f"利差: {diff_signal}")
    if data["symbol"] == "USDJPY":
        parts.append("关注美债收益率与日银/干预风险")
    elif data["symbol"] == "USDCNH":
        parts.append("关注中美利差与政策管理风险")
    else:
        parts.append("关注美元与央行路径")
    return "；".join(parts)


def rates_summary(data: Dict[str, Any]) -> str:
    """收益率曲线 + 对手国利差详细拆解"""
    rates = data.get("structured_drivers", {}).get("rates", {})
    if not rates:
        return "利率数据暂缺"
    lines = []
    us_10y = rates.get("us_10y", {})
    us_5y = rates.get("us_5y", {})
    if us_10y.get("price") and us_5y.get("price"):
        curve = rates.get("curve_5s10s", "N/A")
        lines.append(f"US 10Y: {us_10y['price']:.2f}% | 5Y: {us_5y['price']:.2f}% | 5s10s: {curve}%")
    curve_signal = rates.get("curve_signal", "")
    if curve_signal:
        lines.append(f"曲线信号: {curve_signal}")
    cp = rates.get("counterparty", {})
    if cp:
        cp_note = cp.get("note", "")
        cp_ticker = cp.get("ticker", "?")
        cp_val = cp.get("yield_proxy")
        if cp_val is not None:
            if cp.get("is_yield"):
                lines.append(f"对手利率({cp_ticker}): {cp_val:.2f}% — {cp_note}")
            else:
                lines.append(f"对手期货({cp_ticker}): {cp_val:.2f} ({cp.get('change_pct', 0):+.2f}%) — {cp_note}")
        else:
            lines.append(f"对手利率({cp_ticker}): 无数据 — {cp_note}")
    diff = rates.get("rate_differential")
    if diff is not None:
        lines.append(f"USD-对手利差: {diff:+.2f}%")
    diff_signal = rates.get("diff_signal", "")
    if diff_signal and diff_signal != "N/A":
        lines.append(f"利差信号: {diff_signal}")
    cbe = rates.get("central_bank_events", [])
    if cbe:
        lines.append("央行事件: " + " / ".join(
            f"{e.get('date','?')} {e.get('country','?')} {e.get('title','')}"
            for e in cbe[:3]
        ))
    return "\n".join(f"- {l}" for l in lines)


def macro_event_summary(data: Dict[str, Any]) -> str:
    events = data.get("upcoming_macro_events") or data.get("macro_events", [])
    if not events:
        return "本周高影响事件暂缺"
    parts = []
    for e in events[:3]:
        suffix = f" ({e['delta_hours']})" if e.get("delta_hours") else ""
        parts.append(f"{e['date']} {e['country']} {e['title']}{suffix}")
    return " / ".join(parts)


def cftc_summary(data: Dict[str, Any]) -> str:
    """CFTC 金融期货持仓 — 支持 CSV 结构化 + HTML fallback"""
    cftc = data.get("structured_drivers", {}).get("cftc", {})
    if not cftc or not cftc.get("found"):
        return "CFTC 金融期货持仓暂缺"
    ll = cftc.get("leveraged_long")
    ls = cftc.get("leveraged_short")
    al = cftc.get("asset_mgr_long")
    a_s = cftc.get("asset_mgr_short")
    signal = cftc.get("position_signal", "")
    method = cftc.get("method", "")
    report_date = cftc.get("report_date", "")
    
    if ll is None or ls is None:
        return "CFTC 已抓到但数值不完整"
    lev_bias = "杠杆基金净多" if ll > ls else "杠杆基金净空" if ll < ls else "杠杆基金中性"
    parts = [f"{lev_bias}（多 {ll:,} / 空 {ls:,}）"]
    if al is not None and a_s is not None:
        am_bias = "资管净多" if al > a_s else "资管净空" if al < a_s else "资管中性"
        parts.append(f"{am_bias}（多 {al:,} / 空 {a_s:,}）")
    if signal:
        parts.append(signal)
    if report_date:
        parts.append(f"报告日: {report_date}")
    
    prefix = f"CFTC{'[CSV]' if method == 'csv' else ''}"
    return f"{prefix} {' | '.join(parts)}"


def build_report(data: Dict[str, Any]) -> str:
    daily = data["daily_90d"]
    h4 = data["agg_4h_10d"]
    h1 = data["hourly_10d"]
    votes = directional_evidence(data)
    side = None
    pattern = classify_pattern(h4)
    today = classify_today(h1[-24:] if len(h1) >= 24 else h1)
    actions = recent_key_actions(h4)
    structure = structure_basis(h4)
    levels = structure_levels(h4)
    last = h1[-1]["close"] if h1 else daily[-1]["close"]
    support = levels["support"]
    resistance = levels["resistance"]
    gaps = key_block_gaps(data)
    sl = tp1 = tp2 = tp3 = None
    reason = "方向由 AI 综合各维度证据判断"
    completeness_parts = []
    if gaps:
        completeness_parts.append("关键缺口：" + "、".join(gaps))
    if data.get("errors"):
        completeness_parts.append("抓取缺口：" + "、".join(sorted(data["errors"].keys())))
    completeness = "完整" if not completeness_parts else "；".join(completeness_parts)
    lines = [
        f"## 🎯 {data['label']} 外汇交易决策",
        "",
        f"**分析时间（UTC）**：{data['analysis_time_utc']}",
        "### 方向：由 AI 综合判断",
        "",
        f"**一句话理由**：{reason}",
        f"**数据完整性**：{completeness}",
        "**宏观时效性**：外汇近 24 小时连续交易；央行/数据窗口前后 headline 权重高于图形",
        f"**主导宏观因子**：{macro_summary(data)}",
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
        f"- 利率/美元代理：{macro_summary(data)}",
        f"- 收益率曲线 & 利差拆解：",
        f"{rates_summary(data)}",
        f"- CFTC 摘要：{cftc_summary(data)}",
        f"- 本周高影响事件：{macro_event_summary(data)}",
        f"- 主导叙事：{'日银/干预风险' if data['symbol'] == 'USDJPY' else '人民币管理风险' if data['symbol'] == 'USDCNH' else '美元与央行路径'}",
        f"- 交叉验证：可用代理 {', '.join(sorted(k for k, v in data.get('proxies', {}).items() if v)) or '无'}",
        "",
        "### 各维度证据",
        f"- 技术面：当前价 {last:.5f}，4H 结构为主",
        "- 市场结构：看 5s10s 利差、对手国利差、美元方向与风险偏好",
        f"- 主导力量：{macro_summary(data)}；{cftc_summary(data)}；{macro_event_summary(data)}",
        "- 情绪面：通过 VIX 与 risk-on/risk-off 辅助判断",
        "- 宏观面：央行路径和数据窗口优先级高",
        "- 交叉验证：通过 DXY、收益率、相关货币和风险资产确认",
        "",
        "### 💰 止盈止损计划",
    ]
    if side is None:
        lines.extend([
            "- 当前不追，等待更清晰的 higher low / lower high",
            "- `SL/TP` 暂不建议强行给出执行位",
        ])
    else:
        lines.extend([
            "| 项目 | 价位 | 结构依据 |",
            "|------|------|---------|",
            f"| **入场** | {last:.5f} | 当前区间 + 最近结构位附近 |",
            f"| **🔴 SL** | {sl:.5f} | 锚定最近关键结构位：{'higher low 下方' if side == '做多' else 'lower high 上方'} |",
            "",
            "| 级别 | 平仓% | 触发价 | 结构依据 |",
            "|------|-------|--------|---------|",
            f"| 🟡 TP1 | 30% | {tp1:.5f} | 最近结构 {'阻力' if side == '做多' else '支撑'} |",
            f"| 🟠 TP2 | 30% | {tp2:.5f} | 下一级结构位 |",
            f"| 🟢 TP3 | 40% | {tp3:.5f} | 扩展目标 |",
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
        lines.append("- 风险金额 ÷ |入场价 - SL| = 可开仓位；如用手数交易，需再换算合约单位")
    lines.extend(["", "### 失效条件"])
    lines.extend([
        "1. 等待重大数据窗口过去",
        "2. 等待结构与美元/收益率方向重新一致",
    ])
    lines.extend(["", "### 禁止事项"])
    lines.extend([
        "- ❌ 把货币强弱观点和交易对方向混为一谈",
        "- ❌ 在重大数据公布前追单",
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
