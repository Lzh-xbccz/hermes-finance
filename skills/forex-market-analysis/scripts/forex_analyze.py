#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any, Dict, List


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


def classify_pattern(rows: List[Dict[str, Any]]) -> str:
    if len(rows) < 12:
        return "数据不足"
    closes = [r["close"] for r in rows]
    highs = [r["high"] for r in rows]
    lows = [r["low"] for r in rows]
    chg = (closes[-1] / closes[0] - 1) * 100 if closes[0] else 0
    width = (max(highs) - min(lows)) / min(lows) * 100 if min(lows) else 0
    recent = (closes[-1] / closes[-6] - 1) * 100 if closes[-6] else 0
    if abs(chg) < 2 and width < 4:
        return "箱体洗盘"
    if chg > 1.5 and recent > 0.2:
        return "趋势推进"
    if chg > 1.5 and recent < 0:
        return "冲高派发"
    if closes[-1] > min(lows[-6:]) * 1.005 and min(lows[-3:]) <= min(lows[-6:]) * 1.001:
        return "跌破回收"
    return "阴跌磨人"


def classify_today(rows: List[Dict[str, Any]]) -> str:
    if len(rows) < 8:
        return "数据不足"
    closes = [r["close"] for r in rows]
    highs = [r["high"] for r in rows]
    lows = [r["low"] for r in rows]
    latest = closes[-1]
    prev = closes[-2]
    if latest >= max(highs[-6:]) * 0.999:
        return "延续"
    if latest > prev and latest > min(lows[-6:]) * 1.002:
        return "回踩"
    if latest < prev and latest > min(lows[-6:]) * 1.002:
        return "诱多"
    if latest < min(lows[-6:]) * 0.999:
        return "诱空"
    return "纯噪音"


def recent_key_actions(rows: List[Dict[str, Any]]) -> List[str]:
    if not rows:
        return ["数据不足"]
    events = []
    for row in rows[-12:]:
        o = row["open"]
        c = row["close"]
        h = row["high"]
        l = row["low"]
        body = ((c - o) / o * 100) if o else 0.0
        rng = ((h - l) / o * 100) if o else 0.0
        if abs(body) >= 0.2 or rng >= 0.35:
            if body > 0.15:
                tag = "急拉"
            elif body < -0.15:
                tag = "急跌"
            elif rng >= 0.4 and c < h - (h - l) * 0.4:
                tag = "冲高回落"
            elif rng >= 0.4 and c > l + (h - l) * 0.6:
                tag = "跌破回收"
            else:
                tag = "大波动"
            events.append((abs(body) + rng, f"{row['time_utc']} {tag} body:{body:+.2f}% range:{rng:.2f}%"))
    events.sort(reverse=True)
    return [text for _, text in events[:3]] or ["最近 12 根 4H 未出现显著异常波动"]


def find_swings(rows: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    highs: List[Dict[str, Any]] = []
    lows: List[Dict[str, Any]] = []
    for i in range(2, len(rows) - 2):
        if rows[i]["high"] > rows[i - 1]["high"] and rows[i]["high"] > rows[i - 2]["high"] and rows[i]["high"] > rows[i + 1]["high"] and rows[i]["high"] > rows[i + 2]["high"]:
            highs.append(rows[i])
        if rows[i]["low"] < rows[i - 1]["low"] and rows[i]["low"] < rows[i - 2]["low"] and rows[i]["low"] < rows[i + 1]["low"] and rows[i]["low"] < rows[i + 2]["low"]:
            lows.append(rows[i])
    return {"highs": highs, "lows": lows}


def structure_basis(rows: List[Dict[str, Any]]) -> Dict[str, str]:
    swings = find_swings(rows)
    highs = swings["highs"]
    lows = swings["lows"]
    if len(lows) >= 2 and lows[-1]["low"] > lows[-2]["low"]:
        stance = "higher low"
        detail = f"最近结构摆点为 higher low：{lows[-2]['low']:.5f} -> {lows[-1]['low']:.5f}（{lows[-1]['time_utc']}）"
    elif len(highs) >= 2 and highs[-1]["high"] < highs[-2]["high"]:
        stance = "lower high"
        detail = f"最近结构摆点为 lower high：{highs[-2]['high']:.5f} -> {highs[-1]['high']:.5f}（{highs[-1]['time_utc']}）"
    else:
        stance = "结构模糊"
        detail = "最近 4H 摆点未形成清晰 higher low 或 lower high"
    return {"stance": stance, "detail": detail}


def shape_text(pattern: str) -> str:
    mapping = {
        "趋势推进": "趋势延续结构",
        "箱体洗盘": "区间震荡结构",
        "冲高派发": "高位回落结构",
        "跌破回收": "假跌破回收结构",
        "阴跌磨人": "弱反弹下行结构",
    }
    return mapping.get(pattern, "结构待确认")


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
    # 主导力量：需要 DXY + 利率数据（us_10y/us_5y 或 proxies 中的 ^TNX）
    dxy_ok = bool(proxies.get("DX-Y.NYB")) or bool(rates.get("dxy"))
    rates_ok = bool(rates.get("us_10y")) or bool(proxies.get("^TNX"))
    if not (dxy_ok and rates_ok):
        gaps.append("主导力量")
    if len([k for k, v in proxies.items() if v]) < 2 and not rates:
        gaps.append("交叉验证")
    return gaps


def structure_levels(rows: List[Dict[str, Any]]) -> Dict[str, float]:
    recent = rows[-8:] if len(rows) >= 8 else rows
    return {
        "support": min(r["low"] for r in recent),
        "resistance": max(r["high"] for r in recent),
    }


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
    cftc = data.get("structured_drivers", {}).get("cftc", {})
    if not cftc or not cftc.get("found"):
        return "CFTC 金融期货持仓暂缺"
    ll = cftc.get("leveraged_long")
    ls = cftc.get("leveraged_short")
    al = cftc.get("asset_mgr_long")
    a_s = cftc.get("asset_mgr_short")
    if ll is None or ls is None:
        return "CFTC 已抓到但数值不完整"
    lev_bias = "杠杆基金净多" if ll > ls else "杠杆基金净空" if ll < ls else "杠杆基金中性"
    if al is not None and a_s is not None:
        am_bias = "资管净多" if al > a_s else "资管净空" if al < a_s else "资管中性"
        return f"CFTC {lev_bias}（多 {ll:,} / 空 {ls:,}）；{am_bias}（多 {al:,} / 空 {a_s:,}）"
    return f"CFTC {lev_bias}（多 {ll:,} / 空 {ls:,}）"


def build_report(data: Dict[str, Any]) -> str:
    daily = data["daily_90d"]
    h4 = data["agg_4h_10d"]
    h1 = data["hourly_10d"]
    side = direction(data)
    pattern = classify_pattern(h4)
    today = classify_today(h1[-24:] if len(h1) >= 24 else h1)
    actions = recent_key_actions(h4)
    structure = structure_basis(h4)
    levels = structure_levels(h4)
    last = h1[-1]["close"] if h1 else daily[-1]["close"]
    support = levels["support"]
    resistance = levels["resistance"]
    gaps = key_block_gaps(data)
    if gaps or structure["stance"] == "结构模糊":
        side = "观望"
    if side == "做多":
        sl = support * 0.999
        tp1 = resistance
        tp2 = resistance * 1.003
        tp3 = resistance * 1.006
        reason = "结构偏多，且宏观代理未明显反向"
    elif side == "做空":
        sl = resistance * 1.001
        tp1 = support
        tp2 = support * 0.997
        tp3 = support * 0.994
        reason = "结构偏空，且美元/利率背景未明显打脸"
    else:
        sl = tp1 = tp2 = tp3 = None
        reason = "结构与宏观驱动不够一致" if not gaps and structure["stance"] != "结构模糊" else "关键结构或关键数据不够清晰，按规则降级为观望"
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
        f"### 方向：{'🟢 做多' if side == '做多' else '🔴 做空' if side == '做空' else '⚪ 观望'}",
        "",
        f"**一句话理由**：{reason}",
        f"**数据完整性**：{completeness}",
        "**宏观时效性**：外汇近 24 小时连续交易；央行/数据窗口前后 headline 权重高于图形",
        f"**主导宏观因子**：{macro_summary(data)}",
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
        "### 六维判断",
        f"- 技术面：当前价 {last:.5f}，4H 结构为主",
        "- 市场结构：看 5s10s 利差、对手国利差、美元方向与风险偏好",
        f"- 主导力量：{macro_summary(data)}；{cftc_summary(data)}；{macro_event_summary(data)}",
        "- 情绪面：通过 VIX 与 risk-on/risk-off 辅助判断",
        "- 宏观面：央行路径和数据窗口优先级高",
        "- 交叉验证：通过 DXY、收益率、相关货币和风险资产确认",
        "",
        "### 💰 止盈止损计划",
    ]
    if side == "观望":
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
    if side == "观望":
        lines.append("- 观望阶段不设置移动止损")
    else:
        lines.extend([
            "- 到 TP1 → 移损至开仓价",
            "- 到 TP2 → 移损至 TP1",
            "- 创出新高/新低后，跟踪最近 2 根 4H 结构位",
        ])
    lines.extend(["", "### 仓位"])
    if side == "观望":
        lines.append("- 当前以等待为主，不建议按强方向建仓")
    else:
        lines.append("- 风险金额 ÷ |入场价 - SL| = 可开仓位；如用手数交易，需再换算合约单位")
    lines.extend(["", "### 失效条件"])
    if side == "做多":
        lines.extend([
            f"1. 4H 收盘跌破 {support:.5f} 并未快速收回",
            "2. DXY 与收益率同时明显反向走强/走弱导致逻辑失效",
        ])
    elif side == "做空":
        lines.extend([
            f"1. 4H 收盘重新站上 {resistance:.5f}",
            "2. 央行/宏观消息显著改写利率或美元叙事",
        ])
    else:
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
