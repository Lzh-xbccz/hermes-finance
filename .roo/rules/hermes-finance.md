# Hermes Finance

Use `.roo/mcp.json` to start the `hermes-finance` MCP server. If MCP is unavailable, use:

```bash
python3 -m hermes_finance route BTC
python3 -m hermes_finance fetch crypto BTC --blocks all
python3 -m hermes_finance analyze crypto BTC --blocks all
python3 -m hermes_finance analyze futures CL
```

Read the target market `SKILL.md` before final analysis. Treat CZSC as a confirmation layer and report missing data through source status/errors.

For every market analysis request, do not return a quick summary. Use full data, run CZSC when available, and output the strict eight-dimension framework with `七维主判断`, `方向质量门槛`, `反向审计`, `缠论确认`, and `最终方向`. Do not force `做多` / `做空`; mixed, stale, incomplete, or contradicted evidence must end as `观望`, `震荡`, or `无方向优势`.
