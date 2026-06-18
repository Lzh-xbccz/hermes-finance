#!/usr/bin/env python3
"""Unified Hermes Finance CLI.

This script is kept for backwards compatibility. The implementation now uses
the shared ``hermes_finance`` service layer, which is also used by MCP.
"""

from __future__ import annotations

import argparse
import json
import os
import sys


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from hermes_finance.service import analyze_market, fetch_market_data  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="金融市场统一分析")
    parser.add_argument("market", choices=["crypto", "a-share", "futures", "forex", "us-equity"])
    parser.add_argument("symbol", nargs="?", default=None, help="标的代码")
    parser.add_argument("--blocks", default="all", help="crypto 数据块: all 或逗号分隔列表")
    parser.add_argument("--with-czsc", action="store_true", help="兼容旧参数；Markdown 分析默认会尽量输出缠论第8维确认")
    parser.add_argument("--no-czsc", action="store_true", help="仅调试采集链路时跳过缠论第8维")
    parser.add_argument("--stock", default=None, help="A股个股代码")
    parser.add_argument("--remote", default=None, help="A股远程节点")
    parser.add_argument("--timeout", type=int, default=240, help="采集超时秒数")
    parser.add_argument("--json", action="store_true", help="输出包装后的 JSON 结果")
    parser.add_argument("--markdown", action="store_true", help="输出 Markdown 摘要")
    parser.add_argument("--no-news", action="store_true", help="兼容旧参数；新闻由各采集器自行处理")
    args = parser.parse_args()

    market = {"a-share": "a_share", "us-equity": "us_equity"}.get(args.market, args.market)
    target = args.stock or args.symbol
    if market != "a_share" and not target:
        parser.error(f"{args.market} 需要指定标的代码")

    print("=" * 50, file=sys.stderr)
    print(f"市场: {args.market} | 标的: {target or '大盘'}", file=sys.stderr)
    print("=" * 50, file=sys.stderr)

    should_analyze = args.with_czsc or args.markdown
    if should_analyze:
        result = analyze_market(
            market,
            args.symbol,
            blocks=args.blocks,
            with_czsc=not args.no_czsc,
            stock=args.stock,
            remote=args.remote,
            timeout=args.timeout,
        )
        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print(result["markdown"], end="")
        return 0 if result.get("ok") else 1

    result = fetch_market_data(
        market,
        args.symbol,
        blocks=args.blocks,
        stock=args.stock,
        remote=args.remote,
        timeout=args.timeout,
    )
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    elif result.get("data") is not None:
        print(json.dumps(result["data"], ensure_ascii=False, indent=2))
    else:
        print(result.get("output_text") or "", end="")
    if result.get("stderr"):
        print(result["stderr"], file=sys.stderr, end="" if result["stderr"].endswith("\n") else "\n")
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
