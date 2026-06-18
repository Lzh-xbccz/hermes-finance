# Claude Code Notes

Hermes Finance includes a project-scoped MCP server in `.mcp.json`. Claude Code should prompt for approval the first time it sees this project MCP configuration.

Use the MCP server named `hermes-finance` when available. If MCP is unavailable, use the shared CLI:

```bash
python3 -m hermes_finance route BTC
python3 -m hermes_finance fetch crypto BTC --blocks price
python3 -m hermes_finance analyze crypto BTC --blocks price --no-czsc
```

For BTC, ETH, SOL, and other crypto analysis, do not produce a quick market summary. Use `blocks=all`, run CZSC 4H+15m, and answer with the full crypto eight-dimension framework: 技术结构、链上真相、庄家博弈/合约结构、情绪反指、宏观驱动、交易所交叉验证、期权暗语、缠论结构. Include `七维主判断`, `缠论确认`, and `最终方向`.

Read `AGENTS.md` for repository workflow and validation commands.
