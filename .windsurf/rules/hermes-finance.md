# Hermes Finance

Use Hermes Finance as a market-analysis toolset. Prefer MCP when configured from `integrations/windsurf/mcp_config.example.json`; otherwise use the shared CLI.

```bash
python3 -m hermes_finance route BTC
python3 -m hermes_finance fetch crypto BTC --blocks all
python3 -m hermes_finance analyze crypto BTC --blocks all
```

Before writing analysis, read the target market `SKILL.md` under `skills/`. Keep source status, missing data, inference, and risk notes explicit.

For BTC, ETH, SOL, and other crypto analysis, use the full eight-dimension crypto framework. Fetch `blocks=all`, run 4H+15m CZSC, then output `七维主判断`, `缠论确认`, and `最终方向`. Do not answer with only a price/contracts/macro summary.
