# Hermes Finance

Use `.roo/mcp.json` to start the `hermes-finance` MCP server. If MCP is unavailable, use:

```bash
python3 -m hermes_finance route BTC
python3 -m hermes_finance fetch crypto BTC --blocks price
python3 -m hermes_finance analyze crypto BTC --blocks price --no-czsc
```

Read the target market `SKILL.md` before final analysis. Treat CZSC as a confirmation layer and report missing data through source status/errors.
