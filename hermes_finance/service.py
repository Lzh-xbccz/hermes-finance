"""Shared service layer for finance data and analysis."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from .paths import PROJECT_ROOT, project_path
from .routing import classify, normalize_market
from .runner import parse_json_output, run_python_script


MARKET_SCRIPT = {
    "crypto": project_path("skills", "crypto-market-analysis", "scripts", "fetch_data.py"),
    "a_share": project_path("skills", "a-share-market-analysis", "scripts", "a_share_fetch.py"),
    "futures": project_path("skills", "futures-market-analysis", "scripts", "futures_fetch.py"),
    "forex": project_path("skills", "forex-market-analysis", "scripts", "forex_fetch.py"),
    "us_equity": project_path("skills", "us-equity-market-analysis", "scripts", "us_equity_fetch.py"),
}

COIN_SYMBOL_ALIASES = {
    "bitcoin": "BTC",
    "btc": "BTC",
    "ethereum": "ETH",
    "ether": "ETH",
    "eth": "ETH",
    "solana": "SOL",
    "sol": "SOL",
    "binancecoin": "BNB",
    "bnb": "BNB",
    "ripple": "XRP",
    "xrp": "XRP",
    "cardano": "ADA",
    "ada": "ADA",
    "dogecoin": "DOGE",
    "doge": "DOGE",
    "chainlink": "LINK",
    "link": "LINK",
    "avalanche-2": "AVAX",
    "avalanche": "AVAX",
    "avax": "AVAX",
    "polkadot": "DOT",
    "dot": "DOT",
    "litecoin": "LTC",
    "ltc": "LTC",
    "tron": "TRX",
    "trx": "TRX",
    "toncoin": "TON",
    "ton": "TON",
    "sui": "SUI",
}

FUTURES_SYMBOL_ALIASES = {
    "CLUSDT": "CL",
    "BZUSDT": "BZ",
    "XAUUSDT": "GC",
    "XAGUSDT": "SI",
    "COPPERUSDT": "HG",
    "NATGASUSDT": "NG",
    "XPTUSDT": "PL",
    "XPDUSDT": "PA",
}


def route_market(text: str) -> dict[str, Any]:
    """Route text or a symbol to a market id."""

    result = classify(text)
    result["input"] = text
    return result


def crypto_pair_symbol(symbol: str, quote: str = "USDT") -> str:
    """Normalize a crypto coin id or ticker into an exchange pair."""

    key = symbol.strip().lower()
    if key.endswith(quote.lower()):
        return key.upper()
    base = COIN_SYMBOL_ALIASES.get(key, symbol.strip().upper())
    return f"{base}{quote}"


def futures_symbol(symbol: str) -> str:
    """Normalize a futures shorthand or Binance TradFi perpetual into the internal root."""

    key = symbol.strip().upper().replace("/", "")
    return FUTURES_SYMBOL_ALIASES.get(key, key)


def fetch_market_data(
    market: str,
    symbol: str | None = None,
    *,
    blocks: str = "all",
    stock: str | None = None,
    remote: str | None = None,
    timeout: int = 180,
) -> dict[str, Any]:
    """Fetch market data through the existing collector scripts."""

    normalized = normalize_market(market)
    if normalized == "ambiguous":
        routed = route_market(symbol or stock or "")
        normalized = routed["market"]
    else:
        routed = {"market": normalized, "reason": "explicit market"}

    if normalized not in MARKET_SCRIPT:
        return {
            "ok": False,
            "market": normalized,
            "symbol": symbol or stock,
            "route": routed,
            "error": "ambiguous_market",
            "message": "market is ambiguous; pass an explicit market or clearer symbol",
        }

    script = MARKET_SCRIPT[normalized]
    collector_symbol = futures_symbol(symbol) if normalized == "futures" and symbol else symbol
    args = _collector_args(normalized, symbol=collector_symbol, blocks=blocks, stock=stock, remote=remote)
    result = run_python_script(script, args, timeout=timeout)
    data = parse_json_output(result["stdout"])

    return {
        "ok": result["ok"],
        "market": normalized,
        "symbol": _display_symbol(normalized, symbol=collector_symbol, stock=stock),
        "requested_symbol": symbol,
        "route": routed,
        "collector": str(script.relative_to(PROJECT_ROOT)),
        "command": result["command"],
        "returncode": result["returncode"],
        "data": data,
        "output_text": "" if data is not None else result["stdout"],
        "stderr": result["stderr"],
        "error": result["error"],
    }


def czsc_analyze(
    symbol: str,
    *,
    freqs: str | list[str] = "4h,15m",
    chart: bool = False,
    report: bool = True,
    timeout: int = 240,
) -> dict[str, Any]:
    """Run the CZSC multi-frequency analyzer."""

    freq_arg = ",".join(freqs) if isinstance(freqs, list) else freqs
    args = [symbol.upper().replace("/", ""), "--freqs", freq_arg]
    if chart:
        args.append("--chart")
    if report:
        args.append("--report")
    result = run_python_script(project_path("scripts", "czsc_analyze.py"), args, timeout=timeout)
    report_path = _extract_report_path(result["stdout"])
    report_text = _read_report(report_path)
    return {
        "ok": result["ok"],
        "symbol": symbol.upper().replace("/", ""),
        "freqs": [f.strip() for f in freq_arg.split(",") if f.strip()],
        "command": result["command"],
        "returncode": result["returncode"],
        "output_text": result["stdout"],
        "stderr": result["stderr"],
        "report_path": str(report_path) if report_path else None,
        "report_text": report_text,
        "error": result["error"],
    }


def analyze_market(
    market: str,
    symbol: str | None = None,
    *,
    blocks: str = "all",
    with_czsc: bool = True,
    stock: str | None = None,
    remote: str | None = None,
    timeout: int = 240,
) -> dict[str, Any]:
    """Fetch market data and optional CZSC confirmation in one response."""

    fetch = fetch_market_data(
        market,
        symbol=symbol,
        blocks=blocks,
        stock=stock,
        remote=remote,
        timeout=timeout,
    )
    resolved_market = fetch.get("market")
    czsc = None
    if with_czsc and resolved_market == "crypto" and fetch.get("symbol"):
        czsc_symbol = crypto_pair_symbol(str(fetch["symbol"]))
        czsc = czsc_analyze(czsc_symbol, timeout=timeout)

    result = {
        "ok": bool(fetch.get("ok")) and (czsc is None or bool(czsc.get("ok"))),
        "market": resolved_market,
        "symbol": fetch.get("symbol"),
        "fetch": fetch,
        "czsc": czsc,
        "notes": _analysis_notes(resolved_market, with_czsc, czsc),
    }

    from .formatters.markdown import format_market_result

    result["markdown"] = format_market_result(result)
    return result


def _collector_args(
    market: str,
    *,
    symbol: str | None,
    blocks: str,
    stock: str | None,
    remote: str | None,
) -> list[str]:
    if market == "crypto":
        if not symbol:
            raise ValueError("crypto requires symbol")
        return [symbol, blocks]
    if market == "a_share":
        args = ["--compact"]
        target_stock = stock or symbol
        if target_stock:
            args.extend(["--stock", target_stock])
        if remote:
            args.extend(["--remote", remote])
        return args
    if not symbol:
        raise ValueError(f"{market} requires symbol")
    return [symbol, "--compact"]


def _display_symbol(market: str, *, symbol: str | None, stock: str | None) -> str | None:
    if market == "a_share":
        return stock or symbol or "market"
    return symbol


def _extract_report_path(stdout: str) -> Path | None:
    match = re.search(r"报告:\s*(\S+)", stdout)
    if not match:
        return None
    return Path(match.group(1))


def _read_report(path: Path | None) -> str:
    if not path or not path.exists():
        return ""
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""


def _analysis_notes(market: str | None, with_czsc: bool, czsc: dict[str, Any] | None) -> list[str]:
    notes = [
        "MCP/CLI returns data and technical evidence; the client model should synthesize the final narrative with the relevant Skill framework.",
        "This output is for technical research and does not constitute investment advice.",
    ]
    if with_czsc and market != "crypto":
        notes.append("CZSC confirmation currently runs only for crypto exchange pairs through the ccxt connector.")
    if czsc and not czsc.get("ok"):
        notes.append("CZSC execution failed; use the collector data and mark the technical confirmation as unavailable.")
    return notes
