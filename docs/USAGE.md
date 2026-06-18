# Hermes Finance 使用说明

Hermes Finance 是一个多市场金融分析框架，覆盖加密货币、商品期货、外汇、A股、美股/ETF/指数，并把缠论 CZSC 作为技术确认层。

v1.1.0 起项目支持两种入口，v1.1.1 起补齐常见 AI 客户端适配：

- **Skills 版本**：适合 Codex/Agent 读取 `skills/*/SKILL.md` 后按市场框架完成分析。
- **MCP 版本**：适合支持 Model Context Protocol 的客户端调用标准 tools/resources/prompts。
- **AI 客户端配置**：适合 Claude Code、Codex、Cursor、VS Code/Copilot、Gemini、Roo、Continue、Zed 等从项目直接发现 MCP server。

两种入口共用 `hermes_finance/` 核心库，底层继续复用原有采集脚本。

## 功能概览

| 功能 | 入口 | 说明 |
|---|---|---|
| 智能路由 | CLI / Skill / MCP | 自动识别 BTC、GC、EURUSD、600519、AAPL 等标的所属市场 |
| 加密货币分析 | CLI / Skill / MCP | Binance、CoinGecko、链上、合约、情绪、宏观、期权、缠论 |
| 商品/股指期货 | CLI / Skill / MCP | Yahoo Finance、CFTC、EIA、Google News、相关代理资产 |
| 外汇分析 | CLI / Skill / MCP | 汇率、DXY、VIX、美国利率、对手国利率代理、宏观事件、CFTC |
| A股分析 | CLI / Skill / MCP | 指数、个股、北向/广度/板块资金流，支持国内远程节点和本地降级 |
| 美股/ETF/指数 | CLI / Skill / MCP | 日线/小时线、宏观代理、新闻、财报/监管/业务事件代理 |
| 缠论 CZSC | CLI / Skill / MCP | 4H+15m 多级别联立、中枢、笔、背驰、买卖点候补、报告输出 |
| Sequoia-X | Skill / CLI | A股 7 策略量化扫描 |
| MCP resources | MCP | `finance://routing`、`finance://framework/{market}` |
| MCP prompts | MCP | `deep_market_analysis`、`czsc_confirmation_review` |
| AI 客户端适配 | MCP | Claude Code、Claude Desktop、Codex、Cursor、VS Code/Copilot、Gemini、Windsurf、Cline、Roo、Continue、Zed、Amp |

## 环境要求

- Python 3.10+
- Linux/macOS shell
- Rust 工具链，用于安装 GitHub 源码版 `czsc`
- 网络访问，用于 Yahoo Finance、Binance、CoinGecko、CFTC、Google News 等公开数据源

`czsc` 必须从 GitHub 源码安装。PyPI 的旧版不含当前项目依赖的 Rust 核心能力。

## 安装

### 一键安装

```bash
git clone https://github.com/Lzh-xbccz/hermes-finance.git
cd hermes-finance
bash install.sh
```

同时安装 MCP 可选依赖：

```bash
INSTALL_MCP=1 bash install.sh
```

### 手动安装

```bash
cd hermes-finance

curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
source "$HOME/.cargo/env"

pip install --break-system-packages git+https://github.com/waditu/czsc.git
pip install --break-system-packages ccxt pandas plotly baostock akshare pydantic-settings rich python-dotenv
pip install --break-system-packages -r requirements-mcp.txt
```

如不使用 MCP，可以跳过 `requirements-mcp.txt`。

## 快速验证

```bash
python3 -m hermes_finance route BTC
python3 -m hermes_finance route 600519
python3 -m hermes_finance fetch crypto BTC --blocks price
python3 -m unittest discover -s tests -v
```

预期结果：

- `BTC` 路由到 `crypto`
- `600519` 路由到 `a_share`
- crypto price 能输出近 30 日价格和实时行情；这只是连通性验证，不是正式八维分析
- tests 全部通过

## CLI 使用

### 路由

```bash
python3 -m hermes_finance route BTC
python3 -m hermes_finance route EURUSD
python3 -m hermes_finance route 600519
python3 -m hermes_finance route AAPL
```

### 统一采集

```bash
python3 -m hermes_finance fetch crypto BTC --blocks all
python3 -m hermes_finance fetch crypto bitcoin --blocks all
python3 -m hermes_finance fetch futures GC
python3 -m hermes_finance fetch futures CL
python3 -m hermes_finance fetch forex EURUSD
python3 -m hermes_finance fetch forex DXY
python3 -m hermes_finance fetch us-equity AAPL
python3 -m hermes_finance fetch us-equity SPY
python3 -m hermes_finance fetch a-share
python3 -m hermes_finance fetch a-share --stock 600519
```

输出默认是采集器原始结构；加 `--json` 会输出包装结构，包含 `ok`、`market`、`collector`、`command`、`data`、`stderr` 等字段。

### 统一分析

```bash
python3 -m hermes_finance analyze crypto BTC --blocks all
python3 -m hermes_finance analyze futures GC
python3 -m hermes_finance analyze forex EURUSD
python3 -m hermes_finance analyze us-equity AAPL
python3 -m hermes_finance analyze a-share --stock 600519
```

crypto 可以开启缠论确认：

```bash
python3 -m hermes_finance analyze crypto BTC --blocks all --json
python3 scripts/market_analyze.py crypto bitcoin --with-czsc --markdown
```

`--no-czsc` 只适合调试数据采集链路。正式 crypto 分析不能使用 `--no-czsc`，否则第 8 维缺失，输出必须降级为“不足/不可用”。

### 缠论 CZSC

```bash
python3 scripts/czsc_analyze.py BTCUSDT --freqs 4h,15m --report
python3 -m hermes_finance czsc BTCUSDT --freqs 4h,15m
python3 -m hermes_finance czsc BTCUSDT --freqs 4h,1h,15m --chart
```

报告默认写入 `/tmp/czsc_<SYMBOL>_report.md`。

## Skills 使用

Skills 位于 `skills/`：

- `multi-market-analysis` 是总入口，适合标的不明确或跨市场请求。
- 明确市场时，可以直接使用对应市场 skill。
- 数据获取优先走共享核心：

```bash
python3 -m hermes_finance route "<用户请求或标的>"
python3 -m hermes_finance fetch <market> <symbol>
python3 -m hermes_finance analyze <market> <symbol>
```

市场 ID：

| 市场 | market 参数 |
|---|---|
| 加密货币 | `crypto` |
| A股 | `a-share` 或 `a_share` |
| 商品/股指期货 | `futures` |
| 外汇 | `forex` |
| 美股/ETF/指数 | `us-equity` 或 `us_equity` |

Skill 分析时应读取目标市场的 `SKILL.md`，按该市场的维度框架输出，不要混用其他市场指标。

## MCP 使用

### 启动 server

```bash
cd hermes-finance
python3 bin/hermes_finance_mcp.py
```

server 使用 stdio transport，适合 Claude Code、Claude Desktop、Cursor、Codex、Gemini、Roo 等 MCP host 拉起。`bin/hermes_finance_mcp.py` 会自动定位仓库根目录并设置 `PYTHONPATH`，比直接运行 `hermes_finance_mcp/server.py` 更适合多客户端调用。

MCP server 会在初始化时返回统一 instructions，提示客户端先路由标的、读取对应市场框架、事实和推断分开、报告数据源失败，并把 CZSC 作为技术确认层。

防呆规则：BTC、ETH、SOL 等 crypto 请求不能只输出快速行情摘要。客户端应拉取 `blocks=all`，运行 4H+15m CZSC，并输出完整八维、`七维主判断`、`缠论确认` 和 `最终方向`。

### MCP 配置

仓库提供 `.mcp.json`：

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

如果客户端要求绝对路径，可以改成：

```json
{
  "mcpServers": {
    "hermes-finance": {
      "command": "python3",
      "args": ["/absolute/path/to/hermes-finance/bin/hermes_finance_mcp.py"],
      "env": {
        "PYTHONPATH": "/absolute/path/to/hermes-finance"
      }
    }
  }
}
```

### AI 客户端适配

常见项目级配置已经放在仓库内：

| 工具 | 配置/说明 |
|---|---|
| Claude Code | `.mcp.json`, `CLAUDE.md` |
| Codex CLI / IDE | `.codex/config.toml`, `AGENTS.md` |
| Cursor | `.cursor/mcp.json`, `.cursor/rules/hermes-finance.mdc` |
| VS Code / GitHub Copilot | `.vscode/mcp.json`, `.github/copilot-instructions.md` |
| Gemini CLI | `.gemini/settings.json`, `GEMINI.md` |
| Roo Code | `.roo/mcp.json`, `.roo/rules/hermes-finance.md` |
| Continue | `.continue/mcpServers/hermes-finance.yaml` |
| Zed | `.zed/settings.json` |

用户级模板放在 `integrations/`，适合 Claude Desktop、Windsurf、Cline、Amp 等客户端复制合并：

```bash
python3 scripts/render_ai_client_config.py claude-desktop
python3 scripts/render_ai_client_config.py windsurf
python3 scripts/render_ai_client_config.py cline
python3 scripts/render_ai_client_config.py amp
```

完整矩阵、模板路径和验证方法见 [AI_CLIENTS.md](AI_CLIENTS.md)。

### MCP tools

| Tool | 参数 | 用途 |
|---|---|---|
| `route_market_tool` | `text` | 识别市场 |
| `fetch_market_data_tool` | `market`, `symbol`, `blocks`, `stock`, `remote`, `timeout` | 拉原始数据 |
| `analyze_market_tool` | `market`, `symbol`, `blocks`, `with_czsc`, `stock`, `remote`, `timeout` | 统一分析 |
| `analyze_crypto` | `symbol`, `blocks`, `with_czsc`, `timeout` | 加密货币专用 |
| `analyze_futures` | `symbol`, `timeout` | 期货专用 |
| `analyze_forex` | `symbol`, `timeout` | 外汇专用 |
| `analyze_us_equity` | `symbol`, `timeout` | 美股/ETF/指数专用 |
| `analyze_a_share` | `symbol`, `remote`, `timeout` | A股专用 |
| `czsc_analyze_tool` | `symbol`, `freqs`, `chart`, `report`, `timeout` | 缠论分析 |

### MCP resources

| Resource | 内容 |
|---|---|
| `finance://routing` | 路由参考 |
| `finance://framework/crypto` | 加密货币 Skill 框架 |
| `finance://framework/a_share` | A股 Skill 框架 |
| `finance://framework/futures` | 期货 Skill 框架 |
| `finance://framework/forex` | 外汇 Skill 框架 |
| `finance://framework/us_equity` | 美股 Skill 框架 |
| `finance://framework/multi` | 总路由 Skill 框架 |

### MCP prompts

| Prompt | 用途 |
|---|---|
| `deep_market_analysis` | 生成完整市场分析流程提示 |
| `crypto_eight_dimension_analysis` | 生成严格加密货币八维分析流程提示 |
| `czsc_confirmation_review` | 生成缠论确认审查提示 |

### MCP smoke test

```bash
python3 - <<'PY'
import anyio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def main():
    params = StdioServerParameters(
        command="python3",
        args=["bin/hermes_finance_mcp.py"],
        env={"PYTHONPATH": "."},
    )
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            print([tool.name for tool in tools.tools])
            result = await session.call_tool("route_market_tool", {"text": "BTC"})
            print(result.content[0].text)

anyio.run(main)
PY
```

## 输出结构

`fetch_market_data` 返回：

```json
{
  "ok": true,
  "market": "crypto",
  "symbol": "BTC",
  "route": {"market": "crypto", "reason": "explicit market"},
  "collector": "skills/crypto-market-analysis/scripts/fetch_data.py",
  "command": ["python3", "..."],
  "returncode": 0,
  "data": {},
  "output_text": "",
  "stderr": "",
  "error": null
}
```

有些旧采集器输出文本而不是 JSON，此时 `data` 为 `null`，内容放在 `output_text`。这是为了兼容现有 Skills 和采集脚本。

`analyze_market` 返回：

```json
{
  "ok": true,
  "market": "crypto",
  "symbol": "BTC",
  "fetch": {},
  "czsc": null,
  "notes": [],
  "markdown": "# Hermes Finance Analysis..."
}
```

## 数据源与降级

- 加密货币：Binance、Bybit fallback、OKX、CoinGecko、Alternative.me、Deribit、blockchain.info、Yahoo 宏观代理。
- 期货：Yahoo Finance、CFTC ZIP/CSV、EIA 页面可用性、Google News RSS。
- 外汇：Yahoo Finance、ForexFactory 日历、CFTC、利率代理、Google News RSS。
- A股：国内节点优先，失败时走本地新浪/腾讯/Yahoo/Google News 降级。
- 美股：Yahoo Finance、Google News RSS、NASDAQ earnings 页面代理。

所有实时数据都可能因限流、网络、交易所维护或页面结构变化失败。输出中的 `source_status` 和 `errors` 应作为分析完整性判断的一部分。

## 常见问题

### `ModuleNotFoundError: No module named 'mcp'`

安装 MCP 可选依赖：

```bash
pip install --break-system-packages -r requirements-mcp.txt
```

### `Cannot uninstall jsonschema ... no RECORD file`

某些系统的 `jsonschema` 来自 apt/debian 包。可以在虚拟环境中安装，或在当前机器上用：

```bash
pip install --break-system-packages --ignore-installed jsonschema -r requirements-mcp.txt
```

### `czsc` 安装失败

确认 Rust 已安装：

```bash
rustc --version
cargo --version
```

然后重新安装：

```bash
pip install --break-system-packages --force-reinstall git+https://github.com/waditu/czsc.git
```

### Yahoo/CoinGecko/Binance 请求失败

等待一段时间后重试，或缩小 `blocks`：

```bash
python3 -m hermes_finance fetch crypto BTC --blocks price
```

这个命令只用于快速确认 Binance price block 可用；正式分析请使用 `python3 -m hermes_finance analyze crypto BTC --blocks all`。

### A股远程节点不可用

不传 `--remote` 时会尝试本地降级。需要完整北向资金、板块资金流等数据时，配置可访问国内数据源的 SSH host 后传入：

```bash
python3 -m hermes_finance fetch a-share --stock 600519 --remote ash-remote
```

## 开发与验证

```bash
python3 -m compileall -q bin hermes_finance hermes_finance_mcp scripts skills/multi-market-analysis/scripts tests
python3 -m unittest discover -s tests -v
python3 /root/.codex/skills/.system/skill-creator/scripts/quick_validate.py skills/multi-market-analysis
```

MCP 验证：

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
            print([t.name for t in (await session.list_tools()).tools])
            print([p.name for p in (await session.list_prompts()).prompts])
            print([rt.uriTemplate for rt in (await session.list_resource_templates()).resourceTemplates])

anyio.run(main)
PY
```

## 免责声明

本项目用于技术研究和数据分析流程演示，不构成投资建议。市场有风险，交易决策需自行负责。
