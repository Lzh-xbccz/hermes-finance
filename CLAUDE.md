# Claude Code Notes

Hermes Finance includes a project-scoped MCP server in `.mcp.json`. Claude Code should prompt for approval the first time it sees this project MCP configuration.

Use the MCP server named `hermes-finance` when available. If MCP is unavailable, use the shared CLI:

```bash
python3 -m hermes_finance route BTC
python3 -m hermes_finance fetch crypto BTC --blocks price
python3 -m hermes_finance analyze crypto BTC --blocks price --no-czsc
```

Read `AGENTS.md` for repository workflow and validation commands.
