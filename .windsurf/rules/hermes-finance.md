# Hermes Finance

Use Hermes Finance as a market-analysis toolset. Prefer MCP when configured from `integrations/windsurf/mcp_config.example.json`; otherwise use the shared CLI.

```bash
python3 -m hermes_finance route BTC
python3 -m hermes_finance fetch crypto BTC --blocks price
python3 -m hermes_finance analyze crypto BTC --blocks price --no-czsc
```

Before writing analysis, read the target market `SKILL.md` under `skills/`. Keep source status, missing data, inference, and risk notes explicit.
