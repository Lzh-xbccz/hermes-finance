# Hermes Finance — 缠论+多维度金融市场分析框架

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-v1.0.0-green.svg)](https://github.com/Lzh-xbccz/hermes-finance/releases)

> 基于 [czsc](https://github.com/waditu/czsc) v1.0 缠论库，覆盖 **加密货币/商品期货/外汇/A股/美股** 五大市场。每个市场采用多维因果分析框架，集成缠论作为核心技术分析维度。

---

## 🏗️ 项目架构

```\nhermes-finance/\n├── requirements.txt             # Python 依赖（含 czsc GitHub 源）\n├── install.sh                   # 一键安装脚本\n├── skills/                      # 8 个分析技能
│   ├── crypto-market-analysis/      # 🟠 加密货币（BTC/ETH/山寨）
│   ├── futures-market-analysis/     # 🟡 商品期货（CL/GC/ES/NG）
│   ├── forex-market-analysis/       # 🔵 外汇（DXY/EURUSD/JPY）
│   ├── a-share-market-analysis/     # 🔴 A股
│   ├── us-equity-market-analysis/   # 🟣 美股
│   ├── multi-market-analysis/       # 🔀 多市场智能路由
│   ├── czsc-ccxt-analysis/          # 🎯 缠论核心引擎
│   └── microcap-pnd-system/         # ⚠️ 极端山寨 Pump & Dump 检测
└── scripts/
    ├── czsc_analyze.py              # 缠论一键分析（4H+15min+信号+图表）
    └── market_analyze.py            # 多市场分析
```

---

## 🎯 八大分析技能

### 1. `crypto-market-analysis` — 加密货币八维分析

最完整的分析框架，每个币种强制运行 8 个维度：

| # | 维度 | 核心问题 |
|---|------|---------|
| 1 | 技术结构 | 趋势方向？支撑阻力在哪？ |
| 2 | 合约数据 | OI/资金费率/多空比 — 谁在押注？ |
| 3 | 量价关系 | 放量还是缩量？真实买盘还是对倒？ |
| 4 | 基本面 | 链上数据 — 抛压从哪来？解锁在何时？ |
| 5 | 情绪面 | 恐惧贪婪指数 — 市场狂热还是绝望？ |
| 6 | 宏观联动 | SPX/DXY/BTC — 风险偏好还是避险？ |
| 7 | 流动性/退市 | 深度/滑点 — 能安全进出吗？ |
| 8 | **缠论结构** | **czsc 4H+15min — 中枢在哪？一买二买三买？** |

### 2. `futures-market-analysis` — 商品期货六维分析

覆盖 CL（原油）、GC（黄金）、ES（标普500）、NG（天然气）：

```
维度1: 技术结构 → K线形态 + MACD + 布林
维度2: 宏观驱动 → DXY + 实际利率 + 美联储
维度3: 库存/供需 → EIA原油库存 / COMEX黄金持仓
维度4: 资金面   → COT报告 + OI变化
维度5: 跨市场   → 相关品种联动
维度6: 季节性   → 历史同期表现
```

**核心理念**：利率路径 + 美元方向定大局，缠论结构锚定止盈止损。

### 3. `forex-market-analysis` — 外汇六维分析

覆盖 DXY、EURUSD、USDJPY、GBPUSD、AUDUSD：

```
利率差 → 谁加息谁走强
经济数据 → NFP/CPI/PMI 驱动
技术结构 → K线 + 支撑阻力
情绪面   → VIX + risk-on/risk-off
央行表态 → 鹰鸽切换
资本流   → 债市 + 股市资金方向
```

### 4. `czsc-ccxt-analysis` — 缠论核心引擎 🎯

整个框架的**技术心脏**，基于 [waditu/czsc](https://github.com/waditu/czsc) v1.0（Rust 实现）：

```python
from czsc.connectors.ccxt_connector import get_raw_bars
from czsc import CZSC, format_standard_kline, Freq
from czsc.signals import cxt_first_buy_V221126

# 数据获取（CCXT → Binance）
df = get_raw_bars('BTCUSDT', '4h', sdt='20260401', edt='20260616')
bars = format_standard_kline(df, Freq.F240)

# 缠论分析
c = CZSC(bars, max_bi_num=50)
c.bi_list       # 笔序列：向上/向下
c.fx_list        # 分型：顶/底识别
c.ubi_fxs        # 中枢参与分型

# 220+ 买卖点信号
res = cxt_first_buy_V221126(c)    # 一买？
# → OrderedDict({'240分钟_D1B_BUY1': '其他_任意_任意_0'})
```

**多级别联立分析：**
```
4H 中枢 $63,650 - $64,183（强）
15min 中枢 $65,329 - $65,721（弱）
→ 15min 在 4H 中枢上方 → 顺势做多
→ 一买 + 二买 + 综合决策 = 开多 → 入场信号确认
```

**可视化：**
- `plot_czsc()` — lightweight-charts 交互式 K 线图，含分型/笔/中枢标记
- `CzscTrader` — 多级别交易信号系统，内置 222 个信号

### 5. `multi-market-analysis` — 智能路由 🔀

自动识别标的市场类型，分派到对应分析技能：

```
输入: "分析 BTC"     → crypto-market-analysis
输入: "分析 GC"      → futures-market-analysis
输入: "分析 EURUSD"  → forex-market-analysis
输入: "分析 茅台"    → a-share-market-analysis
```

### 6. `a-share-market-analysis` — A股六维 + 量化选股

| 维度 | 指标 |
|------|------|
| 技术面 | K 线 + 均线 + MACD + KDJ |
| 资金面 | 北向资金净流入（A 股独有） |
| 市场结构 | 涨跌家数 / 涨停跌停统计 |
| 情绪面 | 成交量对比 / 风险偏好 |
| 宏观面 | PMI / 社融 / 利率 / 美股联动 |
| 板块轮动 | 行业资金流向 / 热点概念 |

🆕 **量化选股引擎**（v3.0）— 集成 [Sequoia-X](https://github.com/sngyai/Sequoia-X)：
- 基于 **baostock** 免费数据源（无需注册）→ 本地 SQLite
- 7 种策略自动扫描全市场 5200+ 只 A 股
- 海龟突破 / 均线放量 / 高窄旗形 / 涨停洗盘 / 跌停反包 / RPS 突破 / 定增回补
- 收盘后一键运行，5 分钟出结果

### 7. `us-equity-market-analysis` — 美股六维分析

```
维度1: 多时间框架技术分析
维度2: 基本面（PE / PEG / 营收增长）
维度3: 资金流（机构持仓变化）
维度4: 期权市场（Put/Call 比率）
维度5: 板块轮动
维度6: 宏观（FOMC / CPI / NFP）
```

### 8. `microcap-pnd-system` — 极端山寨检测 ⚠️

专门识别 Pump & Dump 模式：

- 🚩 24h 涨幅 > 50% → 红牌警告
- 🚩 成交量 25x 均量 → 派发特征
- 🚩 单交易所品种 → 流动性风险
- 🚩 无基本面支撑 → 纯资金盘
- 🚩 合约负费率异常 → 空头拥挤

---

## ⚡ 快速开始

> ⚠️ **czsc 必须从 GitHub 源码安装**（PyPI 的 0.10.x 是旧版 Python 实现，不含 Rust 核心）

### 一键安装

```bash
# 1. 安装 Rust 工具链（czsc 编译需要）
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
source "$HOME/.cargo/env"

# 2. 安装 Python 依赖
pip install --break-system-packages git+https://github.com/waditu/czsc.git
pip install --break-system-packages ccxt pandas plotly
```

或者直接：

```bash
bash install.sh
```

| 依赖 | 安装方式 | 用途 |
|------|---------|------|
| czsc | `git+https://github.com/waditu/czsc.git` (v1.0.0rc8) | 缠论核心（Rust + PyO3） |
| ccxt | `pip install ccxt` (≥4.5) | 加密货币数据（Binance 现货+期货） |
| pandas | `pip install pandas` (≥2.0) | 数据处理 |
| plotly | `pip install plotly` (≥5.0) | lightweight-charts 渲染依赖 |

### 运行

```bash
# 缠论分析（BTC 4H + 信号）
python scripts/czsc_analyze.py BTCUSDT 4h --signals --compact

# 缠论 + lightweight-charts 图表
python scripts/czsc_analyze.py BTCUSDT 4h --signals --chart

# 加密货币完整八维分析
python skills/crypto-market-analysis/scripts/fetch_data.py BTC all

# 期货分析
python skills/futures-market-analysis/scripts/futures_fetch.py GC

# 多市场路由
python skills/multi-market-analysis/scripts/route_market.py
```

---

## 📂 每个技能的标准结构

```
skill-name/
├── SKILL.md              # 技能文档（方法论 + 规则 + 框架）
├── references/           # 参考文档
│   ├── xxx-six-dimensions.md   # 维度详细说明
│   ├── xxx-api.md              # API 速查表
│   └── xxx-catalyst.md         # 催化剂日历
└── scripts/              # 可执行脚本
    ├── fetch_data.py     # 数据获取
    └── xxx_analyze.py    # 分析执行
```

---

## 📊 分析报告示例

```
=== BTC 4H 缠论结构 ===
K线: 454 | BI: 31 | FX: 153 | 中枢: $63,650-$64,183 (强)

--- 买卖点信号 ---
【一买】✅ | 【三买】✅ | 【二买】✅ 二买
【综合决策】✅ 开多 | 【笔结束】✅

--- 多级别共振 ---
4H 向下 + 15min 向下 → 同向（短期偏空）
但二买已确认 + 强中枢 → 中线看多

=== 交易计划 ===
方向: 🟢 偏多 | 入场: $64,000-$65,500
SL: $62,900 | TP1: $67,248 | TP2: $70,000
```

---

---

## 📋 更新日志

### v1.0.0 (2026-06-17)

首次正式版本发布。15 项修复（代码 bug + 分析逻辑）：

| 严重度 | 类型 | 修复内容 |
|--------|------|---------|
| 🔴 | 代码 | `forex_fetch.py` 补上缺失的 `import time`，429 限流重试不再崩 |
| 🔴 | 代码 | `market_analyze.py` 硬编码 `/root/.hermes/` 路径改为项目相对路径 |
| 🔴 | 代码 | `feishu.py` `_get_stock_names` 加 `try/finally`，baostock 异常不再泄漏会话 |
| 🔴 | 代码 | `market_analyze.py` 删除 `ANALYZE_SCRIPTS` 死代码（引用 4 个不存在的文件） |
| 🔴 | 分析 | `block_macro` 不再是空壳 — 真正拉 VIX/DXY/SPY 数据 + BTC-SPY 联动判断 |
| 🔴 | 分析 | `akshare` 补入 `requirements.txt` 和 `install.sh`，定增策略不再静默失败 |
| 🟡 | 分析 | `resonance_check` 重写 — 加入中枢位置、嵌套关系、综合评分（-5~+5） |
| 🟡 | 分析 | `forex_fetch.py` 新增利率差模块 — 拉 US 10Y/2Y 利差 + 央行事件筛选 |
| 🟡 | 分析 | CFTC 解析加固 — 窗口 1600→3000、多种段落标记容错、仓位信号输出 |
| 🟡 | 代码 | `czsc-ccxt` / `crypto` 两个 `czsc_analyze.py` 硬编码未来日期改为动态计算 |
| 🟡 | 代码 | `fetch_data.py` 删除从未被调用的 `block_macro_enhanced` 死代码 |
| 🟡 | 代码 | `install.sh` 补全 `baostock` / `pydantic-settings` / `rich` / `python-dotenv` 依赖 |
| 🟡 | 代码 | `scripts/czsc_analyze.py` 替换 `czsc._native.signals.call_signal` 私有 API 为 `czsc.signals` 公开导入 |
| 🟡 | 代码 | `market_analyze.py` 去掉 `tavily_supplement` 里的魔法路径注入 |
| 🟡 | 代码 | `DataEngine` SQLite 连接复用，策略遍历 5200+ 只股票不再每次新建连接 |

---

## ⚠️ 免责声明

本项目仅用于 **技术交流和学习研究**，不构成任何投资建议。市场有风险，投资需谨慎。
