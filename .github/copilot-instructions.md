# Hermes Finance Instructions

Hermes Finance is a multi-market financial analysis toolkit. Prefer these entry points:

- MCP server: `python3 bin/hermes_finance_mcp.py`
- Shared CLI: `python3 -m hermes_finance`
- Legacy-compatible CLI: `python3 scripts/market_analyze.py`

Use the target market skill framework before writing market analysis:

- `skills/multi-market-analysis/SKILL.md` for routing
- `skills/crypto-market-analysis/SKILL.md`
- `skills/futures-market-analysis/SKILL.md`
- `skills/forex-market-analysis/SKILL.md`
- `skills/a-share-market-analysis/SKILL.md`
- `skills/us-equity-market-analysis/SKILL.md`

Useful commands:

```bash
python3 -m hermes_finance route BTC
python3 -m hermes_finance fetch crypto BTC --blocks all
python3 -m hermes_finance analyze crypto BTC --blocks all
python3 -m hermes_finance analyze futures CL
python3 -m unittest discover -s tests -v
```

Keep raw market data, inference, missing source status, and risk notes separate.

For every market analysis, never stop at a quick market summary. Use full data, run CZSC when available, then output all eight dimensions plus `七维主判断`, `缠论确认`, and `最终方向`.
