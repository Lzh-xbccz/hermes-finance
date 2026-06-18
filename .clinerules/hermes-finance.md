# Hermes Finance

Use the Hermes Finance MCP server when the Cline MCP settings include `hermes-finance`.

Fallback commands:

```bash
python3 -m hermes_finance route BTC
python3 -m hermes_finance fetch crypto BTC --blocks all
python3 -m hermes_finance analyze crypto BTC --blocks all
python3 -m hermes_finance analyze futures CL
```

For market analysis, read the matching `skills/*/SKILL.md` first and follow its dimensional framework. State source failures and separate facts from inference.

For every market analysis request, fetch full data and run CZSC when K-lines are available. The final answer must include all eight dimensions, `七维主判断`, `方向质量门槛`, `反向审计`, `缠论确认`, and `最终方向`. Do not force `做多` / `做空`; mixed, stale, incomplete, or contradicted evidence must end as `观望`, `震荡`, or `无方向优势`.
