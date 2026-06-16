#!/usr/bin/env python3
"""czsc 缠论多级别分析脚本 — CCXT(Binance) 数据源

用法:
    python3 czsc_analyze.py ZEC          # 默认: 日线+1H+15min
    python3 czsc_analyze.py BTC D 1H 15  # 指定周期
    python3 czsc_analyze.py ETH --brief  # 简洁输出

输出: 分型/笔/中枢/多级别共振/买卖点判断
"""

import sys, argparse
from datetime import datetime, timezone
import ccxt
from czsc import CZSC, RawBar, Freq

# ── 周期映射 ──
FREQ_MAP = {
    'D':   (Freq.D,   '1d',   90,   '日线'),
    '1H':  (Freq.F60, '1h',  720,   '1H'),
    '15':  (Freq.F15, '15m', 480,   '15min'),
    '5':   (Freq.F5,  '5m',  500,   '5min'),
    '30':  (Freq.F30, '30m', 480,   '30min'),
    'W':   (Freq.W,   '1w',   52,   '周线'),
}

def fetch_bars(symbol, freq_key):
    """拉取K线并转为RawBar列表"""
    freq, interval, limit, _ = FREQ_MAP[freq_key]
    exchange = ccxt.binance({'enableRateLimit': True})
    since = exchange.parse8601('2026-01-01T00:00:00Z')
    symbol_ccxt = f'{symbol}/USDT'
    bars = exchange.fetch_ohlcv(symbol_ccxt, interval, since=since, limit=limit)
    
    result = []
    for i, b in enumerate(bars):
        dt = datetime.fromtimestamp(b[0]/1000, tz=timezone.utc)
        result.append(RawBar(
            symbol=symbol_ccxt, dt=dt, freq=freq,
            open=b[1], close=b[4], high=b[2], low=b[3],
            vol=float(b[5] or 0),
            amount=float(b[5] or 0) * (b[4]+b[1])/2,
            id=i,
        ))
    return result, [b[4] for b in bars]  # bars + closes

def bi_dir(bi):
    """笔方向: '↑' or '↓'"""
    return '↑' if '向上' in str(bi.direction) else '↓'

def bi_desc(bi):
    d = bi_dir(bi)
    lo = bi.low if d == '↑' else bi.high
    hi = bi.high if d == '↑' else bi.low
    return f"{d} {bi.sdt.strftime('%m-%d')} ${lo:.0f}→{bi.edt.strftime('%m-%d')} ${hi:.0f} {bi.power:+.0f}%"

def get_zs(c):
    """提取中枢列表"""
    return [f for f in c.ubi_fxs if f.has_zs]

def analyze(symbol, freqs=None, brief=False):
    freqs = freqs or ['D', '1H', '15']
    results = {}
    
    for fk in freqs:
        _, _, _, label = FREQ_MAP[fk]
        bars, closes = fetch_bars(symbol, fk)
        c = CZSC(bars, max_bi_num=50)
        zs_list = get_zs(c)
        results[fk] = {
            'label': label, 'czsc': c, 'bars': bars, 'closes': closes,
            'zs_list': zs_list, 'n_fx': len(c.fx_list), 'n_bi': len(c.bi_list),
        }
    
    if brief:
        _print_brief(symbol, results)
    else:
        _print_full(symbol, results)

def _print_full(symbol, results):
    for fk, r in results.items():
        c = r['czsc']
        print(f"\n{'='*55}")
        print(f"=== {symbol}/USDT {r['label']} — {r['n_fx']}分型 {r['n_bi']}笔 {len(r['zs_list'])}中枢 ===")
        print(f"{'='*55}")
        
        # 最近5分型
        print(f"\n分型:")
        for fx in c.fx_list[-5:]:
            m = '🔴顶' if '顶' in str(fx.mark) else '🟢底'
            print(f"  {fx.dt.strftime('%m-%d')} {m} @ ${fx.fx:.1f}")
        
        # 最近8笔
        print(f"\n笔:")
        for bi in c.bi_list[-8:]:
            print(f"  {bi_desc(bi)}")
        
        # 中枢
        if r['zs_list']:
            print(f"\n中枢:")
            for zs in r['zs_list'][-3:]:
                print(f"  {zs.dt.strftime('%m-%d')} {zs.mark} ${zs.low:.1f}-${zs.high:.1f} power={zs.power_str}")
        
        cur = r['closes'][-1]
        last_bi = c.bi_list[-1]
        print(f"\n当前: ${cur:.1f} | 最后一笔: {bi_desc(last_bi)}")
    
    _print_resonance(symbol, results)

def _print_brief(symbol, results):
    """简洁模式：仅输出共振 + 买卖点"""
    _print_resonance(symbol, results, brief=True)

def _print_resonance(symbol, results, brief=False):
    print(f"\n{'='*55}")
    print(f"=== 🎯 {symbol}/USDT 多级别联立 + 买卖点 ===")
    print(f"{'='*55}")
    
    dirs = {}
    for fk, r in results.items():
        bi = r['czsc'].bi_list[-1]
        dirs[fk] = bi_dir(bi)
        cur = r['closes'][-1]
        zs_list = r['zs_list']
        zs_str = f"ZS:${zs_list[-1].low:.0f}-{zs_list[-1].high:.0f}" if zs_list else "无中枢"
        print(f"  {r['label']:6s} {dirs[fk]} {bi.power:+.0f}% | 当前${cur:.1f} | {zs_str}")
    
    primary = list(results.keys())[0]
    secondary = list(results.keys())[1] if len(results) > 1 else None
    tertiary = list(results.keys())[2] if len(results) > 2 else None
    
    print(f"\n共振判断:")
    d1 = dirs.get(primary, '?')
    d2 = dirs.get(secondary, '?') if secondary else None
    d3 = dirs.get(tertiary, '?') if tertiary else None
    
    if d1 == d2 == d3 == '↑':
        print("  🟢🟢🟢 三级共振上升 → 强做多")
    elif d1 == d2 == d3 == '↓':
        print("  🔴🔴🔴 三级共振下降 → 强做空")
    elif d1 == '↑' and d2 == '↓':
        print(f"  🟡 {results[primary]['label']}上升+{results[secondary]['label']}回调 → 二买候选")
    elif d1 == '↓' and d2 == '↑':
        print(f"  🟡 {results[primary]['label']}下降+{results[secondary]['label']}反弹 → 二卖候选")
    elif d2 == '↑' and d3 == '↓':
        print(f"  🟡 {results[secondary]['label']}上升+{results[tertiary]['label']}回调 → 短线低吸")
    elif d2 == '↓' and d3 == '↑':
        print(f"  🟡 {results[secondary]['label']}下降+{results[tertiary]['label']}反弹 → 短线高抛")
    else:
        print("  ⚪ 无明确共振 — 等方向确认")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='czsc 缠论多级别分析')
    parser.add_argument('symbol', help='币种符号 (ZEC, BTC, ETH, SOL...)')
    parser.add_argument('freqs', nargs='*', default=['D', '1H', '15'],
                        choices=list(FREQ_MAP.keys()), help='分析周期')
    parser.add_argument('--brief', '-b', action='store_true', help='简洁输出')
    args = parser.parse_args()
    
    symbol = args.symbol.upper()
    analyze(symbol, args.freqs or ['D', '1H', '15'], args.brief)
