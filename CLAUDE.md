# Claude Code Notes

Hermes Finance includes a project-scoped MCP server in `.mcp.json`. Claude Code should prompt for approval the first time it sees this project MCP configuration.

Use the MCP server named `hermes-finance` when available. If MCP is unavailable, use the shared CLI:

```bash
python3 -m hermes_finance route BTC
python3 -m hermes_finance fetch crypto BTC --blocks all
python3 -m hermes_finance analyze crypto BTC --blocks all
python3 -m hermes_finance analyze futures CL
```

For every market analysis, do not produce a quick market summary. Fetch full data, run CZSC when K-lines are available, and answer with the full eight-dimension framework for that market. Include `七维主判断`, `缠论确认`, and `最终方向`; if CZSC is unavailable, mark dimension 8 as insufficient.

Read `AGENTS.md` for repository workflow and validation commands.
