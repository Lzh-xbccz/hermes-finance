#!/usr/bin/env python3
"""
A 股统一采集脚本（第一版）

默认通过已建立的 SSH 复用连接，在国内节点上抓取 A 股关键数据并整合为 JSON：
- 三大指数快照（新浪）
- 三大指数历史日 K + 市场状态（腾讯）
- 北向资金（东方财富 push2）
- 涨跌家数（东方财富 push2）
- 行业 / 概念 / 地域板块资金流（东方财富 push2）
- 指数资金流分时 / 日线（东方财富 push2/push2his）
- 人民币汇率（新浪）
- 美股 / VIX（Yahoo Finance）
- 新闻（Google News RSS）
- 可选：指定个股的快照、历史日 K、资金流

用法：
  python3 a_share_fetch.py
  python3 a_share_fetch.py --remote ash-remote
  python3 a_share_fetch.py --compact
  python3 a_share_fetch.py --stock 600519
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
from typing import Dict, List
import time


_REMOTE_SCRIPT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'a_share_remote.py')


def _load_remote_script() -> str:
    """从独立文件加载远程采集脚本（避免大段字符串嵌在代码里）。"""
    with open(_REMOTE_SCRIPT_PATH, 'r', encoding='utf-8') as f:
        return f.read()


# ── 以下为旧 REMOTE_SCRIPT 提取后的占位（内容已迁移至 a_share_remote.py）──
import json
import os


HEADERS = {"User-Agent": "Mozilla/5.0"}
BJT = timezone(timedelta(hours=8))


def fetch_text(url: str, encoding: str = "utf-8", headers: dict | None = None) -> str:
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, headers=headers or HEADERS)
            with urllib.request.urlopen(req, timeout=20) as resp:
                return resp.read().decode(encoding, "ignore")
        except urllib.request.HTTPError as e:
            if e.code == 429 and attempt < 2:
                time.sleep(2 ** attempt + 1)
                continue
            raise


def fetch_json(url: str, encoding: str = "utf-8", headers: dict | None = None) -> dict:
    return json.loads(fetch_text(url, encoding=encoding, headers=headers))


def parse_float(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def parse_sina_quote_line(line: str):
    line = line.strip()
    if not line or "=" not in line:
        return None
    raw = line.split("=", 1)[1].strip().strip('"').strip(";")
    parts = raw.split(",")
    if len(parts) < 10:
        return None
    return {
        "name": parts[0],
        "current": parse_float(parts[1]),
        "prev_close": parse_float(parts[2]),
        "open": parse_float(parts[3]),
        "high": parse_float(parts[4]),
        "low": parse_float(parts[5]),
        "volume_shou": parse_float(parts[8]),
        "amount_yuan": parse_float(parts[9]),
        "trade_date": parts[30] if len(parts) > 30 else "",
        "trade_time": parts[31] if len(parts) > 31 else "",
    }


def fetch_sina_indices_local():
    url = "https://hq.sinajs.cn/list=sh000001,sz399001,sz399006"
    text = fetch_text(url, encoding="gbk", headers={"Referer": "https://finance.sina.com.cn", **HEADERS})
    codes = ["sh000001", "sz399001", "sz399006"]
    result = {}
    for code, line in zip(codes, text.splitlines()):
        row = parse_sina_quote_line(line)
        if row:
            row["change_pct"] = ((row["current"] - row["prev_close"]) / row["prev_close"] * 100) if row["prev_close"] else 0
            result[code] = row
    return result


def fetch_tencent_kline_local(code: str, limit: int = 30):
    url = f"https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param={code},day,,,{limit},qfq"
    data = fetch_json(url)
    block = data["data"][code]
    day_key = "day" if "day" in block else "qfqday"
    rows = []
    for row in block.get(day_key, []):
        rows.append({
            "date": row[0],
            "open": parse_float(row[1]),
            "close": parse_float(row[2]),
            "high": parse_float(row[3]),
            "low": parse_float(row[4]),
            "volume": parse_float(row[5]),
            "change_pct": ((parse_float(row[2]) - parse_float(row[1])) / parse_float(row[1]) * 100) if parse_float(row[1]) else 0,
        })
    qt = block.get("qt", {})
    market_raw = qt.get("market", [""])[0]
    market_parts = market_raw.split("|") if market_raw else []
    market = {}
    for item in market_parts:
        if "_" in item:
            key = item.split("_", 1)[0]
            market[key] = item
    return {
        "code": code,
        "rows": rows,
        "qt": qt.get(code, []),
        "market_raw": market_raw,
        "market_state": market,
    }


def fetch_yahoo_meta_local(symbol: str):
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=1d&range=5d"
    data = fetch_json(url).get("chart", {}).get("result", [{}])[0].get("meta", {})
    return {
        "current": parse_float(data.get("regularMarketPrice")),
        "prev_close": parse_float(data.get("chartPreviousClose")),
    }


def fetch_google_news_local():
    url = "https://news.google.com/rss/search?q=%E4%B8%8A%E8%AF%81+OR+%E6%B7%B1%E8%AF%81+OR+%E5%88%9B%E4%B8%9A%E6%9D%BF&hl=zh-CN&gl=CN&ceid=CN:zh-Hans"
    root = ET.fromstring(fetch_text(url))
    items = []
    for item in root.findall("./channel/item")[:8]:
        items.append({
            "title": item.findtext("title", "").strip(),
            "pub_date": item.findtext("pubDate", "").strip(),
            "link": item.findtext("link", "").strip(),
            "source": item.findtext("source", ""),
        })
    return items


def normalize_stock_local(raw: str) -> str:
    code = str(raw).strip().lower()
    if code.startswith(("sh", "sz")):
        return code
    if code and code[0] in {"6", "5", "9"}:
        return "sh" + code
    if code and code[0] in {"0", "2", "3"}:
        return "sz" + code
    raise ValueError(f"暂不支持自动识别该代码: {raw}")


def run_local_fallback(sections: List[str] | None, stock: str | None) -> dict:
    now_utc = datetime.now(timezone.utc)
    now_bjt = datetime.now(BJT)
    out = {
        "fetched_at_utc": now_utc.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "fetched_at_bjt": now_bjt.strftime("%Y-%m-%dT%H:%M:%S+08:00"),
        "requested_sections": sections or ["all"],
        "errors": {
            "northbound": "local_fallback: unavailable without mainland remote",
            "breadth": "local_fallback: unavailable without mainland remote",
            "board_flows": "local_fallback: unavailable without mainland remote",
            "capital_flow": "local_fallback: unavailable without mainland remote",
        },
        "availability": {
            "mode": "local_fallback",
            "eastmoney_push2": False,
            "eastmoney_pages": False,
            "xueqiu": False,
            "10jqka": False,
        },
    }
    tencent_sh = fetch_tencent_kline_local("sh000001", limit=30)
    out["tencent_sh"] = tencent_sh
    out["market_state"] = tencent_sh.get("market_state", {})
    out["indices_snapshot"] = fetch_sina_indices_local()
    out["indices_history_daily"] = {
        "sh000001": tencent_sh["rows"],
        "sz399001": fetch_tencent_kline_local("sz399001", limit=30)["rows"],
        "sz399006": fetch_tencent_kline_local("sz399006", limit=30)["rows"],
    }
    out["fx"] = {}
    out["northbound"] = {}
    out["breadth"] = {}
    out["board_flows"] = {}
    out["capital_flow"] = {}
    out["macro"] = {
        "^GSPC": fetch_yahoo_meta_local("^GSPC"),
        "^IXIC": fetch_yahoo_meta_local("^IXIC"),
        "^DJI": fetch_yahoo_meta_local("^DJI"),
        "^VIX": fetch_yahoo_meta_local("^VIX"),
    }
    out["news"] = fetch_google_news_local()
    if stock:
        code = normalize_stock_local(stock)
        stock_hist = fetch_tencent_kline_local(code, limit=30)["rows"]
        last = stock_hist[-1] if stock_hist else {}
        prev = stock_hist[-2] if len(stock_hist) > 1 else last
        out["stock"] = {
            "input": stock,
            "tencent_code": code,
            "snapshot": {
                "current": last.get("close", 0),
                "open": last.get("open", 0),
                "high": last.get("high", 0),
                "low": last.get("low", 0),
                "prev_close": prev.get("close", 0),
                "change_pct": ((last.get("close", 0) - prev.get("close", 0)) / prev.get("close", 1) * 100) if prev.get("close") else 0,
            },
            "history_daily": stock_hist,
            "capital_flow": {"daily_tail": [], "intraday_tail": []},
        }
    return out


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fetch A-share market data via a pre-established SSH connection to a mainland node.")
    parser.add_argument("--remote", default="ash-remote", help="SSH host alias in ~/.ssh/config. Default: ash-remote")
    parser.add_argument("--compact", action="store_true", help="Print compact JSON instead of pretty JSON")
    parser.add_argument(
        "--section",
        action="append",
        choices=["all", "market_state", "indices", "northbound", "breadth", "boards", "capital_flow", "macro", "news", "stock"],
        help="Fetch only selected sections. Can be repeated.",
    )
    parser.add_argument("--stock", help="Optional A-share stock code, e.g. 600519, sh600519, 300750, sz300750")
    return parser.parse_args()


def run_remote(remote: str, sections: List[str] | None, stock: str | None) -> dict:
    cmd = ["ssh", "-o", "BatchMode=yes", remote]
    if sections:
        cmd.extend(["env", f"A_SHARE_SECTIONS={','.join(sections)}"])
    if stock:
        if sections:
            cmd.extend([f"A_SHARE_STOCK={stock}"])
        else:
            cmd.extend(["env", f"A_SHARE_STOCK={stock}"])
    elif sections:
        pass
    cmd.extend(["python3", "-"])
    proc = subprocess.run(cmd, input=_load_remote_script(), text=True, capture_output=True)
    if proc.returncode != 0:
        stderr = proc.stderr.strip() or proc.stdout.strip()
        raise SystemExit(
            "远端采集失败。请先确认 SSH 主连接已建立，并且别名可用。\n"
            f"命令: {' '.join(cmd)}\n"
            f"错误: {stderr}"
        )
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"远端返回不是有效 JSON: {exc}\n原始输出前 1000 字符:\n{proc.stdout[:1000]}")


def main() -> None:
    args = parse_args()
    sections = args.section or ["all"]
    try:
        data = run_remote(args.remote, sections, args.stock)
    except SystemExit as exc:
        message = str(exc)
        if "Permission denied" in message or "远端采集失败" in message:
            data = run_local_fallback(sections, args.stock)
            data.setdefault("errors", {})["remote"] = message
        else:
            raise
    try:
        if args.compact:
            print(json.dumps(data, ensure_ascii=False, separators=(",", ":")))
        else:
            print(json.dumps(data, ensure_ascii=False, indent=2))
    except BrokenPipeError:
        pass


if __name__ == "__main__":
    main()
