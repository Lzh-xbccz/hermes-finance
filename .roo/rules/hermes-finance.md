# Hermes Finance

Use `.roo/mcp.json` to start the `hermes-finance` MCP server. If MCP is unavailable, use:

```bash
python3 -m hermes_finance route BTC
python3 -m hermes_finance fetch crypto BTC --blocks all
python3 -m hermes_finance analyze crypto BTC --blocks all
```

Read the target market `SKILL.md` before final analysis. Treat CZSC as a confirmation layer and report missing data through source status/errors.

For BTC, ETH, SOL, and other crypto requests, do not return a quick summary. Use all crypto data blocks, run CZSC 4H+15m, and output the strict eight-dimension crypto framework with `七维主判断`, `缠论确认`, and `最终方向`.
