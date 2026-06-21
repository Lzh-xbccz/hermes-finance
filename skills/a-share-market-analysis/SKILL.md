---
name: a-share-market-analysis
description: "中国A股八维行情分析：技术、资金、市场结构、情绪、宏观、板块轮动、Sequoia量化信号 + 第8维CZSC缠论确认；支持指数、个股、本地/国内节点降级。"
---

# 中国 A 股行情分析

> ⛔ 铁律：你不是在写行情播报，你是在做证据审计。每个方向判断必须回答"为什么"，并先做反向审计。允许使用"证据不足"、"方向未确认"、"观望"；禁止在证据冲突时硬给做多/做空。

> 🆕 v3.0 — 集成 [Sequoia-X](https://github.com/sngyai/Sequoia-X) 7策略量化选股引擎

## 量化选股（a_share_scanner.py）

基于 baostock 免费数据源，收盘后自动扫描全市场 5200+ 只 A 股：

```bash
# 首次：回填历史数据 (~12分钟)
python a_share_scanner.py --backfill

# 日常：增量更新 + 7策略扫描
python a_share_scanner.py

# 仅跑特定策略
python a_share_scanner.py --strategy turtle
```

| 策略 | 说明 |
|------|------|
| 海龟突破 | 20日新高 + 成交额过亿 + 防诱多阳线 |
| 均线放量 | 均线多头排列 + 放量突破 |
| 高窄旗形 | 强动量后极度收敛缩量 |
| 涨停洗盘 | 涨停后回踩确认 |
| 跌停反包 | 上升趋势中跌停后的反包 |
| RPS突破 | 欧奈尔相对强度突破 |
| 定增回补 | 定增破发后的回补机会 |

数据源：**baostock**（免费、无需注册、后复权）→ 本地 SQLite，彻底规避东方财富反爬。

---

## 八维分析框架

| # | 维度 | 核心关注 | 数据源 | 状态 |
|---|------|---------|--------|------|
| 1 | 📈 技术结构 | K线趋势、量价关系、支撑阻力、形态 | 新浪 API + 腾讯 K 线 | ✅ |
| 2 | 💰 资金面 | **北向资金**净流入/流出（A股独有） | 浏览器→东方财富网页 | 🐢 慢但可用 |
| 3 | 📊 市场结构 | 涨跌家数、涨停跌停统计 | 浏览器→东方财富网页 | 🐢 慢但可用 |
| 4 | 😱 情绪量能 | 成交量对比、风险偏好 | 新浪 API + 腾讯 K 线 | ✅ |
| 5 | 🌍 宏观政策 | 美股联动、人民币汇率、政策要闻 | Yahoo Finance + 新浪/腾讯 + Google News RSS | ✅ |
| 6 | 🔄 板块轮动 | 领涨/领跌板块、热点概念、龙头识别 | 东方财富板块流 + 雪球热股 | 🔴 海外严重受限 |
| 7 | 🧮 量化/Sequoia | 7策略扫描、RPS、突破/洗盘/反包信号 | baostock + SQLite | ✅ |
| 8 | 🧭 缠论结构 | CZSC 中枢、笔、背驰、买卖点候补 | 腾讯日线/个股K线 | 可用则跑 |

**强制输出规则**：
1. 先给 `各维度证据`，只基于第 1-7 维逐项列出每个维度的偏多/偏空/中性/缺失状态及理由。不要用投票计数或权重打分决定方向。
2. 必须做 `反向审计`：若资金、广度、板块或政策新闻与技术方向冲突，最终方向降为震荡或保守档。
3. 再给 `缠论确认`，说明 CZSC 是确认、冲突还是不足。
4. 最终方向由你基于各维度证据的逻辑强度综合判断后决定；A 股受 T+1、涨跌停、政策与板块轮动约束，CZSC 不能覆盖这些限制。
5. 使用 `python3 -m hermes_finance analyze a-share --stock <CODE>` 或 MCP `analyze_a_share`，默认会尽量用采集器 K 线跑 CZSC。

> ⚠️ **海外服务器实测结果（2026-05-04 更新）**：
> - ❌ 东方财富 API（push2/datacenter-web）：TLS 成功，nginx 返回 502（Geo-block）
> - ❌ 同花顺（10jqka.com.cn）：Nginx forbidden，封海外 IP
> - ❌ 新浪 hq.sinajs.cn（浏览器 fetch）：CORS + Forbidden；curl CLI 可用
> - ✅ 新浪财经首页（finance.sina.com.cn）：指数数据可 snapshot 提取
> - ✅ 腾讯 `fqkline` / `kline`：历史日 K + `market` 市场状态可直接返回（含休市/节假日提示）
> - ✅ 雪球（xueqiu.com）：海外可访问，三大指数+热股榜正常，板块排行 API 需登录
> - ✅ 东方财富网页（浏览器）：北向资金历史数据 + 板块持股流可提取，板块排行页 Canvas 渲染不可抓
> - ❌ DuckDuckGo 新闻搜索：已触发 bot challenge，不再适合作为主新闻源
> - ✅ Google News RSS：可直接解析，适合作为新闻主路径
> - 详见 `references/china-finance-apis.md`

### Playwright + Stealth 抓取（东方财富/同花顺等被封 API 的兜底）

当 curl API 被 Geo-block/WAF 拦截时，使用 Playwright 模拟浏览器抓取：

```bash
# 抓取东方财富北向资金页面
node /root/.hermes/scripts/crawl.mjs "https://data.eastmoney.com/hsgt/index.html" \
  --wait ".content-sepe" --extract ".content-sepe" --timeout 20000

# 抓取同花顺板块数据
node /root/.hermes/scripts/crawl.mjs "https://q.10jqka.com.cn/thshy/" \
  --wait "table" --extract "table" --timeout 20000
```

或 Python 统一入口：
```python
import sys; sys.path.insert(0, '/root/.hermes/scripts')
from smart_crawl import smart_crawl
content, method = smart_crawl("https://data.eastmoney.com/hsgt/index.html")
```

---


> **⛔ 禁止调用 mcp_yfinance 系列工具**：Yahoo Finance 频繁 429。所有数据通过 `scripts/a_share_fetch.py` 获取。模型不要额外调 `mcp_yfinance_get_historical_stock_prices` 等 MCP 工具。

## 执行铁律

### 1. 先判断市场状态，再看方向
- 报告开头必须标注**分析时间（UTC + 北京时间）**
- 必须先判断当前属于：`交易中 / 午间休市 / 收盘后 / 周末 / 法定节假日`
- 若指数快照时间戳落后于当前交易日，默认视为**非实时数据**

### 2. 先复盘最近 7-30 日主导手法
- 每次分析必须先回答最近更像：`趋势推进 / 箱体洗盘 / 冲高派发 / 跌破回收 / 阴跌磨人`
- 再判断今天看到的是：`延续 / 回踩 / 诱多 / 诱空 / 纯噪音`

### 3. 数据缺口必须降级处理
- 北向资金、涨跌家数、板块轮动三项里，只要缺两项，最终方向不得给强烈结论，只能 `偏多 / 偏空 / 震荡` 中的保守档。这是数据完整性约束，不是投票计数。
- 若历史 K 线、指数快照、市场状态三者之一缺失，直接标注「数据不足」
- 数据缺失时必须明确写出缺口，**绝不编造**

### 4. 新闻只认硬新闻
- 监管、交易所、央行、部委、官方公告、宏观数据 = A/B 类，可影响方向
- 评论稿、标题党、技术分析文章、ETF营销文 = C 类，只能当背景，不得主导结论

### 5. A 股是 T+1，禁止把它当加密日内盘
- 现价贴近关键阻力/支撑、盈亏比很差时，不追单
- A 股日内分析的实质是**次日预判**，必须在结论中标注 `T+1` 限制

## 覆盖标的

必有三大指数：
- 上证指数 (000001) — `sh000001`
- 深证成指 (399001) — `sz399001`
- 创业板指 (399006) — `sz399006`

可选（用户指定）：科创板 50、沪深 300、中证 500、个股。

---

## 一键分析流程

按顺序执行数据块，最后汇总输出完整报告。

### 块 0：前置检查 — 时间、市场状态、节假日 ⚠️ 必做

> 先确认现在是实时盘、午休、收盘后，还是法定节假日。A 股休市时，所有「实时」分析都必须自动降级成盘后/假期分析。

```bash
# 腾讯 K 线接口自带 market 状态，能直接看到 SH/SZ/CYB 是否开盘或休市
curl -s "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=sh000001,day,,,30,qfq" | python3 -c "
import json, sys
from datetime import datetime, timezone, timedelta

d = json.load(sys.stdin)['data']['sh000001']['qt']
market = d.get('market', [''])[0]
bjt = timezone(timedelta(hours=8))
print('分析时间 UTC :', datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M'))
print('分析时间 BJT :', datetime.now(bjt).strftime('%Y-%m-%d %H:%M'))
print()
print('=== 市场状态 ===')
for item in market.split('|'):
    if item.startswith(('SH_', 'SZ_', 'CYB_', 'NEWSH_', 'NEWSZ_')):
        print(item)
"
```

**执行规则：**
- `SH_close_劳动节休市`、`SZ_close_劳动节休市` 这类状态 = 节假日分析，不得写成实时盘判断
- `11:30-13:00` 北京时间 = 午间休市，不得误判为连续交易
- 若指数快照日期落后于今日，说明市场未开或仍在节假日

### 块 1：三大指数实时行情（新浪 API）

```bash
curl -s "https://hq.sinajs.cn/list=sh000001,sz399001,sz399006" \
  --compressed \
  -H "Referer: https://finance.sina.com.cn" \
  | iconv -f gbk -t utf-8 \
  | python3 -c "
import sys
for line in sys.stdin:
    line = line.strip()
    if not line or '=' not in line: continue
    data = line.split('=', 1)[1].strip('\"').split(',')
    if len(data) < 10: continue
    name = data[0]
    current = float(data[1])
    prev_close = float(data[2])
    open_p = float(data[3]) if data[3] else 0
    high = float(data[4])
    low = float(data[5])
    vol = float(data[8]) if data[8] else 0
    amount = float(data[9]) if data[9] else 0
    trade_date = data[30] if len(data) > 30 else ''
    trade_time = data[31] if len(data) > 31 else ''
    chg_pct = (current - prev_close) / prev_close * 100 if prev_close else 0
    color = '🔴' if chg_pct < 0 else '🟢'
    print(f'{color} {name}: {current:,.2f} ({chg_pct:+.2f}%)')
    print(f'   今开:{open_p:,.2f} 最高:{high:,.2f} 最低:{low:,.2f} 昨收:{prev_close:,.2f}')
    print(f'   成交量:{vol/1e8:.2f}亿手 成交额:{amount/1e8:.1f}亿')
    if trade_date or trade_time:
        print(f'   时间戳:{trade_date} {trade_time}'.strip())
    print()
"
```

**新浪数据字段顺序**：名称, 当前价, 昨收, 今开, 最高, 最低, _, _, 成交量(手), 成交额(元), ...

**备用路径（腾讯快照）**：

```bash
curl -s "https://qt.gtimg.cn/q=sh000001,sz399001,sz399006" | iconv -f gbk -t utf-8
```

> 腾讯返回串里自带 `YYYYMMDDHHMMSS` 时间戳，适合交叉确认是否为节假日/盘后快照。

---

### 块 1.5：指数历史 K 线 + 最近轨迹复盘（腾讯 K 线，零依赖）

> 不再把 AKShare 当硬依赖。优先使用腾讯 `fqkline`/`kline` 接口，既能取近 30 日日 K，也能拿到市场状态字段。

```bash
curl -s "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=sh000001,day,,,30,qfq" | python3 -c "
import json, sys
d = json.load(sys.stdin)['data']['sh000001']
rows = d['day']
print('=== 上证指数 近30日 ===')
for row in rows:
    dt, o, c, h, l, vol = row[:6]
    o, c, h, l, vol = map(float, [o, c, h, l, vol])
    chg = (c - o) / o * 100 if o else 0
    color = '🟢' if chg >= 0 else '🔴'
    print(f'{dt[5:]} {color} O:{o:,.0f} C:{c:,.0f} H:{h:,.0f} L:{l:,.0f} {chg:+.2f}% 量:{vol/1e8:.2f}亿')
"
```

**复盘后必须输出：**
- 最近 `7-30` 日主导手法：`趋势推进 / 箱体洗盘 / 冲高派发 / 跌破回收 / 阴跌磨人`
- 最近 `2-3` 次关键动作：放量突破、长上影冲高回落、跌破后收回、缩量横盘等
- 今天更像：`延续 / 回踩 / 诱多 / 诱空 / 纯噪音`

**AKShare 可选路径：**
- 若本机已装 AKShare，可继续使用 `stock_zh_index_daily_em`
- 若未安装，不得因此跳过历史轨迹复盘；应改走腾讯 K 线

---

### 块 2：资金面 — 北向资金 🌐 浏览器抓取

> **A 股最关键的独有指标。** 北向资金（外资通过沪股通/深股通买卖A股）被称为「聪明钱」。
> 东方财富 API 被墙，但**网页可通过浏览器正常加载并提取数据**（已验证 2026-05-02）。

**步骤：**
1. `browser_navigate` → `https://data.eastmoney.com/hsgt/index.html`
2. 等待页面加载（5-10秒）
3. `browser_console` 执行以下 JS：

```javascript
// 提取北向资金 + 涨跌家数
const rows = document.querySelectorAll('table tbody tr');
const results = [];
rows.forEach(row => {
    const cells = row.querySelectorAll('td');
    if (cells.length >= 11) {
        results.push({
            type: cells[0]?.innerText?.trim(),
            board: cells[1]?.innerText?.trim(),
            status: cells[2]?.innerText?.trim(),
            netBuy: cells[3]?.innerText?.trim(),
            totalVol: cells[4]?.innerText?.trim(),
            balance: cells[5]?.innerText?.trim(),
            up: cells[6]?.innerText?.trim(),
            flat: cells[7]?.innerText?.trim(),
            down: cells[8]?.innerText?.trim(),
            index: cells[9]?.innerText?.trim(),
            indexChg: cells[10]?.innerText?.trim()
        });
    }
});
JSON.stringify(results, null, 2)
```

4. 将提取的 JSON 传给 `scripts/a_share_data.py` 解析：
```bash
python3 ~/.hermes/scripts/a_share_data.py northbound '<json>'
```

**解析规则：**
- 陆股通行（board = "港>沪" / "港>深"）= 北向资金
- `netBuy` 带「亿元」单位，正数=外资净流入（利好），负数=净流出（利空）
- 涨跌家数从「港>沪」行的 up/down/flat 字段提取
- 状态列显示「收盘」或「交易中」

**北向资金判断标准：**
| 净流入 | 信号 |
|--------|------|
| >50亿 | 🟢 强烈看涨 |
| 10~50亿 | 🟢 偏多 |
| -10~10亿 | ⚪ 中性 |
| -50~-10亿 | 🟡 偏空 |
| <-50亿 | 🔴 强烈看空 |

---

### 块 3：市场结构 — 涨跌家数 🌐 浏览器抓取

> 涨跌家数从北向资金同一个页面获取——已在块 2 中一并提取。
> 解析 rules：从返回 JSON 中取 board="港>沪" 行的 up/down/flat 字段。
> 若页面返回 `-`、空值、或市场处于休市/节假日，必须标注「数据暂缺/市场休市」。

**涨跌家数判断标准：**

| 涨跌比 | 信号 |
|--------|------|
| >3:1 | 🔴 极度亢奋（追高风险） |
| 1.5~3:1 | 🟢 偏多 |
| 1:1.5~3 | 🟡 偏空 |
| <1:3 | 🟢 极度恐慌（机会信号） |

**涨停跌停**（需额外浏览器抓取）：
- 涨停 > 100 家 = 赚钱效应强
- 跌停 > 50 家 = 恐慌蔓延
- 数据源：`https://data.eastmoney.com/cjsj/hqtzcj.html`（⚠️ JS 动态加载，可能提取失败，此时标注「数据暂缺」）

---

### 块 4：情绪面

```bash
# 恐惧贪婪指数（加密市场情绪，作为风险偏好参考）
curl -s "https://api.alternative.me/fng/?limit=1" | python3 -c "
import json, sys
d = json.load(sys.stdin)['data'][0]
print(f'加密恐惧贪婪: {d[\"value\"]} ({d[\"value_classification\"]})')
"

# A 股自身情绪：成交额 vs 5日均量（从块 1.5 的 K 线数据计算）
# 公式：今日成交额 / 近5日均量 > 1.5 = 放量（情绪高涨）
#      < 0.7 = 缩量（情绪低迷）
```

---

### 块 5：宏观面 — 美股联动 + 人民币汇率

```bash
# 美股三大指数 + VIX（Yahoo Finance）
curl -s -H "User-Agent: Mozilla/5.0" "https://query1.finance.yahoo.com/v8/finance/chart/^GSPC?interval=1d&range=5d" | python3 -c "
import json, sys
d = json.load(sys.stdin)['chart']['result'][0]
meta = d['meta']
quotes = d['indicators']['quote'][0]
idx = d['timestamp']
from datetime import datetime, timezone
print('=== 标普500 近5日 ===')
for i in range(len(idx)):
    dt = datetime.fromtimestamp(idx[i], tz=timezone.utc).strftime('%m-%d')
    o = quotes['open'][i]
    c = quotes['close'][i]
    chg = (c-o)/o*100 if o else 0
    co = '🟢' if chg>=0 else '🔴'
    print(f'{dt} {co} O:{o:,.0f} C:{c:,.0f} {chg:+.2f}%')
prev = meta.get('chartPreviousClose', 0)
cur = meta.get('regularMarketPrice', 0)
print(f'变动: {(cur-prev)/prev*100:+.2f}%')
"

# VIX
curl -s "https://query1.finance.yahoo.com/v8/finance/chart/^VIX?interval=1d&range=5d" | python3 -c "
import json, sys
meta = json.load(sys.stdin)['chart']['result'][0]['meta']
cur, prev = meta.get('regularMarketPrice',0), meta.get('chartPreviousClose',0)
print(f'VIX: {cur:.1f} (前:{prev:.1f})')
if cur < 15: print('🟢 安逸 → 利好风险资产')
elif cur < 20: print('🟡 正常')
elif cur < 30: print('🟠 担忧 → A股承压')
else: print('🔴 恐慌 → A股大概率大跌')
"

# 人民币汇率（新浪）
curl -s "https://hq.sinajs.cn/list=USDCNY,USDCNH" \
  --compressed \
  -H "Referer: https://finance.sina.com.cn" \
  | iconv -f gbk -t utf-8
```

**宏观执行规则：**
- 若当前为周末/节假日，美股现货与人民币汇率只作为背景过滤，不作为实时触发
- A 股对美股的传导通常是「隔夜情绪 + 次日预期」，独立性高于加密

---

### 块 6：板块轮动 🔄

> ⚠️⚠️ **海外服务器获取板块行排行极度困难。** 同花顺封 IP，雪球板块 API 需登录，东方财富 Canvas 渲染。以下方案用「板块持股资金流」替代纯涨幅排行。

#### 方法 A：东方财富 — 板块持股资金流（🐢 海外可用）

> 东方财富页面含「板块持股」表（Table 11），提供板块涨跌幅 + 资金流向，是目前海外唯一可用的板块维度数据。

**步骤：**
1. `browser_navigate` → `https://data.eastmoney.com/hsgt/index.html`
2. 等待页面加载（5-10 秒）
3. `browser_console` 执行：

```javascript
// 提取板块持股流数据（Table 11）
(() => {
  const tables = document.querySelectorAll('table');
  // 定位板块持股表：headers 含「板块名称」「涨跌幅」
  for (const table of tables) {
    const headers = Array.from(table.querySelectorAll('th')).map(h => h.innerText.trim());
    if (headers.some(h => h.includes('板块名称')) && headers.some(h => h.includes('涨跌幅'))) {
      const rows = table.querySelectorAll('tbody tr');
      return JSON.stringify(Array.from(rows).slice(0, 10).map(row => {
        const cells = row.querySelectorAll('td');
        return {
          sector: cells[1]?.innerText?.trim(),
          changePct: cells[3]?.innerText?.trim(),
          holding: cells[4]?.innerText?.trim(),
          count: cells[5]?.innerText?.trim()
        };
      }), null, 2);
    }
  }
  return '[]';
})()
```

4. 输出结果按涨跌幅排序即为板块强弱排行。

#### 方法 B：雪球热股榜（🐢 辅助参考）

> 雪球（xueqiu.com）海外可访问，首页热股榜可反映当日资金热点，但无板块排行。

**步骤：**
1. `browser_navigate` → `https://xueqiu.com/hq`
2. 从 snapshot 提取「热股榜」列表，观察热门个股所属板块
3. 热门股聚集的板块 = 当日主线

#### 方法 C：东方财富板块排行页（⚠️ Canvas 渲染，仅作最后尝试）

> `https://data.eastmoney.com/bkzj/hy.html` — 表格 Canvas 渲染，不可直接 `querySelectorAll` 提取。但可尝试用 `browser_console` 搜索页面 `<script>` 标签中的 JSON 数据块。

```javascript
// 尝试从页面脚本中提取板块数据 JSON
Array.from(document.querySelectorAll('script')).map(s => s.innerText).join('\n').match(/\{[^}]*"industryName"[^}]*\}/g)
```

#### 板块轮动分析要点

从提取到的数据中判断：
- **当日主线**：资金净流入最多的板块 + 涨幅领先板块的共性主题
- **板块持续性**：对比前几日数据，判断是否连续上榜
- **龙头股**：雪球热股榜中领涨板块的代表个股
- **轮动信号**：
  - 银行/消费领涨 = 🟡 防御/避险
  - 科技/券商领涨 + 放量 = 🟢 进攻
  - 板块全线下挫 = 🔴 系统性恐慌
- **数据质量标注**：板块持股流数据 ≠ 纯涨幅排行，报告中必须标注「数据来自板块资金流」

---

### 块 5b：增强宏观利率 📐 ⚠️ 新增（macro-rates-monitor 精简版）

> A股受美股隔夜情绪+美联储利率路径+美元影响（北向资金对美债收益率和DXY高度敏感）。
> 与块5并行拉取。

```python
# 增强宏观（Yahoo Finance，4符号 + 延迟防429）
import json, urllib.request, time

SYMBOLS = {'^TNX':'10Y','^FVX':'5Y','DX-Y.NYB':'DXY','^VIX':'VIX'}
results = {}
for sym, label in SYMBOLS.items():
    try:
        url = f'https://query1.finance.yahoo.com/v8/finance/chart/{sym}?interval=1d&range=2d'
        req = urllib.request.Request(url, headers={'User-Agent':'Mozilla/5.0'})
        d = json.load(urllib.request.urlopen(req,timeout=10))['chart']['result'][0]
        m = d['meta']
        cur = m.get('regularMarketPrice',0); prev = m.get('chartPreviousClose',0)
        chg = (cur-prev)/prev*100 if prev else 0
        results[label] = {'cur':cur,'chg':chg}
        print(f'{label}: {cur:.2f} ({chg:+.2f}%)')
        time.sleep(0.5)
    except Exception as e:
        if '429' in str(e): print(f'{label}: 429 RATE LIMIT'); break
        print(f'{label}: ERR')

tnx=results.get('10Y',{}).get('cur',0); fvx=results.get('5Y',{}).get('cur',0)
dxy=results.get('DXY',{}).get('cur',0); dxy_chg=results.get('DXY',{}).get('chg',0)
vix=results.get('VIX',{}).get('cur',0)

print(f'\n10Y: {tnx:.1f}% | 5Y: {fvx:.1f}% | DXY: {dxy:.1f}({dxy_chg:+.2f}%) | VIX: {vix:.1f}')

# 北向资金逻辑
if tnx > 4.5: print('10Y>4.5% -> USD attractive -> 北向流出压力')
elif tnx < 3.5: print('10Y<3.5% -> USD weakening -> 北向流入利好')
else: print('10Y neutral -> 北向按自身节奏')

if dxy_chg < -0.5: print('DXY弱 -> 人民币升值预期 -> 北向流入利好A股')
elif dxy_chg > 0.5: print('DXY强 -> 人民币贬值压力 -> 北向流出利空A股')

# 美股隔夜传导
if vix > 25: print('VIX>25 -> 美股恐慌 -> A股开盘承压')
elif vix < 15: print('VIX<15 -> 美股安逸 -> A股开盘偏暖')
else: print(f'VIX正常({vix:.1f}) -> 隔夜传导中性')

print(f'FOMC: Jun 17-18, 2026 | CPI: ~May 12 | A股不受T+1影响隔夜美股')
```

**块5b 北向资金联动逻辑：**

| 美债10Y | DXY | 北向预期 | A股影响 |
|---------|-----|---------|--------|
| >4.5% | >105 | 流出 | 🔴 利空 |
| <3.5% | <100 | 流入 | 🟢 利好 |
| 3.5-4.5% | 100-105 | 中性 | ⚪ 按自身节奏 |

---

### 块 7：新闻搜索（政策面）

> DuckDuckGo 已触发 bot challenge，不再作为主路径。优先用 Google News RSS；若需要中文财经站即时快讯，再用新浪财经首页 headlines 作补充。

```bash
# Google News RSS（中文）
curl -s "https://news.google.com/rss/search?q=%E4%B8%8A%E8%AF%81+OR+%E6%B7%B1%E8%AF%81+OR+%E5%88%9B%E4%B8%9A%E6%9D%BF&hl=zh-CN&gl=CN&ceid=CN:zh-Hans" | python3 -c "
import sys, html, xml.etree.ElementTree as ET
root = ET.fromstring(sys.stdin.read())
items = root.findall('./channel/item')
print('=== A股相关新闻（Google News RSS）===')
for i, item in enumerate(items[:8], 1):
    title = html.unescape(item.findtext('title', '')).strip()
    source = item.findtext('source', '')
    pub = item.findtext('pubDate', '').strip()
    print(f'{i}. {title}')
    if pub:
        print(f'   {pub}')
"

# 新浪财经首页 headlines（补充）
curl -s "https://finance.sina.com.cn" | python3 -c "
import re, sys
html = sys.stdin.read()
matches = re.findall(r'<li><a[^>]+href=\"([^\"]+)\"[^>]*>([^<]+)</a> <span class=\"time fright\">([^<]+)</span></li>', html)
print('=== 新浪财经首页 A股快讯 ===')
shown = 0
for href, title, tm in matches:
    if any(k in title for k in ['A股', '上证', '深证', '创业板', '涨停', '收评', '快讯']):
        print(f'- {title.strip()} ({tm})')
        shown += 1
        if shown >= 5:
            break
"
```

**新闻分类规则：**
- A 类：证监会 / 交易所 / 新华社 / 央行 / 国常会 / 政策文件
- B 类：PMI / 利率 / 汇率 / 海外大盘 / 产业政策
- C 类：评论稿 / KOL / 标题党 / ETF营销 / 技术分析文章
- 只有 A/B 类能影响方向；C 类最多当背景情绪

---

## 分析框架详解

### 📈 技术面（与加密通用，适配 A 股特点）

#### A 股特殊规则 ⚠️
- **T+1 交易**：当日买入次日才能卖出，做日内分析时需标注「T+1 限制」
- **涨跌停板**：主板 ±10%，创业板/科创板 ±20%，ST 股 ±5%
- **交易时间**：9:30-11:30, 13:00-15:00（北京时间）
- **集合竞价**：9:15-9:25 可挂单，9:20 后不可撤单

#### 趋势结构（多周期确认）
- 日线/60min 确定主趋势，30min/15min 寻找入场点
- 均线系统：MA5/MA10/MA20/MA60 多空排列，日线与 60min 共振时信号最强

#### 历史轨迹复盘
- 先判断最近 `7-30` 日主导手法，再解释今天的涨跌
- 若当前信号与最近主导手法冲突，优先怀疑是假突破/假跌破
- A 股常见节奏：放量突破 → 次日高开低走；缩量慢推 → 持续性更好；长上影冲高回落 → 派发风险

#### 形态识别
与加密相同：双顶/双底/头肩/三角形/旗形/W底/M顶

#### A 股特有技术指标
- **分时图形态**：早盘冲高回落 vs 尾盘拉升，反映主力意图
- **集合竞价量**：9:25 撮合成交量异常放大 → 当日可能大幅波动
- **缺口理论**：A 股缺口回补概率高于加密

---

### 💰 资金面（A 股独有，核心维度）

| 指标 | 含义 | 多空判断 |
|------|------|---------|
| 北向资金 | 外资通过沪/深港通净买入 | 连续净流入 = 🟢 看涨 |
| 主力净流入 | 大单资金流向 | 主力净流入 > 0 = 🟢 |
| 融资余额 | 杠杆资金规模 | 融资余额持续上升 = 情绪偏多 |
| 融券余额 | 做空规模 | 融券暴增 = 看空信号 |

---

### 📊 市场结构（A 股独有）

| 指标 | 含义 |
|------|------|
| 涨跌家数比 | 上涨/下跌股票数。>2:1 = 普涨，<1:2 = 普跌 |
| 涨停家数 | >100 家 = 赚钱效应强，<20 家 = 人气冰点 |
| 跌停家数 | >50 家 = 恐慌出逃 |
| 连板高度 | 最高连板数，反映游资活跃度 |

---

### 😱 情绪面

- **成交额**：今日 vs 5日/20日均量。放量上涨 = 健康，缩量上涨 = 警惕
- **融资融券比**：融资/融券 > 100 = 极度看多（拥挤信号）
- **新股破发率**：近期新股上市首日破发比例 → 情绪温度计
- **节假日注意**：休市期间成交额、涨跌家数、北向资金不更新，情绪面只能基于上一交易日收盘数据

---

### 📐 增强宏观
- 美债10Y X.X% | DXY XX.X | VIX XX.X
- 北向联动：[流入利好/流出利空/中性]
- FOMC X月X日 | CPI X月X日

### 🌍 宏观面

#### 🇺🇸 美股联动
- A 股与美股存在情绪传导，但独立性高于加密
- 关注：美联储决议、非农、CPI

#### 🇨🇳 中国特有宏观因子
- **央行政策**：降准/降息/LPR 调整 → 直接利好
- **人民币汇率**：USDCNY > 7.2 → 外资流出压力
- **PMI**：>50 经济扩张，<50 经济收缩
- **政策信号**：国常会、政治局会议、证监会表态

---

### 🔄 板块轮动

- **领涨板块**：资金主攻方向，判断当日主线
- **领跌板块**：资金逃离方向
- **热点概念**：是否有持续性（连续 3 天以上上榜）
- **龙头识别**：板块内率先涨停、封单最大的个股

---

## 报告输出模板

```
## 📊 A 股综合分析报告 — YYYY-MM-DD

**分析时间（UTC）**：[YYYY-MM-DD HH:MM]
**分析时间（BJT）**：[YYYY-MM-DD HH:MM]
**市场状态**：[交易中 / 午休 / 收盘后 / 周末 / 节假日]
**数据完整性**：[完整 / 哪些关键块缺失]

### 🟢 三大指数快照
[上证/深证/创业板：价格、涨跌、成交额]

### 🧭 历史轨迹复盘
[最近 7-30 日主导手法]
[最近 2-3 次关键动作]
[今天更像延续/回踩/诱多/诱空/纯噪音]

### 📈 技术面
[趋势方向 + 关键支撑/阻力位 + 量价判断]
[⚠️ 形态识别结果]

### 💰 资金面
[北向资金净流入/流出 + 主力资金方向]
[「数据暂缺」如海外无法获取]

### 📊 市场结构
[涨跌家数 + 涨跌停统计]
[「数据暂缺」如海外无法获取]

### 😱 情绪面
[成交额 vs 均量 + 整体风险偏好]

### 📐 增强宏观
- 美债10Y X.X% | DXY XX.X | VIX XX.X
- 北向联动：[流入利好/流出利空/中性]
- FOMC X月X日 | CPI X月X日

### 🌍 宏观面
[美股隔夜表现 + 人民币汇率 + 政策要闻]

### 🔄 板块轮动
[领涨板块 TOP5 / 领跌板块 TOP5 / 热点概念]

### 🎯 综合研判
| 维度 | 信号 | 方向 |
|------|------|------|
| 技术面 | [简述] | 🟢/🔴 |
| 资金面 | [简述/暂缺] | 🟢/🔴 |
| 市场结构 | [简述/暂缺] | 🟢/🔴 |
| 情绪面 | [简述] | 🟢/🔴 |
| 宏观面 | [简述] | 🟢/🔴 |
| 板块轮动 | [简述/暂缺] | 🟢/🔴 |

[维度一致/分歧判断]

### 🎯 明日前瞻
- 方向: [偏多 / 偏空 / 震荡]
- 关键点位: 上证支撑 XX / 阻力 XX
- 关注板块: [1-2个]
- 风险提示: [T+1限制 / 涨跌停规则 / 政策风险]

### ⚠️ 免责声明
以上分析基于公开数据，不构成投资建议。A 股有风险，投资需谨慎。
```

---

## 相关文件

- `scripts/a_share_data.py` — 东方财富网页数据提取与标准化脚本。用法：`python3 scripts/a_share_data.py <northbound|sectors|capital_flow|breadth> '<json>'`
- `scripts/a_share_fetch.py` — 通过国内节点统一拉取 A 股关键数据（指数、北向、涨跌家数、板块资金流、指数资金流、汇率等），并支持个股模式。用法：`python3 scripts/a_share_fetch.py --remote ash-remote` 或 `python3 scripts/a_share_fetch.py --stock 600519`
- `scripts/a_share_analyze.py` — 基于采集 JSON 生成 A 股综合分析报告，也支持个股观察段落。用法：`python3 scripts/a_share_analyze.py --input /tmp/a_share.json`
- `references/china-finance-apis.md` — 中国金融数据 API 实测记录（哪些能通、哪些被墙）

## 注意事项

- **涨跌停板规则**：主板 ±10%，创业板/科创板 ±20%，ST ±5%。极端行情下流动性枯竭
- **T+1 制度**：日内分析仅适用于观察，实操需考虑隔夜风险
- **政策风险**：A 股受政策影响极大，突发监管/窗口指导可瞬间转向
- **数据可用性**：海外服务器可通过浏览器提取东方财富网页的北向资金历史数据（hsgt/index.html）+ 板块持股流，但实时北向资金表/涨跌家数休市时为空。新浪财经首页可替代 API 提取指数。板块排行是海外最大缺口。
- **市场状态判断**：优先使用腾讯 `market` 状态和指数时间戳；不要只按本地时钟判断是否开盘
- **午间休市**：11:30-13:00（北京时间）不交易，不能误判为连续盘中
- **历史 K 线**：优先腾讯 `fqkline`/`kline`，AKShare 仅为可选路径
- **交易时间**：只在 9:30-15:00 有实时数据，其他时段为收盘价
- **新浪 API**：GBK 编码，需 `iconv -f gbk -t utf-8` 转码
- **Google News RSS**：可用，但会混入评论和二手转发；必须做 A/B/C 分类
- 预测必须标注「不构成投资建议」
- 数据缺失时明确标注缺口，**绝不编造**
