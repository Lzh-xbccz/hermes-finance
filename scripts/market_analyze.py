#!/usr/bin/env python3
"""金融市场统一分析脚本 — 路由到对应市场的fetch脚本，并行拉取数据
数据源全部来自公开API（Yahoo Finance/Binance/东方财富/CoinGecko），确保真实可信。

用法:
  python3 market_analyze.py crypto bitcoin
  python3 market_analyze.py crypto ethereum
  python3 market_analyze.py a-share                    # 大盘
  python3 market_analyze.py a-share --stock 600519     # 个股
  python3 market_analyze.py futures CL                 # 原油
  python3 market_analyze.py futures GC                 # 黄金
  python3 market_analyze.py forex EURUSD
  python3 market_analyze.py forex DXY                  # 美元指数
  python3 market_analyze.py us-equity AAPL
  python3 market_analyze.py us-equity SPY
"""
import argparse, json, subprocess, sys, os

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILL_BASE = os.path.join(_PROJECT_ROOT, "skills")

MARKET_SCRIPTS = {
    "crypto": os.path.join(SKILL_BASE, "crypto-market-analysis", "scripts", "fetch_data.py"),
    "a-share": os.path.join(SKILL_BASE, "a-share-market-analysis", "scripts", "a_share_fetch.py"),
    "futures": os.path.join(SKILL_BASE, "futures-market-analysis", "scripts", "futures_fetch.py"),
    "forex": os.path.join(SKILL_BASE, "forex-market-analysis", "scripts", "forex_fetch.py"),
    "us-equity": os.path.join(SKILL_BASE, "us-equity-market-analysis", "scripts", "us_equity_fetch.py"),
}

ANALYZE_SCRIPTS = {
    "a-share": os.path.join(_PROJECT_ROOT, "scripts", "a_share_analyze.py"),
    "futures": os.path.join(SKILL_BASE, "futures-market-analysis", "scripts", "futures_analyze.py"),
    "forex": os.path.join(SKILL_BASE, "forex-market-analysis", "scripts", "forex_analyze.py"),
    "us-equity": os.path.join(SKILL_BASE, "us-equity-market-analysis", "scripts", "us_equity_analyze.py"),
}


def run_script(cmd, timeout=120):
    """运行脚本并返回输出"""
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout
        )
        if result.stdout:
            return result.stdout
        if result.returncode != 0 and result.stderr:
            print(f"⚠️ {result.stderr[:500]}", file=sys.stderr)
        return ""
    except subprocess.TimeoutExpired:
        print(f"❌ 超时({timeout}s): {' '.join(cmd)}", file=sys.stderr)
        return ""
    except Exception as e:
        print(f"❌ 执行失败: {e}", file=sys.stderr)
        return ""


def fetch_crypto(symbol, blocks="all"):
    """加密货币数据拉取"""
    script = MARKET_SCRIPTS["crypto"]
    if not os.path.exists(script):
        print(f"❌ 脚本不存在: {script}")
        sys.exit(1)
    
    print(f"🔄 拉取 {symbol} 数据 (blocks={blocks})...", file=sys.stderr)
    output = run_script(["python3", script, symbol, blocks])
    if output:
        print(output)
    else:
        print(f"❌ 无数据返回")


def fetch_ashare(stock=None, remote=None):
    """A股数据拉取"""
    script = MARKET_SCRIPTS["a-share"]
    cmd = ["python3", script]
    if stock:
        cmd.extend(["--stock", stock])
    if remote:
        cmd.extend(["--remote", remote])
    else:
        cmd.append("--compact")
    
    label = f"个股 {stock}" if stock else "大盘"
    print(f"🔄 拉取A股 {label} 数据...", file=sys.stderr)
    output = run_script(cmd, timeout=60)
    if output:
        print(output)
    else:
        print(f"❌ A股数据拉取失败（可能需要 --remote 参数连接国内节点）")


def fetch_futures(symbol):
    """期货数据拉取"""
    script = MARKET_SCRIPTS["futures"]
    if not os.path.exists(script):
        print(f"❌ 脚本不存在: {script}")
        sys.exit(1)
    
    print(f"🔄 拉取期货 {symbol} 数据...", file=sys.stderr)
    output = run_script(["python3", script, symbol])
    if output:
        print(output)
    else:
        print(f"❌ 期货数据拉取失败")


def fetch_forex(pair):
    """外汇数据拉取"""
    script = MARKET_SCRIPTS["forex"]
    if not os.path.exists(script):
        print(f"❌ 脚本不存在: {script}")
        sys.exit(1)
    
    print(f"🔄 拉取外汇 {pair} 数据...", file=sys.stderr)
    output = run_script(["python3", script, pair])
    if output:
        print(output)
    else:
        print(f"❌ 外汇数据拉取失败")


def fetch_us_equity(symbol):
    """美股数据拉取"""
    script = MARKET_SCRIPTS["us-equity"]
    if not os.path.exists(script):
        print(f"❌ 脚本不存在: {script}")
        sys.exit(1)
    
    print(f"🔄 拉取美股 {symbol} 数据...", file=sys.stderr)
    output = run_script(["python3", script, symbol])
    if output:
        print(output)
    else:
        print(f"❌ 美股数据拉取失败")


def tavily_supplement(market, symbol):
    """用Tavily搜索补充最新新闻/事件"""
    try:
        from tavily_client import tavily_batch_search
    except ImportError:
        return ""

    queries_map = {
        "crypto": [f"{symbol} crypto news today price analysis"],
        "a-share": [f"A股 {symbol} 最新消息 分析" if symbol else "A股 大盘 今日行情分析"],
        "futures": [f"{symbol} futures price analysis today"],
        "forex": [f"{symbol} forex analysis today outlook"],
        "us-equity": [f"{symbol} stock analysis news today"],
    }

    queries = queries_map.get(market, [f"{symbol} market analysis"])
    print(f"🔍 Tavily补充搜索...", file=sys.stderr)
    
    results = tavily_batch_search(queries, search_depth="advanced", max_results=5)
    
    news_items = []
    for q, r in results.items():
        answer = r.get("answer", "")
        if answer:
            news_items.append(answer[:300])
        for item in r.get("results", [])[:3]:
            title = item.get("title", "")
            if title:
                news_items.append(f"- {title}")
    
    if news_items:
        print(f"\n## 📰 最新资讯（Tavily）")
        for item in news_items[:5]:
            print(item)
    
    return "\n".join(news_items)


def main():
    parser = argparse.ArgumentParser(description="金融市场统一分析")
    parser.add_argument("market", choices=["crypto", "a-share", "futures", "forex", "us-equity"])
    parser.add_argument("symbol", nargs="?", default=None, help="标的代码")
    parser.add_argument("--blocks", default="all", help="crypto数据块")
    parser.add_argument("--stock", default=None, help="A股个股代码")
    parser.add_argument("--remote", default=None, help="A股远程节点")
    parser.add_argument("--no-news", action="store_true", help="不搜索新闻")
    args = parser.parse_args()

    print(f"{'='*50}", file=sys.stderr)
    print(f"📊 市场: {args.market} | 标的: {args.symbol or args.stock or '大盘'}", file=sys.stderr)
    print(f"{'='*50}", file=sys.stderr)

    # 路由到对应市场
    if args.market == "crypto":
        if not args.symbol:
            print("❌ crypto 需要指定币种，如: bitcoin, ethereum")
            sys.exit(1)
        fetch_crypto(args.symbol, args.blocks)

    elif args.market == "a-share":
        fetch_ashare(stock=args.stock or args.symbol, remote=args.remote)

    elif args.market == "futures":
        if not args.symbol:
            print("❌ futures 需要指定品种，如: CL(原油), GC(黄金), ES(标普)")
            sys.exit(1)
        fetch_futures(args.symbol)

    elif args.market == "forex":
        if not args.symbol:
            print("❌ forex 需要指定货币对，如: EURUSD, USDJPY, DXY")
            sys.exit(1)
        fetch_forex(args.symbol)

    elif args.market == "us-equity":
        if not args.symbol:
            print("❌ us-equity 需要指定股票代码，如: AAPL, TSLA, SPY")
            sys.exit(1)
        fetch_us_equity(args.symbol)

    # 补充新闻
    if not args.no_news:
        tavily_supplement(args.market, args.symbol or args.stock or "")


if __name__ == "__main__":
    main()
