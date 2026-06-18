# AI 工具适配

Hermes Finance 同时提供项目级配置、用户级模板和生成脚本，让常见 AI 编程工具都能走同一个 MCP server：

```bash
python3 bin/hermes_finance_mcp.py
```

这个 launcher 会自动定位仓库根目录、设置 `PYTHONPATH`，避免不同客户端从不同工作目录启动时找不到模块。

MCP server 初始化时会返回统一 instructions：先路由标的、读取对应市场框架、事实和推断分开、报告数据源失败，并把 CZSC 作为第 8 维技术确认层，而不是主决策层。这对支持 MCP instructions 的客户端会自动生效。

为防止 AI 工具把市场分析误写成快速行情摘要，或把缠论分数当成最终交易方向，MCP server instructions、MCP prompts、`AGENTS.md` 和各客户端 rules 都明确要求：所有市场尽量走八维框架，拉取完整数据，先用 1-7 维输出 `七维主判断`，再运行 CZSC 或标注第 8 维不足，最后输出 `缠论确认`、`最终方向`。CZSC 只能确认、冲突、降级置信度或细化执行。

## 支持矩阵

| 工具 | 适配方式 | 文件 |
|---|---|---|
| Claude Code | 项目级 MCP + 项目说明 | `.mcp.json`, `CLAUDE.md` |
| Claude Desktop | 用户级模板 | `integrations/claude-desktop/claude_desktop_config.example.json` |
| Codex CLI / IDE | 项目级 MCP + Agent 说明 | `.codex/config.toml`, `AGENTS.md` |
| Cursor | 项目级 MCP + rules | `.cursor/mcp.json`, `.cursor/rules/hermes-finance.mdc` |
| VS Code / GitHub Copilot | 项目级 MCP + Copilot instructions | `.vscode/mcp.json`, `.github/copilot-instructions.md` |
| Gemini CLI | 项目级 MCP + 项目说明 | `.gemini/settings.json`, `GEMINI.md` |
| Windsurf | 用户级模板 + rules | `integrations/windsurf/mcp_config.example.json`, `.windsurf/rules/hermes-finance.md` |
| Cline | 用户级模板 + rules | `integrations/cline/mcp.example.json`, `.clinerules/hermes-finance.md` |
| Roo Code | 项目级 MCP + rules | `.roo/mcp.json`, `.roo/rules/hermes-finance.md` |
| Continue | 项目级 MCP server YAML | `.continue/mcpServers/hermes-finance.yaml` |
| Zed | 项目级 context server | `.zed/settings.json` |
| Amp | 用户级模板 | `integrations/amp/mcp.example.json` |

不同客户端的 MCP 配置字段会随版本变化。仓库内项目级文件采用各工具常见发现路径；`integrations/` 下的文件是可复制模板，适合放入用户级配置目录。

## 一键生成用户级配置

生成脚本会把当前仓库路径渲染成绝对路径，适合 Claude Desktop、Windsurf、Cline、Zed、Amp 等通常读取用户级配置的工具。

```bash
python3 scripts/render_ai_client_config.py claude-desktop
python3 scripts/render_ai_client_config.py windsurf
python3 scripts/render_ai_client_config.py cline
python3 scripts/render_ai_client_config.py zed
python3 scripts/render_ai_client_config.py codex
```

写入文件示例：

```bash
python3 scripts/render_ai_client_config.py claude-desktop --out /tmp/claude_desktop_config.json
```

支持的目标：

```text
universal, claude-code, claude-desktop, cursor, vscode, windsurf,
cline, roo, gemini, continue, codex, zed, amp
```

## Claude Code

Claude Code 会识别项目级 `.mcp.json`。进入仓库后启动 Claude Code，首次加载项目 MCP 时按客户端提示启用 `hermes-finance`。

```json
{
  "mcpServers": {
    "hermes-finance": {
      "command": "python3",
      "args": ["bin/hermes_finance_mcp.py"],
      "timeout": 600000,
      "env": {
        "PYTHONPATH": "."
      }
    }
  }
}
```

`CLAUDE.md` 提供 Claude Code 的项目内使用说明。

## Codex

Codex CLI 和 Codex IDE Extension 使用 `.codex/config.toml`：

```toml
[mcp_servers.hermes_finance]
command = "python3"
args = ["bin/hermes_finance_mcp.py"]
cwd = ".."
startup_timeout_sec = 20
tool_timeout_sec = 240
enabled = true
default_tools_approval_mode = "prompt"
```

Codex 只会在可信项目中加载项目级 `.codex/config.toml`。`AGENTS.md` 提供仓库工作流、常用命令和验证命令。

## Cursor / VS Code / Gemini / Roo / Continue / Zed

这些客户端都有项目级配置：

- Cursor：`.cursor/mcp.json`
- VS Code / Copilot：`.vscode/mcp.json`
- Gemini CLI：`.gemini/settings.json`
- Roo Code：`.roo/mcp.json`
- Continue：`.continue/mcpServers/hermes-finance.yaml`
- Zed：`.zed/settings.json`

打开项目后，在客户端的 MCP 面板或命令中确认 `hermes-finance` 已连接。

## Claude Desktop / Windsurf / Cline / Amp

这些工具更常见的方式是用户级配置。使用 `integrations/` 模板，或用生成脚本输出当前仓库的绝对路径配置：

```bash
python3 scripts/render_ai_client_config.py claude-desktop
python3 scripts/render_ai_client_config.py windsurf
python3 scripts/render_ai_client_config.py cline
python3 scripts/render_ai_client_config.py amp
```

把输出合并到对应客户端的 MCP 配置文件后重启或刷新客户端。

## 可用 MCP 能力

Tools:

- `route_market_tool`
- `fetch_market_data_tool`
- `analyze_market_tool`
- `analyze_crypto`
- `analyze_futures`
- `analyze_forex`
- `analyze_us_equity`
- `analyze_a_share`
- `czsc_analyze_tool`

Resources:

- `finance://routing`
- `finance://framework/{market}`

Prompts:

- `deep_market_analysis`
- `eight_dimension_analysis`
- `crypto_eight_dimension_analysis`
- `czsc_confirmation_review`

## 验证

```bash
python3 -m compileall -q bin scripts hermes_finance hermes_finance_mcp tests
python3 -m unittest discover -s tests -v
python3 scripts/render_ai_client_config.py claude-desktop
python3 scripts/render_ai_client_config.py codex
```

MCP smoke test:

```bash
python3 - <<'PY'
import anyio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def main():
    params = StdioServerParameters(command="python3", args=["bin/hermes_finance_mcp.py"], env={"PYTHONPATH": "."})
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            print([tool.name for tool in (await session.list_tools()).tools])
            result = await session.call_tool("route_market_tool", {"text": "BTC"})
            print(result.content[0].text)

anyio.run(main)
PY
```
