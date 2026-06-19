# Changelog

## Unreleased

## v1.2.6 (2026-06-19) — Crypto 市场架构趋势修复

### 修复

- 修复 4H 市场架构只取最后4组摆点，导致主升后的短线回调被误判为下降通道的问题。
- 结构线从选中结构的第一个有效摆高/摆低开始绘制，不再向更早取样窗口反推，避免起始点和价格严重失真。
- HTML 中轨改为在上下轨共同时间段内重新投影，避免上下轨起点不同导致中轨错位。

### 改进

- 市场架构新增候选选择：在多组摆点窗口中优先选择覆盖更完整、仍包住当前价格的父级结构。
- 最近4组摆点若与父级结构相反，会显示为 `短线扰动`，不直接覆盖主结构。
- 增加回归测试，覆盖“上升通道后短线回调仍保留父级上升架构”的场景。

### 验证

- `python3 -m py_compile skills/crypto-market-analysis/scripts/fetch_data.py skills/crypto-market-analysis/scripts/market_structure_chart.py tests/test_direction_gates.py`
- `python3 -m unittest tests.test_direction_gates -v`
- `python3 -m unittest discover -s tests`
- `python3 skills/crypto-market-analysis/scripts/market_structure_chart.py ZEC`

## v1.2.5 (2026-06-19) — Crypto 市场架构 HTML 形态图

### 新增

- 新增 `skills/crypto-market-analysis/scripts/market_structure_chart.py`，可生成 standalone lightweight-charts HTML 形态图。
- 图中直接绘制 4H K 线、成交量、上轨/阻力、下轨/支撑、中轨、摆高/摆低锚点，以及上破/下破触发线。
- 市场架构函数新增可视化 payload：结构线端点、摆点锚点、中轨、突破缓冲和逐步逻辑说明。

### 验证

- `python3 -m py_compile skills/crypto-market-analysis/scripts/fetch_data.py skills/crypto-market-analysis/scripts/market_structure_chart.py tests/test_direction_gates.py`
- `python3 -m unittest tests.test_direction_gates -v`
- `python3 -m unittest discover -s tests`

## v1.2.4 (2026-06-19) — 技术结构逻辑图

### 新增

- 新增 `docs/TECHNICAL_ARCHITECTURE.md`，用 Mermaid 展示 Crypto 4H 市场架构识别逻辑。
- 文档说明从 K 线归一化、摆点识别、通道/箱体/楔形分类、上下轨投影，到技术维度归并和七维门槛的完整路径。
- README 增加技术结构逻辑图入口。

### 验证

- `python3 -m py_compile skills/crypto-market-analysis/scripts/fetch_data.py tests/test_direction_gates.py`
- `python3 -m unittest discover -s tests`

## v1.2.3 (2026-06-19) — Crypto 市场架构层

### 新增

- Crypto 4H 技术结构新增市场架构识别：上升通道、下降通道、箱体结构、收敛三角/楔形、扩散震荡和宽幅震荡。
- `klines` 输出新增 `4H市场架构`，包含结构类型、当前位置、下轨/支撑、上轨/阻力和倾向。
- 方向门槛将 `市场架构` 归并到同一个 `技术结构` 独立维度，避免与 4H 主导手法重复计票。

### 测试

- 新增回归测试，覆盖上升通道识别和市场架构只计为一个技术维度。
- `python3 -m unittest discover -s tests`

## v1.2.2 (2026-06-19) — Crypto 技术结构修正

### 修复

- 修复 Crypto 方向门槛中 `技术结构` 同时被判为偏空和核心缺失的矛盾输出。
- 技术结构现在只有在日线或 4H K 线样本不足时才标记为缺失；价格结构无方向时标记为中性，不再触发核心缺失降级。
- 4H 主导手法仍归并到同一个 `技术结构` 独立维度，避免技术内部代理重复计票。

### 测试

- 新增回归测试，覆盖技术结构中性但 4H 模式参与投票时不得进入 `missing`。
- `python3 -m unittest discover -s tests`

## v1.2.1 (2026-06-19) — CZSC 稳定性修复

### 修复

- 修复 `tests/test_czsc_adapter.py` 中重复空函数导致测试套件无法启动的问题。
- 修复 A 股、外汇、美股分析脚本在按文件路径加载或非特定工作目录运行时找不到 `shared_ta` 的问题。
- 修复 crypto CZSC 脚本重复拉取同一周期 K 线的问题，改为一次采集后复用。

### 稳定性改进

- `czsc` 依赖锁定到已对照验证的 commit，避免上游 GitHub HEAD 变化导致分析结果或 API 突然漂移。
- CZSC 分析新增按周期区分的最小 K 线数量门槛，避免样本过少时输出过强结构判断。
- crypto CZSC 回看窗口改为按周期动态设置，长周期分析可获得足够历史样本。
- 报告风险提示明确区分 `czsc` 结构计算与 Hermes 启发式摘要。

### 验证

- `python3 -m py_compile tests/test_czsc_adapter.py hermes_finance/czsc_adapter.py scripts/czsc_analyze.py`
- `python3 -m py_compile skills/forex-market-analysis/scripts/forex_analyze.py skills/us-equity-market-analysis/scripts/us_equity_analyze.py skills/a-share-market-analysis/scripts/a_share_analyze.py`
- `python3 -m unittest discover -s tests`

## v1.1.6 (2026-06-19) — Crypto 新闻/基本面前置

### 新增

- Crypto 采集脚本新增 `news` block，抓取 Google News RSS，并按 ETF 资金、监管、机构需求、交易所风险等关键词归类事件面。
- Crypto `direction` block 现在把 `新闻/事件基本面` 作为独立维度纳入方向门槛，先看新闻/基本面，再结合合约、宏观、情绪、交易所、期权和技术结构。

### 修复

- 修复 BTC/crypto 分析可能只靠技术结构、合约和 CZSC 输出，新闻/ETF/监管/机构基本面没有进入脚本级方向判断的问题。
- 多条同向新闻只归并为一个 `新闻/事件基本面` 维度；多空新闻混合时转为中性，不允许重复投票硬给方向。

### 测试

- 新增 Crypto 新闻维度回归测试，覆盖新闻事件只算一个维度、多空新闻混合转中性。

## v1.1.5 (2026-06-19) — Crypto 脚本级方向门槛

### 新增

- Crypto 采集脚本新增 `direction` block，直接输出加密货币独立维度方向门槛、反向审计和最终方向建议。
- Crypto 方向门槛新增可测试纯函数：合约结构、宏观/风险偏好、技术结构、情绪反指、交易所交叉验证、期权结构和链上/基本面会先合并为独立维度，再参与方向判断。

### 修复

- 修复加密货币此前只靠 Skill / Markdown 契约约束方向输出、缺少脚本级硬门槛的问题。
- 修复合约相关指标重复投票风险：OI、资金费率、多空比、合约涨跌现在只归入 `合约结构` 一个维度。
- 修复宏观相关代理重复投票风险：SPY、VIX、DXY、BTC 5 日趋势现在只归入 `宏观/风险偏好` 一个维度。
- 极端资金费率、极端多空比、极端恐惧贪婪会触发禁止追多/禁止追空；核心技术结构或合约结构缺失时强制观望。

### 测试

- 新增 Crypto 方向门槛回归测试，覆盖合约维度归并、宏观维度归并、极端资金费率禁止追多、核心维度缺失强制观望。

## v1.1.4 (2026-06-18) — 独立维度方向门槛

### 修复

- 修复方向门槛仍按原始证据条目计数的问题：DXY / 10Y / USD 利差、SPY / QQQ、技术结构 / 主导手法等同类代理现在会先合并为独立维度，再参与方向判断。
- 修复期货分析中过度依赖技术与宏观代理的问题：CFTC 持仓、明确供需/库存/地缘/OPEC/天气标题现在作为独立维度参与方向门槛；EIA 页面仅可用但没有库存增减数值时只标记为中性缺口，不再当作方向证据。
- 修复外汇 CFTC 方向映射错误：USDJPY / USDCHF / USDCNH 这类 USD 在前的货币对，会把对手货币 CFTC 看多正确映射为交易对偏空。
- 修复美股 `business_proxy` 公司业务事件没有归入公司事件维度的问题。

### 测试

- 新增方向门槛回归测试，覆盖相关代理只算一个维度、CFTC 对手货币映射、期货供需标题归并和 EIA 非结构化数据中性处理。

## v1.1.3 (2026-06-18) — 方向质量门槛与反向审计

### 新增

- 全市场分析契约新增 `方向质量门槛` 和 `反向审计`：最终方向必须先通过 1-7 维证据门槛，再由 CZSC 作为第 8 维确认/冲突/不足。
- futures / forex / us-equity / a-share 分析脚本新增保守方向门槛，只有同向证据足够、关键维度无缺口且无硬反证时才输出做多/做空或偏多/偏空。
- 新增方向门槛回归测试，覆盖期货/外汇反向宏观证据、美股个股事件缺口、美股指数震荡降级和外汇事件窗口数值判断。

### 改进

- MCP server instructions、prompts、Markdown 输出契约、Skills、README、AGENTS 和各 AI 客户端规则同步要求 `七维主判断`、`方向质量门槛`、`反向审计`、`缠论确认`、`最终方向`。
- Crypto 分析框架补齐方向质量门槛和反向审计，禁止在链上/合约/宏观/技术证据分裂时硬给方向。
- 分析报告中的 `六维判断` 标题改为 `七维主判断`，与八维框架保持一致。

### 修复

- 修复美股指数在结构模糊或数据缺口时可能降为 `观望` 的不一致表达，统一为 `震荡`。
- 修复外汇高影响事件窗口用字符串前缀判断导致 `+2.5h` 被误判进禁止窗口的问题。

## v1.1.2 (2026-06-18) — CI 与脚本稳定性修复

### 新增

- 新增 GitHub Actions CI，在 push / pull_request 时自动执行 compileall 和 unittest。
- 新增回归测试，覆盖 `czsc_analyze.py --signals`、A 股远程命令构造和板块资金解析。

### 修复

- 修复默认 `python -m unittest discover -v` 找不到测试的问题。
- 修复 `scripts/czsc_analyze.py --signals` 参数被解析但未传入输出流程的问题。
- 修复 `skills/czsc-ccxt-analysis/scripts/czsc_4h_15m.py` 固定日期窗口导致脚本随时间过期的问题。
- 修复 A 股远程采集命令在 sections 和 stock 同时存在时的 env 参数拼接不一致。
- 修复 A 股板块资金解析只接受包含“亿”的字段，导致部分流量值被丢弃的问题。

### 稳定性改进

- `scripts/czsc_analyze.py` 缓存共振结果，报告笔编号改为基于切片位置计算。
- futures / forex Yahoo Finance 限流器加锁，降低并发请求触发 429 的概率。
- crypto 采集脚本扩展常见 CoinGecko id 到交易所 ticker 的映射。
- `czsc_signals_compat.py` 增加 czsc 版本提示和安装说明。

### 分析框架改进

- 全市场分析契约升级为“尽可能八维”：futures/forex/us_equity/a_share 也要求 `七维主判断`、`缠论确认`、`最终方向`，CZSC 不可用时必须标注第 8 维不足并降级。
- 新增 collector K-line CZSC 适配层，非 crypto 市场可直接用采集器返回的 Binance/Yahoo/Tencent K 线构造 CZSC，避免只支持 ccxt 交易对。
- MCP `analyze_futures` / `analyze_forex` / `analyze_us_equity` / `analyze_a_share` 默认开启 CZSC，新增通用 `eight_dimension_analysis` prompt。
- README、USAGE、AI 客户端规则和各市场 Skill 统一改为八维输出规则，避免 Claude Code/Codex/Cursor 等客户端继续产出六维摘要。
- 期货/商品分析新增 Binance TradFi 商品永续层：`CLUSDT`、`BZUSDT`、`XAUUSDT`、`XAGUSDT`、`COPPERUSDT`、`NATGASUSDT`、`XPTUSDT`、`XPDUSDT`，采集 1H/4H/1D K线、24h ticker、mark/index、资金费率、OI、OI历史、多空账户/仓位比。
- 共享路由和 service 识别 Binance TradFi 商品永续，避免 `CLUSDT` / `XAUUSDT` 因 `USDT` 被误路由到 crypto；CLI/MCP 可直接传这些符号并映射到 futures root。
- futures skill 更新商品覆盖范围与 Binance TradFi 使用规则，黄金 PAXG 现货代理降级为 `XAUUSDT` 不可用时的最后兜底。
- 加强 crypto 分析防呆：MCP 初始化 instructions、`deep_market_analysis` prompt、AGENTS/Claude/Gemini/Copilot/Cursor/Windsurf/Cline/Roo 规则都明确 BTC/ETH/SOL 必须走八维框架，避免 AI 工具输出压缩行情摘要。
- 新增 MCP prompt `crypto_eight_dimension_analysis`，用于严格生成加密货币八维分析流程。
- `analyze_market` 的 Markdown 输出新增 `Crypto Analysis Contract`，从工具返回层强制提示八维结构、七维主判断、缠论确认和最终方向。
- AI 客户端规则中的 crypto 示例改为 `--blocks all` + 默认 CZSC，避免示例本身诱导快速摘要。
- 修正 `multi-market-analysis` 总路由中的旧“统一六维”描述，明确所有市场尽可能走八维框架。
- 修正 `crypto-market-analysis` skill frontmatter，使其通过当前 skill validator。

## v1.1.1 (2026-06-18) — AI 客户端适配补强

### 新增

- 新增 `bin/hermes_finance_mcp.py` portable MCP launcher，自动定位仓库根目录并设置 `PYTHONPATH`。
- 新增项目级 MCP / agent 配置：
  - Claude Code：`.mcp.json`, `CLAUDE.md`
  - Codex CLI / IDE：`.codex/config.toml`, `AGENTS.md`
  - Cursor：`.cursor/mcp.json`, `.cursor/rules/hermes-finance.mdc`
  - VS Code / GitHub Copilot：`.vscode/mcp.json`, `.github/copilot-instructions.md`
  - Gemini CLI：`.gemini/settings.json`, `GEMINI.md`
  - Roo Code：`.roo/mcp.json`, `.roo/rules/hermes-finance.md`
  - Continue：`.continue/mcpServers/hermes-finance.yaml`
  - Zed：`.zed/settings.json`
- 新增 `integrations/`，提供 Claude Desktop、Windsurf、Cline、Roo、Gemini、Codex、VS Code、Cursor、Continue、Zed、Amp 等用户级模板。
- 新增 `scripts/render_ai_client_config.py`，可按当前仓库绝对路径生成常见客户端配置。
- 新增 `docs/AI_CLIENTS.md` 和 `integrations/README.md`，集中说明支持矩阵、安装位置、生成命令和验证方法。
- 新增 MCP server 初始化 instructions，跨客户端统一提示路由、市场框架、数据源状态和 CZSC 使用规则。

### 改进

- `.mcp.json` 改用 portable launcher，并加入较长 tool timeout。
- MCP 文档和 smoke test 统一改为 `python3 bin/hermes_finance_mcp.py`。

### 验证

- `python3 -m compileall -q bin scripts hermes_finance hermes_finance_mcp tests`
- `python3 -m unittest discover -s tests -v`
- MCP stdio client smoke：通过 `bin/hermes_finance_mcp.py` 读取 server instructions、列出 tools 并调用 `route_market_tool`。
- `python3 scripts/render_ai_client_config.py claude-desktop`
- `python3 scripts/render_ai_client_config.py codex`

## v1.1.0 (2026-06-18) — Skills + MCP 双版本架构

### 新增

- 新增 `hermes_finance/` 共享核心 API：
  - `route_market`
  - `fetch_market_data`
  - `analyze_market`
  - `czsc_analyze`
- 新增 `hermes_finance_mcp/server.py`，提供 MCP stdio server。
- 新增 MCP tools：
  - `route_market_tool`
  - `fetch_market_data_tool`
  - `analyze_market_tool`
  - `analyze_crypto`
  - `analyze_futures`
  - `analyze_forex`
  - `analyze_us_equity`
  - `analyze_a_share`
  - `czsc_analyze_tool`
- 新增 MCP resources：
  - `finance://routing`
  - `finance://framework/{market}`
- 新增 MCP prompts：
  - `deep_market_analysis`
  - `czsc_confirmation_review`
- 新增 `.mcp.json` 客户端配置示例。
- 新增 `requirements-mcp.txt`，MCP 依赖作为可选安装。
- 新增 `docs/USAGE.md`，覆盖安装、CLI、Skills、MCP、功能、排错与验证。
- 新增 `tests/test_core.py`，覆盖路由和核心服务基础行为。

### 改进

- `scripts/market_analyze.py` 改成共享核心薄封装，兼容旧 CLI 入口。
- `skills/multi-market-analysis/scripts/route_market.py` 改成共享路由薄封装，避免路由规则双份漂移。
- `skills/multi-market-analysis/SKILL.md` 增加 Skills/MCP 双入口说明。
- `install.sh` 支持 `INSTALL_MCP=1` 安装 MCP 可选依赖。

### 验证

- `python3 -m unittest discover -s tests -v`
- `python3 -m compileall -q hermes_finance hermes_finance_mcp scripts skills/multi-market-analysis/scripts tests`
- MCP stdio client smoke：列出 tools/resources/prompts，调用 `route_market_tool` 和 `analyze_crypto`。

## v1.0.3 (2026-06-17) — 缠论深度分析增强

### 🆕 新增（源自 czsc_skills by zengbin93）

- **背驰分析** — `FreqAnalysis.divergence_check()` 比较同方向相邻笔振幅，检测上涨/下跌背驰
- **买卖点模式识别** — `FreqAnalysis.buy_sell_pattern()` 基于分型回调手动判断一买/二买/一卖/二卖
- 背驰+模式识别集成到报告输出（`generate_report`）和终端输出（`print_summary`）

---

## v1.0.2 (2026-06-17) — 结构加固 + 补充

### 🟡 代码架构

- **czsc_analyze 三合一** — 两个 skill 级脚本改为薄封装，核心逻辑统一在 `scripts/czsc_analyze.py`
- **a_share_fetch 解耦** — 480 行内嵌 Python 字符串提取为独立文件 `a_share_remote.py`（文件缩小 62%）
- **Sequoia 策略并行化** — `BaseStrategy._run_parallel` + WAL 模式 + `get_ohlcv_batch` 批量读取
- **MaVolumeStrategy 示范** — 用 `_run_parallel` 重写，8 线程并行

### 🟡 数据源升级

- **CFTC 结构化 CSV** — futures/forex 优先读 ZIP/CSV（可靠），HTML 爬虫降级为 fallback
- **对手国利率** — JPY/AUD/CHF/CNH 从"无数据"升级到 BWX/BNDX 国际债券 ETF 代理
- **Yahoo 全局速率限制** — `_yf_throttle()` 确保请求间隔 ≥ 0.5s，降低 429 触发

### 🟢 补充 (2026-06-17)

- **`futures_analyze.py`** — `cftc_summary()` 从死占位符升级，展示 CSV 新字段（投机/套保多空净仓+仓位信号+报告日）
- **`forex_analyze.py`** — `cftc_summary()` 增强：新增 `position_signal`/`report_date`/CSV 来源标注

---

## v1.0.1 (2026-06-17) — 分析逻辑修补 + 补充

### 🔴 修复

- **外汇利率差** — `^IRX`(13周国库券) 换成 `^FVX`(5年国债)，利差从虚假的"3m10s"改为正确的 5s10s
- **外汇利率差** — 新增对手国利率代理（EUR→BUND=F 期货、JPY/AUD/CHF/CNH 明确标注免费源无数据）
- **对手国期货价格 vs 收益率** — 区分 `is_yield` 标志，期货价格反向解读（价涨=收益率跌）

### 🟡 改进

- **共振评分** — 阈值从 1/3 收紧到 2/4，防止单级别笔方向触发假"偏多/偏空"
- **BTC-SPY 联动** — 从不可靠的 24h 快照改为 5 日趋势比较，失败时降级到 24h

### 🟢 补充 (2026-06-17)

- **`forex_analyze.py`** — 接入新 rate 结构（5s10s/curve_signal/counterparty/diff_signal/central_bank_events），不再裸读 `proxies["^TNX"]`
- **`forex_analyze.py`** — 新增 `rates_summary()` 函数，报告中展示完整利差拆解
- **`forex_analyze.py`** — `key_block_gaps()` 改用 `structured_drivers["rates"]` 检查主导力量
- **路径修复** — 4个 analyze 脚本的 FETCHER 路径从硬编码 `/root/.hermes/` 改为 `Path(__file__).parent` 相对路径（forex/us-equity/a-share/futures）

---

## v1.0.0 (2026-06-17) — 首次正式发布 🎉

基于 czsc v1.0 缠论库，覆盖加密货币、商品期货、外汇、A股、美股五大市场的多维分析框架。

### 🔴 严重修复

- **`forex_fetch.py`** — 补上缺失的 `import time`，HTTP 429 限流重试不再抛 `NameError` 崩溃
- **`market_analyze.py`** — 硬编码 `/root/.hermes/` 路径全部改为基于 `__file__` 的项目相对路径
- **`feishu.py`** — `_get_stock_names` 加 `try/finally`，baostock 异常不再泄漏登录会话
- **`market_analyze.py`** — 删除 `ANALYZE_SCRIPTS` 死代码（引用的 4 个文件根本不存在且从未被调用）
- **`block_macro`** — 不再是空壳打印占位文字，真正拉取 VIX/DXY/SPY 实时数据，并输出 BTC-SPY 联动判断
- **`akshare`** — 补入 `requirements.txt` 和 `install.sh`，`PrivatePlacementStrategy` 不再静默失败

### 🟡 分析逻辑改进

- **`resonance_check`（缠论共振）** — 从仅看笔方向，重写为四层判断：笔方向 + 中枢位置 + 中枢嵌套关系 + 综合评分（-5~+5）
- **`forex_fetch.py`（利率差）** — 新增 US 10Y/2Y 利差获取、DXY 趋势、央行事件自动筛选
- **CFTC 持仓解析** — 搜索窗口 1600→3000 字符，增加 4 种段落标记容错，输出仓位多空信号

### 🟡 代码质量

- `czsc-ccxt` / `crypto` 两个 `czsc_analyze.py` — 硬编码未来日期（2026-03-18 等）改为 `datetime.now()` 动态计算
- `crypto/fetch_data.py` — 删除未被调用的 `block_macro_enhanced` 死函数
- `install.sh` — 补全 `baostock`/`pydantic-settings`/`rich`/`python-dotenv` 4 个依赖
- `scripts/czsc_analyze.py` — 替换 `czsc._native.signals.call_signal` 私有 API 为 `czsc.signals` 公开导入
- `market_analyze.py` — 去掉 `tavily_supplement` 的 `sys.path.insert` 魔法路径
- `DataEngine` — SQLite 连接复用，5200+ 只股票遍历不再每次新建连接
