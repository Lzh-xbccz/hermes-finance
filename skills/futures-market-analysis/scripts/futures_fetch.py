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

# ── 禁用缓存：确保每次拉到的都是最新数据 ──
_NO_CACHE_HEADERS = {
    "User-Agent": USER_AGENT,
    "Cache-Control": "no-cache, no-store, must-revalidate",
    "Pragma": "no-cache",
    "Expires": "0",
}


def _bust_cache(url: str) -> str:
    import random
    ts = f'{int(time.time() * 1000)}_{random.randint(0, 9999)}'
    sep = '&' if '?' in url else '?'
    return f'{url}{sep}_nocache={ts}'

# ── 全局 Yahoo Finance 速率限制 ──
_YF_LAST_CALL = 0.0
_YF_MIN_INTERVAL = 0.5


def _yf_throttle():
    global _YF_LAST_CALL
    import time as _time
    now = _time.monotonic()
    wait = _YF_LAST_CALL + _YF_MIN_INTERVAL - now
    if wait > 0:
        _time.sleep(wait)
    _YF_LAST_CALL = _time.monotonic()

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
    url = _bust_cache(url)
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers=_NO_CACHE_HEADERS)
            with urllib.request.urlopen(req, timeout=20) as resp:
                return json.load(resp)
        except urllib.request.HTTPError as e:
            if e.code == 429 and attempt < retries - 1:
                time.sleep(2 ** attempt + 1)
                continue
            raise


def fetch_text(url: str, retries: int = 3) -> str:
    url = _bust_cache(url)
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers=_NO_CACHE_HEADERS)
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
    _yf_throttle()
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


def _cftc_from_csv(url: str, market_name: str) -> Dict[str, Any] | None:
    """从 CFTC 年度 ZIP/CSV 提取数据 — 比 HTML 爬虫可靠得多。
    
    CSV 列: Market_and_Exchange_Names, Report_Date_as_YYYY-MM-DD,
    Open_Interest_All, NonComm_Positions_Long_All, NonComm_Positions_Short_All,
    Comm_Positions_Long_All, Comm_Positions_Short_All, ...
    """
    import io, zipfile
    from datetime import datetime as dt
    try:
        resp = urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": USER_AGENT}), timeout=30)
        zf = zipfile.ZipFile(io.BytesIO(resp.read()))
        # 取最新的 CSV 文件（通常只有一个）
        csv_names = [n for n in zf.namelist() if n.endswith('.csv') or n.endswith('.txt')]
        if not csv_names:
            return None
        # 按年份取最新的
        csv_name = sorted(csv_names)[-1]
        csv_data = zf.read(csv_name).decode('utf-8', 'ignore')
    except Exception:
        return None
    
    lines = csv_data.splitlines()
    if len(lines) < 2:
        return None
    header = lines[0].split(',')
    # 找目标市场行
    for line in lines[1:]:
        if market_name.upper() not in line.upper():
            continue
        cols = line.split(',')
        if len(cols) < 15:
            continue
        try:
            col = lambda name: cols[header.index(name)] if name in header else None
            oi = col('Open_Interest_All')
            nc_long = col('NonComm_Positions_Long_All')
            nc_short = col('NonComm_Positions_Short_All')
            c_long = col('Comm_Positions_Long_All')
            c_short = col('Comm_Positions_Short_All')
            report_date = col('Report_Date_as_YYYY-MM-DD')
            out = {
                "source": url, "market": market_name, "found": True,
                "method": "csv", "report_date": report_date,
                "open_interest": int(float(oi)) if oi else None,
                "non_commercial_long": int(float(nc_long)) if nc_long else None,
                "non_commercial_short": int(float(nc_short)) if nc_short else None,
                "commercial_long": int(float(c_long)) if c_long else None,
                "commercial_short": int(float(c_short)) if c_short else None,
            }
            if out["non_commercial_long"] and out["non_commercial_short"]:
                out["non_commercial_net"] = out["non_commercial_long"] - out["non_commercial_short"]
            if out["commercial_long"] and out["commercial_short"]:
                out["commercial_net"] = out["commercial_long"] - out["commercial_short"]
            # 位置信号
            if out["non_commercial_long"] and out["non_commercial_short"]:
                ratio = out["non_commercial_long"] / max(out["non_commercial_short"], 1)
                if ratio > 3: out["position_signal"] = "🟢 投机极度看多"
                elif ratio > 2: out["position_signal"] = "🟢 投机偏多"
                elif ratio < 0.33: out["position_signal"] = "🔴 投机极度看空"
                elif ratio < 0.5: out["position_signal"] = "🔴 投机偏空"
                else: out["position_signal"] = "⚪ 中性"
            return out
        except (ValueError, IndexError):
            continue
    return None


def extract_cftc_block(symbol: str) -> Dict[str, Any]:
    spec = CFTC_FUTURES_MARKETS.get(symbol)
    if not spec:
        return {}
    url, market = spec
    
    # ── 优先：结构化 CSV（年度 ZIP）──
    year = datetime.now().year
    csv_url = f"https://www.cftc.gov/files/dea/history/fut_disagg_txt_{year}.zip"
    csv_result = _cftc_from_csv(csv_url, market)
    if csv_result:
        return csv_result
    # 试试上一年（年初可能还没更新）
    csv_result = _cftc_from_csv(f"https://www.cftc.gov/files/dea/history/fut_disagg_txt_{year-1}.zip", market)
    if csv_result:
        csv_result["note"] = f"使用 {year-1} 年数据（{year} 年 ZIP 尚未发布）"
        return csv_result
    
    # ── 降级：HTML 爬虫 ──
    try:
        html = fetch_text(url)
    except Exception:
        return {"source": url, "market": market, "found": False, "error": "fetch failed", "method": "html_fallback"}
    idx = html.upper().find(market.upper())
    if idx < 0:
        return {"source": url, "market": market, "found": False, "error": "market not in page", "method": "html_fallback"}
    block = html[idx:idx + 3000]
    out = {"source": url, "market": market, "found": True, "method": "html_fallback"}
    
    lines = [ln.strip() for ln in block.splitlines() if ln.strip()]
    oi_line = ""
    for pattern in ["OPEN INTEREST:", "OPENINTEREST:", "Open interest is", "Open Interest:"]:
        oi_line = next((ln for ln in lines if pattern.upper() in ln.upper()), "")
        if oi_line:
            break
    oi_match = re.search(r"[\d,]{4,}", oi_line) if oi_line else None
    if oi_match:
        out["open_interest"] = int(oi_match.group(0).replace(",", ""))
    
    commit_idx = -1
    for marker in ["COMMITMENTS", "Commitments", "Positions", "POSITIONS"]:
        commit_idx = next((i for i, ln in enumerate(lines) if ln.upper() == marker.upper()), -1)
        if commit_idx >= 0:
            break
    if commit_idx < 0:
        commit_idx = next((i for i, ln in enumerate(lines) if "LONG" in ln.upper() and "SHORT" in ln.upper()), -1)
    
    nums_line = lines[commit_idx + 1] if commit_idx >= 0 and commit_idx + 1 < len(lines) else ""
    row = [int(x.replace(",", "")) for x in re.findall(r"\d[\d,]*", nums_line)]
    
    if len(row) >= 8:
        out["non_commercial_long"] = row[0]
        out["non_commercial_short"] = row[1]
        out["commercial_long"] = row[3]
        out["commercial_short"] = row[4]
        out["non_commercial_net"] = row[0] - row[1]
        out["commercial_net"] = row[3] - row[4]
    elif len(row) >= 4:
        out["non_commercial_long"] = row[0]
        out["non_commercial_short"] = row[1]
        out["non_commercial_net"] = row[0] - row[1]
    else:
        out["parse_warning"] = f"expected >=8 cols, got {len(row)}"
    
    nc_long = out.get("non_commercial_long", 0)
    nc_short = out.get("non_commercial_short", 0)
    if nc_long > 0 and nc_short > 0:
        ratio = nc_long / max(nc_short, 1)
        if ratio > 3: out["position_signal"] = "🟢 投机极度看多"
        elif ratio > 2: out["position_signal"] = "🟢 投机偏多"
        elif ratio < 0.33: out["position_signal"] = "🔴 投机极度看空"
        elif ratio < 0.5: out["position_signal"] = "🔴 投机偏空"
        else: out["position_signal"] = "⚪ 中性"
    
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
