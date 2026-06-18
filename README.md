# Hermes Finance — 面向 AI Agent 的八维金融分析框架

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-v1.1.3-green.svg)](https://github.com/Lzh-xbccz/hermes-finance/releases)
[![Releases](https://img.shields.io/github/v/release/Lzh-xbccz/hermes-finance?include_prereleases&label=latest)](https://github.com/Lzh-xbccz/hermes-finance/releases)

Hermes Finance 是一个给 **Claude Code、Codex、Cursor、Gemini、Cline、Roo、Continue、VS Code Copilot 等 AI 编程/研究工具** 使用的金融市场分析框架。它把行情采集、市场路由、八维分析、CZSC 缠论确认和 MCP/Skills 接入放在同一个仓库里，目标是让 AI 不再只给“涨跌摘要”，而是按统一证据链输出可复核的市场判断。

覆盖市场：

- **加密货币**：BTC、ETH、SOL 等现货/合约/链上/宏观联动。
- **商品与股指期货**：CL、BZ、GC、SI、HG、NG、ES、NQ 等；商品线支持 Binance TradFi 永续如 `CLUSDT`、`XAUUSDT`。
- **外汇**：DXY、EURUSD、USDJPY、GBPUSD、AUDUSD 等。
- **A 股**：指数、个股、市场广度、北向/板块资金、Sequoia-X 量化扫描。
- **美股/ETF/指数**：AAPL、TSLA、SPY、QQQ 等技术、行业、宏观和事件代理。

---

## 项目解决什么问题

很多 AI 工具做金融分析时容易出现三个问题：只看单一价格、漏掉数据源状态、技术图形和基本面判断互相混在一起。Hermes Finance 用固定流程约束输出：

1. 先识别市场和标的，避免把 `CL`、`CLUSDT`、`BTC`、`AAPL` 路由错。
2. 拉取对应市场的数据源，明确哪些成功、哪些降级、哪些不可用。
3. 用前七维形成主判断，先过方向质量门槛和反向审计，再用第八维 CZSC 缠论做确认、冲突或不足标注。
4. 输出 `七维主判断`、`方向质量门槛`、`反向审计`、`缠论确认`、`最终方向`，并给出情景、失效条件和风险点。

这套规则同时写进了 CLI、Skills、MCP server instructions、MCP prompts 和各类 AI 客户端配置，方便不同工具得到一致结果。

---

## 核心特性

| 能力 | 说明 |
|---|---|
| 严格八维分析 | 每个市场都尽量输出 1-7 维主判断 + 第 8 维 CZSC 缠论确认 |
| 双版本接入 | Skills 给 Codex/Agent 读取，MCP 给 Claude Desktop、Cursor 等 MCP 客户端调用 |
| 共享核心库 | `hermes_finance/` 统一路由、采集、分析、CZSC 适配和 Markdown/JSON 输出 |
| 多市场覆盖 | 加密货币、商品/股指期货、外汇、A股、美股/ETF/指数 |
| AI 客户端适配 | Claude Code、Codex、Cursor、Copilot、Gemini、Windsurf、Cline、Roo、Continue、Zed、Amp |
| 缠论集成 | 基于 [czsc](https://github.com/waditu/czsc) v1.0，多级别 K 线、笔、中枢、买卖点候补和结构评分 |
| 数据源降级 | Binance、CoinGecko、Yahoo、CFTC、EIA、baostock、akshare、腾讯等数据源失败时保留状态 |
| 可验证工程 | 单元测试、compileall、Skill 校验和 MCP smoke test 覆盖核心路径 |

---

## 八维输出契约

Hermes Finance 的正式市场分析不是“行情快照”，而是固定输出契约：

| 顺序 | 模块 | 目的 |
|---|---|---|
| 0 | 数据完整性 | 列出行情、合约、宏观、链上、资金、CZSC 等数据是否可用 |
| 1-7 | 七维主判断 | 按市场特征建立方向判断，不让单一指标决定结论 |
| Gate | 方向质量门槛 | 逐项列出偏多/偏空/中性/缺失，只在同向证据足够且无硬反证时允许给方向 |
| Audit | 反向审计 | 做多前先审最强空头证据，做空前先审最强多头证据；证据可比则观望/震荡 |
| 8 | CZSC 缠论结构 | 用缠论确认、冲突或标注不足；不覆盖前七维判断 |
| 结论 | 最终方向 | 给出偏多、偏空、震荡、观望等方向与置信度 |
| 风控 | 情景与失效 | 给出关键价位、触发条件、反证条件和风险提示 |

不同市场的前七维会按资产特征调整，例如加密货币包含链上/合约/流动性，期货包含传统库存/CFTC/跨品种验证，外汇包含利率差和央行路径，A 股包含北向/广度/板块轮动，美股包含公司事件和行业结构。第八维统一使用 CZSC 缠论确认。

---

## 双版本金融分析 + AI 客户端适配

Hermes Finance 现在同时支持 **Skills** 和 **MCP** 两种使用方式：

- **Skills 版**：给 Codex/Agent 使用的市场分析技能，保留八大技能目录和严格输出框架。
- **MCP 版**：给 Claude Desktop、Cursor、支持 MCP 的 Agent 客户端调用，暴露标准 tools/resources/prompts。
- **AI 工具适配**：新增 Claude Code、Codex、Cursor、VS Code/Copilot、Gemini、Roo、Continue、Zed 等项目级配置，以及 Claude Desktop、Windsurf、Cline、Amp 等用户级模板。
- **MCP server instructions**：连接后自动提示 AI 先路由标的、读取市场框架、分离事实与推断，并报告数据源状态。
- **共享核心库**：`hermes_finance/` 统一路由、采集器调用、缠论确认和 Markdown/JSON 输出，避免维护两套行情逻辑。

完整安装、使用、MCP 接入、AI 客户端适配、功能和排错见 [docs/USAGE.md](docs/USAGE.md) 与 [docs/AI_CLIENTS.md](docs/AI_CLIENTS.md)。

---

## 快速体验

```bash
# 安装基础依赖
bash install.sh

# 如需 MCP 客户端接入，同时安装 MCP 依赖
INSTALL_MCP=1 bash install.sh

# 路由标的
python3 -m hermes_finance route BTC
python3 -m hermes_finance route CLUSDT

# 八维分析
python3 -m hermes_finance analyze crypto BTC --blocks all
python3 -m hermes_finance analyze futures CL
python3 -m hermes_finance analyze forex EURUSD
python3 -m hermes_finance analyze us-equity SPY
python3 -m hermes_finance analyze a-share --stock 600519

# MCP server
python3 bin/hermes_finance_mcp.py
```

`czsc` 需要从 GitHub 源码安装；`install.sh` 已包含对应流程。更完整的安装、客户端配置和排错见 [docs/USAGE.md](docs/USAGE.md)。

---

## 适合谁使用

- 想让 Claude Code、Codex、Cursor、Cline、Roo 等工具直接调用金融分析能力的 AI 用户。
- 想把 Skills 和 MCP 两套形态同时维护在一个仓库里的 Agent 开发者。
- 想做多市场联动分析、但又希望输出格式稳定可复核的研究者。
- 想把 CZSC 缠论作为确认层，而不是单独依赖技术图形下结论的交易系统开发者。

---

## 🏗️ 项目架构

```
hermes-finance/
├── requirements.txt                 # Python 依赖
├── requirements-mcp.txt             # MCP 可选依赖
├── .mcp.json                        # Claude Code / 通用 MCP 项目配置
├── .codex/config.toml               # Codex 项目 MCP 配置
├── .cursor/mcp.json                 # Cursor 项目 MCP 配置
├── .vscode/mcp.json                 # VS Code / Copilot MCP 配置
├── .gemini/settings.json            # Gemini CLI MCP 配置
├── .continue/mcpServers/            # Continue MCP server 配置
├── install.sh                       # 一键安装
├── VERSION                          # 版本号
├── CHANGELOG.md                     # 完整更新日志
├── bin/hermes_finance_mcp.py        # 便携 MCP launcher
├── integrations/                    # 各 AI 客户端用户级配置模板
├── hermes_finance/                  # 共享核心 API（CLI / Skills / MCP 共用）
├── hermes_finance_mcp/              # MCP server
├── scripts/
│   ├── czsc_analyze.py              # 缠论多级别联立分析（核心引擎）
│   ├── market_analyze.py            # 多市场统一入口（共享核心薄封装）
│   └── localize_chart.py            # 图表中文化工具
└── skills/                          # 8 个分析技能
    ├── crypto-market-analysis/      # 🟠 加密货币 — 八维分析
    ├── futures-market-analysis/     # 🟡 商品期货 — 八维分析
    ├── forex-market-analysis/       # 🔵 外汇 — 八维分析+利率差
    ├── a-share-market-analysis/     # 🔴 A股 — 八维+量化选股(Sequoia-X)
    ├── us-equity-market-analysis/   # 🟣 美股 — 八维分析
    ├── multi-market-analysis/       # 🔀 智能路由
    ├── czsc-ccxt-analysis/          # 🎯 缠论引擎（薄封装→主脚本）
    └── microcap-pnd-system/         # ⚠️ 极端山寨检测
```

---

## 🔌 双版本入口

### 1. Skills 版本

Skills 目录保留 8 个分析技能：

- `multi-market-analysis`：跨市场总路由
- `crypto-market-analysis`：加密货币七维因果 + 第八维缠论确认
- `futures-market-analysis`：商品/股指期货八维分析
- `forex-market-analysis`：外汇八维 + 利率差
- `a-share-market-analysis`：A股八维 + Sequoia-X 选股
- `us-equity-market-analysis`：美股/ETF/指数八维分析
- `czsc-ccxt-analysis`：缠论引擎
- `microcap-pnd-system`：极端山寨/Pump & Dump 风险识别

### 2. MCP 版本

```bash
pip install -r requirements-mcp.txt
python3 bin/hermes_finance_mcp.py
```

`.mcp.json`、`.codex/config.toml`、`.cursor/mcp.json`、`.vscode/mcp.json`、`.gemini/settings.json` 等项目级配置已放在仓库内；`integrations/` 提供 Claude Desktop、Windsurf、Cline、Amp 等用户级模板。

MCP 暴露的 tools：

- `route_market_tool`
- `fetch_market_data_tool`
- `analyze_market_tool`
- `analyze_crypto`
- `analyze_futures`
- `analyze_forex`
- `analyze_us_equity`
- `analyze_a_share`
- `czsc_analyze_tool`

MCP resources/prompts：

- `finance://routing`
- `finance://framework/{market}`
- `deep_market_analysis`
- `czsc_confirmation_review`

### 3. 共享 CLI

```bash
python3 -m hermes_finance route BTC
python3 -m hermes_finance fetch futures GC
python3 scripts/market_analyze.py crypto bitcoin --markdown
```

### 4. AI 客户端适配

项目内已放好常见 AI 工具的配置：

| 工具 | 文件 |
|---|---|
| Claude Code | `.mcp.json`, `CLAUDE.md` |
| Codex CLI / IDE | `.codex/config.toml`, `AGENTS.md` |
| Cursor | `.cursor/mcp.json`, `.cursor/rules/hermes-finance.mdc` |
| VS Code / GitHub Copilot | `.vscode/mcp.json`, `.github/copilot-instructions.md` |
| Gemini CLI | `.gemini/settings.json`, `GEMINI.md` |
| Roo / Continue / Zed | `.roo/mcp.json`, `.continue/mcpServers/hermes-finance.yaml`, `.zed/settings.json` |

生成用户级配置模板：

```bash
python3 scripts/render_ai_client_config.py claude-desktop
python3 scripts/render_ai_client_config.py windsurf
python3 scripts/render_ai_client_config.py cline
python3 scripts/render_ai_client_config.py codex
```

完整矩阵见 [docs/AI_CLIENTS.md](docs/AI_CLIENTS.md)。

---

## 🎯 八大分析技能

### 1. 加密货币 — 八维分析 🟠

| # | 维度 | 核心问题 |
|---|------|---------|
| 1 | 技术结构 | 趋势方向？支撑阻力在哪？ |
| 2 | 合约数据 | OI / 资金费率 / 多空比 — 谁在押注？ |
| 3 | 量价关系 | 放量还是缩量？真实买盘还是对倒？ |
| 4 | 基本面 | 链上数据 — 抛压从哪来？解锁在何时？ |
| 5 | 情绪面 | 恐惧贪婪指数 — 市场狂热还是绝望？ |
| 6 | 宏观联动 | **实时拉取** VIX / DXY / SPY + BTC-SPY 5日趋势联动 |
| 7 | 流动性 | 深度 / 滑点 — 能安全进出吗？ |
| 8 | **缠论结构** | **czsc 4H+15min — 中枢在哪？一二三买？** |

### 2. 商品期货 — 八维分析 🟡

覆盖 CL（WTI 原油）、BZ（Brent 原油）、GC（黄金）、SI（白银）、HG（铜）、NG（天然气）、PL（铂金）、PA（钯金）、ES/NQ/YM/RTY（股指期货）；商品线自动接入 Binance TradFi 永续 `CLUSDT`、`BZUSDT`、`XAUUSDT`、`XAGUSDT`、`COPPERUSDT`、`NATGASUSDT`、`XPTUSDT`、`XPDUSDT`：

| 维度 | 数据源 |
|------|--------|
| 技术结构 | K线形态 + MACD + 布林 |
| 可执行合约层 | Binance TradFi 永续 K线 / OI / 资金费率 / 多空比 |
| 传统期货结构 | EIA原油库存 / COMEX黄金持仓 / CFTC |
| 主导力量 | OVX/VIX / ETF / DXY / COT |
| 情绪/波动率 | OVX/VIX + 挤仓情绪 |
| 宏观与事件 | DXY + 实际利率 + 美联储/OPEC/地缘 |
| 交叉验证 | 相关品种联动 / ETF / 美债 / 现货代理 |
| 缠论结构 | 采集器 K线转 CZSC，第8维只做确认/冲突/不足 |

Binance TradFi 商品永续作为可执行 K 线、资金费率、OI、多空比层；Yahoo 近月代理、CFTC、EIA、OVX/DXY 继续作为传统期货和宏观验证层。

### 3. 外汇 — 八维分析 + 利率差 🔵

覆盖 DXY、EURUSD、USDJPY、GBPUSD、AUDUSD：

| 维度 | 数据源 |
|------|--------|
| 技术结构 | K线 + 支撑阻力 |
| 利率差 | **US 10Y/5Y 利差 + 对手国利率代理 + DXY 趋势** |
| 央行/主导力量 | Fed/ECB/BoJ/BoE/RBA 政策路径 |
| 情绪面 | VIX + risk-on / risk-off |
| 经济数据 | NFP / CPI / PMI 驱动 + 央行事件日历 |
| 交叉验证 | DXY / 美债 / 相关交叉盘 / 黄金原油 |
| 仓位/CFTC | CFTC 金融期货持仓（CSV优先） |
| 缠论结构 | 采集器 K线转 CZSC，第8维只做确认/冲突/不足 |

### 4. 缠论核心引擎 🎯

基于 [waditu/czsc](https://github.com/waditu/czsc) v1.0（Rust 实现），使用公开 API：

```python
from czsc.connectors.ccxt_connector import get_raw_bars
from czsc import CZSC, format_standard_kline, Freq
from czsc.signals import cxt_first_buy_V221126

# 数据获取
df = get_raw_bars('BTCUSDT', '4h', sdt='20260401', edt='20260616')
bars = format_standard_kline(df, Freq.F240)

# 缠论分析
c = CZSC(bars, max_bi_num=50)
c.bi_list       # 笔序列
c.fx_list       # 分型：顶/底
c.ubi_fxs       # 中枢参与分型

# 信号（公开 czsc.signals 导入）
res = cxt_first_buy_V221126(c)
```

**多级别共振分析（四层）：**

1. 笔方向 — 各级别最后一笔同向？
2. 中枢位置 — 价格在各级别中枢上方/内部/下方？
3. 中枢嵌套 — 小级别中枢是否离开大级别中枢？
4. **综合评分**（-5 ~ +5）— 阈值 2/4，防止假信号

### 5. 智能路由 🔀

自动识别市场类型，分派到对应技能：

| 输入 | 路由到 |
|------|--------|
| `BTC` / `ETH` / `SOL` | crypto-market-analysis |
| `CL` / `GC` / `ES` / `CLUSDT` / `XAUUSDT` | futures-market-analysis |
| `EURUSD` / `DXY` | forex-market-analysis |
| `600519` / `000001` | a-share-market-analysis |
| `AAPL` / `SPY` | us-equity-market-analysis |

### 6. A股 — 八维 + 量化选股 🔴

| 维度 | 指标 |
|------|------|
| 技术结构 | K线 + 均线 + MACD + KDJ |
| 资金面 | 北向资金净流入（A 股独有） |
| 市场结构 | 涨跌家数 / 涨停跌停统计 |
| 情绪量能 | 成交量对比 / 风险偏好 |
| 宏观政策 | PMI / 社融 / 利率 / 美股联动 |
| 板块轮动 | 行业资金流向 / 热点概念 |
| 量化信号 | Sequoia-X 7策略 |
| 缠论结构 | 腾讯日线/个股K线转 CZSC，第8维只做确认/冲突/不足 |

🆕 **Sequoia-X 量化选股引擎** — 7 种策略 × 5200+ 只 A 股：

- 基于 **baostock** 免费数据源（无需注册）→ 本地 SQLite
- 海龟突破 / 均线放量 / 高窄旗形 / 涨停洗盘 / 跌停反包 / RPS 突破 / 定增回补
- **v1.0.2 起 8 线程并行扫描**，收盘后 5 分钟出结果

### 7. 美股 — 八维分析 🟣

多时间框架技术结构 / 市场行业结构 / 公司事件 / 情绪期权代理 / 宏观利率 / 同业ETF交叉验证 / 流动性缺口风险 / CZSC 缠论确认。

### 8. 极端山寨检测 ⚠️

Pump & Dump 模式识别：24h 涨幅 > 50%、成交量异常、单交易所品种、无基本面。

---

## ⚡ 快速开始

> ⚠️ **czsc 必须从 GitHub 源码安装**（PyPI 的 0.10.x 是旧版，不含 Rust 核心）

### 一键安装

```bash
bash install.sh
```

安装 MCP 可选依赖：

```bash
INSTALL_MCP=1 bash install.sh
```

或手动：

```bash
# 1. Rust 工具链
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
source "$HOME/.cargo/env"

# 2. Python 依赖
pip install --break-system-packages git+https://github.com/waditu/czsc.git
pip install --break-system-packages ccxt pandas plotly baostock akshare pydantic-settings rich python-dotenv
pip install --break-system-packages -r requirements-mcp.txt
```

### 依赖表

| 依赖 | 用途 |
|------|------|
| `czsc` (git) | 缠论核心（Rust + PyO3） |
| `ccxt` ≥4.5 | 加密货币数据（Binance） |
| `pandas` ≥2.0 | 数据处理 |
| `plotly` ≥5.0 | lightweight-charts 渲染 |
| `baostock` ≥0.8.8 | A股免费数据源 |
| `akshare` ≥1.10 | A股定增公告 |
| `pydantic-settings` | 配置管理 |
| `rich` ≥13.0 | 终端日志美化 |
| `python-dotenv` ≥1.0 | 环境变量加载 |

### 运行

```bash
# 共享路由
python3 -m hermes_finance route BTC

# 统一采集（crypto 正式分析用 all；price 只适合连通性调试）
python3 -m hermes_finance fetch crypto BTC --blocks all
python3 -m hermes_finance fetch futures GC
python3 -m hermes_finance fetch forex EURUSD
python3 -m hermes_finance fetch us-equity AAPL
python3 -m hermes_finance fetch a-share --stock 600519

# 统一分析（默认尽量包含八维证据和 CZSC）
python3 -m hermes_finance analyze crypto BTC --blocks all
python3 scripts/market_analyze.py crypto bitcoin --markdown

# 缠论分析
python3 scripts/czsc_analyze.py BTCUSDT --freqs 4h,15m --report

# A股量化选股
cd skills/a-share-market-analysis/sequoia && python3 main.py
```

更完整的命令、MCP 客户端配置和输出说明见 [docs/USAGE.md](docs/USAGE.md)。

---

## 📋 更新日志

所有版本详见 [Releases](https://github.com/Lzh-xbccz/hermes-finance/releases) 和 [CHANGELOG.md](CHANGELOG.md)。

### v1.1.3 (2026-06-18) — 方向质量门槛与反向审计

- 新增全市场 `方向质量门槛` 和 `反向审计` 输出要求。
- futures / forex / us-equity / a-share 分析器改为多维证据门槛，证据分裂时默认观望/震荡。
- Crypto、MCP、README、AGENTS 和各 AI 客户端规则同步禁止硬给做多/做空。
- 新增方向门槛回归测试，覆盖反向宏观证据、公司事件缺口和指数震荡降级。

### v1.1.2 (2026-06-18) — CI 与脚本稳定性修复

- 新增 GitHub Actions CI，自动执行 compileall 和 unittest。
- 修复默认 `python -m unittest discover -v` 找不到测试的问题。
- 修复 `scripts/czsc_analyze.py --signals` 参数未生效的问题。
- 修复 `czsc_4h_15m.py` 固定日期窗口，改为动态回看。
- 加固 Yahoo Finance 限流、A 股远程命令构造和板块资金解析。

### v1.1.1 (2026-06-18) — AI 客户端适配补强

- 新增 portable MCP launcher：`bin/hermes_finance_mcp.py`。
- 新增 Claude Code、Codex、Cursor、VS Code/Copilot、Gemini、Roo、Continue、Zed 项目级配置。
- 新增 Claude Desktop、Windsurf、Cline、Amp、Continue、Zed 等 `integrations/` 用户级模板。
- 新增 `scripts/render_ai_client_config.py`，支持渲染多客户端绝对路径配置。
- MCP server 新增初始化 instructions，提升跨客户端使用一致性。
- 新增 [docs/AI_CLIENTS.md](docs/AI_CLIENTS.md)，集中说明 AI 工具适配、安装位置和验证方式。

### v1.1.0 (2026-06-18) — Skills + MCP 双版本架构

- 新增 `hermes_finance/` 共享核心 API，统一 CLI、Skills、MCP 的路由和采集调用。
- 新增 `hermes_finance_mcp/server.py`，提供 MCP tools/resources/prompts。
- 新增 `.mcp.json`、`requirements-mcp.txt` 和 `docs/USAGE.md`。
- `scripts/market_analyze.py` 与 `skills/multi-market-analysis/scripts/route_market.py` 改为共享核心薄封装。
- 新增基础测试，覆盖路由和服务层关键行为。

### v1.0.2 (2026-06-17) — 结构加固

- **czsc_analyze 三合一** — 两个 skill 脚本改为薄封装，核心逻辑统一
- **a_share_fetch 解耦** — 480 行内嵌字符串提取为独立文件（文件缩小 62%）
- **Sequoia 策略并行化** — 8 线程 + WAL 模式 + 批量读取
- **CFTC 升级 CSV** — futures/forex 优先读 ZIP/CSV，HTML 降级
- **对手国利率** — JPY/AUD/CHF/CNH 升级到 BWX/BNDX ETF 代理
- **Yahoo 限速器** — 全局 `_yf_throttle()`，请求间隔 ≥ 0.5s

### v1.0.1 (2026-06-17) — 分析逻辑修补

- **虚假利差修正** — `^IRX`(13周) → `^FVX`(5年)，3m10s → 5s10s
- **对手国利率代理** — EUR→BUND=F 期货，无数据货币对标注
- **共振阈值收紧** — 1/3 → 2/4，防止假信号
- **BTC-SPY 5日趋势** — 24h 快照 → 5日趋势 + 降级 fallback

### v1.0.0 (2026-06-17) — 首次正式发布

15 项修复：`import time` 缺失、硬编码路径/日期、macro 空壳、共振重写、CFTC 加固、私有 API 替换等。

---

## ⚠️ 免责声明

本项目仅用于 **技术交流和学习研究**，不构成任何投资建议。市场有风险，投资需谨慎。
