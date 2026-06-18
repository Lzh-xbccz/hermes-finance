---
name: multi-market-analysis
description: 跨市场分析总路由。先识别标的与市场，再指向对应 skill 处理加密货币、A股、商品期货、股指期货、外汇、美股/ETF/指数等；所有市场尽可能按八维框架，CZSC 为第 8 维确认。Use when Codex needs one entry point for market analysis and must route the request to the correct market-specific skill instead of mixing frameworks.
---

# Multi-Market Analysis

> ⛔ 铁律：你不是在写行情播报，你是在做证据审计。每个方向判断必须回答"为什么"，并先做反向审计。允许使用"证据不足"、"方向未确认"、"观望"；禁止在证据冲突时硬给做多/做空。

这是总入口，不是最终分析模板。先分类，再转 skill。

## 何时使用

- 用户给的是混合市场请求，例如 `CL`、`GC`、`ES`、`EURUSD`、`AAPL`、`SPY`、`BTC`、`000001`
- 用户要统一入口，不想手动挑 skill
- 用户的问题里存在市场歧义，需要先判断是 `加密 / A股 / 外汇 / 期货 / 美股`

## 铁律

1. 这个 skill 只负责路由，不要在这里直接完成长篇分析，除非用户明确只要分类结果。
2. 市场不明时先消歧义；不能把 `黄金`、`原油`、`纳指` 直接当唯一精确标的。
3. 路由完成后，必须使用目标 skill 的八维映射；1-7 维先给主判断，第 8 维缠论只做确认/冲突/不足。
4. 所有实时分析都必须使用最新数据。
5. 缺少目标 skill 的关键数据块时，按目标 skill 的降级规则处理。
6. **⚠️ 数据获取优先通过共享核心 `hermes_finance` 或 MCP tools；底层会调用各市场 fetch 脚本。禁止直接调 mcp_yfinance（429限流）或 curl Yahoo Finance API。** 宏观数据（VIX/DXY/TNX）不足时用 Tavily 搜索补充。

## 路由流程

1. 读取 [references/routing.md](./references/routing.md)。
2. 优先运行 `python3 -m hermes_finance route "<user request or symbol>"` 做第一轮分类；在 MCP 客户端中调用 `route_market_tool`。
   - 兼容入口：`python3 scripts/route_market.py "<user request or symbol>"`。
3. 根据分类结果转入对应 skill：
- `crypto` -> `crypto-market-analysis`
- `a_share` -> `a-share-market-analysis`
- `futures` -> `futures-market-analysis`
- `forex` -> `forex-market-analysis`
- `us_equity` -> `us-equity-market-analysis`
4. 如果 `route_market.py` 返回 `ambiguous`，先向用户确认标的。
5. 一旦进入目标 skill，就按目标 skill 的当前框架完成分析。不要把任何市场降级成快速摘要，也不要把其他市场硬套 crypto 链上/期权指标。

## 双入口执行

- Skills/CLI：使用 `python3 -m hermes_finance fetch <market> <symbol>` 拉结构化数据，或 `python3 -m hermes_finance analyze <market> <symbol>` 生成 Markdown 摘要。
- MCP：调用 `fetch_market_data_tool`、`analyze_market_tool` 或市场专用工具 `analyze_crypto` / `analyze_futures` / `analyze_forex` / `analyze_us_equity` / `analyze_a_share`。
- MCP resources：读取 `finance://framework/{market}` 获取目标市场 Skill 规则，读取 `finance://routing` 获取路由规则。

## 目标 Skill 映射

- `crypto-market-analysis`
  - 加密货币八维分析：1-7 维先给 `七维主判断`，第 8 维 CZSC 只做确认/冲突/不足，最终 `做多 / 做空 / 观望`
- `a-share-market-analysis`
  - A股八维分析，默认 `偏多 / 偏空 / 震荡`，强调 `T+1`
- `futures-market-analysis`
  - 商品期货、股指期货、贵金属、能源、宏观期货
- `forex-market-analysis`
  - 外汇货币对与美元指数相关分析
- `us-equity-market-analysis`
  - 美股个股、ETF、全球主要现金指数

## 框架统一要求

> ✅ **2026-06-18 对齐**：所有市场尽可能使用八维输出。1-7 维按市场专属数据映射形成主判断，第 8 维是 CZSC 缠论确认；CZSC 不可用时明确标注不足并降级。

### 所有市场尽可能八维

所有实时分析都必须使用目标 skill 的八维映射。通用结构如下，具体名称以目标 skill 为准：

1. 技术结构
2. 市场专属结构层（crypto=链上，futures=可执行合约层，forex=利差，美股=行业结构，A股=资金面）
3. 主导资金/主导力量
4. 情绪/波动率
5. 宏观驱动
6. 交叉验证
7. 市场专属增强维度
8. 缠论结构

输出必须包含 `七维主判断`、`方向质量门槛`、`反向审计`、`缠论确认`、`最终方向`。CZSC 不能覆盖 1-7 维。若方向质量门槛不过关，最终方向必须是 `观望 / 震荡 / 无方向优势`，不得硬给做多/做空。

### 非 crypto 维度映射原则

非 crypto 市场不硬套链上/期权指标，使用市场专属替代维度：

| 市场 | 第2维 | 第3维 | 第7维 |
|------|------|------|------|
| futures | Binance/近月可执行层、OI、资金费率 | CFTC/EIA/主导力量 | 传统期货结构/供需增强 |
| forex | 利差与美元结构 | 央行/收益率/政策预期 | 仓位/CFTC |
| us_equity | 市场/行业结构 | 公司事件/机构主导 | 流动性与缺口风险 |
| a_share | 资金面/北向 | 市场结构/涨跌家数 | Sequoia/量化策略信号 |

如果某个维度没有可用数据，必须写「不足」并降级，不得删除该维度。

## 增强分析层（可选）

> 本机已部署 Anthropic `financial-services` 桥接包（60+ 金融技能）。
> 当分析需要比默认八维框架更深的宏观/期权/事件维度时，各市场技能可加载对应增强块。

### 增强块与市场映射

| 增强块 | 来源技能 | 适用市场 | 功能 |
|--------|---------|---------|------|
| 增强宏观 | `macro-rates-monitor` | 全部 | 利率曲线 + DXY + 实际利率 + VIX 全景 |
| BTC 期权面 | `option-vol-analysis` | crypto | Deribit IV + 偏斜 + Put/Call 流 |
| 催化剂日历 | `catalyst-calendar` | 全部 | CPI/FOMC/加密特有事件日历 |
| 财报分析 | `earnings-analysis` | us_equity | 超预期/miss + 指引 + 机构反应 |
| 套息交易 | `fx-carry-trade` | forex | 利差 + 套息吸引力 |
| 利率曲线 | `swap-curve-strategy` | forex | 2s10s 陡峭化/平坦化策略 |

### MCP 数据源（收费，需 API Key）

> `financial-services/.mcp.json` 列出了 11 个 MCP 服务器（LSEG、S&P Global、FactSet、Moody's 等）。
> 已在 `~/.hermes/config.yaml` 注册，但实际调用需要有效的 API Key。
> **优先使用免费替代方案**（Yahoo Finance、Deribit、Google News RSS）。

## 资源

- [references/routing.md](./references/routing.md)
- [scripts/route_market.py](./scripts/route_market.py)

如果用户已经明确指定某个市场 skill，可以跳过本 skill，直接进入目标 skill。
