# Gemini CLI Notes

Use Hermes Finance through the project MCP server when available:

```bash
python3 bin/hermes_finance_mcp.py
```

Gemini CLI can load `.gemini/settings.json` from this repository. The server is named `hermes_finance`.

If MCP is unavailable, use the shared CLI:

```bash
python3 -m hermes_finance route BTC
python3 -m hermes_finance fetch crypto BTC --blocks price
python3 -m hermes_finance analyze crypto BTC --blocks price --no-czsc
```

For crypto analysis requests such as BTC, ETH, and SOL, always use the full eight-dimension crypto framework. Fetch `blocks=all`, run CZSC 4H+15m, then write `七维主判断`, `缠论确认`, and `最终方向`. Do not answer with only price/contracts/macro/CZSC.

Read `AGENTS.md` for repository workflow, market framework rules, and validation commands.
