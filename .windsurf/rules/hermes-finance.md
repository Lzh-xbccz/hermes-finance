# Hermes Finance

Use Hermes Finance as a market-analysis toolset. Prefer MCP when configured from `integrations/windsurf/mcp_config.example.json`; otherwise use the shared CLI.

```bash
python3 -m hermes_finance route BTC
python3 -m hermes_finance fetch crypto BTC --blocks all
python3 -m hermes_finance analyze crypto BTC --blocks all
python3 -m hermes_finance analyze futures CL
```

Before writing analysis, read the target market `SKILL.md` under `skills/`. Keep source status, missing data, inference, and risk notes explicit.

For every market analysis, use the full eight-dimension framework. Fetch full data, run CZSC when available, then output `七维主判断`, `缠论确认`, and `最终方向`. Do not answer with only a price/contracts/macro summary.
