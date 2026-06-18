#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any, Dict, List


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


def classify_pattern(rows: List[Dict[str, Any]]) -> str:
    if len(rows) < 12:
        return "数据不足"
    closes = [r["close"] for r in rows]
    highs = [r["high"] for r in rows]
    lows = [r["low"] for r in rows]
    chg = (closes[-1] / closes[0] - 1) * 100 if closes[0] else 0
    recent = (closes[-1] / closes[-6] - 1) * 100 if closes[-6] else 0
    width = (max(highs) - min(lows)) / min(lows) * 100 if min(lows) else 0
    if abs(chg) < 5 and width < 12:
        return "箱体洗盘"
    if chg > 6 and recent > 1:
        return "趋势推进"
    if chg > 6 and recent < 0:
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
        if abs(body) >= 1.2 or rng >= 2.5:
            if body > 1.0:
                tag = "急拉"
            elif body < -1.0:
                tag = "急跌"
            elif rng >= 3.0 and c < h - (h - l) * 0.4:
                tag = "冲高回落"
            elif rng >= 3.0 and c > l + (h - l) * 0.6:
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


def structure_levels(rows: List[Dict[str, Any]]) -> Dict[str, float]:
    recent = rows[-8:] if len(rows) >= 8 else rows
    return {
        "support": min(r["low"] for r in recent),
        "resistance": max(r["high"] for r in recent),
    }


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
    votes: Dict[str, List[str]] = {"做多": [], "做空": [], "veto": [], "neutral": []}
    technical = direction(data)
    if technical in {"做多", "做空", "偏多", "偏空"}:
        normalized = "做多" if technical in {"做多", "偏多"} else "做空"
        votes[normalized].append(f"技术结构={technical}")

    pattern = classify_pattern(data.get("agg_4h_10d") or data.get("daily_90d", []))
    if pattern == "趋势推进":
        votes["做多"].append("主导手法=趋势推进")
    elif pattern in {"冲高派发", "阴跌磨人"}:
        votes["做空"].append(f"主导手法={pattern}")
    elif pattern in {"箱体洗盘", "跌破回收"}:
        votes["neutral"].append(f"主导手法={pattern}")

    vix_price = _proxy_price(data, "^VIX")
    vix_chg = _proxy_change(data, "^VIX")
    tnx_chg = _proxy_change(data, "^TNX")
    spy_chg = _proxy_change(data, "SPY")
    qqq_chg = _proxy_change(data, "QQQ")

    if vix_price is not None and vix_price >= 25:
        votes["veto"].append(f"VIX={vix_price:.2f} 偏高，方向质量不足")
    if vix_chg is not None:
        if vix_chg > 5:
            votes["做空"].append(f"VIX上升 {vix_chg:+.2f}%")
        elif vix_chg < -5:
            votes["做多"].append(f"VIX下降 {vix_chg:+.2f}%")
    if tnx_chg is not None:
        if tnx_chg > 0.50:
            votes["做空"].append(f"10Y上行 {tnx_chg:+.2f}% 压制权益久期")
        elif tnx_chg < -0.50:
            votes["做多"].append(f"10Y下行 {tnx_chg:+.2f}% 支撑估值")
    for name, chg in {"SPY": spy_chg, "QQQ": qqq_chg}.items():
        if chg is None:
            continue
        if chg > 0.50:
            votes["做多"].append(f"{name}上涨 {chg:+.2f}%")
        elif chg < -0.50:
            votes["做空"].append(f"{name}下跌 {chg:+.2f}%")

    if data.get("instrument_type") == "stock":
        events = data.get("company_event_proxy", {}).get("events", [])
        if not events:
            votes["veto"].append("个股公司事件代理缺失，禁止硬给方向")
        for event in events[:5]:
            event_type = event.get("type")
            title = str(event.get("title", "")).lower()
            if event_type == "earnings_proxy":
                if any(token in title for token in ["miss", "cuts", "lower", "weak", "falls"]):
                    votes["做空"].append(f"公司事件偏空：{event.get('title')}")
                elif any(token in title for token in ["beat", "raise", "strong", "growth"]):
                    votes["做多"].append(f"公司事件偏多：{event.get('title')}")
                else:
                    votes["neutral"].append(f"公司事件未定向：{event.get('title')}")
            elif event_type == "regulatory_proxy":
                votes["做空"].append(f"监管/诉讼风险：{event.get('title')}")
            elif event_type == "business_proxy":
                if any(token in title for token in ["delay", "cut", "weak", "risk", "falls", "probe"]):
                    votes["做空"].append(f"公司业务事件偏空：{event.get('title')}")
                elif any(token in title for token in ["launch", "contract", "approval", "growth", "strong", "ai", "chip", "product"]):
                    votes["做多"].append(f"公司业务事件偏多：{event.get('title')}")
                else:
                    votes["neutral"].append(f"公司业务事件未定向：{event.get('title')}")

    return _dimensionize_votes(votes, _us_equity_dimension)


def _neutral_direction(data: Dict[str, Any]) -> str:
    return "震荡" if data.get("instrument_type") == "index" else "观望"


def direction_from_evidence(data: Dict[str, Any], votes: Dict[str, List[str]] | None = None) -> str:
    votes = votes or directional_evidence(data)
    if votes["veto"]:
        return _neutral_direction(data)
    long_count = len(votes["做多"])
    short_count = len(votes["做空"])
    if data.get("instrument_type") == "index":
        if long_count >= 3 and long_count - short_count >= 2:
            return "偏多"
        if short_count >= 3 and short_count - long_count >= 2:
            return "偏空"
        return "震荡"
    if long_count >= 3 and long_count - short_count >= 2:
        return "做多"
    if short_count >= 3 and short_count - long_count >= 2:
        return "做空"
    return _neutral_direction(data)


def direction_quality_text(votes: Dict[str, List[str]]) -> str:
    return (
        f"多头独立维度 {len(votes['做多'])} 项：{'; '.join(votes['做多']) or '无'}；"
        f"空头独立维度 {len(votes['做空'])} 项：{'; '.join(votes['做空']) or '无'}；"
        f"中性/缺失：{'; '.join(votes['neutral']) or '无'}；"
        f"硬性降级：{'; '.join(votes['veto']) or '无'}"
    )


def counter_audit_text(final_direction: str, votes: Dict[str, List[str]]) -> str:
    long_count = len(votes["做多"])
    short_count = len(votes["做空"])
    neutral_label = "震荡" if final_direction == "震荡" else "观望"
    if votes["veto"]:
        return f"存在硬性降级项，最终方向降为{neutral_label}"
    if final_direction in {"做多", "偏多"}:
        return "最强空头证据：" + ("；".join(votes["做空"]) if votes["做空"] else "无同等级反证")
    if final_direction in {"做空", "偏空"}:
        return "最强多头证据：" + ("；".join(votes["做多"]) if votes["做多"] else "无同等级反证")
    if long_count == short_count:
        return f"多空证据数量相同，方向质量不足，最终{neutral_label}"
    if abs(long_count - short_count) < 2:
        return f"多空证据差距小于 2 项，未通过方向质量门槛，最终{neutral_label}"
    return f"同向维度少于 3 项，未形成可执行方向优势，最终{neutral_label}"


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
    side = direction_from_evidence(data, votes)
    pattern = classify_pattern(h4) if h4 else "数据不足"
    today = classify_today(h1[-24:] if len(h1) >= 24 else h1) if h1 else "数据不足"
    actions = recent_key_actions(h4 or daily)
    structure = structure_basis(h4 or daily)
    levels = structure_levels(h4 or daily)
    support = levels["support"]
    resistance = levels["resistance"]
    last = (h1[-1]["close"] if h1 else daily[-1]["close"]) if daily else 0.0
    gaps = key_block_gaps(data)
    if gaps or structure["stance"] == "结构模糊":
        side = _neutral_direction(data)
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
            f"**结论**：{side}",
            f"**数据完整性**：{completeness}",
            "**宏观时效性**：若处于美股常规时段外，现金指数与 ETF 联动仅作背景过滤",
            f"**主导因子**：{driver_summary(data)}",
            f"**方向质量门槛**：{direction_quality_text(votes)}",
            f"**反向审计**：{counter_audit_text(side, votes)}",
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
            "### 七维主判断",
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
        emoji = "🟢 做多" if side == "做多" else "🔴 做空" if side == "做空" else "⚪ 观望"
        if side == "做多":
            sl = support * 0.997
            tp1 = resistance
            tp2 = resistance * 1.02
            tp3 = resistance * 1.04
            reason = "结构偏多，且大盘/利率背景未明显反向"
        elif side == "做空":
            sl = resistance * 1.003
            tp1 = support
            tp2 = support * 0.98
            tp3 = support * 0.96
            reason = "结构偏空，且风险偏好未明显修复"
        else:
            sl = tp1 = tp2 = tp3 = None
            reason = "结构与市场背景不够一致" if not gaps and structure["stance"] != "结构模糊" else "关键结构或关键数据不够清晰，按规则降级为观望"
        lines.extend([
            f"### 方向：{emoji}",
            "",
            f"**一句话理由**：{reason}",
            f"**数据完整性**：{completeness}",
            "**宏观时效性**：若处于盘前/盘后，个股与ETF价格波动仅作弱确认，常规时段信号优先",
            f"**市场背景**：{driver_summary(data)}",
            f"**方向质量门槛**：{direction_quality_text(votes)}",
            f"**反向审计**：{counter_audit_text(side, votes)}",
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
            "### 七维主判断",
            f"- 技术面：当前价 {last:.2f}",
            "- 市场结构：看 ETF、行业轮动和盘前盘后风险",
            f"- 主导力量：公司事件、行业主线和利率敏感性；{company_event_summary(data)}",
            "- 情绪面：通过 VIX 和大盘风险偏好判断",
            "- 宏观面：Fed、收益率、美元和数据窗口",
            "- 交叉验证：SPY/QQQ/IWM 与同类资产",
            "",
            "### 💰 止盈止损计划",
        ])
        if side == "观望":
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
            lines.append("- 风险金额 ÷ |入场价 - SL| = 可开股数")
        lines.extend(["", "### 失效条件"])
        if side == "做多":
            lines.extend([
                f"1. 4H 收盘跌破 {support:.2f} 并未快速收回",
                "2. 利率与风险偏好同步转坏，破坏当前逻辑",
            ])
        elif side == "做空":
            lines.extend([
                f"1. 4H 收盘重新站上 {resistance:.2f}",
                "2. 大盘与行业主线同步修复，破坏空头逻辑",
            ])
        else:
            lines.extend([
                "1. 等待更清晰的结构位",
                "2. 等待事件窗口过去再评估",
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
