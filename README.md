# Hermes Finance — AI 驱动金融市场分析

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-v1.2.11-green.svg)](https://github.com/Lzh-xbccz/hermes-finance/releases)
[![Releases](https://img.shields.io/github/v/release/Lzh-xbccz/hermes-finance?include_prereleases&label=latest)](https://github.com/Lzh-xbccz/hermes-finance/releases)

让 AI 帮你分析金融市场。喊一声"分析 BTC"，自动拉行情、合约、链上、宏观数据，八维过一遍，过不了方向质量门槛就说观望，过得去才给多空。

覆盖：加密货币 / 商品期货 / 外汇 / A股 / 美股。

---

## 怎么用

### 装上就能用

```bash
bash install.sh
```

### 三种用法

**1. 在 AI 工具里用（推荐）**

支持 Claude Code、Codex、Cursor、VS Code Copilot、Gemini、Roo、Cline 等。项目里配好了对应的 `.mcp.json` 等文件，AI 自动识别。

打开 AI 工具，直接说：

> "分析 BTC"
> "EURUSD 现在怎么看"
> "帮我看看上证指数"

AI 会自动拉数据、过八维、出结论。

**2. 命令行用**

```bash
python3 -m hermes_finance analyze crypto BTC
python3 -m hermes_finance analyze forex EURUSD
python3 -m hermes_finance analyze futures GC
python3 -m hermes_finance analyze us-equity SPY
python3 -m hermes_finance analyze a-share --stock 600519
```

**3. 独立脚本用**

```bash
python3 skills/crypto-market-analysis/scripts/fetch_data.py BTC all
python3 skills/crypto-market-analysis/scripts/market_structure_chart.py BTC
python3 skills/futures-market-analysis/scripts/futures_fetch.py GC
```

### 选交易风格

第一次用的时候，AI 会问你：

> 短线（1H+15min）、中线（1D+4H）、还是长线（1W+1D）？

选完以后所有缠论分析自动用对应级别。想换随时说"切换到中线模式"。

也可以设环境变量：

```bash
export HERMES_TRADING_MODE=medium
```

---

## 怎么分析

不是看一眼 K 线就说涨跌。分六步走：

### 第一步：认市场

你给个标的——BTC、600519、EURUSD、CL、AAPL——它先判断这是什么市场。不会把 A 股代码当成加密货币，也不会把期货当成美股。

### 第二步：拉数据

根据市场类型，跑到各个数据源去抓数据。

拿加密货币举例，同时拉八个来源：

| 拉什么 | 从哪拉 |
|--------|--------|
| K 线（日线、4H、1H） | 币安 |
| 合约数据（持仓量、资金费率、多空比） | 币安/Bybit |
| 链上数据（哈希率、大额转账、Mempool） | Blockchain.info |
| 恐惧贪婪指数 | Alternative.me |
| 宏观（VIX、DXY、标普500） | Yahoo Finance |
| 期权（Put/Call 比率） | Deribit |
| 交易所价差（币安 vs OKX） | 各交易所 API |
| 新闻（ETF、监管、机构动向） | Google News RSS |

每个来源拉成功还是失败都会记下来。缺了什么后面会明确标注。

### 第三步：缠论算结构

把 K 线数据喂给缠论引擎，按你选的交易频段（短线 1H+15min、中线 1D+4H、长线 1W+1D）做多级别分析：

- 找笔——这段行情是向上还是向下
- 划中枢——多空双方在哪个区间打架
- 判买卖点——一买二买三买出现了吗
- 查背驰——价格创新高了但力度跟不上，要反转吗
- 共振评分——大级别和小级别方向一致吗

（A 股、外汇、期货的 K 线由采集器提供，不依赖币安。非加密市场走同一个缠论引擎，只是数据来源不同。）

### 第四步：七维投票

缠论是第八维。前面七个维度先投票：

拿加密货币来说：

| 维度 | 判什么 |
|------|--------|
| 技术结构 | K 线形态——趋势推进还是箱体震荡 |
| 链上真相 | 大户在吸筹还是派发 |
| 合约结构 | 多空比极端了吗，持仓量在增还是减 |
| 情绪反指 | 极度恐惧还是极度贪婪 |
| 宏观驱动 | 美元在走强还是走弱，美股在涨还是跌，VIX 恐慌吗 |
| 交易所验证 | 币安和 OKX 的价差大不大 |
| 新闻事件 | ETF 资金流入还是流出，有没有监管利空 |

每个维度独立投一票：偏多、偏空、或中性。同类的数据源合并成一个维度，不会重复投票。

### 第五步：过方向质量门槛

不是投完票就完了。有三道关卡：

1. **数量关**——至少 3 个维度同方向，且领先反方向至少 2 个维度
2. **关键维度不能缺**——如果 K 线都没拉到，不给方向
3. **不能有硬反证**——比如美元暴涨 + 美股暴跌同时出现，方向打架就观望

### 第六步：缠论确认

前七维过了门槛，再看缠论：

- 缠论也同方向 → 增强信心
- 缠论反方向 → 降级，标出来"缠论冲突"
- 缠论跑不了（缺 K 线）→ 标"缠论不足"，仍以前七维为准

**缠论永远不主导方向。** 它是确认层，不是决策层。

---

## 结论怎么出

过了门槛的给方向，过不了的就说观望。观望不是失败——证据不够还硬给方向才是问题。

输出的报告里有：

- 数据完整性——哪些拉到了，哪些缺了
- 七维主判断——每个维度偏多还是偏空
- 方向质量门槛——逐项列出来，过没过
- 反向审计——做多之前先看做空的最强理由是什么
- 缠论确认——共振还是背驰还是不可用
- 最终方向——偏多、偏空、震荡、观望
- 情景推演——如果涨了怎么办，如果跌了怎么办
- 交易计划——过了门槛才给入场/止损/止盈

---

## 八个市场

| 市场 | 分析重点 |
|------|---------|
| 加密货币 | 链上+合约+情绪+宏观+缠论，八维全量 |
| 商品期货 | K线+OI/费率+EIA库存+CFTC持仓+OVX/DXY |
| 外汇 | K线+利差(5s10s+对手国)+央行日历+CFTC |
| A股 | K线+北向资金+涨跌家数+板块轮动+Sequoia量化选股 |
| 美股 | K线+VIX/10Y+公司事件+ETF交叉验证 |
| 多市场路由 | 输入标的自动识别市场 |
| 缠论引擎 | 多级别联立+中枢嵌套+共振评分 |
| 山寨检测 | 识别 Pump & Dump 模式 |

---

## 项目结构

```
hermes-finance/
├── hermes_finance/          # 共享核心（CLI/MCP/Skills 都用它）
├── hermes_finance_mcp/      # MCP server（给 AI 工具调用）
├── scripts/                 # 可执行脚本
│   ├── czsc_analyze.py      #   缠论引擎
│   └── shared_ta.py         #   共享技术分析
├── skills/                  # 8 个分析技能（每个都有 SKILL.md + 采集脚本 + 分析脚本）
└── bin/                     # 入口脚本
```

---

## 更新日志

完整日志见 [Releases](https://github.com/Lzh-xbccz/hermes-finance/releases) 和 [CHANGELOG.md](CHANGELOG.md)。

技术结构逻辑图和 HTML 形态图说明见 [docs/TECHNICAL_ARCHITECTURE.md](docs/TECHNICAL_ARCHITECTURE.md)。

**v1.2.11** — Crypto 形态图统一改为外沿包络线：上轨包住摆高、下轨托住摆低，避免单币锚点补丁

**v1.2.10** — 修复 Crypto 下降/楔形上轨：使用峰值后的 lower high 链，BTC 上轨不再被早期高点带偏

**v1.2.9** — Crypto 市场架构图新增子趋势层：父级通道保留，最近回调/反弹通道单独绘制

**v1.2.8** — 修复 Crypto 底部趋势模式上轨：连接主升有效摆高，跳过回调 lower high

**v1.2.7** — 优化 Crypto 市场架构图：底部趋势线优先，ZEC 这类 2026-06-05 起涨结构从关键低点开始连线

**v1.2.6** — 修复 Crypto 市场架构图：保留父级上升/下降趋势，短线反向摆点只作为扰动，结构线从有效摆点起画

**v1.2.5** — 新增 Crypto 4H 市场架构 HTML 形态图（上轨/下轨/中轨/摆点/突破触发）

**v1.2.4** — 新增技术结构 Mermaid 逻辑图文档

**v1.2.3** — 新增 Crypto 4H 市场架构识别（通道/箱体/楔形/扩散结构）

**v1.2.2** — 修复 Crypto 技术结构“偏空但缺失”的矛盾判定

**v1.2.1** — CZSC 稳定性修复、版本锁定、动态 K 线窗口、测试恢复

**v1.2.0** — 交易频段系统（短线/中线/长线）、shared_ta 消除重复、默认 1H+15m

**v1.1.x** — Crypto 新闻基本面、方向质量门槛、反向审计、AI 客户端适配

**v1.0.x** — 首次发布，15 项修复


## ⚠️ 免责声明

本项目仅用于技术交流和学习研究，不构成投资建议。市场有风险，投资需谨慎。
