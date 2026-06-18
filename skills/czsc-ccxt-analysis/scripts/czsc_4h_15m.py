import ccxt
from czsc import CZSC, RawBar, Freq
from datetime import datetime, timezone, timedelta

exchange = ccxt.binance({'enableRateLimit': True})

# ── Data Fetch ──
# 30 days of 1H → aggregate to 4H
_since_1h = (datetime.now(timezone.utc) - timedelta(days=30)).strftime('%Y-%m-%dT00:00:00Z')
bars_1h_raw = exchange.fetch_ohlcv('ZEC/USDT', '1h',
    since=exchange.parse8601(_since_1h), limit=720)

# 10 days of 15min
_since_15m = (datetime.now(timezone.utc) - timedelta(days=10)).strftime('%Y-%m-%dT00:00:00Z')
bars_15m_raw = exchange.fetch_ohlcv('ZEC/USDT', '15m',
    since=exchange.parse8601(_since_15m), limit=960)

print(f"原始数据: 1H={len(bars_1h_raw)}根 | 15min={len(bars_15m_raw)}根")

# ── 4H Aggregation ──
bars_4h = []
chunk = []
for b in bars_1h_raw:
    dt = datetime.fromtimestamp(b[0]/1000, tz=timezone.utc)
    hour_block = dt.hour // 4 * 4
    block_key = dt.strftime('%Y-%m-%d') + f'-{hour_block:02d}'
    
    if not chunk or block_key != chunk_key:
        if chunk:
            bars_4h.append([
                chunk[0][0],                           # open timestamp
                chunk[0][1],                           # open
                max(c[2] for c in chunk),              # high
                min(c[3] for c in chunk),              # low
                chunk[-1][4],                          # close
                sum(c[5] for c in chunk),              # volume
            ])
        chunk = [b]
        chunk_key = block_key
    else:
        chunk.append(b)
if chunk:
    bars_4h.append([
        chunk[0][0], chunk[0][1],
        max(c[2] for c in chunk), min(c[3] for c in chunk),
        chunk[-1][4], sum(c[5] for c in chunk),
    ])

print(f"4H聚合: {len(bars_4h)}根 | 15min: {len(bars_15m_raw)}根")

# ── RawBar conversion ──
def to_rawbar(bars, freq):
    result = []
    for i, b in enumerate(bars):
        dt = datetime.fromtimestamp(b[0]/1000, tz=timezone.utc)
        result.append(RawBar(symbol='ZEC/USDT', dt=dt, freq=freq,
                             open=b[1], close=b[4], high=b[2], low=b[3],
                             vol=float(b[5] or 0), amount=0.0, id=i))
    return result

# ⚠️ czsc没有Freq.H4，用Freq.F60作为元数据标签，但不影响算法
c_4h = CZSC(to_rawbar(bars_4h, Freq.F60), max_bi_num=50)
c_15 = CZSC(to_rawbar(bars_15m_raw, Freq.F15), max_bi_num=50)

# ── Helper ──
def bi_short(bi):
    d = 'UP' if '向上' in str(bi.direction) else 'DN'
    return (f"{d} {bi.sdt.strftime('%m-%d %H:%M')} ${bi.low if d=='UP' else bi.high:.1f}"
            f" → {bi.edt.strftime('%m-%d %H:%M')} ${bi.high if d=='UP' else bi.low:.1f}"
            f" | {bi.power:+.0f}% | {bi.length}K SNR={bi.SNR:.2f}")

def gap_analysis(fx_list, label):
    """Detect large gaps in price between consecutive fractals"""
    gaps = []
    for i in range(1, len(fx_list)):
        gap_pct = abs(fx_list[i].fx - fx_list[i-1].fx) / fx_list[i-1].fx * 100
        if gap_pct > 3:
            gaps.append((fx_list[i-1], fx_list[i], gap_pct))
    if gaps:
        print(f"\n  --- {label} 大波动分型 (gap>3%) ---")
        for a, b, g in gaps[-6:]:
            print(f"  {a.dt.strftime('%m-%d %H:%M')} ${a.fx:.0f} → "
                  f"{b.dt.strftime('%m-%d %H:%M')} ${b.fx:.0f} | 跳变 {g:.0f}%")

# ═══════════════════════════════════════
# 4H Analysis
# ═══════════════════════════════════════
print("\n" + "=" * 70)
print("=== 4H 缠论分析 (30日, 聚合自1H) ===")
print("=" * 70)
print(f"K线: {len(bars_4h)} | 分型: {len(c_4h.fx_list)} | 笔: {len(c_4h.bi_list)} | UBI分型: {len(c_4h.ubi_fxs)}")

# 4H Fractals
print(f"\n--- 4H 分型 (全部 {len(c_4h.fx_list)}个) ---")
for fx in c_4h.fx_list:
    m = 'TOP' if '顶' in str(fx.mark) else 'BOT'
    highlight = ''
    if fx.dt >= datetime(2026, 6, 3):
        highlight = ' ◀◀'
    print(f"  {fx.dt.strftime('%m-%d %H:%M')} {m} @ ${fx.fx:.1f}{highlight}")

gap_analysis(c_4h.fx_list, "4H")

# 4H BIs
print(f"\n--- 4H 笔 (全部 {len(c_4h.bi_list)}笔) ---")
for i, bi in enumerate(c_4h.bi_list):
    print(f"  BI#{i}: {bi_short(bi)}")

# 4H ZS
zs_4h = [f for f in c_4h.ubi_fxs if f.has_zs]
print(f"\n--- 4H 中枢 ({len(zs_4h)}个) ---")
for zs in zs_4h:
    print(f"  {zs.dt.strftime('%m-%d %H:%M')} {zs.mark} fx=${zs.fx:.1f} "
          f"range=${zs.low:.1f}-${zs.high:.1f} power={zs.power_str}")

# 4H 买卖点
last_bi_4h = c_4h.bi_list[-1]
last_dir_4h = 'UP' if '向上' in str(last_bi_4h.direction) else 'DN'
print(f"\n--- 4H 当前位置 ---")
print(f"最后一笔: {bi_short(last_bi_4h)}")
print(f"最新价: ${bars_4h[-1][4]:.1f}")

if zs_4h:
    zs = zs_4h[-1]
    cur = bars_4h[-1][4]
    if cur > zs.high:
        print(f"价格 ${cur:.1f} > 中枢上沿 ${zs.high:.1f} → 中枢上方运行")
    elif cur > zs.low:
        pos_pct = (cur - zs.low) / (zs.high - zs.low) * 100 if zs.high != zs.low else 50
        print(f"价格 ${cur:.1f} 在 中枢 ${zs.low:.1f}-${zs.high:.1f} 内部 ({pos_pct:.0f}%)")
    else:
        print(f"价格 ${cur:.1f} < 中枢下沿 ${zs.low:.1f} → 中枢下方 ⚠️")

# Look ahead: unprocessed fractals after last BI
last_bi_end_4h = last_bi_4h.edt
remaining_fxs_4h = [f for f in c_4h.fx_list if f.dt > last_bi_end_4h]
if remaining_fxs_4h:
    print(f"\n  最近笔后未处理分型: {len(remaining_fxs_4h)}个")
    for f in remaining_fxs_4h:
        m = 'TOP' if '顶' in str(f.mark) else 'BOT'
        print(f"    {f.dt.strftime('%m-%d %H:%M')} {m} @ ${f.fx:.1f}")

# ═══════════════════════════════════════
# 15min Analysis  
# ═══════════════════════════════════════
print("\n" + "=" * 70)
print("=== 15min 缠论分析 (10日) ===")
print("=" * 70)
print(f"K线: {len(bars_15m_raw)} | 分型: {len(c_15.fx_list)} | 笔: {len(c_15.bi_list)} | UBI分型: {len(c_15.ubi_fxs)}")

# 15min Fractals (最近20个)
print(f"\n--- 15min 分型 (最近20/共{len(c_15.fx_list)}) ---")
for fx in c_15.fx_list[-20:]:
    m = 'T' if '顶' in str(fx.mark) else 'B'
    print(f"  {fx.dt.strftime('%m-%d %H:%M')} {m} ${fx.fx:.1f}")

gap_analysis(c_15.fx_list, "15min")

# 15min BIs (最近10笔)
print(f"\n--- 15min 笔 (最近10/共{len(c_15.bi_list)}) ---")
for bi in c_15.bi_list[-10:]:
    print(f"  {bi_short(bi)}")

# 15min ZS
zs_15 = [f for f in c_15.ubi_fxs if f.has_zs]
print(f"\n--- 15min 中枢 ({len(zs_15)}个) ---")
for zs in zs_15[-5:]:
    print(f"  {zs.dt.strftime('%m-%d %H:%M')} {zs.mark} fx=${zs.fx:.1f} "
          f"range=${zs.low:.1f}-${zs.high:.1f} power={zs.power_str}")

# 15min current
last_bi_15 = c_15.bi_list[-1]
last_dir_15 = 'UP' if '向上' in str(last_bi_15.direction) else 'DN'
print(f"\n--- 15min 当前位置 ---")
print(f"最后一笔: {bi_short(last_bi_15)}")
print(f"最新价: ${bars_15m_raw[-1][4]:.1f}")

if zs_15:
    zs = zs_15[-1]
    cur = bars_15m_raw[-1][4]
    if cur > zs.high:
        print(f"价格 ${cur:.1f} > 中枢上沿 ${zs.high:.1f} → 中枢上方")
    elif cur > zs.low:
        pos_pct = (cur - zs.low) / (zs.high - zs.low) * 100 if zs.high != zs.low else 50
        print(f"价格 ${cur:.1f} 在 中枢 ${zs.low:.1f}-${zs.high:.1f} 内部 ({pos_pct:.0f}%)")
    else:
        print(f"价格 ${cur:.1f} < 中枢下沿 ${zs.low:.1f} → ⚠️ 中枢下方破位")

# ═══════════════════════════════════════
# Cross-level Summary
# ═══════════════════════════════════════
print("\n" + "=" * 70)
print("=== 📊 4H + 15min 联立总结 ===")
print("=" * 70)

# Direction summary
def dir_sym(bi):
    return '↑' if '向上' in str(bi.direction) else '↓'

print(f"\n{'级别':<8} {'最后笔方向':<12} {'笔力度':<10} {'中枢位置':<20} {'价格vs中枢':<15}")
print("-" * 65)

# 4H
d4 = dir_sym(last_bi_4h)
z4_str = f"${zs_4h[-1].low:.0f}-{zs_4h[-1].high:.0f}" if zs_4h else "无"
cur4 = bars_4h[-1][4]
if zs_4h:
    vs4 = "上方" if cur4 > zs_4h[-1].high else ("内部" if cur4 >= zs_4h[-1].low else "下方⚠️")
else:
    vs4 = "—"
print(f"{'4H':<8} {d4:<12} {last_bi_4h.power:+.0f}%{'':<6} {z4_str:<20} {vs4:<15}")

# 15min
d15 = dir_sym(last_bi_15)
z15_str = f"${zs_15[-1].low:.0f}-{zs_15[-1].high:.0f}" if zs_15 else "无"
cur15 = bars_15m_raw[-1][4]
if zs_15:
    vs15 = "上方" if cur15 > zs_15[-1].high else ("内部" if cur15 >= zs_15[-1].low else "下方⚠️")
else:
    vs15 = "—"
print(f"{'15min':<8} {d15:<12} {last_bi_15.power:+.0f}%{'':<6} {z15_str:<20} {vs15:<15}")

# Resonance
print(f"\n--- 共振判断 ---")
if d4 == '↑' and d15 == '↑':
    print("🟢 4H+15min 双级别共振上升 — 短线偏多")
elif d4 == '↓' and d15 == '↓':
    print("🔴 4H+15min 双级别共振下降 — 短线偏空")
elif d4 == '↑' and d15 == '↓':
    print("🟡 4H上升 + 15min回调 — 等15min回调结束做多（二买）")
else:
    print("🟡 4H下降 + 15min反弹 — 等15min反弹结束做空（二卖）")

# Check if 15min ZS is broken
if zs_15 and vs15 == "下方⚠️":
    print(f"\n⚠️ 15min中枢 ${zs_15[-1].low:.0f} 已被跌破 — 短线结构破坏")

# Check 4H ZS
if zs_4h and vs4 == "下方⚠️":
    print(f"⚠️ 4H中枢 ${zs_4h[-1].low:.0f} 已被跌破 — 中线结构破坏")
