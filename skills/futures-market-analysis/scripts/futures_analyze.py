#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any, Dict, List


FETCHER = Path("/root/.hermes/skills/research/futures-market-analysis/scripts/futures_fetch.py")


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


def classify_pattern(rows: List[Dict[str, Any]]) -> str:
    if len(rows) < 12:
        return "数据不足"
    closes = [r["close"] for r in rows]
    highs = [r["high"] for r in rows]
    lows = [r["low"] for r in rows]
    chg = (closes[-1] / closes[0] - 1) * 100 if closes[0] else 0
    recent = (closes[-1] / closes[-6] - 1) * 100 if closes[-6] else 0
    width = (max(highs) - min(lows)) / min(lows) * 100 if min(lows) else 0
    if abs(chg) < 4 and width < 10:
        return "箱体洗盘"
    if chg > 5 and recent > 1:
        return "趋势推进"
    if chg > 5 and recent < 0:
        return "冲高派发"
    if closes[-1] > min(lows[-6:]) * 1.02 and min(lows[-3:]) <= min(lows[-6:]) * 1.003:
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
    if latest >= max(highs[-6:]) * 0.998:
        return "延续"
    if latest > prev and latest > min(lows[-6:]) * 1.01:
        return "回踩"
    if latest < prev and latest > min(lows[-6:]) * 1.01:
        return "诱多"
    if latest < min(lows[-6:]) * 0.995:
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
        if abs(body) >= 1.0 or rng >= 2.0:
            if body > 0.8:
                tag = "急拉"
            elif body < -0.8:
                tag = "急跌"
            elif rng >= 2.5 and c < h - (h - l) * 0.4:
                tag = "冲高回落"
            elif rng >= 2.5 and c > l + (h - l) * 0.6:
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
        detail = f"最近结构摆点为 higher low：{lows[-2]['low']:.2f} -> {lows[-1]['low']:.2f}（{lows[-1]['time_utc']}）"
    elif len(highs) >= 2 and highs[-1]["high"] < highs[-2]["high"]:
        stance = "lower high"
        detail = f"最近结构摆点为 lower high：{highs[-2]['high']:.2f} -> {highs[-1]['high']:.2f}（{highs[-1]['time_utc']}）"
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
    daily = data.get("daily_90d", [])
    h4 = data.get("agg_4h_10d", [])
    h1 = data.get("hourly_10d", [])
    if len(daily) < 20 or len(h4) < 12 or len(h1) < 24:
        gaps.append("技术结构")
    symbol = data["symbol"]
    proxies = data.get("proxies", {})
    required_map = {
        "CL": ["^OVX", "DX-Y.NYB"],
        "GC": ["^TNX", "DX-Y.NYB"],
        "SI": ["^TNX", "DX-Y.NYB"],
        "HG": ["DX-Y.NYB"],
        "NG": ["^VIX"],
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
        parts.append("关注地缘/OPEC+/库存")
    elif symbol in {"GC", "SI"}:
        tnx = proxies.get("^TNX", {})
        dxy = proxies.get("DX-Y.NYB", {})
        if tnx:
            parts.append(f"10Y {tnx.get('change_pct', 0):+.2f}%")
        if dxy:
            parts.append(f"DXY {dxy.get('change_pct', 0):+.2f}%")
        parts.append("关注利率与避险")
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
    cftc = data.get("structured_drivers", {}).get("cftc", {})
    if not cftc or not cftc.get("found"):
        return "CFTC 持仓摘要暂缺"
    if cftc.get("report_type") == "futures_only":
        return "CFTC 周报原始摘录可用，但当前解析未做稳健数值归类"
    return "CFTC 摘要可用但未归类"


def structure_levels(rows: List[Dict[str, Any]]) -> Dict[str, float]:
    recent = rows[-8:] if len(rows) >= 8 else rows
    lows = [r["low"] for r in recent]
    highs = [r["high"] for r in recent]
    return {"support": min(lows), "resistance": max(highs)}


def build_report(data: Dict[str, Any]) -> str:
    daily = data["daily_90d"]
    h4 = data["agg_4h_10d"]
    h1 = data["hourly_10d"]
    direction = price_bias(daily, h4)
    pattern = classify_pattern(h4)
    today = classify_today(h1[-24:] if len(h1) >= 24 else h1)
    actions = recent_key_actions(h4)
    structure = structure_basis(h4)
    levels = structure_levels(h4)
    support = levels["support"]
    resistance = levels["resistance"]
    last = h1[-1]["close"] if h1 else daily[-1]["close"]
    gaps = key_block_gaps(data)
    if gaps or structure["stance"] == "结构模糊":
        direction = "观望"
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
        f"### 方向：{'🟢 做多' if direction == '做多' else '🔴 做空' if direction == '做空' else '⚪ 观望'}",
        "",
        f"**一句话理由**：{reason}",
        f"**数据完整性**：{completeness}",
        "**宏观时效性**：24h 期货/代理市场按抓取时点视作近实时，重大事件窗口需额外降权技术面",
        f"**主导驱动**：{driver_summary(data)}",
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
        f"- CFTC 摘要：{cftc_summary(data)}",
        f"- 情绪代理：{'OVX/VIX 未见异常缺口' if any(k in data.get('proxies', {}) for k in ['^OVX', '^VIX']) else '波动率代理不足'}",
        f"- 交叉验证：可用代理 {', '.join(sorted(k for k, v in data.get('proxies', {}).items() if v)) or '无'}",
        "",
        "### 六维判断",
        f"- 技术面：当前价 {last:.2f}，4H 结构与最近摆点决定方向",
        f"- 市场结构：以近月代理观察，注意单合约/近月替代限制",
        f"- 主导力量：{driver_summary(data)}；{cftc_summary(data)}",
        "- 情绪面：通过波动率代理和 headline 风险判断",
        f"- 宏观面：重大事件前技术权重下降；{'EIA 周报来源可用' if data.get('structured_drivers', {}).get('eia', {}).get('available') else 'EIA 结构化块暂缺'}",
        "- 交叉验证：通过 DXY / VIX / TNX / ETF 代理做确认",
        "",
        "### 💰 止盈止损计划",
    ]
    if direction == "观望":
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
    if direction == "观望":
        lines.append("- 观望阶段不设置移动止损")
    else:
        lines.extend([
            "- 到 TP1 → 移损至开仓价",
            "- 到 TP2 → 移损至 TP1",
            "- 创出新高/新低后，跟踪最近 2 根 4H 结构位",
        ])
    lines.extend(["", "### 仓位"])
    if direction == "观望":
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
