#!/usr/bin/env python3
"""加密货币八维分析数据采集脚本。用法: python3 fetch_data.py <coin_id> [blocks]
blocks: all | price | klines | chain | contracts | sentiment | macro | exchanges | options
多个block用逗号分隔，如: python3 fetch_data.py bitcoin price,contracts,macro

并发策略：
- Binance组: 全并行（1200 req/min限制远超用量）
- Yahoo组: 串行+0.4s间隔（避免429）
- CoinGecko组: 串行+2s间隔（免费版10-30 req/min）
- 其他组(Deribit/alternative.me/blockchain.info): 全并行
- 组与组之间并行执行
"""
import json, sys, time, urllib.request
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed
from io import StringIO
import threading

UA = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Cache-Control': 'no-cache, no-store, must-revalidate',
    'Pragma': 'no-cache',
    'Expires': '0',
}

COIN_SYMBOL_ALIASES = {
    'bitcoin': 'BTC',
    'btc': 'BTC',
    'ethereum': 'ETH',
    'ether': 'ETH',
    'eth': 'ETH',
    'solana': 'SOL',
    'sol': 'SOL',
    'binancecoin': 'BNB',
    'bnb': 'BNB',
    'ripple': 'XRP',
    'xrp': 'XRP',
    'cardano': 'ADA',
    'ada': 'ADA',
    'dogecoin': 'DOGE',
    'doge': 'DOGE',
    'chainlink': 'LINK',
    'link': 'LINK',
    'avalanche-2': 'AVAX',
    'avalanche': 'AVAX',
    'avax': 'AVAX',
    'polkadot': 'DOT',
    'dot': 'DOT',
    'litecoin': 'LTC',
    'ltc': 'LTC',
    'tron': 'TRX',
    'trx': 'TRX',
    'toncoin': 'TON',
    'ton': 'TON',
    'sui': 'SUI',
    'matic-network': 'POL',
    'polygon': 'POL',
    'pol': 'POL',
    'uniswap': 'UNI',
    'uni': 'UNI',
    'aptos': 'APT',
    'apt': 'APT',
    'arbitrum': 'ARB',
    'arb': 'ARB',
    'optimism': 'OP',
    'op': 'OP',
    'near': 'NEAR',
    'near-protocol': 'NEAR',
    'filecoin': 'FIL',
    'fil': 'FIL',
    'cosmos': 'ATOM',
    'atom': 'ATOM',
    'stellar': 'XLM',
    'xlm': 'XLM',
    'hedera': 'HBAR',
    'hbar': 'HBAR',
    'injective-protocol': 'INJ',
    'injective': 'INJ',
    'inj': 'INJ',
    'pepe': 'PEPE',
    'shiba-inu': 'SHIB',
    'shib': 'SHIB',
}


STRICT_QUERY_HOSTS = (
    'api.binance.com',
    'fapi.binance.com',
    'api.bybit.com',
    'www.okx.com',
    'www.deribit.com',
)


def _bust_cache(url: str) -> str:
    """给 URL 追加时间戳参数；严格校验参数的交易所 API 不能追加。"""
    from urllib.parse import urlparse
    host = urlparse(url).netloc.lower()
    if any(host == h or host.endswith(f'.{h}') for h in STRICT_QUERY_HOSTS):
        return url
    import random
    ts = f'{int(time.time() * 1000)}_{random.randint(0, 9999)}'
    sep = '&' if '?' in url else '?'
    return f'{url}{sep}_nocache={ts}'


def fetch(url, timeout=10):
    req = urllib.request.Request(_bust_cache(url), headers=UA)
    return json.load(urllib.request.urlopen(req, timeout=timeout))


def market_symbol(coin_id: str, quote: str = 'USDT') -> str:
    """将 CoinGecko id / 常见全名 / ticker 统一成交易所交易对。"""
    key = coin_id.strip().lower()
    if key.endswith(quote.lower()):
        return key.upper()
    base = COIN_SYMBOL_ALIASES.get(key, coin_id.strip().upper())
    return f'{base}{quote}'


def okx_inst_id(coin_id: str, quote: str = 'USDT') -> str:
    symbol = market_symbol(coin_id, quote)
    return f'{symbol[:-len(quote)]}-{quote}'

def safe_fetch(url, label="", timeout=10):
    try:
        return fetch(url, timeout)
    except Exception as e:
        print(f'⚠️ {label or url}: {type(e).__name__} {e}')
        return None

def fmt_ts(ts_ms):
    return datetime.fromtimestamp(ts_ms/1000, tz=timezone.utc).strftime('%m-%d %H:%M')

def fmt_date(ts_ms):
    return datetime.fromtimestamp(ts_ms/1000, tz=timezone.utc).strftime('%m-%d')

# ─── 块0: 标的确认 ───
def block_resolve(coin_id):
    print(f'分析时间(UTC): {datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")}')
    if coin_id != 'bitcoin':
        d = safe_fetch(f'https://api.coingecko.com/api/v3/search?query={coin_id}', 'CoinGecko search')
        if d:
            coins = d.get('coins', [])[:5]
            print(f'=== CoinGecko 候选标的 ===')
            for c in coins:
                print(f'{c.get("id","?"):<24} {c.get("symbol","?").upper():<8} rank=#{c.get("market_cap_rank")}')

# ─── 块1: 实时行情+30日历史 ───
def block_price(coin_id):
    symbol = market_symbol(coin_id)
    # 30日日线（Binance）
    d = safe_fetch(f'https://api.binance.com/api/v3/klines?symbol={symbol}&interval=1d&limit=30', '30日价格')
    if d:
        print('=== 近30日价格 ===')
        for row in d:
            o, h, l, c, v = float(row[1]), float(row[2]), float(row[3]), float(row[4]), float(row[5])
            vol_usd = float(row[7])  # quote asset volume
            print(f'{fmt_date(row[0])}: ${c:,.0f}  vol:${vol_usd/1e9:.1f}B')
    # 实时（Binance ticker）
    d = safe_fetch(f'https://api.binance.com/api/v3/ticker/24hr?symbol={symbol}', '实时行情')
    if d:
        cur = float(d['lastPrice'])
        high = float(d['highPrice'])
        low = float(d['lowPrice'])
        chg = float(d['priceChangePercent'])
        vol = float(d['quoteVolume'])
        print(f'\n=== 实时行情 ===')
        print(f'价格: ${cur:,.0f} | 24h: {chg:+.2f}%')
        print(f'24h高/低: ${high:,.0f} / ${low:,.0f}')
        print(f'24h量: ${vol/1e9:.1f}B')

# ─── 块1.2+1.5: K线轨迹复盘 ───
def block_klines(coin_id):
    symbol = market_symbol(coin_id)
    # 30D 4H
    d = safe_fetch(f'https://api.binance.com/api/v3/klines?symbol={symbol}&interval=4h&limit=180', '4H K线')
    if d:
        rows = [{'t':x[0],'o':float(x[1]),'h':float(x[2]),'l':float(x[3]),'c':float(x[4]),'v':float(x[5])} for x in d]
        hi = max(rows, key=lambda r: r['h'])
        lo = min(rows, key=lambda r: r['l'])
        print(f'=== 30D 4H 轨迹复盘 ===')
        print(f'区间: ${lo["l"]:,.0f} ({fmt_ts(lo["t"])}) ~ ${hi["h"]:,.0f} ({fmt_ts(hi["t"])})')
        # 摆点
        ph, pl = [], []
        for i in range(2, len(rows)-2):
            if all(rows[i]['h'] > rows[i+d]['h'] for d in [-2,-1,1,2]): ph.append(rows[i])
            if all(rows[i]['l'] < rows[i+d]['l'] for d in [-2,-1,1,2]): pl.append(rows[i])
        print('摆高:', ' | '.join(f'{fmt_ts(r["t"])} ${r["h"]:,.0f}' for r in ph[-4:]))
        print('摆低:', ' | '.join(f'{fmt_ts(r["t"])} ${r["l"]:,.0f}' for r in pl[-4:]))
        # 大波动
        events = sorted([(abs((r['c']-r['o'])/r['o']*100), r) for r in rows if r['o']], reverse=True)[:5]
        print('大波动K线:')
        for body, r in events:
            print(f'  {fmt_ts(r["t"])} body:{(r["c"]-r["o"])/r["o"]*100:+.2f}% range:{(r["h"]-r["l"])/r["o"]*100:.2f}%')
    # 90D 日线轮廓
    d = safe_fetch(f'https://api.binance.com/api/v3/klines?symbol={symbol}&interval=1d&limit=90', '日线')
    if d:
        o0, c_last, c20, c7 = float(d[0][1]), float(d[-1][4]), float(d[-20][4]), float(d[-7][4])
        print(f'\n=== 90D轮廓 === 90d:{(c_last/o0-1)*100:+.1f}% 20d:{(c_last/c20-1)*100:+.1f}% 7d:{(c_last/c7-1)*100:+.1f}%')
    # 1H 近24h
    d = safe_fetch(f'https://api.binance.com/api/v3/klines?symbol={symbol}&interval=1h&limit=24', '1H K线')
    if d:
        print(f'\n=== 1H K线(近24h) ===')
        for row in d[-16:]:
            o,h,l,c,v = float(row[1]),float(row[2]),float(row[3]),float(row[4]),float(row[5])
            color = '🟢' if c>=o else '🔴'
            print(f'{fmt_ts(row[0])} {color} O:{o:,.0f} H:{h:,.0f} L:{l:,.0f} C:{c:,.0f} body:{abs(c-o)/o*100:.2f}%')

# ─── 块2: 链上+Mempool ───
def block_chain(coin_id):
    if coin_id not in ('bitcoin', 'btc'):
        print('⚠️ 链上数据仅支持BTC，跳过')
        return
    d = safe_fetch('https://api.blockchain.info/stats', '链上')
    if d:
        hr = d.get('hash_rate', 0)
        print(f'=== 链上数据 ===')
        print(f'哈希率: {hr/1e9:.1f} EH/s | 难度: {d.get("difficulty",0)/1e12:.1f}T')
        print(f'24h交易: {d.get("n_tx",0):,}笔 | 出块: {d.get("minutes_between_blocks",0):.1f}min')
        btc_sent = d.get('total_btc_sent', 0) / 1e8
        n_tx = d.get('n_tx', 1)
        avg = btc_sent / n_tx if n_tx else 0
        tag = '⚡庄家活跃' if avg > 5 else '🟡中等' if avg > 2 else '⚪散户为主'
        print(f'平均单笔: {avg:.1f} BTC → {tag}')
    d = safe_fetch('https://mempool.space/api/mempool', 'Mempool')
    if d:
        mb = d.get('vsize', 0) / 1e6
        tag = '🟢低' if mb<1 else '🟡中' if mb<10 else '🟠较高' if mb<50 else '🔴高'
        print(f'Mempool: {d.get("count",0):,}笔 | {mb:.1f}MB | 拥堵:{tag}')

# ─── 块2.5: 合约市场 ───
def block_contracts(coin_id):
    symbol = market_symbol(coin_id)
    print(f'=== 🐋 {symbol} 永续合约 ===')

    from concurrent.futures import ThreadPoolExecutor, as_completed

    # Binance优先，全部失效时fallback Bybit V5（无需key，稳定）
    def _oi():
        d = safe_fetch(f'https://fapi.binance.com/fapi/v1/openInterest?symbol={symbol}', 'OI(Binance)')
        if d: return ('binance', d)
        d = safe_fetch(f'https://api.bybit.com/v5/market/open-interest?category=linear&symbol={symbol}&intervalTime=5min&limit=1', 'OI(Bybit)')
        if d and d.get('retCode') == 0:
            items = d['result']['list']
            return ('bybit', {'openInterest': items[0]['openInterest']}) if items else None
        return None

    def _funding():
        d = safe_fetch(f'https://fapi.binance.com/fapi/v1/fundingRate?symbol={symbol}&limit=5', '费率(Binance)')
        if d: return ('binance', d)
        d = safe_fetch(f'https://api.bybit.com/v5/market/funding/history?category=linear&symbol={symbol}&limit=5', '费率(Bybit)')
        if d and d.get('retCode') == 0:
            return ('bybit', [{'fundingRate': x['fundingRate'], 'fundingTime': int(x['fundingRateTimestamp'])} for x in d['result']['list']])
        return None

    def _ls_ratio():
        d = safe_fetch(f'https://fapi.binance.com/futures/data/topLongShortAccountRatio?symbol={symbol}&period=5m&limit=5', '多空比(Binance)')
        if d: return ('binance', d)
        d = safe_fetch(f'https://api.bybit.com/v5/market/account-ratio?category=linear&symbol={symbol}&period=5min&limit=5', '多空比(Bybit)')
        if d and d.get('retCode') == 0:
            return ('bybit', [{'longShortRatio': str(float(x['buyRatio'])/max(float(x['sellRatio']),0.001)), 'timestamp': int(x['timestamp'])} for x in d['result']['list']])
        return None

    def _oi_hist():
        d = safe_fetch(f'https://fapi.binance.com/futures/data/openInterestHist?symbol={symbol}&period=5m&limit=12', 'OI历史(Binance)')
        if d: return ('binance', d)
        d = safe_fetch(f'https://api.bybit.com/v5/market/open-interest?category=linear&symbol={symbol}&intervalTime=5min&limit=12', 'OI历史(Bybit)')
        if d and d.get('retCode') == 0:
            return ('bybit', [{'sumOpenInterest': x['openInterest'], 'timestamp': x['timestamp']} for x in d['result']['list']])
        return None

    def _ticker():
        d = safe_fetch(f'https://fapi.binance.com/fapi/v1/ticker/24hr?symbol={symbol}', '24h(Binance)')
        if d: return ('binance', d)
        d = safe_fetch(f'https://api.bybit.com/v5/market/tickers?category=linear&symbol={symbol}', '24h(Bybit)')
        if d and d.get('retCode') == 0:
            t = d['result']['list'][0]
            return ('bybit', {'quoteVolume': t.get('turnover24h','0'), 'priceChangePercent': str(float(t.get('price24hPcnt','0'))*100)})
        return None

    # 5个请求全并行
    results = {}
    with ThreadPoolExecutor(max_workers=5) as pool:
        futs = {pool.submit(fn): k for k, fn in [('oi',_oi),('funding',_funding),('ls_ratio',_ls_ratio),('oi_hist',_oi_hist),('ticker',_ticker)]}
        for f in as_completed(futs):
            results[futs[f]] = f.result()

    # 检测数据源
    sources = set()
    for v in results.values():
        if v and isinstance(v, tuple): sources.add(v[0])
    if 'bybit' in sources:
        print(f'⚠️ 部分数据来自Bybit(Binance端点不可用)')

    r = results.get('oi')
    if r: print(f'OI: {float(r[1]["openInterest"]):,.0f}')

    r = results.get('funding')
    if r:
        print('资金费率(近5次):')
        for x in r[1]:
            rate = float(x['fundingRate']) * 100
            emoji = '🔴' if rate > 0.01 else '🟢' if rate < -0.01 else '⚪'
            print(f'  {fmt_ts(x["fundingTime"])} {emoji} {rate:+.4f}%')

    r = results.get('ls_ratio')
    if r:
        latest = float(sorted(r[1], key=lambda x: x.get('timestamp',0))[-1]['longShortRatio'])
        tag = '⚠️多头极端' if latest>2.5 else '🟡偏多' if latest>1.5 else '🟢空头拥挤' if latest<0.7 else '⚪中性'
        print(f'多空比: {latest:.2f} → {tag}')

    r = results.get('oi_hist')
    if r and len(r[1]) >= 2:
        vals = [float(x['sumOpenInterest']) for x in r[1]]
        delta = (vals[-1] - vals[0]) / vals[0] * 100 if vals[0] else 0
        tag = '🟢增仓' if delta > 0.3 else '🟡减仓' if delta < -0.3 else '⚪横盘'
        print(f'OI 60min变化: {delta:+.2f}% → {tag}')

    r = results.get('ticker')
    if r:
        print(f'合约24h: ${float(r[1]["quoteVolume"])/1e9:.1f}B | 涨跌:{float(r[1]["priceChangePercent"]):+.2f}%')


# ─── 块3: 交易所交叉验证 ───
def block_exchanges(coin_id):
    symbol = market_symbol(coin_id)
    print('=== 交易所交叉验证 ===')

    from concurrent.futures import ThreadPoolExecutor, as_completed

    def _binance():
        d = safe_fetch(f'https://api.binance.com/api/v3/ticker/bookTicker?symbol={symbol}', 'Binance')
        if d: return {'name':'Binance','bid':float(d['bidPrice']),'ask':float(d['askPrice']),'price':(float(d['bidPrice'])+float(d['askPrice']))/2}
        return None

    def _bybit():
        d = safe_fetch(f'https://api.bybit.com/v5/market/tickers?category=spot&symbol={symbol}', 'Bybit')
        if d and d.get('retCode')==0:
            t = d['result']['list'][0]
            return {'name':'Bybit','bid':float(t['bid1Price']),'ask':float(t['ask1Price']),'price':float(t['lastPrice'])}
        return None

    def _okx():
        inst = okx_inst_id(coin_id)
        d = safe_fetch(f'https://www.okx.com/api/v5/market/ticker?instId={inst}', 'OKX')
        if d and d.get('code')=='0' and d.get('data'):
            t = d['data'][0]
            return {'name':'OKX','bid':float(t['bidPx']),'ask':float(t['askPx']),'price':float(t['last'])}
        return None

    # 3交易所并行
    results = []
    with ThreadPoolExecutor(max_workers=3) as pool:
        for r in [pool.submit(_binance), pool.submit(_bybit), pool.submit(_okx)]:
            d = r.result()
            if d: results.append(d)

    prices = []
    for r in results:
        spread = (r['ask']-r['bid'])/r['bid']*100
        prices.append(r['price'])
        print(f'  {r["name"]:20s} ${r["price"]:>10,.2f} | spread:{spread:.4f}%')

    if len(prices) >= 2:
        spread_max = (max(prices)-min(prices))/min(prices)*100
        tag = '✅高效' if spread_max < 0.05 else '✅正常' if spread_max < 0.2 else '⚠️偏离'
        print(f'极差: {spread_max:.4f}% → {tag}')
    else:
        print(f'⚠️ 仅{len(prices)}个交易所数据')

# ─── 块4: 情绪面 ───
def block_sentiment(coin_id):
    d = safe_fetch('https://api.alternative.me/fng/?limit=7', '恐惧贪婪')
    if d:
        print('=== 恐惧贪婪指数(7日) ===')
        for x in d['data']:
            val = int(x['value'])
            print(f'{x["timestamp"]}: {val:3d} {"█"*(val//5)}{"░"*(20-val//5)} {x["value_classification"]}')

# ─── 块5: 宏观面 ───
def block_macro(coin_id):
    print('=== 宏观面 ===')
    from concurrent.futures import ThreadPoolExecutor
    import urllib.parse

    symbol = market_symbol(coin_id)

    def _yf_snapshot(ticker):
        """Yahoo Finance 快照 — 轻量调用，只拉 5 天日线取最新价"""
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{urllib.parse.quote(ticker)}?interval=1d&range=5d"
        d = safe_fetch(url, f'YF:{ticker}')
        if not d:
            return None
        try:
            meta = d['chart']['result'][0]['meta']
            return {
                'price': meta.get('regularMarketPrice', 0),
                'prev_close': meta.get('chartPreviousClose', 0),
                'change_pct': (meta.get('regularMarketPrice', 0) / meta.get('chartPreviousClose', 1) - 1) * 100,
            }
        except (KeyError, IndexError, ZeroDivisionError):
            return None

    def _btc_dominance():
        return safe_fetch('https://api.binance.com/api/v3/ticker/24hr?symbol=ETHBTC', 'ETHBTC')

    def _total_market():
        return safe_fetch('https://api.binance.com/api/v3/ticker/24hr?symbol=BTCUSDT', 'BTC24h')

    # Binance 并行 + Yahoo 串行（避免 429）
    results = {}
    with ThreadPoolExecutor(max_workers=2) as pool:
        f_btc = pool.submit(_total_market)
        f_ethbtc = pool.submit(_btc_dominance)
        results['btc'] = f_btc.result()
        results['ethbtc'] = f_ethbtc.result()

    # Yahoo Finance 串行 + 间隔
    for key, ticker in [('vix', '^VIX'), ('dxy', 'DX-Y.NYB'), ('spy', 'SPY')]:
        results[key] = _yf_snapshot(ticker)
        time.sleep(0.4)

    # ── 加密内部风险偏好 ──
    d = results.get('btc')
    if d:
        chg = float(d.get('priceChangePercent', 0))
        vol = float(d.get('quoteVolume', 0))
        if chg > 3: tag = '🟢 Risk-on'
        elif chg < -3: tag = '🔴 Risk-off'
        else: tag = '⚪ 中性'
        print(f'BTC 24h: {chg:+.1f}% | 量:${vol/1e9:.1f}B | 风险偏好: {tag}')

    d = results.get('ethbtc')
    if d:
        chg = float(d.get('priceChangePercent', 0))
        price = float(d.get('lastPrice', 0))
        tag = '🟢山寨强势' if chg > 2 else '🔴BTC独强' if chg < -2 else '⚪均衡'
        print(f'ETH/BTC: {price:.5f} ({chg:+.1f}% 24h) → {tag}')

    # ── 传统市场联动 ──
    print('\n--- 美股/VIX/DXY ---')
    for label, key, fmt, thresholds in [
        ('VIX', 'vix', '.1f', ('🔴恐慌>25', 25, '🟢平静<15', 15)),
        ('DXY', 'dxy', '.2f', ('🟢>105 risk-off', 105, '🔴<100 risk-on', 100)),
        ('SPY', 'spy', '.2f', ('', 0, '', 0)),  # 只展示涨跌
    ]:
        r = results.get(key)
        if r and r['price'] is not None:
            chg_str = f"{r['change_pct']:+.1f}%"
            high_tag, high_val, low_tag, low_val = thresholds
            if key == 'vix':
                tag = high_tag if r['price'] > high_val else (low_tag if r['price'] < low_val else '⚪中性')
            elif key == 'dxy':
                tag = high_tag if r['price'] > high_val else (low_tag if r['price'] < low_val else '⚪中性')
            else:
                tag = '🟢' if r['change_pct'] > 0 else '🔴'
            print(f'  {label:5s} ${r["price"]:{fmt}} ({chg_str}) {tag}')

    # ── BTC 与 SPY 5 日趋势联动 ──
    # 24h 涨跌太短，用 5 日方向判断趋势联动
    try:
        # 拉 BTC 5 日线（用 Binance 而非 Yahoo，零限流）
        btc_5d = safe_fetch(
            f'https://api.binance.com/api/v3/klines?symbol={symbol}&interval=1d&limit=6',
            'BTC 5日线'
        )
        spy_5d_raw = safe_fetch(
            'https://query1.finance.yahoo.com/v8/finance/chart/SPY?interval=1d&range=5d',
            'SPY 5日线'
        )
        btc_trend = None
        spy_trend = None
        if btc_5d and len(btc_5d) >= 5:
            btc_5d_close = float(btc_5d[-1][4])
            btc_5d_ago = float(btc_5d[-5][4])
            btc_trend = (btc_5d_close / btc_5d_ago - 1) * 100
        if spy_5d_raw:
            spy_rows = spy_5d_raw['chart']['result'][0]['indicators']['quote'][0]['close']
            spy_rows = [x for x in spy_rows if x is not None]
            if len(spy_rows) >= 5:
                spy_trend = (spy_rows[-1] / spy_rows[-5] - 1) * 100
        
        if btc_trend is not None and spy_trend is not None:
            print(f'\n🔗 BTC 5日: {btc_trend:+.1f}% | SPY 5日: {spy_trend:+.1f}%')
            if btc_trend > 2 and spy_trend > 1:
                print('   → 风险偏好共振走强，加密处于有利宏观环境')
            elif btc_trend < -2 and spy_trend < -1:
                print('   → 全局风险厌恶，加密承压，关注 DXY 是否同步走高')
            elif btc_trend > 2 and spy_trend < -1:
                print('   → 加密独立走强（5日），可能是避险资金流入 BTC')
            elif btc_trend < -2 and spy_trend > 1:
                print('   → 加密独立走弱（5日），警惕板块资金外流')
            else:
                print('   → 无明确联动信号')
    except Exception:
        # 降级到 24h 快照
        btc_chg = float(results.get('btc', {}).get('priceChangePercent', 0))
        spy_r = results.get('spy')
        if spy_r and spy_r['price'] and btc_chg:
            spy_chg = spy_r['change_pct']
            print(f'\n🔗 BTC 24h: {btc_chg:+.1f}% | SPY 24h: {spy_chg:+.1f}%')
            if btc_chg > 0 and spy_chg > 0:
                print('   → 风险偏好共振（24h快照，可靠性低于5日趋势）')
            elif btc_chg < 0 and spy_chg < 0:
                print('   → 同步避险（24h快照）')

# ─── 块7: 期权(BTC only) ───
def block_options(coin_id):
    if coin_id not in ('bitcoin', 'btc'):
        print('⚠️ 期权数据仅支持BTC')
        return
    print('=== BTC期权(Deribit) ===')
    d = safe_fetch('https://www.deribit.com/api/v2/public/get_index_price?index_name=btc_usd', 'Deribit index')
    if not d: return
    btc_idx = d['result']['index_price']
    print(f'BTC Index: ${btc_idx:,.0f}')
    d = safe_fetch('https://www.deribit.com/api/v2/public/get_book_summary_by_currency?currency=BTC&kind=option', 'Deribit book')
    if d:
        put_vol = sum(float(x.get('volume_usd',0)) for x in d['result'] if x['instrument_name'].endswith('-P'))
        call_vol = sum(float(x.get('volume_usd',0)) for x in d['result'] if x['instrument_name'].endswith('-C'))
        pcr = put_vol / call_vol if call_vol > 0 else 0
        tag = '🔴看跌' if pcr > 1.2 else '🟢看涨' if pcr < 0.8 else '⚪中性'
        print(f'24h Put/Call量比: {pcr:.2f} → {tag} | 总量:${(put_vol+call_vol)/1e6:,.0f}M')

# ─── 主入口 ───
BLOCKS = {
    'resolve': block_resolve, 'price': block_price, 'klines': block_klines,
    'chain': block_chain, 'contracts': block_contracts, 'exchanges': block_exchanges,
    'sentiment': block_sentiment, 'macro': block_macro, 'options': block_options,
}

# 按数据源分组（同源串行避免限流，异源并行加速）
SOURCE_GROUPS = {
    'binance': ['klines', 'contracts', 'price', 'exchanges'],  # 全并行，限制宽松
    'yahoo': ['macro'],                           # 内部不再调Yahoo
    'other': ['resolve', 'chain', 'sentiment', 'options'],  # 全并行
}

# 线程本地存储，用于捕获print输出
_thread_local = threading.local()
_real_stdout = sys.stdout


class _ThreadPrinter:
    """线程安全的stdout代理，每个线程写入自己的buffer"""
    def write(self, s):
        buf = getattr(_thread_local, 'buf', None)
        if buf is not None:
            buf.write(s)
        else:
            _real_stdout.write(s)
    def flush(self):
        pass


def _capture_block(fn, coin_id):
    """在当前线程中捕获一个block的print输出"""
    _thread_local.buf = StringIO()
    try:
        fn(coin_id)
    except Exception as e:
        _thread_local.buf.write(f'⚠️ {type(e).__name__}: {e}\n')
    result = _thread_local.buf.getvalue()
    _thread_local.buf = None
    return result


def _run_serial(blocks, coin_id, delay=0):
    """串行执行blocks，带间隔"""
    parts = []
    for i, name in enumerate(blocks):
        if name in BLOCKS:
            parts.append(f'\n{"="*60}\n')
            parts.append(_capture_block(BLOCKS[name], coin_id))
            if delay and i < len(blocks) - 1:
                time.sleep(delay)
    return ''.join(parts)


def _run_parallel(blocks, coin_id):
    """并行执行blocks"""
    outputs = {}
    def _one(name):
        return _capture_block(BLOCKS[name], coin_id)

    with ThreadPoolExecutor(max_workers=len(blocks)) as pool:
        futures = {pool.submit(_one, name): name for name in blocks}
        for future in as_completed(futures):
            outputs[futures[future]] = future.result()
    return ''.join(f'\n{"="*60}\n' + outputs.get(n, '') for n in blocks)


def main():
    if len(sys.argv) < 2:
        _real_stdout.write(f'用法: python3 {sys.argv[0]} <coin_id> [blocks]\n')
        _real_stdout.write(f'blocks: {",".join(BLOCKS.keys())} | all\n')
        return
    coin_id = sys.argv[1].lower()
    blocks_arg = sys.argv[2] if len(sys.argv) > 2 else 'all'
    if blocks_arg == 'all':
        run_blocks = list(BLOCKS.keys())
    else:
        run_blocks = [b.strip() for b in blocks_arg.split(',')]

    # 安装线程安全的stdout代理
    sys.stdout = _ThreadPrinter()

    # 过滤出实际要运行的blocks，按数据源分组
    groups_to_run = {}
    for group_name, group_blocks in SOURCE_GROUPS.items():
        active = [b for b in group_blocks if b in run_blocks]
        if active:
            groups_to_run[group_name] = active

    # 各组并行执行
    group_outputs = {}

    def _execute_group(group_name, blocks):
        if group_name == 'binance':
            return _run_parallel(blocks, coin_id)
        elif group_name == 'yahoo':
            return _run_serial(blocks, coin_id, delay=0)
        else:
            return _run_parallel(blocks, coin_id)

    with ThreadPoolExecutor(max_workers=len(groups_to_run)) as pool:
        futures = {
            pool.submit(_execute_group, gn, gb): gn
            for gn, gb in groups_to_run.items()
        }
        for future in as_completed(futures):
            gn = futures[future]
            try:
                group_outputs[gn] = future.result()
            except Exception as e:
                group_outputs[gn] = f'⚠️ {gn}组错误: {e}\n'

    # 恢复stdout，按block原始顺序输出
    sys.stdout = _real_stdout
    printed_groups = set()
    for name in run_blocks:
        for gn, gb in groups_to_run.items():
            if name in gb and gn not in printed_groups:
                print(group_outputs.get(gn, ''), end='')
                printed_groups.add(gn)
                break

if __name__ == '__main__':
    main()
