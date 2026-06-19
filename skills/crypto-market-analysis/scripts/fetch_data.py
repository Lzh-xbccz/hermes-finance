#!/usr/bin/env python3
"""加密货币八维分析数据采集脚本。用法: python3 fetch_data.py <coin_id> [blocks]
blocks: all | price | klines | chain | contracts | sentiment | macro | news | exchanges | options
多个block用逗号分隔，如: python3 fetch_data.py bitcoin price,contracts,macro

并发策略：
- Binance组: 全并行（1200 req/min限制远超用量）
- Yahoo组: 串行+0.4s间隔（避免429）
- CoinGecko组: 串行+2s间隔（免费版10-30 req/min）
- 其他组(Deribit/alternative.me/blockchain.info): 全并行
- 组与组之间并行执行
"""
import json, sys, time, urllib.parse, urllib.request
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed
from io import StringIO
import threading
import xml.etree.ElementTree as ET

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


def _curl_fetch(url, timeout=10):
    """urllib SSL 不兼容时降级到 curl subprocess。"""
    import subprocess as _sp
    try:
        r = _sp.run(['curl', '-s', '--connect-timeout', str(timeout), url],
                    capture_output=True, text=True, timeout=timeout + 5)
        if r.returncode == 0 and r.stdout.strip():
            return json.loads(r.stdout)
    except Exception:
        pass
    raise OSError('curl fallback failed')


def fetch(url, timeout=10):
    req = urllib.request.Request(_bust_cache(url), headers=UA)
    try:
        return json.load(urllib.request.urlopen(req, timeout=timeout))
    except (urllib.request.URLError, OSError):
        return _curl_fetch(url, timeout=timeout)


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


def fetch_text(url, timeout=10):
    req = urllib.request.Request(_bust_cache(url), headers=UA)
    try:
        return urllib.request.urlopen(req, timeout=timeout).read().decode('utf-8', 'ignore')
    except (urllib.request.URLError, OSError):
        import subprocess as _sp
        r = _sp.run(['curl', '-s', '--connect-timeout', str(timeout), url],
                    capture_output=True, text=True, timeout=timeout + 5)
        if r.returncode == 0:
            return r.stdout
        raise OSError('curl fallback failed')


def safe_fetch_text(url, label="", timeout=10):
    try:
        return fetch_text(url, timeout)
    except Exception as e:
        print(f'⚠️ {label or url}: {type(e).__name__} {e}')
        return ''

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
        arch = _crypto_market_architecture(rows)
        print(
            '4H市场架构: '
            f'{arch["kind"]} | {arch["position"]} | '
            f'下轨/支撑 ${_fmt_level(arch["lower"])} | 上轨/阻力 ${_fmt_level(arch["upper"])} | '
            f'倾向 {arch["stance"]}'
        )
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


# ─── 块4.5: 新闻/事件面 ───
def fetch_crypto_news(coin_id, limit=8):
    base = COIN_SYMBOL_ALIASES.get(coin_id.lower(), coin_id.upper())
    query = f'{base} bitcoin ETF OR crypto regulation OR exchange hack OR institutional inflow when:7d'
    url = 'https://news.google.com/rss/search?q=' + urllib.parse.quote(query) + '&hl=en-US&gl=US&ceid=US:en'
    text = safe_fetch_text(url, 'Google News')
    if not text:
        return []
    try:
        root = ET.fromstring(text)
    except ET.ParseError:
        return []
    out = []
    for item in root.findall('./channel/item')[:limit]:
        out.append({
            'title': item.findtext('title', '').strip(),
            'source': item.findtext('source', '').strip(),
            'pubDate': item.findtext('pubDate', '').strip(),
        })
    return out


def _news_signal(title):
    text = title.lower()
    bullish = [
        'etf inflow',
        'etfs inflow',
        'record inflow',
        'spot bitcoin etf inflows',
        'buys bitcoin',
        'adds bitcoin',
        'bitcoin treasury',
        'approval',
        'approved',
        'reserve',
        'institutional demand',
        'rate cut',
    ]
    bearish = [
        'etf outflow',
        'etfs outflow',
        'record outflow',
        'spot bitcoin etf outflows',
        'sells bitcoin',
        'sold bitcoin',
        'lawsuit',
        'probe',
        'sec charges',
        'hack',
        'exploit',
        'ban',
        'crackdown',
        'liquidation',
        'rate hike',
    ]
    has_bullish = any(token in text for token in bullish)
    has_bearish = any(token in text for token in bearish)
    if has_bullish and not has_bearish:
        return '做多'
    if has_bearish and not has_bullish:
        return '做空'
    if has_bullish and has_bearish:
        return 'neutral'
    return None


def classify_crypto_news(news):
    out = {'events': news[:8], 'bullish': [], 'bearish': [], 'neutral': []}
    for item in news[:8]:
        signal = _news_signal(item.get('title', ''))
        if signal == '做多':
            out['bullish'].append(item)
        elif signal == '做空':
            out['bearish'].append(item)
        elif signal == 'neutral':
            out['neutral'].append(item)
    return out


def block_news(coin_id):
    print('=== 新闻/事件面 ===')
    classified = classify_crypto_news(fetch_crypto_news(coin_id))
    events = classified['events']
    if not events:
        print('新闻源暂缺，事件面不参与定向')
        return
    for item in events:
        signal = _news_signal(item.get('title', ''))
        tag = '🟢' if signal == '做多' else '🔴' if signal == '做空' else '⚪'
        print(f'{tag} {item.get("title", "")} | {item.get("source", "")}')
    print(
        f"事件归类: 偏多 {len(classified['bullish'])} / "
        f"偏空 {len(classified['bearish'])} / 中性 {len(classified['neutral'])}"
    )

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


# ─── 块6: 独立维度方向门槛 ───
def _to_float(value, default=None):
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _row_value(row, key, alt=None):
    if isinstance(row, dict):
        value = row.get(key)
        if value is None and alt is not None:
            value = row.get(alt)
        return _to_float(value)
    return None


def _close(row):
    return _row_value(row, 'close', 'c')


def _high(row):
    return _row_value(row, 'high', 'h')


def _low(row):
    return _row_value(row, 'low', 'l')


def _open(row):
    return _row_value(row, 'open', 'o')


def _volume(row):
    return _row_value(row, 'volume', 'v') or 0.0


def _normalize_kline_rows(rows):
    out = []
    for row in rows or []:
        if isinstance(row, dict):
            out.append(row)
        elif isinstance(row, list) and len(row) >= 6:
            out.append({
                'ts': row[0],
                'open': _to_float(row[1]),
                'high': _to_float(row[2]),
                'low': _to_float(row[3]),
                'close': _to_float(row[4]),
                'volume': _to_float(row[5], 0.0),
            })
    return [r for r in out if None not in {_open(r), _high(r), _low(r), _close(r)}]


def _crypto_pattern(rows):
    rows = _normalize_kline_rows(rows)
    if len(rows) < 12:
        return '数据不足'
    closes = [_close(r) for r in rows]
    highs = [_high(r) for r in rows]
    lows = [_low(r) for r in rows]
    chg = (closes[-1] / closes[0] - 1) * 100 if closes[0] else 0
    recent = (closes[-1] / closes[-6] - 1) * 100 if closes[-6] else 0
    width = (max(highs) - min(lows)) / min(lows) * 100 if min(lows) else 0
    if abs(chg) < 5 and width < 14:
        return '箱体洗盘'
    if chg > 8 and recent > 1:
        return '趋势推进'
    if chg > 8 and recent < 0:
        return '冲高派发'
    if closes[-1] > min(lows[-6:]) * 1.02 and min(lows[-3:]) <= min(lows[-6:]) * 1.003:
        return '跌破回收'
    return '阴跌磨人'


def _crypto_swings(rows, radius=2):
    highs, lows = [], []
    for i in range(radius, len(rows) - radius):
        high = _high(rows[i])
        low = _low(rows[i])
        if all(high > _high(rows[i + d]) for d in range(-radius, radius + 1) if d != 0):
            highs.append({'idx': i, 'price': high, 'row': rows[i]})
        if all(low < _low(rows[i + d]) for d in range(-radius, radius + 1) if d != 0):
            lows.append({'idx': i, 'price': low, 'row': rows[i]})
    return {'highs': highs, 'lows': lows}


def _swing_slope_pct(points):
    if len(points) < 2:
        return 0.0
    first, last = points[0], points[-1]
    base = first['price'] or 1.0
    return (last['price'] / base - 1) * 100


def _project_line(points, target_idx):
    if len(points) < 2:
        return points[-1]['price'] if points else None
    first, last = points[0], points[-1]
    idx_delta = last['idx'] - first['idx']
    if idx_delta == 0:
        return last['price']
    slope = (last['price'] - first['price']) / idx_delta
    return last['price'] + slope * (target_idx - last['idx'])


def _architecture_line(points, start_idx, end_idx, fallback):
    fallback = float(fallback or 0.0)
    if len(points) >= 2:
        start_price = _project_line(points, start_idx)
        end_price = _project_line(points, end_idx)
        anchors = [{'idx': int(p['idx']), 'price': float(p['price'])} for p in points]
    else:
        start_price = fallback
        end_price = fallback
        anchors = []
    return {
        'points': [
            {'idx': int(start_idx), 'price': float(start_price if start_price is not None else fallback)},
            {'idx': int(end_idx), 'price': float(end_price if end_price is not None else fallback)},
        ],
        'anchors': anchors,
    }


def _architecture_kind(high_slope, low_slope, width_pct, threshold=1.0):
    high_up = high_slope > threshold
    high_down = high_slope < -threshold
    low_up = low_slope > threshold
    low_down = low_slope < -threshold
    if high_up and low_up:
        return '上升通道'
    if high_down and low_down:
        return '下降通道'
    if high_down and low_up:
        return '收敛三角/楔形'
    if high_up and low_down:
        return '扩散震荡'
    return '箱体结构' if width_pct < 18 else '宽幅震荡'


def _candidate_width_pct(rows, start_idx, end_idx):
    segment = rows[max(0, int(start_idx)):int(end_idx) + 1]
    if not segment:
        return 0.0
    high = max(_high(r) for r in segment)
    low = min(_low(r) for r in segment)
    return (high - low) / max(low, 0.01) * 100


def _architecture_candidate(rows, highs, lows, end_idx, current, threshold=1.0):
    if len(highs) < 2 or len(lows) < 2:
        return None
    start_idx = min(highs[0]['idx'], lows[0]['idx'])
    high_slope = _swing_slope_pct(highs)
    low_slope = _swing_slope_pct(lows)
    width_pct = _candidate_width_pct(rows, start_idx, end_idx)
    kind = _architecture_kind(high_slope, low_slope, width_pct, threshold)
    upper = _project_line(highs, end_idx)
    lower = _project_line(lows, end_idx)
    if upper is None or lower is None:
        return None
    upper = float(upper)
    lower = float(lower)
    span = max(abs(upper - lower), current * 0.005, 0.01)
    low_level, high_level = sorted((lower, upper))
    ratio = (current - low_level) / span
    outside = max(0.0, -ratio, ratio - 1.0)
    last_anchor_idx = max(highs[-1]['idx'], lows[-1]['idx'])
    duration = max(1, last_anchor_idx - start_idx)
    freshness = max(0, end_idx - last_anchor_idx)
    count = min(len(highs), len(lows))
    kind_bonus = {
        '上升通道': 8.0,
        '下降通道': 8.0,
        '收敛三角/楔形': 4.0,
        '扩散震荡': 2.0,
    }.get(kind, -4.0)
    parallel_penalty = 0.0
    if kind in {'上升通道', '下降通道'}:
        parallel_penalty = abs(abs(high_slope) - abs(low_slope)) * 0.15
    score = (
        duration * 0.9
        + count * 4.0
        + min(abs(high_slope) + abs(low_slope), 60.0) * 0.35
        + kind_bonus
        - freshness * 0.25
        - outside * 60.0
        - parallel_penalty
    )
    return {
        'kind': kind,
        'highs': highs,
        'lows': lows,
        'high_slope': high_slope,
        'low_slope': low_slope,
        'upper': upper,
        'lower': lower,
        'start_idx': start_idx,
        'last_anchor_idx': last_anchor_idx,
        'count': count,
        'score': score,
        'ratio': ratio,
    }


def _select_architecture_candidate(rows, swings, end_idx, current, threshold=1.0):
    min_idx = max(0, end_idx - 96)
    all_highs = [p for p in swings['highs'] if p['idx'] >= min_idx]
    all_lows = [p for p in swings['lows'] if p['idx'] >= min_idx]
    max_count = min(12, len(all_highs), len(all_lows))
    if max_count < 2:
        return None, None
    min_count = 4 if max_count >= 4 else 2
    candidates = []
    for count in range(min_count, max_count + 1):
        cand = _architecture_candidate(
            rows,
            all_highs[-count:],
            all_lows[-count:],
            end_idx,
            current,
            threshold,
        )
        if cand:
            candidates.append(cand)
    if not candidates:
        return None, None
    selected = max(candidates, key=lambda x: (x['score'], x['count'], x['last_anchor_idx']))
    recent = None
    if max_count >= 4:
        recent = _architecture_candidate(
            rows,
            all_highs[-4:],
            all_lows[-4:],
            end_idx,
            current,
            threshold,
        )
    return selected, recent


def _crypto_market_architecture(rows):
    rows = _normalize_kline_rows(rows)
    if len(rows) < 20:
        return {
            'kind': '数据不足',
            'stance': '中性',
            'position': '结构不足',
            'lower': 0.0,
            'upper': 0.0,
            'mid': 0.0,
            'break_buffer': 0.0,
            'upper_breakout': 0.0,
            'lower_breakdown': 0.0,
            'upper_line': {'points': [], 'anchors': []},
            'lower_line': {'points': [], 'anchors': []},
            'logic': [{'step': '数据检查', 'detail': '4H K线少于20根，不能确认市场架构'}],
            'reason': '市场架构=数据不足',
        }

    current = _close(rows[-1])
    recent = rows[-60:] if len(rows) >= 60 else rows
    start_idx = len(rows) - len(recent)
    end_idx = len(rows) - 1
    recent_high = max(_high(r) for r in recent)
    recent_low = min(_low(r) for r in recent)
    swings = _crypto_swings(rows)
    threshold = 1.0
    selected, recent_probe = _select_architecture_candidate(rows, swings, end_idx, current, threshold)

    if selected:
        highs = selected['highs']
        lows = selected['lows']
        high_slope = selected['high_slope']
        low_slope = selected['low_slope']
        kind = selected['kind']
        upper = selected['upper']
        lower = selected['lower']
        upper_line = _architecture_line(highs, highs[0]['idx'], end_idx, upper)
        lower_line = _architecture_line(lows, lows[0]['idx'], end_idx, lower)
        start_idx = selected['start_idx']
    else:
        highs = swings['highs'][-4:]
        lows = swings['lows'][-4:]
        high_slope = _swing_slope_pct(highs)
        low_slope = _swing_slope_pct(lows)
        width_pct = (recent_high - recent_low) / max(recent_low, 0.01) * 100
        kind = '箱体结构' if width_pct < 18 else '结构待确认'
        upper = recent_high
        lower = recent_low
        upper_line = _architecture_line([], start_idx, end_idx, upper)
        lower_line = _architecture_line([], start_idx, end_idx, lower)

    if lower > upper:
        lower, upper = upper, lower
        lower_line, upper_line = upper_line, lower_line

    span = max(upper - lower, current * 0.005, 0.01)
    break_buffer = max(current * 0.006, span * 0.08)
    mid = lower + span * 0.5
    upper_breakout = upper + break_buffer
    lower_breakdown = lower - break_buffer
    if current > upper + break_buffer:
        position = '上破上轨'
        stance = '做多'
    elif current < lower - break_buffer:
        position = '下破下轨'
        stance = '做空'
    else:
        ratio = (current - lower) / span
        if ratio >= 0.75:
            zone = '靠近上轨'
        elif ratio <= 0.25:
            zone = '靠近下轨'
        else:
            zone = '中轨附近'
        position = f'通道内{zone}'
        if kind == '上升通道' and current >= mid:
            stance = '做多'
        elif kind == '下降通道' and current <= mid:
            stance = '做空'
        else:
            stance = '中性'

    reason = f'市场架构={kind}，{position}，下轨/支撑 {_fmt_level(lower)}，上轨/阻力 {_fmt_level(upper)}'
    logic = [
        {'step': '取样', 'detail': f'最近{len(recent)}根4H K线，选中摆高{len(highs)}个、摆低{len(lows)}个作为主结构'},
        {'step': '斜率', 'detail': f'摆高斜率{high_slope:+.2f}%，摆低斜率{low_slope:+.2f}%'},
        {'step': '分类', 'detail': kind},
        {'step': '轨道', 'detail': f'下轨/支撑 {_fmt_level(lower)}，中轨 {_fmt_level(mid)}，上轨/阻力 {_fmt_level(upper)}'},
        {'step': '触发', 'detail': f'上破 {_fmt_level(upper_breakout)} / 下破 {_fmt_level(lower_breakdown)}'},
    ]
    if selected:
        logic.insert(1, {'step': '起点', 'detail': f'结构线从第{start_idx}根K线附近的有效摆点开始，不向更早窗口反推'})
    if selected and recent_probe and recent_probe['kind'] != kind:
        logic.insert(
            3,
            {
                'step': '短线扰动',
                'detail': f'最近4组摆点={recent_probe["kind"]}，作为主结构内的回调/反弹处理',
            },
        )
    return {
        'kind': kind,
        'stance': stance,
        'position': position,
        'lower': float(lower),
        'upper': float(upper),
        'mid': float(mid),
        'break_buffer': float(break_buffer),
        'upper_breakout': float(upper_breakout),
        'lower_breakdown': float(lower_breakdown),
        'upper_line': upper_line,
        'lower_line': lower_line,
        'high_slope_pct': high_slope,
        'low_slope_pct': low_slope,
        'structure_start_idx': int(start_idx),
        'logic': logic,
        'reason': reason,
    }


def _fmt_level(value):
    value = float(value)
    if abs(value) >= 1000:
        return f'{value:,.0f}'
    if abs(value) >= 10:
        return f'{value:,.2f}'
    return f'{value:,.4f}'


def _crypto_price_bias(daily, h4):
    daily = _normalize_kline_rows(daily)
    h4 = _normalize_kline_rows(h4)
    if len(daily) < 20 or len(h4) < 8:
        return '观望'
    daily_up = _close(daily[-1]) > _close(daily[-20])
    daily_down = _close(daily[-1]) < _close(daily[-20])
    hl = _low(h4[-1]) > _low(h4[-3])
    lh = _high(h4[-1]) < _high(h4[-3])
    if daily_up and hl:
        return '做多'
    if daily_down and lh:
        return '做空'
    return '观望'


def _crypto_dimension(reason):
    if reason.startswith(('新闻/事件', 'ETF/监管/机构')):
        return '新闻/事件基本面'
    if reason.startswith('技术结构') or reason.startswith('市场架构') or '4H主导手法' in reason:
        return '技术结构'
    if reason.startswith(('合约', 'OI', '资金费率', '多空比')):
        return '合约结构'
    if reason.startswith(('VIX', 'DXY', 'SPY', 'BTC 5日', '宏观')):
        return '宏观/风险偏好'
    if reason.startswith(('恐惧贪婪', 'FNG')):
        return '情绪反指'
    if reason.startswith('交易所'):
        return '交易所交叉验证'
    if reason.startswith('期权'):
        return '期权结构'
    if reason.startswith('链上'):
        return '链上/基本面'
    return '其他'


def _dimensionize_votes(votes, classifier):
    buckets = {}
    for side in ('做多', '做空'):
        for reason in votes.get(side, []):
            bucket = classifier(reason)
            buckets.setdefault(bucket, {'做多': [], '做空': []})[side].append(reason)

    collapsed = {
        '做多': [],
        '做空': [],
        'neutral': list(votes.get('neutral', [])),
        'veto': list(votes.get('veto', [])),
        'veto_long': list(votes.get('veto_long', [])),
        'veto_short': list(votes.get('veto_short', [])),
        'missing': list(votes.get('missing', [])),
        'dimensions': {},
    }
    for name, sides in buckets.items():
        long_reasons = sides['做多']
        short_reasons = sides['做空']
        if long_reasons and not short_reasons:
            collapsed['做多'].append(f"{name}: {'；'.join(long_reasons)}")
            collapsed['dimensions'][name] = {'stance': '做多', 'reasons': long_reasons}
        elif short_reasons and not long_reasons:
            collapsed['做空'].append(f"{name}: {'；'.join(short_reasons)}")
            collapsed['dimensions'][name] = {'stance': '做空', 'reasons': short_reasons}
        else:
            reason = '多空内部冲突：多(' + '；'.join(long_reasons) + ') / 空(' + '；'.join(short_reasons) + ')'
            collapsed['neutral'].append(f'{name}: {reason}')
            collapsed['dimensions'][name] = {'stance': '中性', 'reasons': long_reasons + short_reasons}
    return collapsed


def _contract_votes(data, votes):
    contracts = data.get('contracts') or {}
    if not contracts:
        votes['missing'].append('合约结构')
        return
    price_chg = _to_float(contracts.get('price_change_pct_24h'))
    oi_chg = _to_float(contracts.get('oi_60m_change_pct'))
    funding = _to_float(contracts.get('latest_funding_rate'))
    ls_ratio = _to_float(contracts.get('latest_long_short_ratio'))

    if price_chg is not None and oi_chg is not None:
        if price_chg > 1.0 and oi_chg > 0.3:
            votes['做多'].append(f'合约增仓上涨 price={price_chg:+.2f}% OI={oi_chg:+.2f}%')
        elif price_chg < -1.0 and oi_chg > 0.3:
            votes['做空'].append(f'合约增仓下跌 price={price_chg:+.2f}% OI={oi_chg:+.2f}%')
        elif abs(oi_chg) <= 0.3:
            votes['neutral'].append(f'OI横盘 {oi_chg:+.2f}%')
        else:
            votes['neutral'].append(f'OI与价格未形成趋势确认 price={price_chg:+.2f}% OI={oi_chg:+.2f}%')

    if funding is not None:
        if funding >= 0.0003:
            votes['veto_long'].append(f'资金费率 {funding * 100:+.4f}% 多头拥挤，禁止追多')
        elif funding <= -0.0003:
            votes['veto_short'].append(f'资金费率 {funding * 100:+.4f}% 空头拥挤，禁止追空')
        elif funding > 0.00008:
            votes['neutral'].append(f'资金费率偏正 {funding * 100:+.4f}%')
        elif funding < -0.00008:
            votes['neutral'].append(f'资金费率偏负 {funding * 100:+.4f}%')

    if ls_ratio is not None:
        if ls_ratio >= 2.5:
            votes['veto_long'].append(f'多空比 {ls_ratio:.2f} 多头极端，禁止追多')
        elif ls_ratio <= 0.7:
            votes['veto_short'].append(f'多空比 {ls_ratio:.2f} 空头极端，禁止追空')
        elif 1.2 <= ls_ratio <= 1.8:
            votes['做多'].append(f'多空比 {ls_ratio:.2f} 温和偏多')
        elif 0.8 <= ls_ratio <= 0.95:
            votes['做空'].append(f'多空比 {ls_ratio:.2f} 温和偏空')


def _macro_votes(data, votes):
    macro = data.get('macro') or {}
    if not macro:
        votes['missing'].append('宏观/风险偏好')
        return
    spy_5d = _to_float(macro.get('spy_5d_change_pct'))
    vix_price = _to_float(macro.get('vix_price'))
    dxy_chg = _to_float(macro.get('dxy_change_pct'))
    btc_5d = _to_float(macro.get('asset_5d_change_pct'))

    if spy_5d is not None:
        if spy_5d > 1:
            votes['做多'].append(f'SPY 5日 {spy_5d:+.2f}% 风险偏好修复')
        elif spy_5d < -1:
            votes['做空'].append(f'SPY 5日 {spy_5d:+.2f}% 风险偏好走弱')
    if vix_price is not None:
        if vix_price >= 25:
            votes['做空'].append(f'VIX={vix_price:.2f} 风险厌恶')
        elif vix_price <= 15:
            votes['做多'].append(f'VIX={vix_price:.2f} 波动率低位')
    if dxy_chg is not None:
        if dxy_chg > 0.5:
            votes['做空'].append(f'DXY走强 {dxy_chg:+.2f}% 压制风险资产')
        elif dxy_chg < -0.5:
            votes['做多'].append(f'DXY走弱 {dxy_chg:+.2f}% 支撑风险资产')
    if btc_5d is not None:
        if btc_5d > 3:
            votes['做多'].append(f'BTC 5日 {btc_5d:+.2f}% 内部风险偏好走强')
        elif btc_5d < -3:
            votes['做空'].append(f'BTC 5日 {btc_5d:+.2f}% 内部风险偏好走弱')


def _news_votes(data, votes):
    news = data.get('news') or {}
    bullish = news.get('bullish') or []
    bearish = news.get('bearish') or []
    if not news:
        votes['missing'].append('新闻/事件基本面')
        return
    if bullish and not bearish:
        votes['做多'].append('新闻/事件偏多：' + '；'.join(item.get('title', '') for item in bullish[:3]))
    elif bearish and not bullish:
        votes['做空'].append('新闻/事件偏空：' + '；'.join(item.get('title', '') for item in bearish[:3]))
    elif bullish and bearish:
        votes['neutral'].append(
            f"新闻/事件多空混合：偏多{len(bullish)}条 / 偏空{len(bearish)}条"
        )
    else:
        votes['neutral'].append('新闻/事件未发现明确 ETF/监管/机构方向信号')


def directional_evidence(data):
    votes = {
        '做多': [],
        '做空': [],
        'neutral': [],
        'veto': [],
        'veto_long': [],
        'veto_short': [],
        'missing': [],
    }

    daily = data.get('daily') or data.get('daily_90d') or []
    h4 = data.get('h4') or data.get('agg_4h_30d') or data.get('agg_4h_10d') or []
    daily_rows = _normalize_kline_rows(daily)
    h4_rows = _normalize_kline_rows(h4)
    if len(daily_rows) < 20 or len(h4_rows) < 8:
        votes['missing'].append('技术结构')
    else:
        tech = _crypto_price_bias(daily_rows, h4_rows)
        if tech in {'做多', '做空'}:
            votes[tech].append(f'技术结构={tech}')
        else:
            votes['neutral'].append('技术结构=震荡/无方向优势')

    pattern = _crypto_pattern(h4_rows)
    if pattern == '趋势推进':
        votes['做多'].append('4H主导手法=趋势推进')
    elif pattern in {'冲高派发', '阴跌磨人'}:
        votes['做空'].append(f'4H主导手法={pattern}')
    elif pattern in {'箱体洗盘', '跌破回收'}:
        votes['neutral'].append(f'4H主导手法={pattern}')

    arch = _crypto_market_architecture(h4_rows)
    if arch['stance'] in {'做多', '做空'}:
        votes[arch['stance']].append(arch['reason'])
    elif arch['kind'] != '数据不足':
        votes['neutral'].append(arch['reason'])

    _contract_votes(data, votes)
    _news_votes(data, votes)
    _macro_votes(data, votes)

    sentiment = data.get('sentiment') or {}
    fng = _to_float(sentiment.get('fear_greed'))
    if fng is not None:
        if fng >= 80:
            votes['veto_long'].append(f'恐惧贪婪={fng:.0f} 极端贪婪，禁止追多')
        elif fng <= 20:
            votes['veto_short'].append(f'恐惧贪婪={fng:.0f} 极端恐惧，禁止追空')
        elif fng < 35:
            votes['做多'].append(f'恐惧贪婪={fng:.0f} 偏恐惧，反指偏多')
        elif fng > 65:
            votes['做空'].append(f'恐惧贪婪={fng:.0f} 偏贪婪，反指偏空')
    else:
        votes['missing'].append('情绪反指')

    exchanges = data.get('exchanges') or {}
    spread = _to_float(exchanges.get('spread_pct'))
    if spread is not None:
        if spread >= 0.2:
            votes['veto'].append(f'交易所价差 {spread:.3f}% 偏离过大，禁止硬给方向')
        else:
            votes['neutral'].append(f'交易所价差 {spread:.3f}% 正常')

    options = data.get('options') or {}
    pcr = _to_float(options.get('put_call_ratio'))
    if pcr is not None:
        if pcr > 1.2:
            votes['做空'].append(f'期权 Put/Call={pcr:.2f} 看跌需求占优')
        elif pcr < 0.8:
            votes['做多'].append(f'期权 Put/Call={pcr:.2f} 看涨需求占优')
        else:
            votes['neutral'].append(f'期权 Put/Call={pcr:.2f} 中性')

    chain = data.get('chain') or {}
    avg_tx_btc = _to_float(chain.get('avg_tx_btc'))
    if avg_tx_btc is not None:
        if avg_tx_btc >= 5:
            votes['neutral'].append(f'链上大额转账活跃 avg={avg_tx_btc:.1f} BTC，需结合交易所流向')
        else:
            votes['neutral'].append(f'链上活跃度未见强方向 avg={avg_tx_btc:.1f} BTC')

    return _dimensionize_votes(votes, _crypto_dimension)


def direction_from_evidence(votes):
    if votes.get('veto'):
        return '观望'
    missing_core = {'技术结构', '合约结构'} & set(votes.get('missing', []))
    if missing_core:
        return '观望'
    long_count = len(votes['做多'])
    short_count = len(votes['做空'])
    if long_count >= 3 and long_count - short_count >= 2 and not votes.get('veto_long'):
        return '做多'
    if short_count >= 3 and short_count - long_count >= 2 and not votes.get('veto_short'):
        return '做空'
    return '观望'


def direction_quality_text(votes):
    return (
        f"多头独立维度 {len(votes['做多'])} 项：{'; '.join(votes['做多']) or '无'}；"
        f"空头独立维度 {len(votes['做空'])} 项：{'; '.join(votes['做空']) or '无'}；"
        f"中性/缺失：{'; '.join(votes['neutral'] + votes.get('missing', [])) or '无'}；"
        f"硬性降级：{'; '.join(votes['veto']) or '无'}；"
        f"禁止追多：{'; '.join(votes.get('veto_long', [])) or '无'}；"
        f"禁止追空：{'; '.join(votes.get('veto_short', [])) or '无'}"
    )


def counter_audit_text(final_direction, votes):
    long_count = len(votes['做多'])
    short_count = len(votes['做空'])
    if votes.get('veto'):
        return '存在硬性降级项，最终观望'
    if {'技术结构', '合约结构'} & set(votes.get('missing', [])):
        return '核心维度缺失，最终观望'
    if final_direction == '观望' and votes.get('veto_long') and long_count > short_count:
        return '多头证据虽占优，但合约/情绪存在禁止追多项，最终观望'
    if final_direction == '观望' and votes.get('veto_short') and short_count > long_count:
        return '空头证据虽占优，但合约/情绪存在禁止追空项，最终观望'
    if final_direction == '做多':
        return '最强空头证据：' + ('；'.join(votes['做空']) if votes['做空'] else '无同等级反证')
    if final_direction == '做空':
        return '最强多头证据：' + ('；'.join(votes['做多']) if votes['做多'] else '无同等级反证')
    if long_count == short_count:
        return '多空维度数量相同，方向质量不足，最终观望'
    if abs(long_count - short_count) < 2:
        return '多空维度差距小于 2 项，未通过方向质量门槛，最终观望'
    return '同向维度少于 3 项，未形成可执行方向优势，最终观望'


def _optional_fetch(url, timeout=10):
    try:
        return fetch(url, timeout)
    except Exception:
        return None


def _latest_funding_rate(rows):
    if not rows:
        return None
    latest = sorted(rows, key=lambda x: x.get('fundingTime', 0))[-1]
    return _to_float(latest.get('fundingRate'))


def _latest_long_short_ratio(rows):
    if not rows:
        return None
    latest = sorted(rows, key=lambda x: x.get('timestamp', 0))[-1]
    return _to_float(latest.get('longShortRatio'))


def _oi_change(rows):
    if not rows or len(rows) < 2:
        return None
    vals = [_to_float(x.get('sumOpenInterest')) for x in rows]
    vals = [x for x in vals if x is not None]
    if len(vals) < 2 or vals[0] == 0:
        return None
    return (vals[-1] / vals[0] - 1) * 100


def _yf_snapshot(ticker):
    import urllib.parse
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{urllib.parse.quote(ticker)}?interval=1d&range=5d"
    d = _optional_fetch(url)
    try:
        meta = d['chart']['result'][0]['meta']
        price = _to_float(meta.get('regularMarketPrice'))
        prev = _to_float(meta.get('chartPreviousClose'))
        return {
            'price': price,
            'change_pct': (price / prev - 1) * 100 if price is not None and prev else None,
        }
    except (TypeError, KeyError, IndexError, ZeroDivisionError):
        return {}


def _series_change(rows, close_index=4, lookback=5):
    if not rows or len(rows) < lookback:
        return None
    latest = _to_float(rows[-1][close_index] if isinstance(rows[-1], list) else _close(rows[-1]))
    prior = _to_float(rows[-lookback][close_index] if isinstance(rows[-lookback], list) else _close(rows[-lookback]))
    return (latest / prior - 1) * 100 if latest is not None and prior else None


def _exchange_spread(coin_id):
    symbol = market_symbol(coin_id)
    prices = []
    d = _optional_fetch(f'https://api.binance.com/api/v3/ticker/bookTicker?symbol={symbol}')
    if d:
        bid, ask = _to_float(d.get('bidPrice')), _to_float(d.get('askPrice'))
        if bid and ask:
            prices.append((bid + ask) / 2)
    d = _optional_fetch(f'https://api.bybit.com/v5/market/tickers?category=spot&symbol={symbol}')
    if d and d.get('retCode') == 0 and d.get('result', {}).get('list'):
        price = _to_float(d['result']['list'][0].get('lastPrice'))
        if price:
            prices.append(price)
    d = _optional_fetch(f'https://www.okx.com/api/v5/market/ticker?instId={okx_inst_id(coin_id)}')
    if d and d.get('code') == '0' and d.get('data'):
        price = _to_float(d['data'][0].get('last'))
        if price:
            prices.append(price)
    if len(prices) < 2 or min(prices) == 0:
        return None
    return (max(prices) - min(prices)) / min(prices) * 100


def _option_put_call_ratio(coin_id):
    if coin_id not in ('bitcoin', 'btc'):
        return None
    d = _optional_fetch('https://www.deribit.com/api/v2/public/get_book_summary_by_currency?currency=BTC&kind=option')
    try:
        put_vol = sum(_to_float(x.get('volume_usd'), 0) for x in d['result'] if x['instrument_name'].endswith('-P'))
        call_vol = sum(_to_float(x.get('volume_usd'), 0) for x in d['result'] if x['instrument_name'].endswith('-C'))
        return put_vol / call_vol if call_vol > 0 else None
    except (TypeError, KeyError):
        return None


def collect_direction_snapshot(coin_id):
    symbol = market_symbol(coin_id)
    daily = _optional_fetch(f'https://api.binance.com/api/v3/klines?symbol={symbol}&interval=1d&limit=90') or []
    h4 = _optional_fetch(f'https://api.binance.com/api/v3/klines?symbol={symbol}&interval=4h&limit=180') or []
    ticker = _optional_fetch(f'https://fapi.binance.com/fapi/v1/ticker/24hr?symbol={symbol}') or {}
    funding = _optional_fetch(f'https://fapi.binance.com/fapi/v1/fundingRate?symbol={symbol}&limit=5') or []
    ls_ratio = _optional_fetch(f'https://fapi.binance.com/futures/data/topLongShortAccountRatio?symbol={symbol}&period=5m&limit=5') or []
    oi_hist = _optional_fetch(f'https://fapi.binance.com/futures/data/openInterestHist?symbol={symbol}&period=5m&limit=12') or []

    asset_5d = _series_change(daily, lookback=5)
    spy_raw = _optional_fetch('https://query1.finance.yahoo.com/v8/finance/chart/SPY?interval=1d&range=5d')
    try:
        spy_rows = [x for x in spy_raw['chart']['result'][0]['indicators']['quote'][0]['close'] if x is not None]
        spy_5d = (spy_rows[-1] / spy_rows[-5] - 1) * 100 if len(spy_rows) >= 5 and spy_rows[-5] else None
    except (TypeError, KeyError, IndexError, ZeroDivisionError):
        spy_5d = None
    vix = _yf_snapshot('^VIX')
    time.sleep(0.4)
    dxy = _yf_snapshot('DX-Y.NYB')

    fng = _optional_fetch('https://api.alternative.me/fng/?limit=1') or {}
    try:
        fear_greed = _to_float(fng['data'][0]['value'])
    except (TypeError, KeyError, IndexError):
        fear_greed = None
    news = classify_crypto_news(fetch_crypto_news(coin_id))

    return {
        'symbol': symbol,
        'daily': _normalize_kline_rows(daily),
        'h4': _normalize_kline_rows(h4),
        'contracts': {
            'price_change_pct_24h': _to_float(ticker.get('priceChangePercent')),
            'latest_funding_rate': _latest_funding_rate(funding),
            'latest_long_short_ratio': _latest_long_short_ratio(ls_ratio),
            'oi_60m_change_pct': _oi_change(oi_hist),
        },
        'macro': {
            'asset_5d_change_pct': asset_5d,
            'spy_5d_change_pct': spy_5d,
            'vix_price': vix.get('price'),
            'dxy_change_pct': dxy.get('change_pct'),
        },
        'news': news,
        'sentiment': {'fear_greed': fear_greed},
        'exchanges': {'spread_pct': _exchange_spread(coin_id)},
        'options': {'put_call_ratio': _option_put_call_ratio(coin_id)},
    }


def block_direction_gate(coin_id):
    print('=== 方向质量门槛（独立维度） ===')
    data = collect_direction_snapshot(coin_id)
    votes = directional_evidence(data)
    direction = direction_from_evidence(votes)
    label = '🟢 做多' if direction == '做多' else '🔴 做空' if direction == '做空' else '⚪ 观望'
    print(f'最终方向建议: {label}')
    print(direction_quality_text(votes))
    print('反向审计: ' + counter_audit_text(direction, votes))
    if direction == '观望':
        print('执行结论: 当前不强行开仓，只给触发条件；CZSC 只能确认或降级，不能覆盖本门槛。')


# ─── 主入口 ───
BLOCKS = {
    'resolve': block_resolve, 'price': block_price, 'klines': block_klines,
    'chain': block_chain, 'contracts': block_contracts, 'exchanges': block_exchanges,
    'sentiment': block_sentiment, 'macro': block_macro, 'news': block_news,
    'direction': block_direction_gate, 'options': block_options,
}

# 按数据源分组（同源串行避免限流，异源并行加速）
SOURCE_GROUPS = {
    'binance': ['klines', 'contracts', 'price', 'exchanges'],  # 全并行，限制宽松
    'yahoo': ['news', 'macro', 'direction'],      # direction 内含新闻/Yahoo，串行避免限流
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
