# Changelog

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
