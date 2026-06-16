#!/usr/bin/env python3
import json
import re
import sys


def classify(text: str) -> dict:
    s = (text or "").strip()
    u = s.upper()

    # A-shares
    if re.search(r"\b(SH|SZ)\d{6}\b", u) or re.search(r"\b(000|001|002|003|300|600|601|603|605|688)\d{3}\b", u):
        return {"market": "a_share", "reason": "matched A-share style code"}
    if any(k in s for k in ["A股", "上证", "深证", "创业板", "沪深", "科创板"]):
        return {"market": "a_share", "reason": "matched A-share keywords"}

    # Crypto
    crypto_tokens = [
        "BTC", "ETH", "SOL", "DOGE", "XRP", "BNB", "ADA", "AVAX", "CRYPTO", "比特币", "以太坊",
        "USDT", "USDC", "BINANCE", "BYBIT", "OKX"
    ]
    if any(t in u for t in crypto_tokens) or any(t in s for t in ["比特币", "以太坊", "山寨币", "合约资金费率"]):
        return {"market": "crypto", "reason": "matched crypto symbols/venue terms"}

    # Forex
    if re.search(r"\b[A-Z]{3}/?[A-Z]{3}\b", u):
        pair = re.search(r"\b([A-Z]{3})/?([A-Z]{3})\b", u)
        if pair and pair.group(1) != pair.group(2):
            majors = {"EUR", "USD", "JPY", "GBP", "CHF", "AUD", "NZD", "CAD", "CNH", "CNY"}
            if pair.group(1) in majors and pair.group(2) in majors:
                return {"market": "forex", "reason": "matched FX pair"}
    if any(k in s for k in ["外汇", "汇率", "美元指数", "非农", "欧元兑美元", "英镑兑美元", "美元兑日元"]):
        return {"market": "forex", "reason": "matched FX keywords"}

    # Futures
    futures_symbols = {
        "CL", "GC", "SI", "HG", "NG", "RB", "HO", "ZC", "ZS", "ZW",
        "ES", "NQ", "YM", "RTY", "MES", "MNQ", "MGC", "MCL"
    }
    if any(re.search(rf"\b{sym}\b", u) for sym in futures_symbols):
        return {"market": "futures", "reason": "matched common futures symbol"}
    if any(k in s for k in ["期货", "原油", "黄金", "白银", "铜", "天然气", "股指期货", "纳指期货", "标普期货"]):
        return {"market": "futures", "reason": "matched futures/commodity keywords"}

    # US equities / ETF / global indices
    if re.search(r"\b[A-Z]{1,5}\b", u):
        stock = re.search(r"\b([A-Z]{1,5})\b", u)
        if stock and stock.group(1) not in {"A", "AN", "THE", "AND"}:
            if stock.group(1) in {"SPY", "QQQ", "IWM", "DIA", "VOO", "AAPL", "MSFT", "NVDA", "TSLA", "AMZN", "META"}:
                return {"market": "us_equity", "reason": "matched common US ticker"}
    if any(k in s for k in ["美股", "纳指", "标普", "道指", "ETF", "个股", "苹果", "英伟达", "特斯拉"]):
        return {"market": "us_equity", "reason": "matched US equity/index keywords"}

    return {"market": "ambiguous", "reason": "no reliable market match"}


def main() -> int:
    text = " ".join(sys.argv[1:]).strip()
    if not text:
        print(json.dumps({"market": "ambiguous", "reason": "empty input"}))
        return 0
    print(json.dumps(classify(text), ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
