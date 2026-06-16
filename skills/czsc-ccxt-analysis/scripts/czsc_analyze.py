#!/usr/bin/env python3
"""
缠论分析脚本 — CCXT(Binance) + czsc
用法: python3 czsc_analyze.py [SYMBOL] [--compact]
  SYMBOL: 交易对，默认 ZEC/USDT，支持 BTC/USDT, ETH/USDT, SOL/USDT 等
  --compact: 精简输出，省略笔列表详情
"""
import sys, ccxt
from czsc import CZSC, RawBar, Freq
from datetime import datetime, timezone

symbol = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith('--') else 'ZEC/USDT'
compact = '--compact' in sys.argv

exchange = ccxt.binance({'enableRateLimit': True})

# Fetch data
bars_d = exchange.fetch_ohlcv(symbol, '1d', since=exchange.parse8601('2026-03-18T00:00:00Z'), limit=90)
bars_1h = exchange.fetch_ohlcv(symbol, '1h', since=exchange.parse8601('2026-05-17T00:00:00Z'), limit=720)
bars_15m = exchange.fetch_ohlcv(symbol, '15m', since=exchange.parse8601('2026-06-12T00:00:00Z'), limit=480)

print(f"标的: {symbol} | 数据: 日线{len(bars_d)}根 | 1H{len(bars_1h)}根 | 15min{len(bars_15m)}根")
print(f"当前价: ${bars_d[-1][4]:.1f} (日线) | ${bars_1h[-1][4]:.1f} (1H)\n")

def to_rawbar(bars, freq):
    result = []
    for i, b in enumerate(bars):
        dt = datetime.fromtimestamp(b[0]/1000, tz=timezone.utc)
        result.append(RawBar(symbol=symbol, dt=dt, freq=freq,
                             open=b[1], close=b[4], high=b[2], low=b[3],
                             vol=float(b[5] or 0), amount=0.0, id=i))
    return result

c_d = CZSC(to_rawbar(bars_d, Freq.D), max_bi_num=50)
c_1h = CZSC(to_rawbar(bars_1h, Freq.F60), max_bi_num=50)
c_15 = CZSC(to_rawbar(bars_15m, Freq.F15), max_bi_num=50)

def bi_str(bi):
    d = 'UP' if '向上' in str(bi.direction) else 'DN'
    return f"{d} {bi.sdt.strftime('%m-%d')} ${bi.low if d=='UP' else bi.high:.1f} -> {bi.edt.strftime('%m-%d')} ${bi.high if d=='UP' else bi.low:.1f} | {bi.power:+.0f}%"

def show_czsc(c, label, bars, n_bi=8, n_fx=5):
    print("=" * 60)
    print(f"=== {label} 缠论分析 ===")
    print("=" * 60)
    print(f"K线: {len(bars)} | 分型: {len(c.fx_list)} | 笔: {len(c.bi_list)} | UBI分型: {len(c.ubi_fxs)}")
    
    zs_fxs = [f for f in c.ubi_fxs if f.has_zs]
    print(f"含中枢的分型: {len(zs_fxs)}")
    
    if not compact:
        print(f"\n--- 分型 (最近{n_fx}) ---")
        for fx in c.fx_list[-n_fx:]:
            m = 'TOP' if '顶' in str(fx.mark) else 'BOT'
            print(f"  {fx.dt.strftime('%m-%d')} {m} @ ${fx.fx:.1f}")
        
        print(f"\n--- 笔 (最近{n_bi}) ---")
        for bi in c.bi_list[-n_bi:]:
            print(f"  {bi_str(bi)}")
    
    if zs_fxs:
        print(f"\n--- 中枢 ---")
        for f in zs_fxs[-3:]:
            print(f"  {f.dt.strftime('%m-%d')} {f.mark} fx=${f.fx:.1f} range=${f.low:.1f}-${f.high:.1f} power={f.power_str}")
    
    cur = bars[-1][4]
    last_bi = c.bi_list[-1]
    print(f"\n当前价: ${cur:.1f} | 最后一笔: {bi_str(last_bi)}")

# Show all levels
show_czsc(c_d, "日线 (90日)", bars_d)
show_czsc(c_1h, "1H (30日)", bars_1h)
show_czsc(c_15, "15min (5日)", bars_15m)

# Combined analysis
print("\n" + "=" * 60)
print("=== 多级别联立 + 买卖点 ===")
print("=" * 60)

bi_d = c_d.bi_list[-1]
dir_d = 'UP' if '向上' in str(bi_d.direction) else 'DN'
bi_1h = c_1h.bi_list[-1]
dir_1h = 'UP' if '向上' in str(bi_1h.direction) else 'DN'
bi_15 = c_15.bi_list[-1]
dir_15 = 'UP' if '向上' in str(bi_15.direction) else 'DN'

print(f"\n日线: {dir_d} {bi_d.power:+.0f}% ({bi_d.sdt.strftime('%m-%d')} -> {bi_d.edt.strftime('%m-%d')})")
print(f"1H:   {dir_1h} {bi_1h.power:+.0f}% ({bi_1h.sdt.strftime('%m-%d %H:%M')} -> {bi_1h.edt.strftime('%m-%d %H:%M')})")
print(f"15min:{dir_15} {bi_15.power:+.0f}% ({bi_15.sdt.strftime('%m-%d %H:%M')} -> {bi_15.edt.strftime('%m-%d %H:%M')})")

print("\n--- 共振判断 ---")
if dir_d == 'UP' and dir_1h == 'UP' and dir_15 == 'UP':
    print("GREEN: 三级共振上升 -> 强做多")
elif dir_d == 'DN' and dir_1h == 'DN' and dir_15 == 'DN':
    print("RED: 三级共振下降 -> 强做空")
elif dir_d == 'UP' and dir_1h == 'DN':
    print("YELLOW: 日线上升+1H回调 -> 二买候选")
elif dir_d == 'DN' and dir_1h == 'UP':
    print("YELLOW: 日线下降+1H反弹 -> 二卖候选")
elif dir_1h == 'UP' and dir_15 == 'DN':
    print("YELLOW: 1H上升+15min回调 -> 短线低吸")
elif dir_1h == 'DN' and dir_15 == 'UP':
    print("YELLOW: 1H下降+15min反弹 -> 短线高抛")
else:
    print("GREY: 无明确共振")

# 中枢汇总
print("\n--- 中枢汇总 ---")
for name, c_obj in [("日线", c_d), ("1H", c_1h), ("15min", c_15)]:
    zs_fxs = [f for f in c_obj.ubi_fxs if f.has_zs]
    if zs_fxs:
        zs = zs_fxs[-1]
        print(f"  {name}: ${zs.low:.1f} - ${zs.high:.1f} ({zs.dt.strftime('%m-%d')} {zs.mark}, power={zs.power_str})")
    else:
        print(f"  {name}: 无中枢")
