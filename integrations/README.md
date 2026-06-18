# AI Client Integrations

Hermes Finance exposes the same finance tools through a stdio MCP server:

```bash
python3 bin/hermes_finance_mcp.py
```

Project-level configs are checked in for clients that commonly load settings from the repository:

| Client | Project file |
|---|---|
| Claude Code | `.mcp.json`, `CLAUDE.md` |
| Codex CLI / IDE | `.codex/config.toml`, `AGENTS.md` |
| Cursor | `.cursor/mcp.json`, `.cursor/rules/hermes-finance.mdc` |
| VS Code / GitHub Copilot | `.vscode/mcp.json`, `.github/copilot-instructions.md` |
| Gemini CLI | `.gemini/settings.json`, `GEMINI.md` |
| Continue | `.continue/mcpServers/hermes-finance.yaml` |
| Roo Code | `.roo/mcp.json`, `.roo/rules/hermes-finance.md` |
| Zed | `.zed/settings.json` |

User-level templates are under the client folders in this directory. Generate an absolute-path config for your local checkout with:

```bash
python3 scripts/render_ai_client_config.py claude-desktop
python3 scripts/render_ai_client_config.py cursor
python3 scripts/render_ai_client_config.py codex
python3 scripts/render_ai_client_config.py gemini
```

Supported generator targets:

```text
universal, claude-code, claude-desktop, cursor, vscode, windsurf,
cline, roo, gemini, continue, codex, zed, amp
```
