#!/usr/bin/env python3
"""
A 股综合分析器（第一版）

输入：
  1. 默认直接调用 a_share_fetch.py 获取最新数据
  2. 或用 --input 读取既有 JSON

输出：
  - Markdown 报告
"""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any, Dict, List


FETCHER = Path("/root/.hermes/skills/research/a-share-market-analysis/scripts/a_share_fetch.py")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate an A-share analysis report from fetched JSON data.")
    parser.add_argument("--input", help="Path to a previously fetched JSON file. If omitted, fetch live data first.")
    parser.add_argument("--remote", default="ash-remote", help="SSH alias passed through to the fetcher when pulling live data.")
    parser.add_argument("--stock", help="Optional stock code passed through to the fetcher when pulling live data.")
    return parser.parse_args()


def load_json(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def fetch_live(remote: str, stock: str | None) -> Dict[str, Any]:
    cmd = ["python3", str(FETCHER), "--remote", remote, "--compact"]
    if stock:
        cmd.extend(["--stock", stock])
    proc = subprocess.run(cmd, text=True, capture_output=True)
    if proc.returncode != 0:
        raise SystemExit(proc.stderr.strip() or proc.stdout.strip())
    return json.loads(proc.stdout)


def market_status_text(state: Dict[str, str]) -> str:
    if not state:
        return "未知"
    sh = state.get("SH", "")
    if "休市" in sh:
        return "节假日/休市"
    if "午间休市" in sh:
        return "午休"
    if "交易中" in sh:
        return "交易中"
    return sh or "未知"


def classify_pattern(rows: List[Dict[str, Any]]) -> str:
    if len(rows) < 10:
        return "数据不足"
    closes = [r["close"] for r in rows]
    highs = [r["high"] for r in rows]
    lows = [r["low"] for r in rows]
    chg30 = (closes[-1] / rows[0]["open"] - 1) * 100 if rows[0]["open"] else 0
    chg5 = (closes[-1] / closes[-6] - 1) * 100 if len(closes) >= 6 and closes[-6] else 0
    range_pct = (max(highs) - min(lows)) / min(lows) * 100 if min(lows) else 0
    recent_high = max(highs[-5:])
    recent_low = min(lows[-5:])
    latest_close = closes[-1]
    prev_close = closes[-2]

    if abs(chg30) < 4 and range_pct < 12:
        return "箱体洗盘"
    if chg30 > 5 and chg5 > 1 and latest_close >= prev_close:
        return "趋势推进"
    if chg30 > 5 and latest_close < recent_high * 0.992 and chg5 < 0:
        return "冲高派发"
    if latest_close > recent_low * 1.02 and min(lows[-3:]) <= recent_low:
        return "跌破回收"
    return "阴跌磨人"


def classify_today(rows: List[Dict[str, Any]]) -> str:
    if len(rows) < 5:
        return "数据不足"
    closes = [r["close"] for r in rows]
    highs = [r["high"] for r in rows]
    lows = [r["low"] for r in rows]
    latest = closes[-1]
    prev = closes[-2]
    recent_high = max(highs[-5:])
    recent_low = min(lows[-5:])
    if latest >= recent_high * 0.998:
        return "延续"
    if latest > prev and latest > recent_low * 1.01:
        return "回踩"
    if latest < prev and latest > recent_low * 1.01:
        return "诱多"
    if latest < recent_low * 0.995:
        return "诱空"
    return "纯噪音"


def summarize_breadth(breadth: Dict[str, Any], key: str) -> str:
    row = breadth.get(key, {})
    up = row.get("up_count", 0)
    down = row.get("down_count", 0)
    flat = row.get("flat_count", 0)
    ratio = up / down if down else None
    if ratio is None:
        signal = "中性"
    elif ratio > 1.5:
        signal = "偏强"
    elif ratio < 0.8:
        signal = "偏弱"
    else:
        signal = "均衡"
    ratio_text = f"{ratio:.2f}:1" if ratio is not None else "N/A"
    return f"{up}/{down}/{flat}（涨跌比 {ratio_text}，{signal}）"


def summarize_northbound(nb: Dict[str, Any], status_text: str) -> str:
    latest = nb.get("latest_balance", {})
    if not latest:
        return "数据缺失"
    net_wan = latest.get("north_total_net_inflow_wan", 0)
    net_yi = net_wan / 10000
    if "休市" in status_text:
        return f"休市日，接口保留值约 {net_yi:.2f} 亿（不视为实时流向）"
    if net_yi > 50:
        signal = "强烈偏多"
    elif net_yi > 10:
        signal = "偏多"
    elif net_yi < -50:
        signal = "强烈偏空"
    elif net_yi < -10:
        signal = "偏空"
    else:
        signal = "中性"
    return f"{net_yi:.2f} 亿（{signal}）"


def summarize_macro(macro: Dict[str, Any]) -> str:
    if not macro:
        return "宏观外盘暂缺"
    sp = macro.get("^GSPC", {})
    ix = macro.get("^IXIC", {})
    vix = macro.get("^VIX", {})
    parts = []
    if sp:
        parts.append(f"S&P {(sp.get('current',0) - sp.get('prev_close',0)) / sp.get('prev_close',1) * 100:+.2f}%")
    if ix:
        parts.append(f"Nasdaq {(ix.get('current',0) - ix.get('prev_close',0)) / ix.get('prev_close',1) * 100:+.2f}%")
    if vix:
        parts.append(f"VIX {vix.get('current',0):.2f}")
    return "，".join(parts) if parts else "宏观外盘暂缺"


def classify_news(title: str) -> str:
    a_keywords = ["证监会", "上交所", "深交所", "央行", "国务院", "国常会", "新华社", "财政部", "发改委", "交易所"]
    b_keywords = ["PMI", "CPI", "LPR", "汇率", "美联储", "非农", "标普", "纳指", "人民币"]
    if any(k in title for k in a_keywords):
        return "A"
    if any(k in title for k in b_keywords):
        return "B"
    return "C"


def completeness_text(data: Dict[str, Any]) -> str:
    requested = data.get("requested_sections", ["all"])
    errors = data.get("errors", {})
    if requested != ["all"]:
        base = "部分抓取：" + ",".join(requested)
        if errors:
            return base + "；缺口：" + "、".join(sorted(errors.keys()))
        return base
    if errors:
        return "存在缺口：" + "、".join(sorted(errors.keys()))
    return "完整"


def score_breakdown(data: Dict[str, Any]) -> Dict[str, int]:
    scores = {
        "technical": 0,
        "northbound": 0,
        "breadth": 0,
        "boards": 0,
        "macro": 0,
        "stock": 0,
    }

    sh_rows = data.get("indices_history_daily", {}).get("sh000001", [])
    if sh_rows:
        pattern = classify_pattern(sh_rows)
        if pattern == "趋势推进":
            scores["technical"] += 1
        elif pattern in {"冲高派发", "阴跌磨人"}:
            scores["technical"] -= 1

    breadth = data.get("breadth", {})
    sz = breadth.get("0.399001", {})
    if sz.get("down_count"):
        ratio = sz.get("up_count", 0) / sz["down_count"]
        if ratio > 1.3:
            scores["breadth"] += 1
        elif ratio < 0.8:
            scores["breadth"] -= 1

    nb = data.get("northbound", {}).get("latest_balance", {})
    net_yi = (nb.get("north_total_net_inflow_wan", 0) or 0) / 10000
    if net_yi > 10:
        scores["northbound"] += 1
    elif net_yi < -10:
        scores["northbound"] -= 1

    industry = data.get("board_flows", {}).get("industry", {}).get("rows", [])
    if industry:
        top = industry[0]
        if top.get("main_net_inflow_yuan", 0) > 1_000_000_000 and top.get("change_pct", 0) > 0:
            scores["boards"] += 1
        elif top.get("main_net_inflow_yuan", 0) < -1_000_000_000:
            scores["boards"] -= 1

    macro = data.get("macro", {})
    vix = macro.get("^VIX", {}).get("current", 99)
    sp = macro.get("^GSPC", {})
    if vix < 20:
        scores["macro"] += 1
    elif vix > 30:
        scores["macro"] -= 1
    if sp and sp.get("prev_close"):
        chg = (sp.get("current", 0) - sp.get("prev_close", 0)) / sp.get("prev_close", 1) * 100
        if chg > 1:
            scores["macro"] += 1
        elif chg < -1:
            scores["macro"] -= 1

    stock = data.get("stock", {})
    hist = stock.get("history_daily", [])
    snap = stock.get("snapshot", {})
    if hist:
        p = classify_pattern(hist)
        if p == "趋势推进":
            scores["stock"] += 1
        elif p in {"冲高派发", "阴跌磨人"}:
            scores["stock"] -= 1
    if snap:
        if snap.get("change_pct", 0) > 2:
            scores["stock"] += 1
        elif snap.get("change_pct", 0) < -2:
            scores["stock"] -= 1
    daily_ff = stock.get("capital_flow", {}).get("daily_tail", [])
    if daily_ff:
        last = daily_ff[-1]
        if last.get("main_net_pct", 0) > 0.5:
            scores["stock"] += 1
        elif last.get("main_net_pct", 0) < -0.5:
            scores["stock"] -= 1
    return scores


def direction_from_score(score: int, status_text: str) -> str:
    if "休市" in status_text:
        if score >= 2:
            return "偏多"
        if score <= -2:
            return "偏空"
        return "震荡"
    if score >= 2:
        return "偏多"
    if score <= -2:
        return "偏空"
    return "震荡"


def render_report(data: Dict[str, Any]) -> str:
    status_text = market_status_text(data.get("market_state", {}))
    sh_rows = data.get("indices_history_daily", {}).get("sh000001", [])
    pattern = classify_pattern(sh_rows)
    today_type = "假期/盘后观察" if "休市" in status_text else classify_today(sh_rows)
    scores = score_breakdown(data)
    score = sum(scores.values())
    direction = direction_from_score(score, status_text)
    industry_rows = data.get("board_flows", {}).get("industry", {}).get("rows", [])
    concept_rows = data.get("board_flows", {}).get("concept", {}).get("rows", [])
    region_rows = data.get("board_flows", {}).get("region", {}).get("rows", [])
    news = data.get("news", [])
    useful_news = [n for n in news if classify_news(n.get("title", "")) in {"A", "B"}][:5]
    stock = data.get("stock", {})

    idx = data.get("indices_snapshot", {})
    sh = idx.get("sh000001", {})
    sz = idx.get("sz399001", {})
    cyb = idx.get("sz399006", {})

    lines = []
    lines.append(f"## 📊 A股综合分析报告 — {data.get('fetched_at_bjt','')[:10]}")
    lines.append("")
    lines.append(f"**分析时间（UTC）**：{data.get('fetched_at_utc','').replace('T',' ')[:-1]}")
    lines.append(f"**分析时间（BJT）**：{data.get('fetched_at_bjt','').replace('T',' ')[:-6]}")
    lines.append(f"**市场状态**：{status_text}")
    lines.append(f"**数据完整性**：{completeness_text(data)}")
    lines.append("")
    lines.append("### 🟢 三大指数快照")
    for name, row in [("上证", sh), ("深证", sz), ("创业板", cyb)]:
        if row:
            lines.append(f"- {name}：{row.get('current',0):,.2f}（{row.get('change_pct',0):+.2f}%） 额:{row.get('amount_yuan',0)/1e8:,.0f}亿")
    lines.append("")
    lines.append("### 🧭 历史轨迹复盘")
    lines.append(f"- 最近 7-30 日主导手法：{pattern}")
    lines.append(f"- 今天更像：{today_type}")
    if sh_rows:
        chg30 = (sh_rows[-1]['close'] / sh_rows[0]['open'] - 1) * 100 if sh_rows[0]['open'] else 0
        lines.append(f"- 上证近30日涨跌：{chg30:+.2f}%")
    lines.append("")
    if stock:
        stock_hist = stock.get("history_daily", [])
        stock_snap = stock.get("snapshot", {})
        lines.append("### 🎯 个股观察")
        lines.append(f"- 标的：{stock_snap.get('name', stock.get('code', ''))}（{stock.get('exchange','').upper()}{stock.get('code','')}）")
        if stock_snap:
            lines.append(f"- 现价：{stock_snap.get('current',0):,.2f}（{stock_snap.get('change_pct',0):+.2f}%） 额:{stock_snap.get('amount_yuan',0)/1e8:,.2f}亿")
        if stock_hist:
            lines.append(f"- 最近主导手法：{classify_pattern(stock_hist)}")
            lines.append(f"- 当前更像：{'假期/盘后观察' if '休市' in status_text else classify_today(stock_hist)}")
        stock_ff = stock.get("capital_flow", {}).get("daily_tail", [])
        if stock_ff:
            last_ff = stock_ff[-1]
            lines.append(f"- 最近日线主力净流占比：{last_ff.get('main_net_pct',0):+.2f}%")
        lines.append("")
    lines.append("### 💰 资金面")
    lines.append(f"- 北向资金：{summarize_northbound(data.get('northbound', {}), status_text)}")
    lines.append("- 指数资金流（日线）：" + ("可用" if data.get("capital_flow", {}).get("1.000001", {}).get("daily_tail") else "暂缺"))
    lines.append("")
    lines.append("### 📊 市场结构")
    lines.append(f"- 上证广度：{summarize_breadth(data.get('breadth', {}), '1.000001')}")
    lines.append(f"- 深证广度：{summarize_breadth(data.get('breadth', {}), '0.399001')}")
    lines.append(f"- 创业板广度：{summarize_breadth(data.get('breadth', {}), '0.399006')}")
    lines.append("")
    lines.append("### 🔄 板块轮动")
    if industry_rows:
        lines.append("- 行业资金流 TOP3：")
        for row in industry_rows[:3]:
            lines.append(f"  - {row['board_name']}：{row['main_net_inflow_yuan']/1e8:,.2f}亿，涨跌幅 {row['change_pct']:+.2f}%")
    if concept_rows:
        lines.append("- 概念资金流 TOP3：")
        for row in concept_rows[:3]:
            lines.append(f"  - {row['board_name']}：{row['main_net_inflow_yuan']/1e8:,.2f}亿，涨跌幅 {row['change_pct']:+.2f}%")
    if region_rows:
        lines.append(f"- 地域资金流第一：{region_rows[0]['board_name']}（{region_rows[0]['main_net_inflow_yuan']/1e8:,.2f}亿）")
    lines.append("")
    lines.append("### 🌍 宏观面")
    lines.append(f"- {summarize_macro(data.get('macro', {}))}")
    fx = data.get("fx", {}).get("USDCNY", {})
    if fx:
        lines.append(f"- 美元人民币：{fx.get('last',0):.4f}")
    lines.append("")
    lines.append("### 📰 新闻")
    if useful_news:
        for item in useful_news:
            lines.append(f"- [{classify_news(item.get('title',''))}] {item.get('title','')}")
    else:
        lines.append("- 可用硬新闻不足，暂不纳入方向判断")
    lines.append("")
    lines.append("### 🎯 综合研判")
    lines.append(f"- 方向：**{direction}**")
    lines.append(f"- 内部评分：{score:+d}")
    lines.append(f"- 分项评分：技术{scores['technical']:+d} / 北向{scores['northbound']:+d} / 广度{scores['breadth']:+d} / 板块{scores['boards']:+d} / 宏观{scores['macro']:+d}" + (f" / 个股{scores['stock']:+d}" if stock else ""))
    lines.append("- 风险提示：A 股为 T+1，当前分析更适合次日预判；节假日/休市期间的‘实时资金’默认降权处理。")
    lines.append("")
    lines.append("### ⚠️ 免责声明")
    lines.append("以上分析基于公开数据，不构成投资建议。A 股有风险，投资需谨慎。")
    return "\n".join(lines)


def main() -> None:
    args = parse_args()
    data = load_json(args.input) if args.input else fetch_live(args.remote, args.stock)
    print(render_report(data))


if __name__ == "__main__":
    main()
