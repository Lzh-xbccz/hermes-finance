#!/usr/bin/env python3
"""美股六维数据采集脚本。用法: python3 fetch_data.py <TICKER> [blocks]
blocks: all | price | klines | structure | drivers | sentiment | macro | crossval
"""
import json, sys, time, urllib.request, xml.etree.ElementTree as ET
from datetime import datetime, timezone

UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

def fetch(url, timeout=10, retries=3):
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers=UA)
            return json.load(urllib.request.urlopen(req, timeout=timeout))
        except urllib.request.HTTPError as e:
            if e.code == 429 and attempt < retries - 1:
                import time; time.sleep(2 ** attempt + 1)
                continue
            raise

def safe_fetch(url, label="", timeout=10):
    try:
        return fetch(url, timeout)
    except Exception as e:
        print(f'⚠️ {label or url}: {type(e).__name__}')
        return None

def yahoo_chart(symbol, range_='30d', interval='1d'):
    return safe_fetch(f'https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval={interval}&range={range_}', symbol)

# ─── 块0: 市场状态 ───
def block_status(ticker):
    now = datetime.now(timezone.utc)
    hour, minute, weekday = now.hour, now.minute, now.weekday()
    is_dst = 3 <= now.month <= 11
    open_h, close_h = (13, 20) if is_dst else (14, 21)
    total_min = hour * 60 + minute
    if weekday >= 5: status = '🔴 周末休市'
    elif total_min < open_h * 60 + 30: status = '🌅 盘前'
    elif total_min < close_h * 60: status = '🟢 盘中'
    else: status = '🌆 盘后'
    print(f'分析时间(UTC): {now.strftime("%Y-%m-%d %H:%M")} | 美股: {status}')
    print(f'标的: {ticker}')

# ─── 块1: 价格+30日历史 ───
def block_price(ticker):
    d = yahoo_chart(ticker, '30d', '1d')
    if not d: return
    data = d['chart']['result'][0]
    meta, quotes, idx = data['meta'], data['indicators']['quote'][0], data['timestamp']
    print(f'=== {ticker} 近30日 ===')
    for i in range(len(idx)):
        o, c, h, l, v = quotes['open'][i], quotes['close'][i], quotes['high'][i], quotes['low'][i], quotes['volume'][i]
        if o is None: continue
        dt = datetime.fromtimestamp(idx[i], tz=timezone.utc).strftime('%m-%d')
        chg = (c-o)/o*100
        print(f'{dt} {"🟢" if chg>=0 else "🔴"} O:{o:,.2f} H:{h:,.2f} L:{l:,.2f} C:{c:,.2f} {chg:+.2f}% vol:{v:,.0f}')
    prev, cur = meta.get('chartPreviousClose',0), meta.get('regularMarketPrice',0)
    print(f'\n当前: ${cur:,.2f} | 前收: ${prev:,.2f} | 变动: {(cur-prev)/prev*100:+.2f}%')
    print(f'52周: ${meta.get("fiftyTwoWeekLow",0):,.2f} ~ ${meta.get("fiftyTwoWeekHigh",0):,.2f}')

# ─── 块1.2: 轨迹复盘 ───
def block_klines(ticker):
    d = yahoo_chart(ticker, '30d', '1d')
    if not d: return
    data = d['chart']['result'][0]
    quotes, idx = data['indicators']['quote'][0], data['timestamp']
    rows = [{'t':idx[i],'o':quotes['open'][i],'h':quotes['high'][i],'l':quotes['low'][i],'c':quotes['close'][i],'v':quotes['volume'][i]}
            for i in range(len(idx)) if quotes['open'][i] is not None]
    hi = max(rows, key=lambda r: r['h'])
    lo = min(rows, key=lambda r: r['l'])
    print(f'=== {ticker} 30D轨迹复盘 ===')
    print(f'区间: ${lo["l"]:,.2f} ({datetime.fromtimestamp(lo["t"],tz=timezone.utc).strftime("%m-%d")}) ~ ${hi["h"]:,.2f} ({datetime.fromtimestamp(hi["t"],tz=timezone.utc).strftime("%m-%d")})')
    # 摆点
    ph, pl = [], []
    for i in range(2, len(rows)-2):
        if all(rows[i]['h'] > rows[i+d]['h'] for d in [-2,-1,1,2]): ph.append(rows[i])
        if all(rows[i]['l'] < rows[i+d]['l'] for d in [-2,-1,1,2]): pl.append(rows[i])
    print('摆高:', ' | '.join(f'{datetime.fromtimestamp(r["t"],tz=timezone.utc).strftime("%m-%d")} ${r["h"]:,.2f}' for r in ph[-4:]))
    print('摆低:', ' | '.join(f'{datetime.fromtimestamp(r["t"],tz=timezone.utc).strftime("%m-%d")} ${r["l"]:,.2f}' for r in pl[-4:]))
    # 90D轮廓
    d90 = yahoo_chart(ticker, '90d', '1d')
    if d90:
        closes = [x for x in d90['chart']['result'][0]['indicators']['quote'][0]['close'] if x]
        if len(closes) >= 20:
            print(f'90d:{(closes[-1]/closes[0]-1)*100:+.1f}% 20d:{(closes[-1]/closes[-20]-1)*100:+.1f}% 7d:{(closes[-1]/closes[-7]-1)*100:+.1f}%')
    # 1H
    d1h = yahoo_chart(ticker, '7d', '60m')
    if d1h:
        quotes1h = d1h['chart']['result'][0]['indicators']['quote'][0]
        idx1h = d1h['chart']['result'][0]['timestamp']
        print(f'\n=== 1H K线(近16根) ===')
        start = max(0, len(idx1h)-16)
        for i in range(start, len(idx1h)):
            o,h,l,c = quotes1h['open'][i],quotes1h['high'][i],quotes1h['low'][i],quotes1h['close'][i]
            if o is None: continue
            dt = datetime.fromtimestamp(idx1h[i], tz=timezone.utc).strftime('%m-%d %H:%M')
            print(f'{dt} {"🟢" if c>=o else "🔴"} O:{o:,.2f} H:{h:,.2f} L:{l:,.2f} C:{c:,.2f} body:{abs(c-o)/o*100:.2f}%')

# ─── 块2: 市场结构 ───
def block_structure(ticker):
    symbols = ['SPY', 'QQQ', 'IWM', 'XLF', 'XLK', 'XLE', 'XLV', 'XLI', 'XLY']
    print('=== 市场结构 ===')
    for sym in symbols:
        d = yahoo_chart(sym, '5d', '1d')
        if d:
            m = d['chart']['result'][0]['meta']
            cur, prev = m.get('regularMarketPrice',0), m.get('chartPreviousClose',0)
            chg = (cur-prev)/prev*100 if prev else 0
            print(f'{"🟢" if chg>0 else "🔴"} {sym:<6} ${cur:,.2f} {chg:+.2f}%')
        time.sleep(0.2)

# ─── 块2.5: 主导力量 ───
def block_drivers(ticker):
    print(f'=== {ticker} 主导力量 ===')
    # 财报新闻
    try:
        url = f'https://news.google.com/rss/search?q={ticker}+earnings+report+date&hl=en-US&gl=US&ceid=US:en'
        req = urllib.request.Request(url, headers=UA)
        root = ET.fromstring(urllib.request.urlopen(req, timeout=10).read().decode())
        print('--- 财报日历 ---')
        for item in root.findall('./channel/item')[:3]:
            print(f'  {item.findtext("title","").strip()}')
    except: print('  财报日历获取失败')
    # 期权OI
    try:
        d = safe_fetch(f'https://query1.finance.yahoo.com/v7/finance/options/{ticker}', '期权')
        if d:
            opt = d.get('optionChain',{}).get('result',[{}])[0]
            calls = opt.get('options',[{}])[0].get('calls',[])
            puts = opt.get('options',[{}])[0].get('puts',[])
            call_oi = sum(c.get('openInterest',0) or 0 for c in calls[:5])
            put_oi = sum(p.get('openInterest',0) or 0 for p in puts[:5])
            tag = '🔴Put>Call' if put_oi > call_oi*1.2 else '🟢Call>Put' if call_oi > put_oi*1.2 else '⚪均衡'
            print(f'期权OI(前5档): Call:{call_oi:,} Put:{put_oi:,} → {tag}')
    except: pass

# ─── 块4: 情绪面 ───
def block_sentiment(ticker):
    print('=== 情绪面 ===')
    d = yahoo_chart('^VIX', '10d', '1d')
    if d:
        m = d['chart']['result'][0]['meta']
        cur = m.get('regularMarketPrice',0)
        tag = '🟢安逸' if cur<15 else '🟡正常' if cur<20 else '🟠警惕' if cur<25 else '🔴恐慌'
        print(f'VIX: {cur:.1f} → {tag}')
    # SPY vs IWM广度
    for sym in ['SPY', 'IWM']:
        d = yahoo_chart(sym, '5d', '1d')
        if d:
            m = d['chart']['result'][0]['meta']
            cur, prev = m.get('regularMarketPrice',0), m.get('chartPreviousClose',0)
            print(f'{sym}: {(cur-prev)/prev*100:+.2f}%')

# ─── 块5: 宏观面 ───
def block_macro(ticker):
    print('=== 宏观面 ===')
    for sym, label in {'^TNX':'10Y', '^FVX':'5Y', 'DX-Y.NYB':'DXY', '^VIX':'VIX'}.items():
        d = yahoo_chart(sym, '2d', '1d')
        if d:
            m = d['chart']['result'][0]['meta']
            cur, prev = m.get('regularMarketPrice',0), m.get('chartPreviousClose',0)
            chg = (cur-prev)/prev*100 if prev else 0
            print(f'{label}: {cur:.2f} ({chg:+.2f}%)')
        time.sleep(0.3)
    # 宏观新闻
    try:
        url = 'https://news.google.com/rss/search?q=Federal+Reserve+interest+rate+stock+market&hl=en-US&gl=US&ceid=US:en'
        req = urllib.request.Request(url, headers=UA)
        root = ET.fromstring(urllib.request.urlopen(req, timeout=10).read().decode())
        print('\n--- 宏观新闻 ---')
        for item in root.findall('./channel/item')[:3]:
            print(f'  {item.findtext("title","").strip()}')
    except: pass

# ─── 块6: 交叉验证 ───
def block_crossval(ticker):
    peers_map = {
        'AAPL': ['MSFT','GOOGL','XLK','SPY','QQQ'], 'TSLA': ['RIVN','GM','XLY','SPY','QQQ'],
        'NVDA': ['AMD','INTC','SMH','SPY','QQQ'], 'MSFT': ['AAPL','GOOGL','XLK','SPY','QQQ'],
        'AMZN': ['WMT','TGT','XLY','SPY','QQQ'], 'META': ['GOOGL','SNAP','XLK','SPY','QQQ'],
        'JPM': ['BAC','GS','XLF','SPY','IWM'], 'XOM': ['CVX','COP','XLE','SPY','IWM'],
    }
    peers = peers_map.get(ticker.upper(), ['SPY', 'QQQ', 'IWM'])
    print(f'=== 交叉验证: {ticker} vs {peers} ===')
    results = {}
    for sym in [ticker] + peers:
        d = yahoo_chart(sym, '5d', '1d')
        if d:
            m = d['chart']['result'][0]['meta']
            cur, prev = m.get('regularMarketPrice',0), m.get('chartPreviousClose',0)
            chg = (cur-prev)/prev*100 if prev else 0
            results[sym] = chg
            print(f'{"🟢" if chg>0 else "🔴"} {sym:<6} {chg:+.2f}%')
        time.sleep(0.2)
    if ticker in results and len(results) >= 4:
        t_up = results[ticker] > 0
        consistent = sum(1 for s in peers if s in results and (results[s]>0)==t_up)
        print(f'方向一致性: {consistent}/{len(peers)} → {"✅高共识" if consistent>=len(peers)*0.6 else "🔴分歧"}')

# ─── 主入口 ───
BLOCKS = {
    'status': block_status, 'price': block_price, 'klines': block_klines,
    'structure': block_structure, 'drivers': block_drivers,
    'sentiment': block_sentiment, 'macro': block_macro, 'crossval': block_crossval,
}

def main():
    if len(sys.argv) < 2:
        print(f'用法: python3 {sys.argv[0]} <TICKER> [blocks]')
        print(f'blocks: {",".join(BLOCKS.keys())} | all')
        return
    ticker = sys.argv[1].upper()
    blocks_arg = sys.argv[2] if len(sys.argv) > 2 else 'all'
    run_blocks = list(BLOCKS.keys()) if blocks_arg == 'all' else [b.strip() for b in blocks_arg.split(',')]
    for name in run_blocks:
        if name in BLOCKS:
            print(f'\n{"="*60}')
            BLOCKS[name](ticker)

if __name__ == '__main__':
    main()
