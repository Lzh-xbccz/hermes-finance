#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from typing import Any, Dict, List


USER_AGENT = "Mozilla/5.0"

COMMON_ETFS = {"SPY", "QQQ", "IWM", "DIA", "XLE", "XLK", "XLF", "GLD", "TLT", "USO"}
COMMON_INDEX = {"^GSPC", "^IXIC", "^DJI", "^RUT", "^VIX"}
PROXIES = ["^VIX", "^TNX", "SPY", "QQQ", "IWM"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fetch US equity market data into JSON.")
    parser.add_argument("symbol", help="Ticker such as AAPL, SPY, ^GSPC")
    parser.add_argument("--compact", action="store_true")
    return parser.parse_args()


def fetch_json(url: str, retries: int = 3) -> Dict[str, Any]:
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=20) as resp:
                return json.load(resp)
        except urllib.request.HTTPError as e:
            if e.code == 429 and attempt < retries - 1:
                import time; time.sleep(2 ** attempt + 1)
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
                import time; time.sleep(2 ** attempt + 1)
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
    result = fetch_json(url)["chart"]["result"][0]
    meta = result.get("meta", {})
    quote = (result.get("indicators", {}).get("quote") or [{}])[0]
    rows = []
    for i, ts in enumerate(result.get("timestamp", []) or []):
        o = to_float((quote.get("open") or [None])[i] if i < len(quote.get("open") or []) else None)
        h = to_float((quote.get("high") or [None])[i] if i < len(quote.get("high") or []) else None)
        l = to_float((quote.get("low") or [None])[i] if i < len(quote.get("low") or []) else None)
        c = to_float((quote.get("close") or [None])[i] if i < len(quote.get("close") or []) else None)
        v = to_float((quote.get("volume") or [None])[i] if i < len(quote.get("volume") or []) else None)
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


def fetch_quote(ticker: str) -> Dict[str, Any]:
    rows = fetch_chart(ticker, "1d", "5d")["rows"]
    latest = rows[-1]
    prev = rows[-2] if len(rows) > 1 else latest
    return {
        "symbol": ticker,
        "price": latest["close"],
        "prev_close": prev["close"],
        "change_pct": ((latest["close"] - prev["close"]) / prev["close"] * 100) if prev["close"] else 0.0,
    }


def fetch_news(query: str, limit: int = 6) -> List[Dict[str, str]]:
    url = "https://news.google.com/rss/search?q=" + urllib.parse.quote(query) + "&hl=en-US&gl=US&ceid=US:en"
    root = ET.fromstring(fetch_text(url))
    out = []
    for item in root.findall("./channel/item")[:limit]:
        out.append({
            "title": item.findtext("title", "").strip(),
            "source": item.findtext("source", "").strip(),
            "pubDate": item.findtext("pubDate", "").strip(),
        })
    return out


def classify_company_events(news: List[Dict[str, str]]) -> Dict[str, Any]:
    events = []
    for item in news:
        title = item["title"].lower()
        if any(k in title for k in ["earnings", "results", "revenue", "profit", "guidance"]):
            events.append({"type": "earnings_proxy", "title": item["title"], "source": item["source"]})
        elif any(k in title for k in ["sec", "lawsuit", "probe", "antitrust", "regulator"]):
            events.append({"type": "regulatory_proxy", "title": item["title"], "source": item["source"]})
        elif any(k in title for k in ["launch", "ai", "chip", "iphone", "product"]):
            events.append({"type": "business_proxy", "title": item["title"], "source": item["source"]})
    return {"events": events[:5], "has_earnings_proxy": any(e["type"] == "earnings_proxy" for e in events)}


def nasdaq_earnings_page_status(symbol: str) -> Dict[str, Any]:
    url = f"https://www.nasdaq.com/market-activity/stocks/{symbol.lower()}/earnings"
    html = fetch_text(url)
    return {
        "source": url,
        "available": "earnings date" in html.lower() or "reported eps" in html.lower(),
        "has_reported_eps": "reported eps" in html.lower(),
    }


def instrument_type(symbol: str) -> str:
    if symbol in COMMON_INDEX or symbol.startswith("^"):
        return "index"
    if symbol in COMMON_ETFS:
        return "etf"
    return "stock"


def main() -> int:
    args = parse_args()
    symbol = args.symbol.strip().upper()
    chart = fetch_chart(symbol, "1d", "3mo")
    hourly = fetch_chart(symbol, "1h", "10d")
    data = {
        "analysis_time_utc": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M"),
        "symbol": symbol,
        "instrument_type": instrument_type(symbol),
        "meta": chart["meta"],
        "daily_90d": chart["rows"],
        "hourly_10d": hourly["rows"],
        "agg_4h_10d": aggregate_4h(hourly["rows"]),
        "news": fetch_news(symbol),
        "company_event_proxy": {},
        "proxies": {},
        "source_status": {"yahoo_chart": "ok", "google_news": "ok"},
        "errors": {},
    }
    if data["instrument_type"] == "stock":
        data["company_event_proxy"] = classify_company_events(data["news"])
        try:
            data["company_event_proxy"]["nasdaq_earnings_page"] = nasdaq_earnings_page_status(symbol)
        except Exception as exc:  # pragma: no cover
            data["errors"]["nasdaq_earnings_page"] = str(exc)
            data["source_status"]["nasdaq_earnings_page"] = "error"
        else:
            data["source_status"]["nasdaq_earnings_page"] = "ok" if data["company_event_proxy"]["nasdaq_earnings_page"].get("available") else "missing"
    for proxy in PROXIES:
        if proxy == symbol:
            continue
        try:
            data["proxies"][proxy] = fetch_quote(proxy)
        except Exception as exc:  # pragma: no cover
            data["errors"][proxy] = str(exc)
            data["source_status"][proxy] = "error"
        else:
            data["source_status"][proxy] = "ok"
    print(json.dumps(data, ensure_ascii=False, indent=None if args.compact else 2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
