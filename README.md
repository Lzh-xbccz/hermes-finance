# Hermes Finance — 缠论+多维度金融市场分析框架

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-v1.0.3-green.svg)](https://github.com/Lzh-xbccz/hermes-finance/releases)
[![Releases](https://img.shields.io/github/v/release/Lzh-xbccz/hermes-finance?include_prereleases&label=latest)](https://github.com/Lzh-xbccz/hermes-finance/releases)

> 基于 [czsc](https://github.com/waditu/czsc) v1.0 缠论库，覆盖 **加密货币 / 商品期货 / 外汇 / A股 / 美股** 五大市场。每个市场采用多维因果分析框架，集成缠论作为核心技术分析维度。

---

## 🏗️ 项目架构

```
hermes-finance/
├── requirements.txt                 # Python 依赖
├── install.sh                       # 一键安装
├── VERSION                          # 版本号
├── CHANGELOG.md                     # 完整更新日志
├── scripts/
│   ├── czsc_analyze.py              # 缠论多级别联立分析（核心引擎）
│   ├── market_analyze.py            # 多市场统一路由入口
│   └── localize_chart.py            # 图表中文化工具
└── skills/                          # 8 个分析技能
    ├── crypto-market-analysis/      # 🟠 加密货币 — 八维分析
    ├── futures-market-analysis/     # 🟡 商品期货 — 六维分析
    ├── forex-market-analysis/       # 🔵 外汇 — 六维分析+利率差
    ├── a-share-market-analysis/     # 🔴 A股 — 六维+量化选股(Sequoia-X)
    ├── us-equity-market-analysis/   # 🟣 美股 — 六维分析
    ├── multi-market-analysis/       # 🔀 智能路由
    ├── czsc-ccxt-analysis/          # 🎯 缠论引擎（薄封装→主脚本）
    └── microcap-pnd-system/         # ⚠️ 极端山寨检测
```

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

### 2. 商品期货 — 六维分析 🟡

覆盖 CL（原油）、GC（黄金）、ES（标普500）、NG（天然气）：

| 维度 | 数据源 |
|------|--------|
| 技术结构 | K线形态 + MACD + 布林 |
| 宏观驱动 | DXY + 实际利率 + 美联储 |
| 库存/供需 | EIA原油库存 / COMEX黄金持仓 |
| 资金面 | **COT报告（CSV优先，HTML降级）** + OI变化 |
| 跨市场 | 相关品种联动 |
| 季节性 | 历史同期表现 |

### 3. 外汇 — 六维分析 + 利率差 🔵

覆盖 DXY、EURUSD、USDJPY、GBPUSD、AUDUSD：

| 维度 | 数据源 |
|------|--------|
| 利率差 | **US 10Y/5Y 利差 + 对手国利率代理 + DXY 趋势** |
| 经济数据 | NFP / CPI / PMI 驱动 + 央行事件日历 |
| 技术结构 | K线 + 支撑阻力 |
| 情绪面 | VIX + risk-on / risk-off |
| 资金面 | CFTC 金融期货持仓（CSV优先） |
| 资本流 | 债市 + 股市资金方向 |

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
| `CL` / `GC` / `ES` | futures-market-analysis |
| `EURUSD` / `DXY` | forex-market-analysis |
| `600519` / `000001` | a-share-market-analysis |
| `AAPL` / `SPY` | us-equity-market-analysis |

### 6. A股 — 六维 + 量化选股 🔴

| 维度 | 指标 |
|------|------|
| 技术面 | K线 + 均线 + MACD + KDJ |
| 资金面 | 北向资金净流入（A 股独有） |
| 市场结构 | 涨跌家数 / 涨停跌停统计 |
| 情绪面 | 成交量对比 / 风险偏好 |
| 宏观面 | PMI / 社融 / 利率 / 美股联动 |
| 板块轮动 | 行业资金流向 / 热点概念 |

🆕 **Sequoia-X 量化选股引擎** — 7 种策略 × 5200+ 只 A 股：

- 基于 **baostock** 免费数据源（无需注册）→ 本地 SQLite
- 海龟突破 / 均线放量 / 高窄旗形 / 涨停洗盘 / 跌停反包 / RPS 突破 / 定增回补
- **v1.0.2 起 8 线程并行扫描**，收盘后 5 分钟出结果

### 7. 美股 — 六维分析 🟣

多时间框架技术分析 / 基本面 / 资金流 / 期权市场 / 板块轮动 / 宏观。

### 8. 极端山寨检测 ⚠️

Pump & Dump 模式识别：24h 涨幅 > 50%、成交量异常、单交易所品种、无基本面。

---

## ⚡ 快速开始

> ⚠️ **czsc 必须从 GitHub 源码安装**（PyPI 的 0.10.x 是旧版，不含 Rust 核心）

### 一键安装

```bash
bash install.sh
```

或手动：

```bash
# 1. Rust 工具链
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
source "$HOME/.cargo/env"

# 2. Python 依赖
pip install --break-system-packages git+https://github.com/waditu/czsc.git
pip install --break-system-packages ccxt pandas plotly baostock akshare pydantic-settings rich python-dotenv
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
# 缠论分析
python scripts/czsc_analyze.py BTCUSDT 4h --signals --chart

# 加密八维分析
python skills/crypto-market-analysis/scripts/fetch_data.py BTC all

# 期货分析
python skills/futures-market-analysis/scripts/futures_fetch.py GC

# A股量化选股
cd skills/a-share-market-analysis/sequoia && python main.py
```

---

## 📋 更新日志

所有版本详见 [Releases](https://github.com/Lzh-xbccz/hermes-finance/releases) 和 [CHANGELOG.md](CHANGELOG.md)。

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
