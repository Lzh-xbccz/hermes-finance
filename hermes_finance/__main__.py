"""Command line entry point for the shared Hermes Finance API."""

from __future__ import annotations

import argparse
import json
from typing import Any

from .service import analyze_market, czsc_analyze, fetch_market_data, route_market


def main() -> int:
    parser = argparse.ArgumentParser(description="Hermes Finance shared CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    p_route = sub.add_parser("route", help="Route a symbol/request to a market")
    p_route.add_argument("text", nargs="+")

    p_fetch = sub.add_parser("fetch", help="Fetch market data")
    p_fetch.add_argument("market")
    p_fetch.add_argument("symbol", nargs="?")
    p_fetch.add_argument("--blocks", default="all")
    p_fetch.add_argument("--stock")
    p_fetch.add_argument("--remote")
    p_fetch.add_argument("--timeout", type=int, default=180)
    p_fetch.add_argument("--json", action="store_true", help="Print the full wrapper JSON")

    p_analyze = sub.add_parser("analyze", help="Fetch data and optional CZSC confirmation")
    p_analyze.add_argument("market")
    p_analyze.add_argument("symbol", nargs="?")
    p_analyze.add_argument("--blocks", default="all")
    p_analyze.add_argument("--stock")
    p_analyze.add_argument("--remote")
    p_analyze.add_argument("--timeout", type=int, default=240)
    p_analyze.add_argument("--no-czsc", action="store_true")
    p_analyze.add_argument("--json", action="store_true")

    p_czsc = sub.add_parser("czsc", help="Run CZSC multi-frequency analysis")
    p_czsc.add_argument("symbol")
    p_czsc.add_argument("--freqs", default="4h,15m")
    p_czsc.add_argument("--chart", action="store_true")
    p_czsc.add_argument("--no-report", action="store_true")
    p_czsc.add_argument("--timeout", type=int, default=240)
    p_czsc.add_argument("--json", action="store_true")

    args = parser.parse_args()
    if args.command == "route":
        _print_json(route_market(" ".join(args.text)))
        return 0
    if args.command == "fetch":
        result = fetch_market_data(
            args.market,
            args.symbol,
            blocks=args.blocks,
            stock=args.stock,
            remote=args.remote,
            timeout=args.timeout,
        )
        _print_fetch(result, full_json=args.json)
        return 0 if result.get("ok") else 1
    if args.command == "analyze":
        result = analyze_market(
            args.market,
            args.symbol,
            blocks=args.blocks,
            with_czsc=not args.no_czsc,
            stock=args.stock,
            remote=args.remote,
            timeout=args.timeout,
        )
        if args.json:
            _print_json(result)
        else:
            print(result["markdown"], end="")
        return 0 if result.get("ok") else 1
    if args.command == "czsc":
        result = czsc_analyze(
            args.symbol,
            freqs=args.freqs,
            chart=args.chart,
            report=not args.no_report,
            timeout=args.timeout,
        )
        if args.json:
            _print_json(result)
        else:
            print(result.get("report_text") or result.get("output_text") or "", end="")
        return 0 if result.get("ok") else 1
    return 2


def _print_fetch(result: dict[str, Any], *, full_json: bool) -> None:
    if full_json:
        _print_json(result)
    elif result.get("data") is not None:
        _print_json(result["data"])
    else:
        print(result.get("output_text") or "", end="")


def _print_json(value: Any) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    raise SystemExit(main())
