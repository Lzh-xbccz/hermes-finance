# Changelog

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
