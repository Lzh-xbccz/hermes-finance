# Hermes Finance Agent Guide

Use this repository as a financial market data and analysis toolset.

## Preferred Entry Points

- MCP server: `python3 bin/hermes_finance_mcp.py`
- Shared CLI: `python3 -m hermes_finance`
- Legacy-compatible CLI: `python3 scripts/market_analyze.py`

## Common Commands

```bash
python3 -m hermes_finance route BTC
python3 -m hermes_finance fetch crypto BTC --blocks all
python3 -m hermes_finance fetch futures GC
python3 -m hermes_finance fetch forex EURUSD
python3 -m hermes_finance fetch us-equity AAPL
python3 -m hermes_finance fetch a-share --stock 600519
python3 -m hermes_finance analyze crypto BTC --blocks all
python3 scripts/czsc_analyze.py BTCUSDT --freqs 4h,15m --report
```

## MCP Tools

- `route_market_tool`
- `fetch_market_data_tool`
- `analyze_market_tool`
- `analyze_crypto`
- `analyze_futures`
- `analyze_forex`
- `analyze_us_equity`
- `analyze_a_share`
- `czsc_analyze_tool`

## MCP Resources And Prompts

- `finance://routing`
- `finance://framework/{market}`
- `deep_market_analysis`
- `czsc_confirmation_review`

## Rules

- Use latest market data for live analysis.
- Read the target market Skill framework before writing a final market view.
- For BTC, ETH, SOL, and other crypto requests, do not give a quick summary. Run/fetch `crypto` with `--blocks all`, run 4H+15m CZSC, and output all eight crypto dimensions.
- Crypto answers must include `七维主判断`, `缠论确认`, and `最终方向` in that order. CZSC cannot override dimensions 1-7.
- Treat CZSC as technical confirmation, not as the only decision layer.
- Separate raw facts from inference.
- State missing data and source failures using `source_status` / `errors`.
- This project is for technical research, not investment advice.

## Validation

```bash
python3 -m compileall -q bin hermes_finance hermes_finance_mcp scripts skills/multi-market-analysis/scripts tests
python3 -m unittest discover -s tests -v
python3 /root/.codex/skills/.system/skill-creator/scripts/quick_validate.py skills/multi-market-analysis
```
