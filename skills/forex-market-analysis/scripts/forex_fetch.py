#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List


USER_AGENT = "Mozilla/5.0"

SYMBOL_MAP = {
    "EURUSD": {"ticker": "EURUSD=X", "label": "EUR/USD", "query": "EURUSD"},
    "USDJPY": {"ticker": "JPY=X", "label": "USD/JPY", "query": "USDJPY"},
    "GBPUSD": {"ticker": "GBPUSD=X", "label": "GBP/USD", "query": "GBPUSD"},
    "AUDUSD": {"ticker": "AUDUSD=X", "label": "AUD/USD", "query": "AUDUSD"},
    "USDCHF": {"ticker": "CHF=X", "label": "USD/CHF", "query": "USDCHF"},
    "USDCNH": {"ticker": "CNH=X", "label": "USD/CNH", "query": "USDCNH"},
    "DXY": {"ticker": "DX-Y.NYB", "label": "Dollar Index", "query": "DXY"},
}

PROXIES = {
    "EURUSD": ["DX-Y.NYB", "^TNX", "^VIX"],
    "USDJPY": ["DX-Y.NYB", "^TNX", "^VIX"],
    "GBPUSD": ["DX-Y.NYB", "^TNX", "^VIX"],
    "AUDUSD": ["DX-Y.NYB", "^TNX", "^VIX"],
    "USDCHF": ["DX-Y.NYB", "^TNX", "^VIX"],
    "USDCNH": ["DX-Y.NYB", "^TNX", "^VIX"],
    "DXY": ["^TNX", "^VIX", "EURUSD=X"],
}

CFTC_FINANCIAL_MARKETS = {
    "EURUSD": "EURO FX",
    "USDJPY": "JAPANESE YEN",
    "GBPUSD": "BRITISH POUND STERLING",
    "AUDUSD": "AUSTRALIAN DOLLAR",
    "USDCHF": "SWISS FRANC",
    "USDCNH": "CHINESE RENMINBI",
    "DXY": "U.S. DOLLAR INDEX",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fetch FX market data into JSON.")
    parser.add_argument("symbol", help="FX symbol such as EURUSD, USDJPY, DXY")
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


def fetch_chart(ticker: str, interval: str, range_: str) -> List[Dict[str, Any]]:
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{urllib.parse.quote(ticker)}?interval={interval}&range={range_}"
    result = fetch_json(url)["chart"]["result"][0]
    quote = (result.get("indicators", {}).get("quote") or [{}])[0]
    rows = []
    for i, ts in enumerate(result.get("timestamp", []) or []):
        o = to_float((quote.get("open") or [None])[i] if i < len(quote.get("open") or []) else None)
        h = to_float((quote.get("high") or [None])[i] if i < len(quote.get("high") or []) else None)
        l = to_float((quote.get("low") or [None])[i] if i < len(quote.get("low") or []) else None)
        c = to_float((quote.get("close") or [None])[i] if i < len(quote.get("close") or []) else None)
        if None in {o, h, l, c}:
            continue
        rows.append({
            "ts": ts,
            "time_utc": datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d %H:%M"),
            "open": o,
            "high": h,
            "low": l,
            "close": c,
        })
    return rows


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
        })
    return out


def fetch_quote(ticker: str) -> Dict[str, Any]:
    rows = fetch_chart(ticker, "1d", "5d")
    latest = rows[-1]
    prev = rows[-2] if len(rows) > 1 else rows[-1]
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


def fetch_macro_events(symbol: str, limit: int = 6) -> List[Dict[str, str]]:
    root = ET.fromstring(fetch_text("https://nfs.faireconomy.media/ff_calendar_thisweek.xml"))
    keywords = {
        "EURUSD": ["EUR", "USD", "ECB", "Fed"],
        "USDJPY": ["USD", "JPY", "BoJ", "Fed"],
        "GBPUSD": ["GBP", "USD", "BoE", "Fed"],
        "AUDUSD": ["AUD", "USD", "RBA", "Fed"],
        "USDCHF": ["USD", "CHF", "SNB", "Fed"],
        "USDCNH": ["USD", "CNY", "CNH", "PBOC", "Fed"],
        "DXY": ["USD", "Fed"],
    }[symbol]
    out = []
    for item in root.findall("./event"):
        title = (item.findtext("title") or "").strip()
        country = (item.findtext("country") or "").strip()
        impact = (item.findtext("impact") or "").strip()
        date = (item.findtext("date") or "").strip()
        if any(k.lower() in title.lower() or k.lower() == country.lower() for k in keywords):
            out.append({"title": title, "country": country, "impact": impact, "date": date, "time": (item.findtext("time") or "").strip()})
    return out[:limit]


def upcoming_macro_events(events: List[Dict[str, str]], horizon_hours: int = 48, limit: int = 5) -> List[Dict[str, str]]:
    now = datetime.now(timezone.utc)
    scored = []
    for event in events:
        dt = parse_event_datetime(event.get("date", ""), event.get("time", ""))
        impact = event.get("impact", "")
        score = {"High": 3, "Medium": 2, "Low": 1}.get(impact, 0)
        if dt is None:
            scored.append((999999, -score, event))
            continue
        delta_hours = (dt - now).total_seconds() / 3600
        if delta_hours < -12 or delta_hours > horizon_hours:
            continue
        scored.append((abs(delta_hours), -score, {**event, "delta_hours": f"{delta_hours:+.1f}h"}))
    scored.sort(key=lambda x: (x[0], x[1]))
    return [event for _, _, event in scored[:limit]]


def parse_event_datetime(date_str: str, time_str: str) -> datetime | None:
    if not date_str or not time_str:
        return None
    ts = time_str.strip().lower()
    if ts in {"all day", "tentative"}:
        return None
    try:
        dt = datetime.strptime(f"{date_str} {time_str}", "%m-%d-%Y %I:%M%p")
        return dt.replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def extract_cftc_financial(symbol: str) -> Dict[str, Any]:
    market = CFTC_FINANCIAL_MARKETS.get(symbol)
    if not market:
        return {}
    url = "https://www.cftc.gov/dea/options/financial_lof.htm"
    html = fetch_text(url)
    idx = html.upper().find(market.upper())
    if idx < 0:
        return {"source": url, "market": market, "found": False}
    block = html[idx:idx + 1800]
    lines = [ln.strip() for ln in block.splitlines() if ln.strip()]
    oi_line = next((ln for ln in lines if "Open Interest is" in ln), "")
    pos_idx = next((i for i, ln in enumerate(lines) if ln == "Positions"), -1)
    pos_line = lines[pos_idx + 1] if pos_idx >= 0 and pos_idx + 1 < len(lines) else ""
    oi_match = re.search(r"Open Interest is\s*([\d,]+)", oi_line, re.I)
    row = [int(x.replace(",", "")) for x in re.findall(r"\d[\d,]*", pos_line)]
    out = {"source": url, "market": market, "found": True, "report_type": "financial_lof", "raw_excerpt": block[:900]}
    if oi_match:
        out["open_interest"] = int(oi_match.group(1).replace(",", ""))
    if len(row) >= 14:
        keys = [
            "dealer_long", "dealer_short", "dealer_spread",
            "asset_mgr_long", "asset_mgr_short", "asset_mgr_spread",
            "leveraged_long", "leveraged_short", "leveraged_spread",
            "other_long", "other_short", "other_spread",
            "nonreportable_long", "nonreportable_short",
        ]
        out.update(dict(zip(keys, row[:14])))
    return out


def main() -> int:
    args = parse_args()
    symbol = args.symbol.strip().replace("/", "").upper()
    if symbol not in SYMBOL_MAP:
        raise SystemExit(f"Unsupported FX symbol: {symbol}")
    spec = SYMBOL_MAP[symbol]
    data = {
        "analysis_time_utc": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M"),
        "symbol": symbol,
        "ticker": spec["ticker"],
        "label": spec["label"],
        "daily_90d": fetch_chart(spec["ticker"], "1d", "3mo"),
        "hourly_10d": fetch_chart(spec["ticker"], "1h", "10d"),
        "news": fetch_news(spec["query"]),
        "macro_events": [],
        "upcoming_macro_events": [],
        "structured_drivers": {},
        "proxies": {},
        "source_status": {"yahoo_chart": "ok", "google_news": "ok"},
        "errors": {},
    }
    try:
        data["macro_events"] = fetch_macro_events(symbol)
        data["upcoming_macro_events"] = upcoming_macro_events(data["macro_events"])
    except Exception as exc:  # pragma: no cover
        data["errors"]["macro_events"] = str(exc)
        data["source_status"]["macro_events"] = "error"
    else:
        data["source_status"]["macro_events"] = "ok" if data["macro_events"] else "empty"
    data["agg_4h_10d"] = aggregate_4h(data["hourly_10d"])
    for proxy in PROXIES.get(symbol, []):
        try:
            data["proxies"][proxy] = fetch_quote(proxy)
        except Exception as exc:  # pragma: no cover
            data["errors"][proxy] = str(exc)
            data["source_status"][proxy] = "error"
        else:
            data["source_status"][proxy] = "ok"
    try:
        data["structured_drivers"]["cftc"] = extract_cftc_financial(symbol)
    except Exception as exc:  # pragma: no cover
        data["errors"]["cftc"] = str(exc)
        data["source_status"]["cftc"] = "error"
    else:
        data["source_status"]["cftc"] = "ok" if data["structured_drivers"].get("cftc", {}).get("found") else "missing"
    print(json.dumps(data, ensure_ascii=False, indent=None if args.compact else 2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
