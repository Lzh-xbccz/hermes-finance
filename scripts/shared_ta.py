#!/usr/bin/env python3
"""
共享技术分析函数 — 被 a_share_analyze / forex_analyze / us_equity_analyze 引用。
消除 classify_pattern / classify_today / find_swings 等函数的重复实现。
"""

from typing import Any, Dict, List


def classify_pattern(rows: List[Dict[str, Any]], *,
                     box_chg_pct: float, box_width_pct: float,
                     trend_chg_pct: float, trend_recent_pct: float,
                     recovery_pct: float) -> str:
    """根据最近 K 线识别市场阶段。"""
    if len(rows) < 12:
        return "数据不足"
    closes = [r["close"] for r in rows]
    highs = [r["high"] for r in rows]
    lows = [r["low"] for r in rows]
    chg = (closes[-1] / closes[0] - 1) * 100 if closes[0] else 0
    recent = (closes[-1] / closes[-6] - 1) * 100 if closes[-6] else 0
    width = (max(highs) - min(lows)) / min(lows) * 100 if min(lows) else 0
    if abs(chg) < box_chg_pct and width < box_width_pct:
        return "箱体洗盘"
    if chg > trend_chg_pct and recent > trend_recent_pct:
        return "趋势推进"
    if chg > trend_chg_pct and recent < 0:
        return "冲高派发"
    if closes[-1] > min(lows[-6:]) * (1 + recovery_pct / 100) and min(lows[-3:]) <= min(lows[-6:]) * 1.001:
        return "跌破回收"
    return "阴跌磨人"


def classify_today(rows: List[Dict[str, Any]], *,
                   continuation_ratio: float,
                   bounce_ratio: float,
                   breakdown_ratio: float) -> str:
    """判断当日/最近一根 K 线的行为类型。"""
    if len(rows) < 8:
        return "数据不足"
    closes = [r["close"] for r in rows]
    highs = [r["high"] for r in rows]
    lows = [r["low"] for r in rows]
    latest = closes[-1]
    prev = closes[-2]
    recent_window = 6
    if latest >= max(highs[-recent_window:]) * continuation_ratio:
        return "延续"
    if latest > prev and latest > min(lows[-recent_window:]) * bounce_ratio:
        return "回踩"
    if latest < prev and latest > min(lows[-recent_window:]) * bounce_ratio:
        return "诱多"
    if latest < min(lows[-recent_window:]) * breakdown_ratio:
        return "诱空"
    return "纯噪音"


def find_swings(rows: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """识别局部摆点（2 周期两侧确认）。"""
    highs: List[Dict[str, Any]] = []
    lows: List[Dict[str, Any]] = []
    for i in range(2, len(rows) - 2):
        if all(rows[i]["high"] > rows[i + d]["high"] for d in [-2, -1, 1, 2]):
            highs.append(rows[i])
        if all(rows[i]["low"] < rows[i + d]["low"] for d in [-2, -1, 1, 2]):
            lows.append(rows[i])
    return {"highs": highs, "lows": lows}


def structure_basis(rows: List[Dict[str, Any]]) -> Dict[str, str]:
    """从摆点序列判断当前结构偏向。"""
    swings = find_swings(rows)
    highs = swings["highs"]
    lows = swings["lows"]
    if len(lows) >= 2 and lows[-1]["low"] > lows[-2]["low"]:
        return {
            "stance": "higher low",
            "detail": f"最近结构摆点为 higher low：{lows[-2]['low']:.5f} -> {lows[-1]['low']:.5f}（{lows[-1].get('time_utc','?')}）"
        }
    if len(highs) >= 2 and highs[-1]["high"] < highs[-2]["high"]:
        return {
            "stance": "lower high",
            "detail": f"最近结构摆点为 lower high：{highs[-2]['high']:.5f} -> {highs[-1]['high']:.5f}（{highs[-1].get('time_utc','?')}）"
        }
    return {"stance": "结构模糊", "detail": "最近摆动点未形成清晰 higher low 或 lower high"}


def recent_key_actions(rows: List[Dict[str, Any]], *,
                       body_threshold: float, range_threshold: float) -> List[str]:
    """提取最近显著波动事件。"""
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
        if abs(body) >= body_threshold or rng >= range_threshold:
            if body > body_threshold * 0.8:
                tag = "急拉"
            elif body < -body_threshold * 0.8:
                tag = "急跌"
            elif rng >= range_threshold * 1.2 and c < h - (h - l) * 0.4:
                tag = "冲高回落"
            elif rng >= range_threshold * 1.2 and c > l + (h - l) * 0.6:
                tag = "跌破回收"
            else:
                tag = "大波动"
            events.append((abs(body) + rng, f"{row.get('time_utc','?')} {tag} body:{body:+.2f}% range:{rng:.2f}%"))
    events.sort(reverse=True)
    return [text for _, text in events[:3]] or ["最近 12 根未出现显著异常波动"]


def structure_levels(rows: List[Dict[str, Any]]) -> Dict[str, float]:
    """从最近 K 线提取支撑/阻力。"""
    recent = rows[-8:] if len(rows) >= 8 else rows
    return {
        "support": min(r["low"] for r in recent),
        "resistance": max(r["high"] for r in recent),
    }


def shape_text(pattern: str) -> str:
    mapping = {
        "趋势推进": "趋势延续结构",
        "箱体洗盘": "区间震荡结构",
        "冲高派发": "高位回落结构",
        "跌破回收": "假跌破回收结构",
        "阴跌磨人": "弱反弹下行结构",
    }
    return mapping.get(pattern, "结构待确认")
