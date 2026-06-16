#!/usr/bin/env python3
"""
缠论分析脚本 v3.1 — czsc v1.0.0rc8 (Rust 核心)
用法: python3 czsc_analyze.py [SYMBOL] [PERIOD] [--compact] [--chart] [--signals]
  SYMBOL: 默认 ZECUSDT (不带斜杠)
  PERIOD: 默认 4h
  --compact: 精简输出
  --chart: 生成 lightweight-charts HTML 图表
  --signals: 输出买卖点信号

v3.1 修正 (2026-06-16):
  - czsc v1.0.0rc8: plot_czsc_chart/kline_pro 已移除，改用 lightweight plot_czsc()
  - --echarts 自动回退到 lightweight
"""
import sys
import os
from datetime import datetime, timedelta

from czsc.connectors.ccxt_connector import get_raw_bars
from czsc import CZSC, format_standard_kline, Freq, resample_bars
from czsc._native.signals import call_signal

# ── 参数解析 ──
symbol = 'ZECUSDT'
period = '4h'
compact = False
do_chart = False
do_echarts = False
do_signals = False

for arg in sys.argv[1:]:
    if arg == '--compact':
        compact = True
    elif arg == '--chart':
        do_chart = True
    elif arg == '--echarts':
        do_echarts = True
    elif arg == '--signals':
        do_signals = True
    elif not arg.startswith('--'):
        if '/' in arg:
            symbol = arg.replace('/', '')
        elif arg.endswith('USDT') or arg.endswith('USDC') or arg.endswith('BTC'):
            symbol = arg
        elif arg in ('1m','5m','15m','30m','1h','4h','1d','1w'):
            period = arg
        else:
            symbol = arg

# ── Freq 映射 ──
FREQ_MAP = {
    '1m': Freq.F1, '5m': Freq.F5, '15m': Freq.F15, '30m': Freq.F30,
    '1h': Freq.F60, '2h': Freq.F120, '4h': Freq.F240,   # ⚠️ 4H=F240, NOT F60!
    '1d': Freq.D, '1w': Freq.W,
}
freq = FREQ_MAP.get(period, Freq.F240)

# ── 数据获取 ──
edt = datetime.now().strftime('%Y%m%d')
sdt = (datetime.now() - timedelta(days=90)).strftime('%Y%m%d')

print(f'标的: {symbol} | 周期: {period} (Freq.{freq}) | {sdt}-{edt}')

df = get_raw_bars(symbol, period, sdt=sdt, edt=edt)
print(f'K线: {len(df)}根')

# ⚠️ 必须传 Freq！
bars = format_standard_kline(df, freq)
c = CZSC(bars, max_bi_num=50)

# ── 基础统计 ──
n_bi = len(c.bi_list)
n_fx = len(c.fx_list)
n_ubi_fx = len(c.ubi_fxs)
zs_fxs = [f for f in c.ubi_fxs if f.has_zs]
n_ubi = len(c.ubi)  # ⚠️ 这是字符串计数，不是BI对象

print(f'分型: {n_fx} | 笔: {n_bi} | UBI分型: {n_ubi_fx} | UBI笔: {n_ubi} | 中枢参与分型: {len(zs_fxs)}')

# ── 笔序列 ──
if not compact:
    print('\n--- 笔 ---')
    for i, bi in enumerate(c.bi_list):
        d = bi.direction.value
        print(f'BI#{i+1}: {bi.fx_a.dt.strftime("%m-%d %H:%M")} ${bi.fx_a.fx:.2f} -> '
              f'{bi.fx_b.dt.strftime("%m-%d %H:%M")} ${bi.fx_b.fx:.2f} | '
              f'{d} | power={bi.power:+.1f}% | {bi.length}K')

# ── 中枢 ──
if zs_fxs:
    print('\n--- 中枢参与分型 ---')
    for z in zs_fxs:
        print(f'{z.dt.strftime("%m-%d %H:%M")} fx=${z.fx:.2f} range=${z.low:.2f}-${z.high:.2f} '
              f'power={z.power_str} has_zs={z.has_zs}')

# ── 当前位置 ──
last_bi = c.bi_list[-1]
cur = bars[-1].close
d = last_bi.direction.value
print(f'\n当前价: ${cur:.4f}')
print(f'最后笔: BI#{n_bi} {d} {last_bi.fx_a.dt.strftime("%m-%d")}->{last_bi.fx_b.dt.strftime("%m-%d")} '
      f'{last_bi.power:+.0f}%')

if zs_fxs:
    z = zs_fxs[-1]
    if cur > z.high: vs = '中枢上方 🟢'
    elif cur >= z.low: vs = '中枢内部 ⚪'
    else: vs = '中枢下方 🔴'
    print(f'vs ZS ${z.low:.2f}-${z.high:.2f}: {vs}')

# ── 笔后分型 ──
rem = [f for f in c.fx_list if f.dt > last_bi.fx_b.dt]
if rem:
    print(f'\n笔后分型: {len(rem)}个')
    for f in rem:
        label = '顶' if '顶' in str(f.mark) else '底'
        print(f'  {f.dt.strftime("%m-%d %H:%M")} {label} @ ${f.fx:.2f}')

# ── 买卖点信号 ──
if do_signals:
    print('\n=== 缠论买卖点信号 ===')
    sig_tests = [
        ('一买', 'cxt_first_buy_V221126'),
        ('综合决策', 'cxt_decision_V240614'),
        ('笔结束', 'cxt_bi_end_V230104'),
    ]
    for name, sig_name in sig_tests:
        try:
            res = call_signal(sig_name, c)
            if res:
                print(f'【{name}】✅ {res}')
            else:
                print(f'【{name}】❌ 无信号')
        except Exception as e:
            print(f'【{name}】Error: {e}')

# ── 图表 ──
if do_chart:
    from czsc.utils.plotting.lightweight import plot_czsc
    outfile = f'/tmp/czsc_{symbol}_{period}.html'
    plot_czsc(c, path=outfile)
    print(f'\n图表: {outfile} ({os.path.getsize(outfile)} bytes)')

if do_echarts:
    print('⚠️ ECharts 在 czsc v1.0.0rc8 中已移除，请使用 --chart (lightweight-charts)')
    do_chart = True  # fallback to lightweight
