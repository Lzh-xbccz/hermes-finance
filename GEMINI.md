# Gemini CLI Notes

Use Hermes Finance through the project MCP server when available:

```bash
python3 bin/hermes_finance_mcp.py
```

Gemini CLI can load `.gemini/settings.json` from this repository. The server is named `hermes_finance`.

If MCP is unavailable, use the shared CLI:

```bash
python3 -m hermes_finance route BTC
python3 -m hermes_finance fetch crypto BTC --blocks all
python3 -m hermes_finance analyze crypto BTC --blocks all
python3 -m hermes_finance analyze futures CL
```

For every market analysis request, use the full eight-dimension framework. Fetch full data, run CZSC when K-lines are available, then write `七维主判断`, `方向质量门槛`, `反向审计`, `缠论确认`, and `最终方向`. Do not answer with only price/contracts/macro/CZSC. The final stance must be driven by dimensions 1-7 first, then pass the direction quality gate and counter-direction audit. Do not force `做多` / `做空`; mixed, stale, incomplete, or contradicted evidence must end as `观望`, `震荡`, or `无方向优势`. CZSC only confirms, conflicts, downgrades confidence, or refines entry/exit timing.

Read `AGENTS.md` for repository workflow, market framework rules, and validation commands.
