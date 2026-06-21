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
python3 -m hermes_finance analyze futures CL
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
- `eight_dimension_analysis`
- `czsc_confirmation_review`

## Rules

- Use latest market data for live analysis.
- Read the target market Skill framework before writing a final market view.
- For every market analysis request, do not give a quick summary. Fetch full market data, run CZSC when K-lines are available, and output all eight dimensions.
- All market answers must include `各维度证据`, `方向判断依据`, `反向审计`, `缠论确认`, and `最终方向` in that order. CZSC cannot override dimensions 1-7; if unavailable, mark dimension 8 as insufficient.
- Treat CZSC as technical confirmation, not as the primary decision layer. Never make `CZSC score` the main reason for the final stance.
- Build `各维度证据` from dimensions 1-7 first, then synthesize direction from evidence strength and run counter-direction audit before `最终方向`; use CZSC only to confirm, conflict, downgrade confidence, and refine entry/exit timing. Do not use voting counts or weighted scoring to decide direction.
- Do not force `做多` / `做空`. If evidence is mixed, stale, incomplete, or contradicted, final direction must be `观望`, `震荡`, or `无方向优势`.
- Separate raw facts from inference.
- State missing data and source failures using `source_status` / `errors`.
- This project is for technical research, not investment advice.

## Validation

```bash
python3 -m compileall -q bin hermes_finance hermes_finance_mcp scripts skills/multi-market-analysis/scripts tests
python3 -m unittest discover -s tests -v
python3 /root/.codex/skills/.system/skill-creator/scripts/quick_validate.py skills/multi-market-analysis
```
