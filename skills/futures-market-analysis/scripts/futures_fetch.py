#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from typing import Any, Dict, List


USER_AGENT = "Mozilla/5.0"

SYMBOL_MAP = {
    "CL": {"ticker": "CL=F", "label": "WTI Crude Oil", "kind": "energy", "news": "WTI oil"},
    "GC": {"ticker": "GC=F", "label": "Gold", "kind": "metal", "news": "gold price"},
    "SI": {"ticker": "SI=F", "label": "Silver", "kind": "metal", "news": "silver price"},
    "HG": {"ticker": "HG=F", "label": "Copper", "kind": "metal", "news": "copper price"},
    "NG": {"ticker": "NG=F", "label": "Natural Gas", "kind": "energy", "news": "natural gas"},
    "ES": {"ticker": "ES=F", "label": "E-mini S&P 500", "kind": "index_future", "news": "S&P 500 futures"},
    "NQ": {"ticker": "NQ=F", "label": "E-mini Nasdaq 100", "kind": "index_future", "news": "Nasdaq futures"},
    "YM": {"ticker": "YM=F", "label": "E-mini Dow", "kind": "index_future", "news": "Dow futures"},
    "RTY": {"ticker": "RTY=F", "label": "Russell 2000 futures", "kind": "index_future", "news": "Russell 2000 futures"},
}

PROXIES = {
    "CL": ["DX-Y.NYB", "^OVX", "USO"],
    "GC": ["DX-Y.NYB", "^TNX", "GLD"],
    "SI": ["DX-Y.NYB", "SLV", "^TNX"],
    "HG": ["DX-Y.NYB", "COPX", "^TNX"],
    "NG": ["DX-Y.NYB", "^VIX", "UNG"],
    "ES": ["^VIX", "^TNX", "SPY"],
    "NQ": ["^VIX", "^TNX", "QQQ"],
    "YM": ["^VIX", "^TNX", "DIA"],
    "RTY": ["^VIX", "^TNX", "IWM"],
}

CFTC_FUTURES_MARKETS = {
    "CL": ("https://www.cftc.gov/dea/futures/deanymesf.htm", "CRUDE OIL"),
    "GC": ("https://www.cftc.gov/dea/futures/deacmxsf.htm", "GOLD"),
    "SI": ("https://www.cftc.gov/dea/futures/deacmxsf.htm", "SILVER"),
    "HG": ("https://www.cftc.gov/dea/futures/deacmxsf.htm", "COPPER"),
    "ES": ("https://www.cftc.gov/dea/futures/deacmesf.htm", "E-MINI S&P 500 STOCK INDEX"),
    "NQ": ("https://www.cftc.gov/dea/futures/deacmesf.htm", "NASDAQ-100 STOCK INDEX (MINI)"),
    "YM": ("https://www.cftc.gov/dea/futures/deacbotf.htm", "DJIA x $10"),
    "RTY": ("https://www.cftc.gov/dea/futures/deacmesf.htm", "RUSSELL 2000"),
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fetch futures market data into JSON.")
    parser.add_argument("symbol", help="Common futures symbol such as CL, GC, ES, NQ")
    parser.add_argument("--compact", action="store_true", help="Compact JSON output")
    return parser.parse_args()


def fetch_json(url: str, retries: int = 3) -> Dict[str, Any]:
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=20) as resp:
                return json.load(resp)
        except urllib.request.HTTPError as e:
            if e.code == 429 and attempt < retries - 1:
                time.sleep(2 ** attempt + 1)
                continue
            raise


def fetch_text(url: str, retries: int = 3) -> str:
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=20) as resp:
                return resp.read().decode("utf-8", "ignore")
        except urllib.request.HTTPError as e:
            if e.code == 429 and attempt < retries - 1:
                time.sleep(2 ** attempt + 1)
                continue
            raise


def to_float(value: Any) -> float | None:
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def fetch_chart(ticker: str, interval: str, range_: str) -> Dict[str, Any]:
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{urllib.parse.quote(ticker)}?interval={interval}&range={range_}"
    data = fetch_json(url)
    result = data["chart"]["result"][0]
    meta = result.get("meta", {})
    timestamps = result.get("timestamp", []) or []
    quote = (result.get("indicators", {}).get("quote") or [{}])[0]
    rows = []
    opens = quote.get("open", [])
    highs = quote.get("high", [])
    lows = quote.get("low", [])
    closes = quote.get("close", [])
    vols = quote.get("volume", [])
    for i, ts in enumerate(timestamps):
        o = to_float(opens[i] if i < len(opens) else None)
        h = to_float(highs[i] if i < len(highs) else None)
        l = to_float(lows[i] if i < len(lows) else None)
        c = to_float(closes[i] if i < len(closes) else None)
        v = to_float(vols[i] if i < len(vols) else None)
        if None in {o, h, l, c}:
            continue
        rows.append({
            "ts": ts,
            "time_utc": datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d %H:%M"),
            "open": o,
            "high": h,
            "low": l,
            "close": c,
            "volume": v or 0.0,
        })
    return {"meta": meta, "rows": rows}


def aggregate_4h(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    out = []
    for i in range(0, len(rows) - 3, 4):
        chunk = rows[i:i + 4]
        out.append({
            "ts": chunk[0]["ts"],
            "time_utc": chunk[0]["time_utc"],
            "open": chunk[0]["open"],
            "high": max(x["high"] for x in chunk),
            "low": min(x["low"] for x in chunk),
            "close": chunk[-1]["close"],
            "volume": sum(x["volume"] for x in chunk),
        })
    return out


def fetch_news(query: str, limit: int = 6) -> List[Dict[str, str]]:
    url = "https://news.google.com/rss/search?q=" + urllib.parse.quote(query) + "&hl=en-US&gl=US&ceid=US:en"
    root = ET.fromstring(fetch_text(url))
    items = []
    for item in root.findall("./channel/item")[:limit]:
        items.append({
            "title": item.findtext("title", "").strip(),
            "source": item.findtext("source", "").strip(),
            "pubDate": item.findtext("pubDate", "").strip(),
        })
    return items


def fetch_quote_snapshot(ticker: str) -> Dict[str, Any]:
    chart = fetch_chart(ticker, "1d", "5d")
    rows = chart["rows"]
    if not rows:
        return {}
    latest = rows[-1]
    prev = rows[-2] if len(rows) > 1 else latest
    prev_close = prev["close"]
    return {
        "symbol": ticker,
        "price": latest["close"],
        "prev_close": prev_close,
        "change_pct": ((latest["close"] - prev_close) / prev_close * 100) if prev_close else 0.0,
    }


def extract_cftc_block(symbol: str) -> Dict[str, Any]:
    spec = CFTC_FUTURES_MARKETS.get(symbol)
    if not spec:
        return {}
    url, market = spec
    try:
        html = fetch_text(url)
    except Exception:
        return {"source": url, "market": market, "found": False, "error": "fetch failed"}
    idx = html.upper().find(market.upper())
    if idx < 0:
        return {"source": url, "market": market, "found": False, "error": "market not in page"}
    # 窗口从 1600 扩到 3000，避免市场名出现在靠后位置时截断
    block = html[idx:idx + 3000]
    out = {"source": url, "market": market, "found": True}
    
    # 尝试多种段落标记
    lines = [ln.strip() for ln in block.splitlines() if ln.strip()]
    
    # ── OI 提取：多种模式 ──
    oi_line = ""
    for pattern in ["OPEN INTEREST:", "OPENINTEREST:", "Open interest is", "Open Interest:"]:
        oi_line = next((ln for ln in lines if pattern.upper() in ln.upper()), "")
        if oi_line:
            break
    oi_match = re.search(r"[\d,]{4,}", oi_line) if oi_line else None
    if oi_match:
        out["open_interest"] = int(oi_match.group(0).replace(",", ""))
    
    # ── 持仓数据提取：多种行标记 ──
    commit_idx = -1
    for marker in ["COMMITMENTS", "Commitments", "Positions", "POSITIONS"]:
        commit_idx = next((i for i, ln in enumerate(lines) if ln.upper() == marker.upper()), -1)
        if commit_idx >= 0:
            break
    # fallback: 找含 "LONG" 和 "SHORT" 的行
    if commit_idx < 0:
        commit_idx = next((i for i, ln in enumerate(lines) if "LONG" in ln.upper() and "SHORT" in ln.upper()), -1)
    
    nums_line = lines[commit_idx + 1] if commit_idx >= 0 and commit_idx + 1 < len(lines) else ""
    row = [int(x.replace(",", "")) for x in re.findall(r"\d[\d,]*", nums_line)]
    
    # ── 根据列数推断数据布局 ──
    if len(row) >= 8:
        out["non_commercial_long"] = row[0]
        out["non_commercial_short"] = row[1]
        out["commercial_long"] = row[3]
        out["commercial_short"] = row[4]
        # 计算净头寸
        out["non_commercial_net"] = row[0] - row[1]
        out["commercial_net"] = row[3] - row[4]
    elif len(row) >= 4:
        # 降级：只有 4 列时尝试最佳猜测
        out["non_commercial_long"] = row[0]
        out["non_commercial_short"] = row[1]
        out["non_commercial_net"] = row[0] - row[1]
    else:
        out["parse_warning"] = f"expected >=8 cols, got {len(row)}"
        out["raw_nums"] = row
    
    # ── 验证 ──
    nc_long = out.get("non_commercial_long", 0)
    nc_short = out.get("non_commercial_short", 0)
    if nc_long > 0 and nc_short > 0:
        ratio = nc_long / max(nc_short, 1)
        if ratio > 3:
            out["position_signal"] = "🟢 投机极度看多"
        elif ratio > 2:
            out["position_signal"] = "🟢 投机偏多"
        elif ratio < 0.33:
            out["position_signal"] = "🔴 投机极度看空"
        elif ratio < 0.5:
            out["position_signal"] = "🔴 投机偏空"
        else:
            out["position_signal"] = "⚪ 中性"
    
    return out


def eia_proxy(symbol: str) -> Dict[str, Any]:
    if symbol == "CL":
        url = "https://www.eia.gov/petroleum/supply/weekly/"
        title = "Weekly Petroleum Status Report"
    elif symbol == "NG":
        url = "https://www.eia.gov/naturalgas/weekly/"
        title = "Weekly Natural Gas Storage Report"
    else:
        return {}
    html = fetch_text(url)
    return {"source": url, "title": title, "available": title.lower() in html.lower()}


def main() -> int:
    args = parse_args()
    symbol = args.symbol.strip().upper()
    if symbol not in SYMBOL_MAP:
        raise SystemExit(f"Unsupported futures symbol: {symbol}")
    spec = SYMBOL_MAP[symbol]
    ticker = spec["ticker"]

    data = {
        "analysis_time_utc": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M"),
        "symbol": symbol,
        "ticker": ticker,
        "label": spec["label"],
        "kind": spec["kind"],
        "proxies": {},
        "structured_drivers": {},
        "source_status": {},
        "errors": {},
    }

    # ─── Yahoo组：串行+0.4s间隔避免429 ───
    def fetch_yahoo_group():
        results = {}
        # 主标的日线和小时线
        results["daily_90d"] = fetch_chart(ticker, "1d", "3mo")["rows"]
        time.sleep(0.4)
        results["hourly_10d"] = fetch_chart(ticker, "1h", "10d")["rows"]
        # proxy快照（串行限速）
        proxies = {}
        for proxy in PROXIES.get(symbol, []):
            time.sleep(0.4)
            try:
                proxies[proxy] = fetch_quote_snapshot(proxy)
            except Exception as exc:
                results.setdefault("errors", {})[proxy] = str(exc)
        results["proxies"] = proxies
        return results

    # ─── 非Yahoo组：全并行 ───
    def fetch_news_task():
        return fetch_news(spec["news"])

    def fetch_cftc_task():
        return extract_cftc_block(symbol)

    def fetch_eia_task():
        return eia_proxy(symbol)

    # 并行执行：Yahoo组(内部串行) + 其他组(各自独立)
    with ThreadPoolExecutor(max_workers=4) as pool:
        f_yahoo = pool.submit(fetch_yahoo_group)
        f_news = pool.submit(fetch_news_task)
        f_cftc = pool.submit(fetch_cftc_task)
        f_eia = pool.submit(fetch_eia_task) if symbol in {"CL", "NG"} else None

        # Yahoo结果
        try:
            yahoo_res = f_yahoo.result(timeout=60)
            data["daily_90d"] = yahoo_res["daily_90d"]
            data["hourly_10d"] = yahoo_res["hourly_10d"]
            data["proxies"] = yahoo_res["proxies"]
            data["source_status"]["yahoo_chart"] = "ok"
            for proxy in yahoo_res["proxies"]:
                data["source_status"][proxy] = "ok"
            for k, v in yahoo_res.get("errors", {}).items():
                data["errors"][k] = v
                data["source_status"][k] = "error"
        except Exception as exc:
            data["errors"]["yahoo"] = str(exc)
            data["source_status"]["yahoo_chart"] = "error"
            data["daily_90d"] = []
            data["hourly_10d"] = []

        # News结果
        try:
            data["news"] = f_news.result(timeout=30)
            data["source_status"]["google_news"] = "ok"
        except Exception as exc:
            data["errors"]["news"] = str(exc)
            data["source_status"]["google_news"] = "error"
            data["news"] = []

        # CFTC结果
        try:
            cftc = f_cftc.result(timeout=30)
            data["structured_drivers"]["cftc"] = cftc
            data["source_status"]["cftc"] = "ok" if cftc.get("found") else "missing"
        except Exception as exc:
            data["errors"]["cftc"] = str(exc)
            data["source_status"]["cftc"] = "error"

        # EIA结果
        if f_eia:
            try:
                eia = f_eia.result(timeout=30)
                if eia:
                    data["structured_drivers"]["eia"] = eia
                    data["source_status"]["eia"] = "ok" if eia.get("available") else "missing"
            except Exception as exc:
                data["errors"]["eia"] = str(exc)
                data["source_status"]["eia"] = "error"

    data["agg_4h_10d"] = aggregate_4h(data.get("hourly_10d", []))

    print(json.dumps(data, ensure_ascii=False, indent=None if args.compact else 2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
