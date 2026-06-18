"""Hermes Finance MCP server."""

from __future__ import annotations

from pathlib import Path
from typing import Any

try:
    from mcp.server.fastmcp import FastMCP
except ModuleNotFoundError as exc:  # pragma: no cover - exercised by users without optional deps
    raise SystemExit("Missing MCP SDK. Install optional runtime with: pip install -r requirements-mcp.txt") from exc

from hermes_finance.paths import PROJECT_ROOT
from hermes_finance.service import analyze_market, czsc_analyze, fetch_market_data, route_market


SERVER_INSTRUCTIONS = (
    "Hermes Finance provides multi-market financial research tools for crypto, "
    "A-shares, futures, forex, and US equities. Route ambiguous symbols first, "
    "read finance://framework/{market} before final analysis, keep raw facts "
    "separate from inference, report source_status/errors, and treat CZSC as "
    "technical confirmation rather than standalone investment advice. For BTC, "
    "ETH, SOL, and other crypto analysis requests, do not return a quick market "
    "summary: fetch crypto blocks=all, run 4H+15m CZSC, then output the required "
    "eight dimensions, seven-dimension main judgment, CZSC confirmation, final "
    "direction, scenarios, and invalidation levels."
)


mcp = FastMCP("Hermes Finance", instructions=SERVER_INSTRUCTIONS, json_response=True)


@mcp.tool()
def route_market_tool(text: str) -> dict[str, Any]:
    """Route a symbol or request to crypto, A-share, futures, forex, or US equity."""

    return route_market(text)


@mcp.tool()
def fetch_market_data_tool(
    market: str,
    symbol: str | None = None,
    blocks: str = "all",
    stock: str | None = None,
    remote: str | None = None,
    timeout: int = 180,
) -> dict[str, Any]:
    """Fetch raw market data from the existing Hermes Finance collectors."""

    return fetch_market_data(market, symbol, blocks=blocks, stock=stock, remote=remote, timeout=timeout)


@mcp.tool()
def analyze_market_tool(
    market: str,
    symbol: str | None = None,
    blocks: str = "all",
    with_czsc: bool = True,
    stock: str | None = None,
    remote: str | None = None,
    timeout: int = 240,
) -> dict[str, Any]:
    """Fetch market data and optional CZSC confirmation for downstream analysis."""

    return analyze_market(
        market,
        symbol,
        blocks=blocks,
        with_czsc=with_czsc,
        stock=stock,
        remote=remote,
        timeout=timeout,
    )


@mcp.tool()
def analyze_crypto(symbol: str, blocks: str = "all", with_czsc: bool = True, timeout: int = 240) -> dict[str, Any]:
    """Fetch crypto data. For user-facing crypto analysis, use blocks='all' and write the eight-dimension framework."""

    return analyze_market("crypto", symbol, blocks=blocks, with_czsc=with_czsc, timeout=timeout)


@mcp.tool()
def analyze_futures(symbol: str, timeout: int = 180) -> dict[str, Any]:
    """Fetch futures or commodity market data."""

    return analyze_market("futures", symbol, with_czsc=False, timeout=timeout)


@mcp.tool()
def analyze_forex(symbol: str, timeout: int = 180) -> dict[str, Any]:
    """Fetch foreign exchange market data."""

    return analyze_market("forex", symbol, with_czsc=False, timeout=timeout)


@mcp.tool()
def analyze_us_equity(symbol: str, timeout: int = 180) -> dict[str, Any]:
    """Fetch US stock, ETF, or index data."""

    return analyze_market("us_equity", symbol, with_czsc=False, timeout=timeout)


@mcp.tool()
def analyze_a_share(symbol: str | None = None, remote: str | None = None, timeout: int = 180) -> dict[str, Any]:
    """Fetch A-share index or stock data."""

    return analyze_market("a_share", symbol, with_czsc=False, remote=remote, timeout=timeout)


@mcp.tool()
def czsc_analyze_tool(
    symbol: str,
    freqs: str = "4h,15m",
    chart: bool = False,
    report: bool = True,
    timeout: int = 240,
) -> dict[str, Any]:
    """Run CZSC multi-frequency technical analysis for a crypto exchange pair."""

    return czsc_analyze(symbol, freqs=freqs, chart=chart, report=report, timeout=timeout)


@mcp.resource("finance://routing")
def routing_resource() -> str:
    """Return market routing guidance."""

    return _read_text("skills/multi-market-analysis/references/routing.md")


@mcp.resource("finance://framework/{market}")
def framework_resource(market: str) -> str:
    """Return the Skill framework for one market."""

    mapping = {
        "crypto": "skills/crypto-market-analysis/SKILL.md",
        "a_share": "skills/a-share-market-analysis/SKILL.md",
        "a-share": "skills/a-share-market-analysis/SKILL.md",
        "futures": "skills/futures-market-analysis/SKILL.md",
        "forex": "skills/forex-market-analysis/SKILL.md",
        "us_equity": "skills/us-equity-market-analysis/SKILL.md",
        "us-equity": "skills/us-equity-market-analysis/SKILL.md",
        "multi": "skills/multi-market-analysis/SKILL.md",
    }
    rel = mapping.get(market.strip().lower())
    if not rel:
        return "Unknown market. Use crypto, a_share, futures, forex, us_equity, or multi."
    return _read_text(rel)


@mcp.prompt()
def deep_market_analysis(market: str, symbol: str) -> str:
    """Create a prompt for a full Hermes Finance market analysis."""

    return f"""Use Hermes Finance to analyze {market} {symbol}.

1. Call route_market_tool if the market is ambiguous.
2. Read finance://framework/{market} before writing the answer.
3. For crypto, call analyze_market_tool with blocks="all" and with_czsc=true, or call analyze_crypto with blocks="all".
4. For crypto, do not write a compressed price/contracts/macro summary. Output all eight dimensions in order, then "七维主判断", "缠论确认", "最终方向", scenarios, and invalidation conditions.
5. For other markets, follow the target Skill's dimensional framework.
6. Separate raw data facts from inference.
7. Produce a clear final stance. This is technical research, not investment advice.
"""


@mcp.prompt()
def crypto_eight_dimension_analysis(symbol: str) -> str:
    """Create a strict prompt for full crypto eight-dimension analysis."""

    return f"""Use Hermes Finance to analyze crypto {symbol} with the strict crypto eight-dimension framework.

Required procedure:
1. Call analyze_crypto(symbol="{symbol}", blocks="all", with_czsc=true).
2. If CZSC details are missing or stale, call czsc_analyze_tool(symbol="{symbol}USDT", freqs="4h,15m").
3. Read finance://framework/crypto and follow it strictly.

Required output:
- 数据完整性
- 七维主判断
- 缠论确认
- 最终方向
- 因果叙事
- 1. 技术结构
- 2. 链上真相
- 3. 庄家博弈 / 合约结构
- 4. 情绪反指
- 5. 宏观驱动
- 6. 交易所交叉验证
- 7. 期权暗语
- 8. 缠论结构
- 情景推演
- 交易计划和失效条件

Do not answer with only price, contracts, macro, or CZSC. CZSC is confirmation only; the seven-dimension main judgment must be produced before the CZSC confirmation.
"""


@mcp.prompt()
def czsc_confirmation_review(symbol: str) -> str:
    """Create a prompt for reviewing CZSC confirmation only."""

    return f"""Run czsc_analyze_tool for {symbol} with freqs="4h,15m".

Summarize:
- last BI direction and strength by frequency
- center range and price location
- active buy/sell signals, excluding `其他/任意`
- divergence and candidate buy/sell pattern
- whether CZSC confirms, conflicts with, or is insufficient for a broader market thesis
"""


def _read_text(relative_path: str) -> str:
    path = PROJECT_ROOT / Path(relative_path)
    try:
        return path.read_text(encoding="utf-8")
    except OSError as exc:
        return f"Unable to read {relative_path}: {exc}"


if __name__ == "__main__":
    mcp.run(transport="stdio")
