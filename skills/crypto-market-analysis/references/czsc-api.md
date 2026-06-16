# czsc 官方 API 速查（v3.0 — 2026-06-16 全面对照 GitHub）

> 基于 waditu/czsc v1.0.x Rust+Python  
> ⚠️ 完整内容见 `czsc-ccxt-analysis` 技能，此处为浓缩引用

---

## 数据获取

```python
from czsc.connectors.ccxt_connector import get_raw_bars
from czsc import format_standard_kline, Freq

# ⚠️ API已改: sdt/edt日期参数，exchange用kwargs
df = get_raw_bars('ZECUSDT', '4h', sdt='20260401', edt='20260616')
bars = format_standard_kline(df, Freq.F240)  # ⚠️ 必须传Freq！
```

## CZSC 对象

```python
c = CZSC(bars, max_bi_num=50)

# 关键属性
c.bi_list        # 已确认笔 List[BI]: .fx_a, .fx_b, .direction, .power, .high, .low
c.fx_list        # 分型 List[FX]: .dt, .fx(顶/底), .price, .power, .has_zs
c.ubi_fxs        # 未确认分型（中枢信息在这里）
c.ubi            # ⚠️ List[str], 不是BI对象！
c.signals        # 空 OrderedDict（构造时），信号来自信号函数

# 中枢（没有 .zs_list！）
zs_fxs = [f for f in c.ubi_fxs if f.has_zs]  # f.low, f.high, f.dt, f.fx
```

## 信号系统（222信号，v1.0.0rc8）

```python
from czsc._native.signals import call_signal

# v1.0.0rc8 新调用方式（信号名字符串）
res = call_signal('cxt_first_buy_V221126', c)    # 一买
res = call_signal('cxt_first_sell_V221126', c)   # 一卖
res = call_signal('cxt_second_bs_V230320', c)    # 二买二卖
res = call_signal('cxt_third_buy_V230228', c)    # 三买
res = call_signal('cxt_decision_V240614', c)     # ⭐ 综合决策
res = call_signal('cxt_bi_end_V230104', c)       # 笔结束
res = call_signal('cxt_decision_V240614', c)     # → [Signal(...)] 开多是直接做多指令
```

### 信号优先级（实战验证）
| 优先级 | 信号组合 | 结论 |
|--------|---------|------|
| ⭐最高 | 综合决策=开多 + 二买 + 小级别反转 | 🟢 做多 |
| 高 | 综合决策=开多 + 一买 + 笔结束 | 🟢 做多 |
| 中 | 二买 + 笔结束 | 🟡 观望偏多 |
| 低 | 中枢破位 + 一卖 | 🔴 不做多 |

## 可视化

```python
# lightweight-charts (czsc v1.0.0rc8 唯一可用)
from czsc.utils.plotting.lightweight import plot_czsc

# 暗色主题 + 多级别
plot_czsc(c, path='out.html', theme='dark', title='BTC 4H')

# plot_czsc_trader 用于 CzscTrader 实例
from czsc.utils.plotting.lightweight import plot_czsc_trader
plot_czsc_trader(ct, path='trader.html', theme='dark')
```

## Freq枚举

```
F1, F5, F15, F30, F60, F120, F240, F360, D, W, M
```

## GitHub HEAD Phase J 变更（升级后生效）

| 模块 | pip版 | HEAD | 影响 |
|------|------|------|------|
| `echarts_plot` / `kline_pro` | ✅ 256信号可用 | ❌ 已删除 | 改用 `lightweight.plot_czsc()` |
| `czsc/signals/` Python层 | ✅ 可用 | ❌ 已删除 | `from czsc.signals import ...` 失效 |
| `lightweight` charts | ❌ 不存在 | ✅ 新增 | 自包含HTML，多周期联立 |
| `czsc CLI` | ❌ 不存在 | ✅ 新增 | `czsc analyze/backtest/plot` |
| `plotting/backtest.py` | — | ❌ 删除 | 用 `wbt.generate_backtest_report` |
| 信号数量 | 256 | 246（精简） | 10个冗余信号被移除 |

### 从源码升级
```bash
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
source "$HOME/.cargo/env" && pip install maturin --break-system-packages
git clone --depth 1 https://github.com/waditu/czsc.git /tmp/czsc
cd /tmp/czsc && maturin build --release  # 首次15-25分钟
pip install target/wheels/*.whl --break-system-packages --force-reinstall
```

---

## 关键坑点（vs v2.0修正）

| 坑 | 新发现 | 正确做法 |
|---|--------|---------|
| get_raw_bars API | `(symbol, period, sdt=, edt=)` 非 `(symbol, period, exchange, num=)` | 加 sdt=/edt= |
| format_standard_kline | 需要 Freq 参数! | `format_standard_kline(df, Freq.F240)` |
| CZSC构造 | 不接受 freq/verbose | `CZSC(bars, max_bi_num=50)` |
|| to_echarts/to_plotly | 返回字符串 "not implemented" | 用 lightweight.plot_czsc() |
| c.ubi | 是 List[str] 非 BI对象! | 只判长度 len(c.ubi) |
| c.signals | 构造时为空 OrderedDict | 调用信号函数获取 |
| Freq有F240 | ⭐ 4H是 Freq.F240 | 不需要手写4H聚合! |
| 信号函数 | ⭐ 220+ 全可用 | 标准化分析中启用 `--signals` |
| 🆕 resample_bars | ⚠️ 不接受 Freq.F240 直接传入 | `resample_bars(df, '240分钟')` |
| 🆕 generate_czsc_signals | ⚠️ 需要足够warmup K线(init_n) | 至少200+根K线，或设置 init_n=50 |
