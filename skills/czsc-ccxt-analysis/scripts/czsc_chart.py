#!/usr/bin/env python3
"""czsc手动Plotly图表生成 — Rust版to_echarts()不可用的替代方案
用法: python3 czsc_chart.py [SYMBOL]
  SYMBOL: 默认 BTC/USDT, 支持 ZEC/USDT, BANANAS31/USDT 等
输出: /tmp/czsc_{SYMBOL}_4h.html 交互式图表
"""
import ccxt, sys, os
from czsc import CZSC, RawBar, Freq
from datetime import datetime, timezone
import plotly.graph_objects as go
from plotly.subplots import make_subplots

sym = sys.argv[1] if len(sys.argv) > 1 else 'BTC/USDT'
ex = ccxt.binance({'enableRateLimit': True})

# Fetch + aggregate 4H
bars_1h = ex.fetch_ohlcv(sym, '1h', limit=720)
bars_4h = []; chunk = []; ck = ''
for b in bars_1h:
    dt = datetime.fromtimestamp(b[0]/1000, tz=timezone.utc)
    hb = dt.hour // 4 * 4
    bk = dt.strftime('%Y-%m-%d') + '-{:02d}'.format(hb)
    if not chunk or bk != ck:
        if chunk:
            bars_4h.append([chunk[0][0], chunk[0][1],
                max(c[2] for c in chunk), min(c[3] for c in chunk),
                chunk[-1][4], sum(c[5] for c in chunk)])
        chunk = [b]; ck = bk
    else:
        chunk.append(b)
if chunk:
    bars_4h.append([chunk[0][0], chunk[0][1],
        max(c[2] for c in chunk), min(c[3] for c in chunk),
        chunk[-1][4], sum(c[5] for c in chunk)])

def rb(bars, freq):
    r = []
    for i, b in enumerate(bars):
        dt = datetime.fromtimestamp(b[0]/1000, tz=timezone.utc)
        r.append(RawBar(symbol=sym, dt=dt, freq=freq, open=b[1], close=b[4],
                        high=b[2], low=b[3], vol=float(b[5] or 0), amount=0.0, id=i))
    return r

c = CZSC(rb(bars_4h, Freq.F60), max_bi_num=50)
bars = c.bars_raw
zs_list = [f for f in c.ubi_fxs if f.has_zs]

# Build chart
dates = [b.dt for b in bars]
fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.7, 0.3],
                    subplot_titles=(f'{sym} 4H 缠论', 'Volume'))

# Candlestick
fig.add_trace(go.Candlestick(
    x=dates, open=[b.open for b in bars], high=[b.high for b in bars],
    low=[b.low for b in bars], close=[b.close for b in bars],
    name='Price', increasing_line_color='#26a69a', decreasing_line_color='#ef5350'
), row=1, col=1)

# Volume bars
colors = ['#26a69a' if bars[i].close >= bars[i].open else '#ef5350' for i in range(len(bars))]
fig.add_trace(go.Bar(x=dates, y=[b.vol for b in bars], name='Volume',
                      marker_color=colors), row=2, col=1)

# BI strokes (green=UP, red=DOWN)
for bi in c.bi_list:
    d = 'UP' if '向上' in str(bi.direction) else 'DN'
    color = '#00ff00' if d == 'UP' else '#ff0000'
    lo = bi.low if d == 'UP' else bi.high
    hi = bi.high if d == 'UP' else bi.low
    fig.add_trace(go.Scatter(x=[bi.sdt, bi.edt], y=[lo, hi], mode='lines+markers',
        line=dict(color=color, width=3), name=f'BI_{d}'), row=1, col=1)

# ZS rectangles (yellow semi-transparent)
for z in zs_list:
    fig.add_hrect(y0=z.low, y1=z.high, line_width=0, fillcolor='yellow',
                  opacity=0.15, row=1, col=1)

# FX markers (green=底分型, red=顶分型)
fx_dates = [f.dt for f in c.fx_list]
fx_prices = [f.fx for f in c.fx_list]
fx_colors = ['green' if '底' in str(f.mark) else 'red' for f in c.fx_list]
fig.add_trace(go.Scatter(x=fx_dates, y=fx_prices, mode='markers',
    marker=dict(color=fx_colors, size=8, symbol='triangle-up'), name='FX'), row=1, col=1)

fig.update_layout(template='plotly_dark', height=800, hovermode='x unified')
out = f'/tmp/czsc_{sym.replace("/","_")}_4h.html'
fig.write_html(out)
print(f'Chart saved: {out} ({os.path.getsize(out)} bytes)')
