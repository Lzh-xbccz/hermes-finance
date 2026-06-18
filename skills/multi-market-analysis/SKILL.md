---
name: multi-market-analysis
description: 跨市场分析总路由。先识别标的与市场，再指向对应 skill 处理加密货币、A股、商品期货、股指期货、外汇、美股/ETF/指数等，并统一要求按六维框架输出。Use when Codex needs one entry point for market analysis and must route the request to the correct market-specific skill instead of mixing frameworks.
---

# Multi-Market Analysis

> ⛔ 铁律：你不是在写行情播报，你是在做法医解剖。每句话必须回答"为什么"。禁止"可能""或许""值得关注"。每个数据必须有对比基准。每个判断必须有因果链。

这是总入口，不是最终分析模板。先分类，再转 skill。

## 何时使用

- 用户给的是混合市场请求，例如 `CL`、`GC`、`ES`、`EURUSD`、`AAPL`、`SPY`、`BTC`、`000001`
- 用户要统一入口，不想手动挑 skill
- 用户的问题里存在市场歧义，需要先判断是 `加密 / A股 / 外汇 / 期货 / 美股`

## 铁律

1. 这个 skill 只负责路由，不要在这里直接完成长篇分析，除非用户明确只要分类结果。
2. 市场不明时先消歧义；不能把 `黄金`、`原油`、`纳指` 直接当唯一精确标的。
3. 路由完成后，必须使用目标 skill 的六维框架，不要混用别的市场指标。
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
5. 一旦进入目标 skill，就按目标 skill 的六维框架完成分析。

## 双入口执行

- Skills/CLI：使用 `python3 -m hermes_finance fetch <market> <symbol>` 拉结构化数据，或 `python3 -m hermes_finance analyze <market> <symbol>` 生成 Markdown 摘要。
- MCP：调用 `fetch_market_data_tool`、`analyze_market_tool` 或市场专用工具 `analyze_crypto` / `analyze_futures` / `analyze_forex` / `analyze_us_equity` / `analyze_a_share`。
- MCP resources：读取 `finance://framework/{market}` 获取目标市场 Skill 规则，读取 `finance://routing` 获取路由规则。

## 目标 Skill 映射

- `crypto-market-analysis`
  - 加密货币六维分析，严格单方向 `做多 / 做空 / 观望`
- `a-share-market-analysis`
  - A股六维分析，默认 `偏多 / 偏空 / 震荡`，强调 `T+1`
- `futures-market-analysis`
  - 商品期货、股指期货、贵金属、能源、宏观期货
- `forex-market-analysis`
  - 外汇货币对与美元指数相关分析
- `us-equity-market-analysis`
  - 美股个股、ETF、全球主要现金指数

## 六维统一要求

> ✅ **2026-05-06 基本对齐**：所有六个市场技能已升级到统一六维框架，尽量向 `crypto-market-analysis` 靠拢；但仍须按各市场的数据缺口规则保守降级，不能因为完成路由就跳过 `观望 / 偏保守` 处理。

除非目标市场有特别限制，否则各 skill 都应严格按六维输出：

1. 技术面
2. 市场结构
3. 大资金/主导力量
4. 情绪面
5. 宏观基本面
6. 交叉验证

如果某个市场没有天然对应项，例如外汇没有链上、商品没有资金费率，就必须在该 skill 中定义替代指标。

## 增强分析层（可选）

> 本机已部署 Anthropic `financial-services` 桥接包（60+ 金融技能）。
> 当分析需要比六维框架更深的宏观/期权/事件维度时，各市场技能可加载对应增强块。

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
