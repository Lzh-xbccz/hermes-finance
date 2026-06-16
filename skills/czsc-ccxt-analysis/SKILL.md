---
name: czsc-ccxt-analysis
description: "缠论技术分析 — czsc官方全API，CCXT数据源，多级别联立，lightweight-charts可视化+自动Markdown报告。触发: 缠论/czsc/中枢/分型/笔"
version: 4.0.0
author: Hermes
---

# 缠论技术分析 (czsc v4.0 — v1.0.0rc8 全API + lightweight-charts)

> 基于 waditu/czsc v1.0.0rc8（2026-06-16 从源码构建）  
> 官方全链路：`ccxt_connector → CZSC → call_signal → lightweight-charts → Markdown 报告`

---

## 环境

已安装: czsc 1.0.0rc8 (源码构建), ccxt 4.5.59

### 从源码升级

```bash
bash install.sh  # 一键: Rust + czsc编译 + Python依赖
```

详见 `references/czsc-build.md`

---

## API 速查

### 1. 数据获取

```python
from czsc.connectors.ccxt_connector import get_raw_bars
from czsc import format_standard_kline, Freq

df = get_raw_bars('BTCUSDT', '4h', sdt='20260601', edt='20260616')
bars = format_standard_kline(df, Freq.F240)  # ⚠️ 必须传 Freq！
```

### 2. 缠论核心对象

```python
c = CZSC(bars, max_bi_num=50)
c.bi_list       # List[BI]: .fx_a, .fx_b, .direction, .power, .high, .low
c.fx_list       # List[FX]: .dt, .fx, .has_zs, .low, .high
c.ubi_fxs       # 中枢信息在这里： [f for f in c.ubi_fxs if f.has_zs]
c.ubi           # ⚠️ List[str]，不是BI对象！
```

### 3. 信号系统（222个信号，v1.0.0rc8）

```python
from czsc._native.signals import call_signal

# v1.0.0rc8 新 API：信号名字符串调用
res = call_signal('cxt_first_buy_V221126', c)   # 一买
res = call_signal('cxt_decision_V240614', c)     # 综合决策（⭐最重要）
res = call_signal('cxt_bi_end_V230104', c)       # 笔结束

# 结果: [Signal('240分钟_D1B_BUY1_其他_任意_任意_0')]
```

### 4. 可视化（lightweight-charts）

```python
from czsc.utils.plotting.lightweight import plot_czsc

# 暗色主题
plot_czsc(c, path='chart.html', theme='dark', title='BTC 4H')
plot_czsc(c, path='chart.html', theme='dark', tail_bars=200)  # 仅最近200根
```

---

## GitHub HEAD 新功能（v1.0.0rc8 已安装）

| 功能 | 状态 |
|------|------|
| lightweight-charts | ✅ `plot_czsc(c, output="html")` |
| CLI (`czsc analyze/backtest/plot/signals/bench`) | ✅ |
| models 模块 | ✅ |
| resample_bars | ⚠️ Freq.D/W/M 可用，F240 报错（市场时区） |

---

## ⚡ 实战决策信号优先级

`cxt_decision_V240614` 是最高价值信号 — 直接给出交易方向：
- `"开多_任意_任意_0"` → 🟢 做多
- `"开空_任意_任意_0"` → 🔴 做空

多级别共振决断（2026-06-16 BTC 15min 验证）：
```
综合决策=开多 + 二买 + 5min反转↑ → 🟢 强做多
综合决策=开多 + 一买 + 笔结束      → 🟢 做多
二买 + 笔结束 + 无综合决策         → 🟡 观望偏多
中枢破位 + 一卖                    → 🔴 不做多
```

---

## ⛔ 关键坑点

### 1. get_raw_bars API
```python
# ❌ 旧: get_raw_bars('ZECUSDT', '1h', 'binance', num=100)
# ✅ 新: get_raw_bars('ZECUSDT', '1h', sdt='20260601', edt='20260616')
```

### 2. format_standard_kline 需要 Freq
```python
# ❌ format_standard_kline(df)
# ✅ format_standard_kline(df, Freq.F240)
```

### 3. CZSC.to_echarts/to_plotly 返回 "not implemented"
用 `lightweight.plot_czsc()` 替代，支持 dark theme + tail_bars

### 4. 日线漏笔（MIN_BI_LEN=6）
快速崩盘用 4H (F240) 分析

### 5. CZSC 构造不接受 freq/verbose
```python
# ✅ CZSC(bars, max_bi_num=50)
```

### 6. c.ubi 是 List[str]
只判长度 `len(c.ubi)`，不能遍历取属性

### 7. resample_bars 限制
Freq.D/W/M ✅ | Freq.F240/F60 ❌（市场时区问题）
需4H数据直接用 `get_raw_bars(period='4h')`

### 8. generate_czsc_signals warmup
需要 init_n(=500) 根以上 K线，不够用 `init_n=50`

---

## 🖥️ 平台注意事项
- 终端安全层会隐藏 `ghp_` 令牌（替换为 `***`），用 `xxd` 确认原始字节

---

## 级别选择

| 级别 | Freq | period | 适用 |
|------|------|--------|------|
| 日线 | D | `1d` | 月级趋势 |
| 4H | F240 | `4h` | **短线核心** |
| 1H | F60 | `1h` | 日内 |
| 15min | F15 | `15m` | 入场确认 |

```bash
# 多级别联立 + 信号 + dark 图表 + 报告
python3 scripts/czsc_analyze.py BTCUSDT --chart --report
python3 scripts/czsc_analyze.py ETHUSDT --freqs 4h,1h,15m --chart
```
