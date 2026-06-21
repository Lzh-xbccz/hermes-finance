# Claude Code Notes

Hermes Finance includes a project-scoped MCP server in `.mcp.json`. Claude Code should prompt for approval the first time it sees this project MCP configuration.

Use the MCP server named `hermes-finance` when available. If MCP is unavailable, use the shared CLI:

```bash
python3 -m hermes_finance route BTC
python3 -m hermes_finance fetch crypto BTC --blocks all
python3 -m hermes_finance analyze crypto BTC --blocks all
python3 -m hermes_finance analyze futures CL
```

For every market analysis, do not produce a quick market summary. Fetch full data, run CZSC when K-lines are available, and answer with the full eight-dimension framework for that market. Include `各维度证据`, `方向判断依据`, `反向审计`, `缠论确认`, and `最终方向`; if CZSC is unavailable, mark dimension 8 as insufficient. The final stance must come from dimensions 1-7 first, then be synthesized from evidence strength and pass the counter-direction audit. Do not use voting counts or weighted scoring to decide direction. Do not force `做多` / `做空`; mixed, stale, incomplete, or contradicted evidence must end as `观望`, `震荡`, or `无方向优势`. CZSC only confirms, conflicts, downgrades confidence, or refines entry/exit timing.

Read `AGENTS.md` for repository workflow and validation commands.
