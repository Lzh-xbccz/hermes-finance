import json
import os
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Cache-Control": "no-cache, no-store, must-revalidate",
    "Pragma": "no-cache",
    "Expires": "0",
}
BJT = timezone(timedelta(hours=8))


def _bust_cache(url):
    import random, time as _time
    ts = f'{int(_time.time() * 1000)}_{random.randint(0, 9999)}'
    sep = '&' if '?' in url else '?'
    return f'{url}{sep}_nocache={ts}'


def fetch_text(url, encoding="utf-8", headers=None):
    url = _bust_cache(url)
    req = urllib.request.Request(url, headers=headers or HEADERS)
    with urllib.request.urlopen(req, timeout=20) as resp:
        return resp.read().decode(encoding, "ignore")


def fetch_json(url, encoding="utf-8", headers=None):
    return json.loads(fetch_text(url, encoding=encoding, headers=headers))


def parse_float(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def parse_int(value, default=0):
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default


def parse_sina_quote_line(line):
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


def fetch_sina_indices():
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


def fetch_sina_fx():
    url = "https://hq.sinajs.cn/list=USDCNY,USDCNH"
    text = fetch_text(url, encoding="gbk", headers={"Referer": "https://finance.sina.com.cn", **HEADERS})
    result = {}
    for code, line in zip(["USDCNY", "USDCNH"], text.splitlines()):
        line = line.strip()
        if not line or "=" not in line:
            continue
        raw = line.split("=", 1)[1].strip().strip(";").strip('"')
        if not raw:
            result[code] = {}
            continue
        parts = raw.split(",")
        # 该接口字段很短，保守只拿最稳定的几个
        result[code] = {
            "time": parts[0] if len(parts) > 0 else "",
            "bid": parse_float(parts[1]) if len(parts) > 1 else 0,
            "prev_close": parse_float(parts[2]) if len(parts) > 2 else 0,
            "open": parse_float(parts[3]) if len(parts) > 3 else 0,
            "high": parse_float(parts[4]) if len(parts) > 4 else 0,
            "low": parse_float(parts[5]) if len(parts) > 5 else 0,
            "last": parse_float(parts[8]) if len(parts) > 8 else 0,
            "name": parts[9] if len(parts) > 9 else code,
            "trade_date": parts[10] if len(parts) > 10 else "",
        }
    return result


def fetch_tencent_kline(code, limit=30):
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


def normalize_stock(raw):
    if not raw:
        raise ValueError("empty stock code")
    code = str(raw).strip().lower()
    if code.startswith(("sh", "sz")):
        exchange = code[:2]
        digits = code[2:]
    else:
        digits = code
        if digits[0] in {"6", "5", "9"}:
            exchange = "sh"
        elif digits[0] in {"0", "2", "3"}:
            exchange = "sz"
        else:
            raise ValueError(f"暂不支持自动识别该代码: {raw}；第一版仅支持 SH/SZ A 股")
    if not digits.isdigit():
        raise ValueError(f"无效股票代码: {raw}")
    secid = f"{1 if exchange == 'sh' else 0}.{digits}"
    return {
        "input": raw,
        "exchange": exchange,
        "code": digits,
        "tencent_code": f"{exchange}{digits}",
        "secid": secid,
    }


def fetch_stock_snapshot(secid):
    url = (
        "https://push2.eastmoney.com/api/qt/stock/get"
        f"?secid={secid}"
        "&fields=f57,f58,f43,f44,f45,f46,f47,f48,f60,f169,f170,f168,f50,f51,f52"
    )
    data = fetch_json(url).get("data", {})
    return {
        "code": data.get("f57"),
        "name": data.get("f58"),
        "current": parse_float(data.get("f43")) / 100,
        "high": parse_float(data.get("f44")) / 100,
        "low": parse_float(data.get("f45")) / 100,
        "open": parse_float(data.get("f46")) / 100,
        "volume_shou": parse_float(data.get("f47")),
        "amount_yuan": parse_float(data.get("f48")),
        "prev_close": parse_float(data.get("f60")) / 100,
        "change_abs": parse_float(data.get("f169")) / 100,
        "change_pct": parse_float(data.get("f170")) / 100,
        "turnover_rate_pct": parse_float(data.get("f168")) / 100,
        "volume_ratio": parse_float(data.get("f50")) / 100 if data.get("f50") is not None else 0,
        "limit_up": parse_float(data.get("f51")) / 100 if data.get("f51") is not None else 0,
        "limit_down": parse_float(data.get("f52")) / 100 if data.get("f52") is not None else 0,
    }


def fetch_eastmoney_northbound():
    root = "https://push2.eastmoney.com/"
    jme = fetch_json(
        root + "api/qt/kamtbs.rtmin/get?fields1=f1,f2,f3,f4&fields2=f51,f54,f52,f58,f53,f62,f56,f57,f60,f61&ut=b2884a393a59ad64002292a3e90d46a5"
    )
    zjl = fetch_json(
        root + "api/qt/kamt.rtmin/get?fields1=f1,f2,f3,f4&fields2=f51,f52,f53,f54,f55,f56&ut=b2884a393a59ad64002292a3e90d46a5"
    )

    def parse_jme_row(row):
        parts = row.split(",")
        if len(parts) < 10:
            return {"raw": row}
        return {
            "time": parts[0],
            "hgt_net_buy_yi_guess": parse_float(parts[1]),
            "hgt_buy_yi_guess": parse_float(parts[2]),
            "sgt_net_buy_yi_guess": parse_float(parts[3]),
            "hgt_sell_yi_guess": parse_float(parts[4]),
            "north_total_net_buy_yi_guess": parse_float(parts[5]),
            "sgt_buy_yi_guess": parse_float(parts[6]),
            "sgt_sell_yi_guess": parse_float(parts[7]),
            "north_total_buy_yi_guess": parse_float(parts[8]),
            "north_total_sell_yi_guess": parse_float(parts[9]),
        }

    def parse_zjl_row(row):
        parts = row.split(",")
        if len(parts) < 6:
            return {"raw": row}
        return {
            "time": parts[0],
            "hgt_net_inflow_wan": parse_float(parts[1]),
            "hgt_balance_wan": parse_float(parts[2]),
            "sgt_net_inflow_wan": parse_float(parts[3]),
            "sgt_balance_wan": parse_float(parts[4]),
            "north_total_net_inflow_wan": parse_float(parts[5]),
        }

    jme_rows = jme.get("data", {}).get("s2n", [])
    zjl_rows = zjl.get("data", {}).get("s2n", [])
    return {
        "latest_jme": parse_jme_row(jme_rows[-1]) if jme_rows else {},
        "latest_balance": parse_zjl_row(zjl_rows[-1]) if zjl_rows else {},
        "timeline_jme_tail": [parse_jme_row(x) for x in jme_rows[-10:]],
        "timeline_balance_tail": [parse_zjl_row(x) for x in zjl_rows[-10:]],
    }


def fetch_eastmoney_breadth():
    url = (
        "https://push2.eastmoney.com/api/qt/ulist.np/get"
        "?fltt=2&secids=1.000001,0.399001,0.399006"
        "&fields=f1,f2,f3,f4,f6,f12,f13,f104,f105,f106"
        "&ut=b2884a393a59ad64002292a3e90d46a5"
    )
    data = fetch_json(url).get("data", {}).get("diff", [])
    mapping = {}
    for item in data:
        key = f"{item.get('f13')}.{item.get('f12')}"
        mapping[key] = {
            "latest": parse_float(item.get("f2")),
            "change_pct": parse_float(item.get("f3")),
            "change_abs": parse_float(item.get("f4")),
            "amount_yuan": parse_float(item.get("f6")),
            "up_count": parse_int(item.get("f104")),
            "down_count": parse_int(item.get("f105")),
            "flat_count": parse_int(item.get("f106")),
        }
    return mapping


def fetch_eastmoney_board_flow(name, fs, limit=10):
    url = (
        "https://push2.eastmoney.com/api/qt/clist/get"
        f"?pn=1&pz={limit}&po=1&np=1&fltt=2&invt=2&fid=f62"
        f"&fs={urllib.parse.quote(fs, safe=':')}"
        "&fields=f12,f14,f2,f3,f62,f184,f104,f105,f128,f136,f140,f141"
    )
    diff = fetch_json(url).get("data", {}).get("diff", [])
    rows = []
    for item in diff:
        rows.append({
            "board_code": item.get("f12"),
            "board_name": item.get("f14"),
            "latest": parse_float(item.get("f2")),
            "change_pct": parse_float(item.get("f3")),
            "main_net_inflow_yuan": parse_float(item.get("f62")),
            "net_ratio_guess": parse_float(item.get("f184")),
            "up_count": parse_int(item.get("f104")),
            "down_count": parse_int(item.get("f105")),
            "leader_name": item.get("f128"),
            "leader_change_pct": parse_float(item.get("f136")),
            "leader_code": item.get("f140"),
            "leader_market": item.get("f141"),
        })
    return {"name": name, "fs": fs, "rows": rows}


def parse_fflow_line(line):
    parts = line.split(",")
    if len(parts) == 6:
        return {
            "time": parts[0],
            "main_net_yuan": parse_float(parts[1]),
            "super_large_net_yuan": parse_float(parts[2]),
            "large_net_yuan": parse_float(parts[3]),
            "medium_net_yuan": parse_float(parts[4]),
            "small_net_yuan": parse_float(parts[5]),
        }
    if len(parts) < 12:
        return {"raw": line}
    return {
        "time": parts[0],
        "main_net_yuan": parse_float(parts[1]),
        "super_large_net_yuan": parse_float(parts[2]),
        "large_net_yuan": parse_float(parts[3]),
        "medium_net_yuan": parse_float(parts[4]),
        "small_net_yuan": parse_float(parts[5]),
        "main_net_pct": parse_float(parts[6]),
        "super_large_pct": parse_float(parts[7]),
        "large_pct": parse_float(parts[8]),
        "medium_pct": parse_float(parts[9]),
        "small_pct": parse_float(parts[10]),
        "close": parse_float(parts[11]),
        "change_pct": parse_float(parts[12]) if len(parts) > 12 else 0,
    }


def fetch_eastmoney_fflow(secid, intraday_tail=20, daily_tail=20):
    intraday_url = (
        "https://push2.eastmoney.com/api/qt/stock/fflow/kline/get"
        f"?secid={secid}&lmt=0&klt=1&fields1=f1,f2,f3,f7"
        "&fields2=f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61,f62,f63,f64,f65"
        "&ut=b2884a393a59ad64002292a3e90d46a5"
    )
    daily_url = (
        "https://push2his.eastmoney.com/api/qt/stock/fflow/daykline/get"
        f"?secid={secid}&lmt=30&klt=101&fields1=f1,f2,f3,f7"
        "&fields2=f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61,f62,f63,f64,f65"
        "&ut=b2884a393a59ad64002292a3e90d46a5"
    )
    intraday = fetch_json(intraday_url).get("data", {}).get("klines", [])
    daily = fetch_json(daily_url).get("data", {}).get("klines", [])
    return {
        "intraday_tail": [parse_fflow_line(x) for x in intraday[-intraday_tail:]],
        "daily_tail": [parse_fflow_line(x) for x in daily[-daily_tail:]],
    }


def fetch_yahoo_meta(symbol):
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=1d&range=5d"
    data = fetch_json(url).get("chart", {}).get("result", [{}])[0].get("meta", {})
    return {
        "current": parse_float(data.get("regularMarketPrice")),
        "prev_close": parse_float(data.get("chartPreviousClose")),
    }


def fetch_stooq_meta(symbol):
    mapping = {
        "^GSPC": "^spx",
        "^IXIC": "^ndq",
        "^DJI": "^dji",
        "^VIX": "^vix",
    }
    code = mapping[symbol]
    text = fetch_text(f"https://stooq.com/q/l/?s={urllib.parse.quote(code)}&i=d")
    parts = text.strip().split(",")
    if len(parts) < 7 or parts[1] == "N/D":
        return {"current": 0.0, "prev_close": 0.0}
    open_p = parse_float(parts[3])
    close_p = parse_float(parts[6])
    return {"current": close_p, "prev_close": open_p}


def fetch_google_news():
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


def fetch_tencent_stock_snapshot(code):
    text = fetch_text(f"https://qt.gtimg.cn/q={code}", encoding="gbk")
    raw = text.split("=", 1)[1].strip().strip(";").strip('"')
    parts = raw.split("~")
    if len(parts) < 6:
        return {}
    current = parse_float(parts[3])
    prev_close = parse_float(parts[4])
    open_p = parse_float(parts[5]) if len(parts) > 5 else 0
    return {
        "current": current,
        "prev_close": prev_close,
        "open": open_p,
        "high": parse_float(parts[33]) if len(parts) > 33 else 0,
        "low": parse_float(parts[34]) if len(parts) > 34 else 0,
        "change_pct": ((current - prev_close) / prev_close * 100) if prev_close else 0,
    }


def fetch_stock_bundle(raw_stock):
    stock = normalize_stock(raw_stock)
    try:
        stock["snapshot"] = fetch_stock_snapshot(stock["secid"])
    except Exception:
        stock["snapshot"] = fetch_tencent_stock_snapshot(stock["tencent_code"])
    stock["history_daily"] = fetch_tencent_kline(stock["tencent_code"], limit=30)["rows"]
    try:
        stock["capital_flow"] = fetch_eastmoney_fflow(stock["secid"])
    except Exception:
        stock["capital_flow"] = {"intraday_tail": [], "daily_tail": []}
    return stock


def collect(target, key, default, func):
    try:
        target[key] = func()
    except Exception as exc:
        target["errors"][key] = f"{type(exc).__name__}: {exc}"
        target[key] = default


def main():
    now_utc = datetime.now(timezone.utc)
    now_bjt = datetime.now(BJT)
    wanted = {x.strip() for x in os.environ.get("A_SHARE_SECTIONS", "all").split(",") if x.strip()}
    want_all = not wanted or "all" in wanted
    stock_code = os.environ.get("A_SHARE_STOCK", "").strip()

    def enabled(name):
        return want_all or name in wanted

    out = {
        "fetched_at_utc": now_utc.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "fetched_at_bjt": now_bjt.strftime("%Y-%m-%dT%H:%M:%S+08:00"),
        "requested_sections": sorted(wanted) if wanted else ["all"],
        "errors": {},
        "availability": {
            "eastmoney_push2": True,
            "eastmoney_pages": True,
            "xueqiu": False,
            "10jqka": False,
        },
    }

    tencent_sh = {"rows": [], "market_state": {}, "qt": [], "market_raw": ""}
    if enabled("market_state") or enabled("indices") or enabled("all"):
        collect(out, "tencent_sh", tencent_sh, lambda: fetch_tencent_kline("sh000001", limit=30))
        out["market_state"] = out["tencent_sh"].get("market_state", {})
    else:
        out["tencent_sh"] = tencent_sh
        out["market_state"] = {}

    if enabled("indices") or enabled("all"):
        collect(out, "indices_snapshot", {}, fetch_sina_indices)
        collect(
            out,
            "indices_history_daily",
            {"sh000001": [], "sz399001": [], "sz399006": []},
            lambda: {
                "sh000001": out["tencent_sh"]["rows"],
                "sz399001": fetch_tencent_kline("sz399001", limit=30)["rows"],
                "sz399006": fetch_tencent_kline("sz399006", limit=30)["rows"],
            },
        )
        collect(out, "fx", {}, fetch_sina_fx)

    if enabled("northbound") or enabled("all"):
        collect(out, "northbound", {}, fetch_eastmoney_northbound)

    if enabled("breadth") or enabled("all"):
        collect(out, "breadth", {}, fetch_eastmoney_breadth)

    if enabled("boards") or enabled("all"):
        collect(
            out,
            "board_flows",
            {"industry": {}, "concept": {}, "region": {}},
            lambda: {
                "industry": fetch_eastmoney_board_flow("industry", "m:90+s:4", limit=10),
                "concept": fetch_eastmoney_board_flow("concept", "m:90+t:3", limit=10),
                "region": fetch_eastmoney_board_flow("region", "m:90+t:1", limit=10),
            },
        )

    if enabled("capital_flow") or enabled("all"):
        collect(
            out,
            "capital_flow",
            {"1.000001": {}, "0.399001": {}, "0.399006": {}},
            lambda: {
                "1.000001": fetch_eastmoney_fflow("1.000001"),
                "0.399001": fetch_eastmoney_fflow("0.399001"),
                "0.399006": fetch_eastmoney_fflow("0.399006"),
            },
        )

    if enabled("macro") or enabled("all"):
        def macro_bundle():
            out_macro = {}
            for sym in ["^GSPC", "^IXIC", "^DJI", "^VIX"]:
                try:
                    out_macro[sym] = fetch_yahoo_meta(sym)
                except Exception:
                    out_macro[sym] = fetch_stooq_meta(sym)
            return out_macro

        collect(out, "macro", {}, macro_bundle)

    if enabled("news") or enabled("all"):
        try:
            out["news"] = fetch_google_news()
        except Exception as exc:
            out["errors"]["news"] = f"{type(exc).__name__}: {exc}"
            out["news"] = []

    if stock_code and (enabled("stock") or enabled("all")):
        collect(out, "stock", {}, lambda: fetch_stock_bundle(stock_code))

    print(json.dumps(out, ensure_ascii=False))


main()
