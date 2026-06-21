---
name: forex-market-analysis
description: "外汇货币对与美元指数八维分析。利率路径与美元方向定大局，1-7维先形成主判断，第8维用CZSC缠论确认/冲突/不足，结构锚定止盈止损。"
---

# 外汇货币对日内交易全流程

> ⛔ 铁律：你不是在写行情播报，你是在做证据审计。每个方向判断必须回答"为什么"，并先做反向审计。允许使用"证据不足"、"方向未确认"、"观望"；禁止在证据冲突时硬给做多/做空。

> **核心理念：利率路径与美元方向定大局，结构位定执行。**
> 外汇的核心在利率预期、央行政策路径、美元强弱和风险偏好，不在链上或资金费率。

---


> **⛔ 禁止调用 mcp_yfinance 系列工具**：Yahoo Finance 频繁 429。所有数据通过 `scripts/` 目录下的 fetch 脚本获取（内置延迟+重试）。模型不要额外调 `mcp_yfinance_get_historical_stock_prices` 等 MCP 工具。

## 一、铁律（不可违反）

### 1. 先判断是否有方向优势
- 输出只能是 🟢 做多 / 🔴 做空 / ⚪ 观望，但默认不是强行二选一。
- 方向由你基于各维度证据的逻辑强度和可靠性综合判断得出，不要用投票计数或权重打分决定方向。
- 判断不出方向、数据窗口临近、美元与对手货币驱动冲突时，必须输出 ⚪ 观望。
- 方向针对用户给的交易对本身，不是对某个货币的主观看法。

### 2. 止盈止损必须锚定客观技术结构
- ✅ 允许参考的结构：前高/前低（独立摆点）、形态颈线、趋势线交点、斐波那契回撤位、密集成交区上沿/下沿、EMA21/EMA55
- ❌ **禁止**使用：24h 最高/最低点、今日开盘价、「跌 2% 就走」等固定百分比、任何以时间为边界而非结构为边界的价位
- 每一个 SL/TP 价位必须在报告中标注「结构依据」——具体说明这是哪个结构、什么时候形成的

### 3. 止损幅度由结构决定
- 做多止损：放在最近关键结构低点下方 0.2%-0.3%
- 做空止损：放在最近关键结构高点上方 0.2%-0.3%
- 止损幅度不由百分比决定（但如果结构决定的幅度超过账户风控上限，需特别标注风险，建议减小仓位而非放宽止损）
- 外汇波动较加密小，SL 缓冲可适当收窄至 0.15%-0.25%，但必须以结构位为准

### 4. 必须带失效条件
- 至少 2 个明确的「不等止损、立即手动平仓」的条件
- 失效条件必须是客观可观察的（4H K 线收盘、DXY 突破关键位、央行/宏观消息驱动转向等）

### 5. 数据缺口必须降级处理
- 报告开头必须标注**分析时间（UTC）**
- 技术结构、主导力量（央行/利率）、交叉验证三项里只要缺 1 项，默认降级为 ⚪ 观望
- 新闻、情绪等非关键块缺失时，可继续分析，但必须明确写出「数据缺口」
- 若 Yahoo Finance / Google News 返回 429、4xx、空数据，先减少请求并复用已拉取数据；仍失败则停止补抓，**绝不编造**
- 若处于周末或美国节假日，美股/DXY 现货数据默认视为上一交易日参考，不得当作实时盘中联动
- 重大数据公布前 30 分钟，自动降级为观望

### 6. 先复盘轨迹，再谈方向
- 每做一个货币对，必须先看它最近 `30D 4H` 是怎么走出来的，再看当前截面
- 必须回答：这个货币对最近更像 `趋势推进 / 箱体洗盘 / 冲高派发 / 跌破回收 / 阴跌磨人` 里的哪一种
- 如果你连最近主导手法都说不清，就不能把当前波动解读为高置信度机会

### 7. 分清货币对分子分母
- 始终明确货币对的 numerator / denominator 方向
- 做多 EURUSD = 看涨欧元、看跌美元；做空 USDJPY = 看跌美元、看涨日元
- 不要把「美元走强」的宏观判断直接等同于「做多 USDXXX」

### 8. 央行与宏观事件优先
- 外汇的核心驱动是利率路径和央行政策
- 若当前处在央行决议窗口（前 48h 内或后 24h 内），宏观权重大于技术面
- 若结构与利率/美元方向冲突，优先服从利率/美元方向

### 9. 禁止用固定止损距离
- 外汇波动率因货币对而异：GBPUSD 日均波动远大于 EURUSD，USDCNH 有管理波动
- 止损必须以各货币对自身结构位为准，不可统一套用「30 pips」「50 pips」

### 10. 仓位公式固定
- 仓位 = risk_amount / |entry - SL|
- 不可用其他公式代替
- 需要换算合约单位时在报告中注明

---

## 二、八维分析框架

| # | 维度 | 核心关注 | 外汇对应项 |
|---|------|---------|-----------|
| 1 | 📈 技术结构 | K线趋势、支撑阻力、形态识别 | 多周期结构、波段节奏 |
| 2 | ⛓️ 利差与美元结构 | 利差预期、DXY关系、避险/风险偏好结构 | 替代链上数据 |
| 3 | 🏦 主导力量 | 央行路径、收益率差、政策预期 | 替代 OI/资金费率 |
| 4 | 😱 情绪面 | VIX、避险流、risk-on/risk-off | 替代恐惧贪婪指数 |
| 5 | 🌍 宏观基本面 | CPI、NFP、GDP、PMI、央行会议、地缘 | 权重高于技术面 |
| 6 | 🔍 交叉验证 | DXY、美债收益率、相关交叉盘、黄金/原油 | 替代多交易所验证 |
| 7 | 📊 仓位/CFTC | 杠杆基金、资产管理、美元指数持仓 | 外汇市场专属增强 |
| 8 | 🧭 缠论结构 | CZSC 中枢、笔、背驰、买卖点候补 | 只做确认/冲突/不足 |

**强制输出规则**：
1. 先给 `各维度证据`，只基于第 1-7 维逐项列出每个维度的偏多/偏空/中性/缺失状态及理由。不要用投票计数或权重打分决定方向。
2. 必须做 `反向审计`：若美元、利差、央行路径或风险情绪与技术方向冲突，最终方向降级为观望。
3. 再给 `缠论确认`，说明 CZSC 是确认、冲突还是不足。
4. 最终方向由你基于各维度证据的逻辑强度综合判断后决定，不能由缠论单独决定；与利率/央行路径冲突时必须降级。
5. 使用 `python3 -m hermes_finance analyze forex <SYMBOL>` 或 MCP `analyze_forex`，默认会尽量用采集器 K 线跑 CZSC。

### 维度详解

#### 📈 技术面
- **趋势定义**：higher highs + higher lows = 上升趋势（至少 2 组）；lower highs + lower lows = 下降趋势
- **均线系统**：EMA21/EMA55 多空排列，4H 与 1H 共振时信号最强
- **关键形态**：双顶/双底、头肩顶/底、上升/下降三角形、旗形/三角旗、W 底 / M 顶
- **量价关系**：外汇无集中交易所成交量，Yahoo Finance 成交量仅作弱代理，不单独作为执行依据

#### ⛓️ 市场结构（外汇版）
- **利差预期**：通过 `^TNX`（10Y）/ `^FVX`（5Y）利差变化判断美元吸引力
- **美元指数**：DXY 直接影响所有 USD 对手货币对方向
- **避险结构**：VIX > 30 → 日元/瑞郎走强；VIX < 15 → 套利货币（AUD/NZD）走强

#### 🏦 主导力量（央行/利率）
- **央行路径**：Fed vs ECB/BOJ/BOE/RBA 的政策预期差
- **收益率差**：美德利差对 EURUSD；美日利差对 USDJPY；中美利差对 USDCNH
- **美元强弱**：DXY 趋势是最大单一因子
- **CFTC 持仓**（如有）：杠杆基金净头寸方向

#### 😱 情绪面
- **VIX**：< 15 = risk-on（利好套利货币）；20-30 = 担忧；> 30 = 恐慌（利好避险货币）
- **避险流**：股市大跌 → JPY/CHF 走强，AUD/NZD 走弱
- **Fear & Greed**（Alternative.me，仅作弱参考）

#### 🌍 宏观基本面
- **核心数据**：NFP、CPI、GDP、PMI、零售销售、央行利率决议
- **事件驱动**：FOMC 会议纪要、央行行长讲话、地缘事件
- **权重规则**：央行决议窗口期宏观权重 > 60%；日常 > 30%

#### 🔍 交叉验证
- **DXY**：所有 USD 对手盘的背景板
- **美债收益率**：`^TNX`（10Y）和 `^FVX`（5Y）
- **相关交叉盘**：做 EURUSD 时看 GBPUSD、USDCHF
- **关联资产**：黄金（XAUUSD，避险）、原油（通胀预期）
- **利差对标**：2Y 和 10Y 美债利差作为衰退/加息预期代理

---

## 三、决策流程（从数据到方向）

### 第零步：复盘这个货币对最近的走势（决定值不值得做）

**三层复盘窗口：**
```text
90D 日线轮廓 → 看大环境（央行路径变化痕迹）
30D 4H 轨迹 → 看主导手法（这个货币对平时怎么走）
24H 1H 节奏 → 看今天是在延续、回踩还是诱多/诱空
```

**常见走势手法分类：**
- `趋势推进`：higher highs + higher lows，回调浅，沿均线运行
- `箱体洗盘`：长时间区间震荡，上下插针多，真假突破反复出现
- `冲高派发`：急拉后高位横盘，长上影增多，然后回落
- `跌破回收`：先破关键位触发止损，再快速收回区间内部
- `阴跌磨人`：lower highs 持续，反弹弱，量能难以跟上

**执行规则：**
- 今天的判断必须和最近 `30D 4H` 主导手法对照，说明当前是**延续**还是**反着来**
- 若今天的短线信号和最近主导手法明显冲突，优先怀疑是假突破/假跌破
- 若 DXY 与货币对方向背离，优先服从 DXY 方向（美元是最大单一驱动）

### 第一步：判断趋势结构（决定能不能做）

**多周期确认（自上而下）：**
```
日线趋势 → 4H 结构 → 1H 入场点
```

**趋势定义（最客观的标准）：**
- 上升趋势 = higher highs + higher lows（至少 2 组）
- 下降趋势 = lower highs + lower lows（至少 2 组）
- 震荡 = 无明显高/低点序列，价格在区间内

**关键问题**：最近一个结构摆点是 higher low 还是 lower high？
- 如果最近是 higher low → 上升结构未破坏 → 只考虑做多
- 如果最近是 lower high → 下降结构未破坏 → 只考虑做空
- 如果结构模糊 → 观望

### 第二步：判断主导力量（央行/利率/美元方向）

这是外汇八维中第 3 维最重要的维度。按货币对优先级不同：

| 货币对 | 第一驱动 | 第二驱动 | 第三驱动 |
|--------|---------|---------|---------|
| EURUSD | Fed vs ECB 路径差 | DXY | 美德利差 |
| USDJPY | 美债收益率 | BOJ 政策 / 干预风险 | 风险偏好 |
| GBPUSD | 英国通胀 / BOE 路径 | 美元方向 | 脱欧/政治风险 |
| AUDUSD | 中国 + 全球风险偏好 | 大宗商品 | 美元 / RBA |
| USDCNH | 中美利差 | PBOC 管理 | 风险事件 |
| DXY | Fed 路径 | 全球风险偏好 | 对手货币（EUR为主） |

**主导力量判断矩阵：**

| 条件 | 信号 | 操作 |
|------|------|------|
| DXY ↗ + 10Y ↗ + Fed 鹰派 | 🟢 美元走强 | USDXXX 做多 / XXXUSD 做空 |
| DXY ↘ + 10Y ↘ + Fed 鸽派 | 🔴 美元走弱 | USDXXX 做空 / XXXUSD 做多 |
| DXY ↗ + VIX ↗ | 🟡 避险 + 美元强 | USDJPY 承压（日元更强），AUDUSD 承压 |
| DXY ↘ + VIX ↘ | 🟢 risk-on | AUDUSD/GBPUSD 走强 |
| 央行路径分歧大 | 🟡 | 按利差方向 + 结构确认 |

### 第三步：量价验证（决定时机对不对）

- 外汇无集中成交量，Yahoo Finance 成交量仅作弱参考
- 主要看价格行为：突破是否坚决、回踩是否缩量（参考 tick volume 或跳动量）
- 关键 K 线形态：长上影/下影、吞没、pin bar、inside bar
- 若在关键央行事件前后，量价验证权重降低，宏观因子权重提高

### 第四步：精算止盈止损位

**做多场景：**
```
SL  = 最近结构低点 × (1 - 0.25%)   ← 必须是独立的4H/1H摆低点
TP1 = 最近的结构阻力              ← 前高、趋势线上轨、形态颈线
TP2 = 下一级结构阻力              ← 更远的独立结构峰
TP3 = 形态理论目标                ← 旗杆高度投影、斐波那契延伸
```

**做空场景：**
```
SL  = 最近结构高点 × (1 + 0.25%)
TP1 = 最近的结构支撑
TP2 = 下一级结构支撑
TP3 = 形态理论目标
```

**移动止损：**
- 到 TP1 → 移损至开仓价
- 到 TP2 → 移损至 TP1
- 创新高/低 → 跟踪最近 2 根 4H K 线的结构摆点

**仓位计算：**
```
仓位 = risk_amount / |entry - SL|
以 $10,000 账户 2% 风险为例：$200 / |entry - SL| = 可开仓位
```

---

## 四、数据采集（按顺序执行以下数据块）

### ⚠️ 强制规则：一键脚本采集（禁止手动 curl Yahoo）

```bash
# 一键采集（内置429重试+并行）
python3 /root/.hermes/skills/research/forex-market-analysis/scripts/forex_fetch.py EURUSD --compact
# 替换为: EURUSD / USDJPY / GBPUSD / AUDUSD / USDCHF / USDCNH / DXY
```

**宏观数据（TNX/DXY/VIX）通过 fetch 脚本获取，禁止调 mcp_yfinance。**




```

**❌ 绝对禁止直接 curl Yahoo Finance API。下面的代码块仅作参考文档，不要复制执行。**

### 块 0：执行前检查 ⚠️ 必做

> 先确认分析时间和货币对。标的都没对齐，后面的数据越多越危险。

```bash
# 记录分析时间（报告中必须回填）
date -u '+分析时间(UTC): %Y-%m-%d %H:%M'

# 解析并确认货币对
echo "确认货币对: 用户输入 → 标准化为 [EURUSD / USDJPY / GBPUSD / AUDUSD / USDCHF / USDCNH / DXY]"
```

**执行规则：**
- 如果货币对不在支持列表中，停止分析并要求确认
- 日内结构优先使用 Yahoo Finance 1H 真实 OHLC；聚合采样价格只可用于宏观轮廓，不可直接拿来卡精确止损
- 一次分析尽量复用同一批响应，避免 Yahoo Finance 频率限制
- 如果当前价格已经贴近最近主阻力/主支撑，导致首个止盈空间过小、盈亏比低于 1.5，则不追价，等待回踩/反抽或直接观望
- 重大宏观数据公布前 30 分钟内，自动降级为观望

---

### 块 1：实时报价 + 30日历史（Yahoo Finance）

> 外汇对使用 Yahoo Finance 的 FX 代码。注意：EURUSD → `EURUSD=X`，USDJPY → `JPY=X`，GBPUSD → `GBPUSD=X`，AUDUSD → `AUDUSD=X`，USDCNH → `CNH=X`，DXY → `DX-Y.NYB`。

```bash
# === 实时报价（最新价格 + 变动）===
# 替换 PAIR=X 为实际货币对代码
curl -s -H "User-Agent: Mozilla/5.0" "https://query1.finance.yahoo.com/v8/finance/chart/PAIR=X?interval=1d&range=5d" | python3 -c "
import json, sys
from datetime import datetime, timezone
d = json.load(sys.stdin)['chart']['result'][0]
meta = d['meta']
quotes = d['indicators']['quote'][0]
idx = d['timestamp']
print('=== 实时报价 ===')
prev = meta.get('chartPreviousClose', 0)
cur = meta.get('regularMarketPrice', 0)
chg = (cur - prev) / prev * 100 if prev else 0
print(f'当前价: {cur:.5f}')
print(f'前收盘: {prev:.5f}')
print(f'变动: {chg:+.3f}%')
print(f'交易所: {meta.get(\"exchangeName\", \"?\")}')
print(f'货币: {meta.get(\"currency\", \"?\")}')
print()
print('=== 近5日收盘 ===')
for i in range(len(idx)):
    dt = datetime.fromtimestamp(idx[i], tz=timezone.utc).strftime('%m-%d')
    o = quotes['open'][i]
    c = quotes['close'][i]
    h = quotes['high'][i]
    l = quotes['low'][i]
    chg_d = (c - o) / o * 100 if o else 0
    emoji = '🟢' if chg_d >= 0 else '🔴'
    print(f'{dt} {emoji} O:{o:.5f} H:{h:.5f} L:{l:.5f} C:{c:.5f} 涨跌:{chg_d:+.3f}%')
"

# === 30日历史（日线，用于轮廓判断）===
curl -s -H "User-Agent: Mozilla/5.0" "https://query1.finance.yahoo.com/v8/finance/chart/PAIR=X?interval=1d&range=1mo" | python3 -c "
import json, sys
from datetime import datetime, timezone
d = json.load(sys.stdin)['chart']['result'][0]
quotes = d['indicators']['quote'][0]
idx = d['timestamp']
print('=== 30日价格走势 ===')
closes = []
for i in range(len(idx)):
    dt = datetime.fromtimestamp(idx[i], tz=timezone.utc).strftime('%m-%d')
    o = quotes['open'][i]
    h = quotes['high'][i]
    l = quotes['low'][i]
    c = quotes['close'][i]
    closes.append(c)
    v = quotes['volume'][i] if quotes.get('volume') and i < len(quotes['volume']) else 0
    chg = (c - o) / o * 100 if o else 0
    emoji = '🟢' if chg >= 0 else '🔴'
    print(f'{dt} {emoji} O:{o:.5f} H:{h:.5f} L:{l:.5f} C:{c:.5f} vol:{v:,.0f}')
if len(closes) >= 2:
    chg_30 = (closes[-1] / closes[0] - 1) * 100 if closes[0] else 0
    hi_30 = max(closes)
    lo_30 = min(closes)
    print(f'30日涨跌: {chg_30:+.3f}% | 区间高: {hi_30:.5f} | 区间低: {lo_30:.5f}')
"
```

---

### 块 1.2：30日 4H 轨迹复盘 ⚠️ 必做

> 不要只看当前一屏数据。先复盘这个货币对近 `30D 4H` 的主轨迹，再决定今天看到的是延续、洗盘还是陷阱。
> Yahoo Finance 没有原生 4H，需要用 1H 数据聚合。

```bash
# === 30日 4H 轨迹复盘（从 1H 聚合） ===
curl -s -H "User-Agent: Mozilla/5.0" "https://query1.finance.yahoo.com/v8/finance/chart/PAIR=X?interval=1h&range=1mo" | python3 -c "
import json, sys
from datetime import datetime, timezone
d = json.load(sys.stdin)['chart']['result'][0]
quotes = d['indicators']['quote'][0]
idx = d['timestamp']

# 聚合 1H 到 4H
rows = []
for i in range(len(idx)):
    o = quotes['open'][i]
    h = quotes['high'][i]
    l = quotes['low'][i]
    c = quotes['close'][i]
    v = quotes['volume'][i] if quotes.get('volume') and i < len(quotes['volume']) else 0
    if o is not None and h is not None and l is not None and c is not None:
        rows.append({'t': idx[i], 'o': o, 'h': h, 'l': l, 'c': c, 'v': v})

agg = []
for i in range(0, len(rows) - 3, 4):
    chunk = rows[i:i+4]
    agg.append({
        't': chunk[0]['t'],
        'o': chunk[0]['o'],
        'h': max(x['h'] for x in chunk),
        'l': min(x['l'] for x in chunk),
        'c': chunk[-1]['c'],
    })

print('=== 🧭 30日 4H 轨迹复盘（从1H聚合）===')
if not agg:
    print('数据不足')
    sys.exit(0)

hi = max(agg, key=lambda r: r['h'])
lo = min(agg, key=lambda r: r['l'])
print(f'区间低点: {lo[\"l\"]:.5f} @ {datetime.fromtimestamp(lo[\"t\"], tz=timezone.utc).strftime(\"%m-%d %H:%M\")}')
print(f'区间高点: {hi[\"h\"]:.5f} @ {datetime.fromtimestamp(hi[\"t\"], tz=timezone.utc).strftime(\"%m-%d %H:%M\")}')

# 找摆高摆低
ph, pl = [], []
for i in range(2, len(agg)-2):
    if agg[i]['h'] > agg[i-1]['h'] and agg[i]['h'] > agg[i-2]['h'] and agg[i]['h'] > agg[i+1]['h'] and agg[i]['h'] > agg[i+2]['h']:
        ph.append(agg[i])
    if agg[i]['l'] < agg[i-1]['l'] and agg[i]['l'] < agg[i-2]['l'] and agg[i]['l'] < agg[i+1]['l'] and agg[i]['l'] < agg[i+2]['l']:
        pl.append(agg[i])

print('最近摆高:')
for r in ph[-4:]:
    print(f'  {datetime.fromtimestamp(r[\"t\"], tz=timezone.utc).strftime(\"%m-%d %H:%M\")}  {r[\"h\"]:.5f}')
print('最近摆低:')
for r in pl[-4:]:
    print(f'  {datetime.fromtimestamp(r[\"t\"], tz=timezone.utc).strftime(\"%m-%d %H:%M\")}  {r[\"l\"]:.5f}')

# 大波动K线
events = []
for r in agg:
    body = (r['c'] - r['o']) / r['o'] * 100 if r['o'] else 0
    rng = (r['h'] - r['l']) / r['o'] * 100 if r['o'] else 0
    if abs(body) >= 0.5 or rng >= 0.8:
        events.append((abs(body), body, rng, r))

print('大波动K线（帮助识别急拉/急砸/洗盘）:')
for _, body, rng, r in sorted(events, reverse=True)[:6]:
    dt = datetime.fromtimestamp(r['t'], tz=timezone.utc).strftime('%m-%d %H:%M')
    print(f'  {dt} body:{body:+.3f}% range:{rng:.3f}% O:{r[\"o\"]:.5f} C:{r[\"c\"]:.5f}')
"

# === 90日 日线轮廓（大环境）===
curl -s -H "User-Agent: Mozilla/5.0" "https://query1.finance.yahoo.com/v8/finance/chart/PAIR=X?interval=1d&range=3mo" | python3 -c "
import json, sys
d = json.load(sys.stdin)['chart']['result'][0]
quotes = d['indicators']['quote'][0]
idx = d['timestamp']
closes = [quotes['close'][i] for i in range(len(idx)) if quotes['close'][i] is not None]
if len(closes) < 20:
    print('=== 🗺️ 90日 日线轮廓 === 数据不足')
else:
    chg_90 = (closes[-1] / closes[0] - 1) * 100
    chg_20 = (closes[-1] / closes[-20] - 1) * 100 if len(closes) >= 20 else 0
    chg_7 = (closes[-1] / closes[-7] - 1) * 100 if len(closes) >= 7 else 0
    print('=== 🗺️ 90日 日线轮廓 ===')
    print(f'90日涨跌: {chg_90:+.3f}%')
    print(f'20日涨跌: {chg_20:+.3f}%')
    print(f'7日涨跌: {chg_7:+.3f}%')
    print(f'90日高: {max(closes):.5f} | 90日低: {min(closes):.5f}')
"
```

**复盘后必须输出：**
- 最近 `30D 4H` 主导手法是什么
- 最近 `2-3` 次关键动作是什么（急拉、急跌、假突破、回收、派发）
- 今天看到的信号属于 `延续 / 回踩 / 诱多 / 诱空 / 纯噪音`

---

### 块 1.5：4H/1H 真实蜡烛 ⚠️ 日内交易者必看

> 日内交易要看**真实 OHLC**。Yahoo Finance 1H 数据直接提供 OHLC，不需聚合即可用于 1H 结构判断。4H 从 1H 聚合。

```bash
# === 1H K线（精确日内级别，Yahoo Finance） ===
curl -s -H "User-Agent: Mozilla/5.0" "https://query1.finance.yahoo.com/v8/finance/chart/PAIR=X?interval=1h&range=5d" | python3 -c "
import json, sys
from datetime import datetime, timezone
d = json.load(sys.stdin)['chart']['result'][0]
quotes = d['indicators']['quote'][0]
idx = d['timestamp']
print('=== 📊 1H K线（近5日，最近24根）===')
count = 0
for i in range(len(idx)):
    o = quotes['open'][i]
    h = quotes['high'][i]
    l = quotes['low'][i]
    c = quotes['close'][i]
    if o is None or h is None or l is None or c is None:
        continue
    count += 1
rows_total = count
shown = 0
for i in range(max(0, len(idx) - 24), len(idx)):
    o = quotes['open'][i]
    h = quotes['high'][i]
    l = quotes['low'][i]
    c = quotes['close'][i]
    if o is None or h is None or l is None or c is None:
        continue
    dt = datetime.fromtimestamp(idx[i], tz=timezone.utc).strftime('%m-%d %H:%M')
    color = '🟢' if c >= o else '🔴'
    body_pct = abs(c - o) / o * 100 if o else 0
    wick_up = (h - max(o, c)) / o * 100 if o else 0
    wick_down = (min(o, c) - l) / o * 100 if o else 0
    print(f'{dt} {color} O:{o:.5f} H:{h:.5f} L:{l:.5f} C:{c:.5f} | 实体:{body_pct:.3f}% 上影:{wick_up:.3f}% 下影:{wick_down:.3f}%')
    shown += 1
print(f'显示 {shown}/{rows_total} 根K线')
"

# === 4H K线（从1H聚合，用于趋势+形态识别） ===
curl -s -H "User-Agent: Mozilla/5.0" "https://query1.finance.yahoo.com/v8/finance/chart/PAIR=X?interval=1h&range=10d" | python3 -c "
import json, sys
from datetime import datetime, timezone
d = json.load(sys.stdin)['chart']['result'][0]
quotes = d['indicators']['quote'][0]
idx = d['timestamp']

rows = []
for i in range(len(idx)):
    o = quotes['open'][i]
    h = quotes['high'][i]
    l = quotes['low'][i]
    c = quotes['close'][i]
    if o is not None and h is not None and l is not None and c is not None:
        rows.append({'t': idx[i], 'o': o, 'h': h, 'l': l, 'c': c})

agg = []
for i in range(0, len(rows) - 3, 4):
    chunk = rows[i:i+4]
    agg.append({
        't': chunk[0]['t'],
        'o': chunk[0]['o'],
        'h': max(x['h'] for x in chunk),
        'l': min(x['l'] for x in chunk),
        'c': chunk[-1]['c'],
    })

print('=== 📊 4H K线（从1H聚合，近10日，最近20根）===')
for r in agg[-20:]:
    dt = datetime.fromtimestamp(r['t'], tz=timezone.utc).strftime('%m-%d %H:%M')
    color = '🟢' if r['c'] >= r['o'] else '🔴'
    body_pct = abs(r['c'] - r['o']) / r['o'] * 100 if r['o'] else 0
    wick_up = (r['h'] - max(r['o'], r['c'])) / r['o'] * 100 if r['o'] else 0
    wick_down = (min(r['o'], r['c']) - r['l']) / r['o'] * 100 if r['o'] else 0
    print(f'{dt} {color} O:{r[\"o\"]:.5f} H:{r[\"h\"]:.5f} L:{r[\"l\"]:.5f} C:{r[\"c\"]:.5f} | 实体:{body_pct:.3f}% 上影:{wick_up:.3f}% 下影:{wick_down:.3f}%')
"
```

---

### 块 2：市场结构（DXY、收益率、利差）⚠️ 必查

> DXY 是美元对一篮子货币的加权指数，是所有 USD 货币对的背景板。`^TNX`（10Y）和 `^FVX`（5Y）反映美债收益率。

```bash
# === DXY 美元指数（近5日 + 实时） ===
curl -s -H "User-Agent: Mozilla/5.0" "https://query1.finance.yahoo.com/v8/finance/chart/DX-Y.NYB?interval=1d&range=5d" | python3 -c "
import json, sys
from datetime import datetime, timezone
d = json.load(sys.stdin)['chart']['result'][0]
meta = d['meta']
quotes = d['indicators']['quote'][0]
idx = d['timestamp']
prev = meta.get('chartPreviousClose', 0)
cur = meta.get('regularMarketPrice', 0)
print('=== 💵 DXY 美元指数 ===')
print(f'当前: {cur:.3f} | 前收: {prev:.3f} | 变动: {(cur-prev)/prev*100:+.3f}%' if prev else f'当前: {cur:.3f}')
if cur > 105:
    print('状态: 🟢 美元强势 (>105)')
elif cur > 100:
    print('状态: 🟡 美元中性 (100-105)')
else:
    print('状态: 🔴 美元弱势 (<100)')
print()
print('近5日:')
for i in range(len(idx)):
    dt = datetime.fromtimestamp(idx[i], tz=timezone.utc).strftime('%m-%d')
    o = quotes['open'][i]
    c = quotes['close'][i]
    chg = (c-o)/o*100 if o else 0
    emoji = '🟢' if chg>=0 else '🔴'
    print(f'{dt} {emoji} O:{o:.3f} C:{c:.3f} {chg:+.3f}%')
"

# === 10Y 美债收益率 (^TNX) ===
curl -s -H "User-Agent: Mozilla/5.0" "https://query1.finance.yahoo.com/v8/finance/chart/%5ETNX?interval=1d&range=5d" | python3 -c "
import json, sys
from datetime import datetime, timezone
d = json.load(sys.stdin)['chart']['result'][0]
meta = d['meta']
quotes = d['indicators']['quote'][0]
idx = d['timestamp']
prev = meta.get('chartPreviousClose', 0)
cur = meta.get('regularMarketPrice', 0)
print('=== 📈 10Y 美债收益率 (^TNX) ===')
print(f'当前: {cur:.3f}% | 前收: {prev:.3f}% | 变动: {cur-prev:+.3f} bp' if prev else f'当前: {cur:.3f}%')
if cur > 4.5:
    print('状态: 🟢 高收益率 → 美元吸引力强')
elif cur > 3.5:
    print('状态: 🟡 中等收益率')
else:
    print('状态: 🔴 低收益率 → 美元吸引力弱')
print()
print('近5日:')
for i in range(len(idx)):
    dt = datetime.fromtimestamp(idx[i], tz=timezone.utc).strftime('%m-%d')
    o = quotes['open'][i]
    c = quotes['close'][i]
    chg = c - o if o else 0
    emoji = '🟢' if chg>=0 else '🔴'
    print(f'{dt} {emoji} O:{o:.3f}% C:{c:.3f}% {chg:+.3f}bp')
"

# === 5Y 美债收益率 (^FVX) ===
curl -s -H "User-Agent: Mozilla/5.0" "https://query1.finance.yahoo.com/v8/finance/chart/%5EFVX?interval=1d&range=5d" | python3 -c "
import json, sys
d = json.load(sys.stdin)['chart']['result'][0]
meta = d['meta']
prev = meta.get('chartPreviousClose', 0)
cur = meta.get('regularMarketPrice', 0)
print('=== 📈 5Y 美债收益率 (^FVX) ===')
print(f'当前: {cur:.3f}% | 前收: {prev:.3f}% | 变动: {cur-prev:+.3f} bp' if prev else f'当前: {cur:.3f}%')
# 2s10s 利差判断（简化：10Y - 5Y 近似）
spread = cur - prev if prev else 0
if cur < 3.5:
    print('状态: 利率预期偏鸽')
elif cur > 4.5:
    print('状态: 利率预期偏鹰')
"

# === 利差概览（10Y - 2Y 代理 = ^TNX - ^FVX 作为弱近似） ===
curl -s -H "User-Agent: Mozilla/5.0" "https://query1.finance.yahoo.com/v8/finance/chart/%5ETNX?interval=1d&range=2d" | python3 -c "
import json, sys
d = json.load(sys.stdin)['chart']['result'][0]
meta = d['meta']
tnx = meta.get('regularMarketPrice', 0)
" && curl -s -H "User-Agent: Mozilla/5.0" "https://query1.finance.yahoo.com/v8/finance/chart/%5EFVX?interval=1d&range=2d" | python3 -c "
import json, sys
d = json.load(sys.stdin)['chart']['result'][0]
meta = d['meta']
fvx = meta.get('regularMarketPrice', 0)
print(f'当前 10Y (^TNX): -- (需要结合上一条) / 5Y (^FVX): {fvx:.3f}%')
" 2>/dev/null || true
echo "注：10Y-2Y 利差精确值需 ^IRX (13W) + ^FVX (5Y) + ^TNX (10Y) 组合计算，此处仅拉取 TNX 和 FVX 作为方向性参考"
```

---

### 块 3：交叉验证（相关货币对 + 黄金 + 原油）⚠️ 必查

> 单一货币对可能被操纵或受本地事件干扰。必须用相关资产交叉验证。

```bash
# === 交叉盘验证：EURUSD 查看 GBPUSD、USDCHF；USDJPY 查看 EURJPY 等 ===
# 以下拉取主要关联品种，根据分析标的选取 2-3 个

# 欧元交叉验证（EURUSD 场景）
echo "=== 🔍 交叉验证：欧元区 ==="
curl -s -H "User-Agent: Mozilla/5.0" "https://query1.finance.yahoo.com/v8/finance/chart/GBPUSD=X?interval=1d&range=2d" | python3 -c "
import json, sys
d = json.load(sys.stdin)['chart']['result'][0]
m = d['meta']
print(f'GBPUSD: {m.get(\"regularMarketPrice\",\"?\"):.5f} (前收:{m.get(\"chartPreviousClose\",0):.5f})')
"
curl -s -H "User-Agent: Mozilla/5.0" "https://query1.finance.yahoo.com/v8/finance/chart/CHF=X?interval=1d&range=2d" | python3 -c "
import json, sys
d = json.load(sys.stdin)['chart']['result'][0]
m = d['meta']
print(f'USDCHF: {m.get(\"regularMarketPrice\",\"?\"):.5f} (前收:{m.get(\"chartPreviousClose\",0):.5f})')
"

# 日元交叉验证（USDJPY 场景）
echo "=== 🔍 交叉验证：日元区 ==="
curl -s -H "User-Agent: Mozilla/5.0" "https://query1.finance.yahoo.com/v8/finance/chart/EURJPY=X?interval=1d&range=2d" | python3 -c "
import json, sys
d = json.load(sys.stdin)['chart']['result'][0]
m = d['meta']
print(f'EURJPY: {m.get(\"regularMarketPrice\",\"?\"):.3f}')
"
curl -s -H "User-Agent: Mozilla/5.0" "https://query1.finance.yahoo.com/v8/finance/chart/GBPJPY=X?interval=1d&range=2d" | python3 -c "
import json, sys
d = json.load(sys.stdin)['chart']['result'][0]
m = d['meta']
print(f'GBPJPY: {m.get(\"regularMarketPrice\",\"?\"):.3f}')
"

# 商品货币交叉验证（AUDUSD 场景）
echo "=== 🔍 交叉验证：商品货币区 ==="
curl -s -H "User-Agent: Mozilla/5.0" "https://query1.finance.yahoo.com/v8/finance/chart/NZDUSD=X?interval=1d&range=2d" | python3 -c "
import json, sys
d = json.load(sys.stdin)['chart']['result'][0]
m = d['meta']
print(f'NZDUSD: {m.get(\"regularMarketPrice\",\"?\"):.5f}')
"

# 美元兑人民币（USDCNH 场景）
echo "=== 🔍 交叉验证：人民币区 ==="
curl -s -H "User-Agent: Mozilla/5.0" "https://query1.finance.yahoo.com/v8/finance/chart/USDCNY=X?interval=1d&range=2d" | python3 -c "
import json, sys
d = json.load(sys.stdin)['chart']['result'][0]
m = d['meta']
print(f'USDCNY (在岸): {m.get(\"regularMarketPrice\",\"?\"):.5f}')
"

# === 黄金（避险代理）===
curl -s -H "User-Agent: Mozilla/5.0" "https://query1.finance.yahoo.com/v8/finance/chart/GC=F?interval=1d&range=5d" | python3 -c "
import json, sys
d = json.load(sys.stdin)['chart']['result'][0]
m = d['meta']
prev = m.get('chartPreviousClose', 0)
cur = m.get('regularMarketPrice', 0)
print('=== 🥇 黄金期货 (GC=F) ===')
print(f'当前: \${cur:,.1f} | 前收: \${prev:,.1f} | 变动: {(cur-prev)/prev*100:+.2f}%' if prev else f'当前: \${cur:,.1f}')
if cur > prev * 1.01:
    print('黄金走强 → 避险需求上升 / 美元预期走弱')
elif cur < prev * 0.99:
    print('黄金走弱 → risk-on / 美元预期走强')
"

# === 原油（通胀/风险代理）===
curl -s -H "User-Agent: Mozilla/5.0" "https://query1.finance.yahoo.com/v8/finance/chart/CL=F?interval=1d&range=5d" | python3 -c "
import json, sys
d = json.load(sys.stdin)['chart']['result'][0]
m = d['meta']
prev = m.get('chartPreviousClose', 0)
cur = m.get('regularMarketPrice', 0)
print('=== 🛢️ 原油期货 (CL=F) ===')
print(f'当前: \${cur:,.1f} | 前收: \${prev:,.1f} | 变动: {(cur-prev)/prev*100:+.2f}%' if prev else f'当前: \${cur:,.1f}')
"
```

---

### 块 4：情绪面（VIX + Fear & Greed）

```bash
# === VIX 恐慌指数（外汇核心情绪指标）===
curl -s -H "User-Agent: Mozilla/5.0" "https://query1.finance.yahoo.com/v8/finance/chart/%5EVIX?interval=1d&range=5d" | python3 -c "
import json, sys
from datetime import datetime, timezone
d = json.load(sys.stdin)['chart']['result'][0]
meta = d['meta']
quotes = d['indicators']['quote'][0]
idx = d['timestamp']
prev = meta.get('chartPreviousClose', 0)
cur = meta.get('regularMarketPrice', 0)
print('=== 😨 VIX 恐慌指数 ===')
print(f'当前: {cur:.1f} | 前日: {prev:.1f} | 变化: {(cur-prev)/prev*100:+.1f}%' if prev else f'当前: {cur:.1f}')
if cur < 15:
    print('状态: 🟢 安逸 → risk-on → 利好 AUD/NZD，利空 JPY/CHF')
elif cur < 20:
    print('状态: 🟡 正常 → 中性')
elif cur < 30:
    print('状态: 🟠 担忧 → risk-off → 利好 JPY/CHF，利空 AUD/NZD')
else:
    print('状态: 🔴 恐慌 → 避险模式 → JPY/CHF 走强，套利货币暴跌')
print()
print('近5日 VIX:')
for i in range(len(idx)):
    dt = datetime.fromtimestamp(idx[i], tz=timezone.utc).strftime('%m-%d')
    c = quotes['close'][i]
    if c is not None:
        emoji = '🟢' if c < 15 else '🟡' if c < 20 else '🟠' if c < 30 else '🔴'
        print(f'{dt} {emoji} {c:.1f}')
"

# === Fear & Greed 指数（Alternative.me，弱参考）===
curl -s "https://api.alternative.me/fng/?limit=3" | python3 -c "
import json, sys
data = json.load(sys.stdin)['data']
print('=== 😱 Fear & Greed（弱参考）===')
for d in data:
    val = int(d['value'])
    cls = d['value_classification']
    bar = '█' * (val // 5) + '░' * (20 - val // 5)
    print(f'{d[\"timestamp\"]}: {val:3d} [{bar}] {cls}')
print('注：外汇市场 Fear & Greed 仅作弱参考，主要看 VIX')
"
```

---

### 块 5：宏观基本面（央行日历 + 经济数据 + 新闻）⚠️ 必查

> 外汇的命脉在央行。宏观块是外汇分析中权重最高的数据源之一。

```bash
# === Google News RSS：货币对相关硬新闻 ===
# 替换 CURRENCY_PAIR_QUERY 为实际搜索词
# EURUSD → "EURUSD+OR+ECB+OR+Fed+OR+euro+dollar"
# USDJPY → "USDJPY+OR+BOJ+OR+yen+OR+Japan+rate"
# GBPUSD → "GBPUSD+OR+BOE+OR+sterling+OR+UK+inflation"
# AUDUSD → "AUDUSD+OR+RBA+OR+Australian+dollar"
# USDCNH → "USDCNH+OR+PBOC+OR+yuan+OR+China+central+bank"
# DXY → "Dollar+Index+OR+DXY+OR+Federal+Reserve"

curl -s "https://news.google.com/rss/search?q=CURRENCY_PAIR_QUERY+when:1d&hl=en-US&gl=US&ceid=US:en" | python3 -c "
import sys, html, xml.etree.ElementTree as ET
root = ET.fromstring(sys.stdin.read())
items = root.findall('./channel/item')
print('=== 📰 货币对相关新闻（Google News RSS）===')
for i, item in enumerate(items[:5], 1):
    title = html.unescape(item.findtext('title', '')).strip()
    source = item.findtext('source', '').strip()
    pub = item.findtext('pubDate', '').strip()
    print(f'{i}. {title}')
    print(f'   {source} | {pub}')
"

# === Google News RSS：央行/宏观事件级 ===
curl -s "https://news.google.com/rss/search?q=central+bank+(Fed+OR+ECB+OR+BOJ+OR+BOE)+interest+rate+when:3d&hl=en-US&gl=US&ceid=US:en" | python3 -c "
import sys, html, xml.etree.ElementTree as ET
root = ET.fromstring(sys.stdin.read())
items = root.findall('./channel/item')
print()
print('=== 🏛️ 央行/利率宏观新闻（Google News RSS）===')
for i, item in enumerate(items[:5], 1):
    title = html.unescape(item.findtext('title', '')).strip()
    source = item.findtext('source', '').strip()
    pub = item.findtext('pubDate', '').strip()
    print(f'{i}. {title}')
    print(f'   {source} | {pub}')
"

# === 美联储相关新闻 ===
curl -s "https://news.google.com/rss/search?q=Federal+Reserve+(rate+OR+inflation+OR+employment+OR+GDP)+when:3d&hl=en-US&gl=US&ceid=US:en" | python3 -c "
import sys, html, xml.etree.ElementTree as ET
root = ET.fromstring(sys.stdin.read())
items = root.findall('./channel/item')
print()
print('=== 🏦 美联储相关宏观新闻 ===')
for i, item in enumerate(items[:4], 1):
    title = html.unescape(item.findtext('title', '')).strip()
    source = item.findtext('source', '').strip()
    pub = item.findtext('pubDate', '').strip()
    print(f'{i}. {title}')
    print(f'   {source} | {pub}')
"

# === 经济数据日历（通过 Google News 搜索）===
echo ""
echo "=== 📅 经济数据提醒 ==="
echo "本周关键数据：NFP（每月第一个周五）、CPI（月中）、FOMC（约每6周）、PMI（月初）"
echo "请核对当前日期判断是否处于数据窗口期"
date -u '+当前UTC: %Y-%m-%d %H:%M'
```



### 块 5b：增强利率仪表盘 ⚠️ 新增（macro-rates-monitor 精简版）

> 外汇的核心驱动是利率路径。此块将块2（DXY+TNX+FVX）升级为完整的利率环境判断。
> 与块5并行拉取，不增加等待时间。

```python
# 增强利率仪表盘（Yahoo Finance，4符号 + 延迟防429）
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

# 利率环境判断
spread = tnx - fvx
real_10y = tnx - 2.8
print(f'\n2s10s(proxy): {spread:+.0f}bp | Real10Y(est): {real_10y:.1f}%')
print(f'DXY: {dxy:.1f} ({dxy_chg:+.2f}%) | VIX: {vix:.1f}')

# 利率路径判断
if real_10y > 1.5: regime = 'RESTRICTIVE -> USD supportive, risk assets pressured'
elif real_10y > 0.5: regime = 'NEUTRAL'
else: regime = 'ACCOMMODATIVE -> USD weakening, risk assets benefit'
print(f'Rate Regime: {regime}')

# FOMC日历
print('FOMC: Jun 17-18, 2026 (next)')
print('RATE PATH: Fed at 4.25-4.50%, market pricing ~85% hold')
```

**块5b执行规则**：
- 报告中输出 2 行：利率环境 + FOMC日历
- 利率路径判断优先级：real rate regime > 2s10s slope > absolute yield level
- 429 时标注「宏观数据暂缺」，使用上一交易日数据作参考
- FOMC 48h内 → 宏观权重 > 技术面

---

**新闻块执行规则：**
- 默认从 3 路 RSS 里提炼 `2-4` 条真正影响交易判断的新闻，不要把整屏标题搬进最终报告
- `price today / current price / prediction / forecast / technical analysis / opinion / recap` 这类标题默认降权
- `Fed / ECB / BOJ / BOE / rate decision / inflation / NFP / GDP / PMI / central bank / hike / cut` 这类带明确事件主体的标题优先保留
- 同一事件若被多家媒体重复转载，只保留最接近原始事件的一条
- 如果没有筛出明确硬新闻，就写"新闻面无央行级强驱动，主要是价格播报/观点稿"，不要硬凑事件
- 注意当前是否处于重大数据窗口期（NFP 周、FOMC 周、CPI 周）

---

## 五、严格输出模板（不可偏离）

```markdown
## 🎯 [货币对标签，如 EUR/USD] 外汇交易决策

**分析时间（UTC）**：[YYYY-MM-DD HH:MM]

### 方向：🟢 做多 / 🔴 做空 / ⚪ 观望

**一句话理由**：[最核心的结构依据 + 利率/美元驱动，一句话说清楚]
**数据完整性**：[完整 / 缺少哪几块；若关键块缺失则只能观望]
**宏观时效性**：[外汇 24h 连续交易，央行/数据窗口前后 headline 权重高于图形]
**主导宏观因子**：[Fed / ECB / BOJ / DXY / 10Y 收益率 / VIX 避险]

### 历史轨迹复盘
- 最近 `30D 4H` 主导手法：[趋势推进 / 箱体洗盘 / 冲高派发 / 跌破回收 / 阴跌磨人]
- 最近关键动作：[列出 2-3 次关键轨迹动作 + 时间]
- 今天更像：[延续 / 回踩 / 诱多 / 诱空 / 纯噪音]

### 结构依据
- 最近结构摆点：[higher low / lower high，具体价位和形成时间]
- 当前形态：[楔形/旗形/双底/头肩/区间等]
- 量价状态：[放量/缩量 + 方向 → 健康/危险，或标注外汇无集中成交量]

### 📐 增强利率仪表盘
- 利率：10Y X.X% | 5Y X.X% | 实际利率 X.X%（限制性/中性/宽松）
- DXY：XX.X (日变 ±X.X%) | VIX：XX.X
- FOMC：下次 X月X日（N天后）| 事件窗口：[是/否]

### 主导力量立场
- DXY：[数值 + 方向 + 强弱判断]
- 10Y 收益率：[数值 + 方向 + 对货币对的影响]
- 央行路径：[Fed vs 对手央行的政策预期差]
- CFTC / 市场持仓：[如有数据，杠杆基金偏多/偏空]
- 本周高影响事件：[NFP Week / FOMC Week / CPI Week / 暂无]

### 八维判断
- 技术面：[多周期结构、关键位、形态]
- 利差与美元结构：[利差预期、DXY 方向、避险结构]
- 主导力量：[央行路径 + 收益率差 + 美元强弱]
- 情绪面：[VIX + risk-on/risk-off 判断]
- 宏观面：[央行窗口期、核心数据、事件驱动]
- 交叉验证：[DXY 一致/背离、相关货币对、黄金/原油]
- 仓位/CFTC：[杠杆基金/资产管理净头寸]
- 缠论结构：[CZSC 确认/冲突/不足 + 中枢/笔/背驰]

### 💰 止盈止损计划

| 项目 | 价位 | 结构依据 |
|------|------|---------|
| **入场** | X.XXXXX | [当前区间 + 结构位支撑/压力] |
| **🔴 SL** | X.XXXXX（-X.X%） | [**锚定的结构位名称 + 形成时间**] |

| 级别 | 平仓% | 触发价 | 盈利% | 结构依据 |
|------|-------|--------|-------|---------|
| 🔴 SL | 全部 | X.XXXXX | -X.X% | [结构位名称] |
| 🟡 TP1 | 30% | X.XXXXX | +X.X% | [结构位名称] |
| 🟠 TP2 | 30% | X.XXXXX | +X.X% | [结构位名称] |
| 🟢 TP3 | 40% | X.XXXXX | +X.X% | [结构位名称] |

### 移动止损
- 到 TP1 → 移损至开仓价
- 到 TP2 → 移损至 TP1
- 创新高/低 → 跟踪最近 2 根 4H K 线的结构摆点

### 仓位
- 风险金额 ÷ |入场价 - SL| = 可开仓位
- 以 $10,000 账户 2% 风险为例：**X.XX 标准手（或 X,XXX 单位）**
- 注意：若使用标准手（100k 单位），需换算

### 失效条件（不等止损，手动离场）
1. [客观条件 1，如：4H 收盘跌破 X.XXXXX 并未快速收回]
2. [客观条件 2，如：DXY 与收益率同时反向突破关键位]
3. [客观条件 3，如：央行/宏观消息显著改写利率或美元叙事，可选]

### 禁止事项
- ❌ 止损后立即反向开仓
- ❌ 浮盈加仓（除非趋势非常明确，且有新高/低确认）
- ❌ 在重大数据公布前 30 分钟开新仓
- ❌ 把货币强弱观点和交易对方向混为一谈
- ❌ 一天超过 3 笔交易

### 新闻观察
- [硬新闻 1 | 来源]
- [硬新闻 2 | 来源]

### 免责声明
以上分析基于公开数据，不构成投资建议。外汇交易存在重大风险。
```

---

## 六、决策检查清单

- [ ] 已标注分析时间（UTC）与数据缺口
- [ ] 已确认货币对标准化（EURUSD / USDJPY 等）
- [ ] 已复盘最近 `30D 4H` 主导手法
- [ ] 已说明今天更像延续、回踩还是陷阱
- [ ] 最近结构摆点是 higher low 还是 lower high？
- [ ] 引用的 `4H/1H` 结构位是否都来自**已收盘 K 线**？未收盘 K 线只能写「临时高/低」，不得写成已确认摆点
- [ ] 如果写了「连续 lower highs / higher lows」，对应价位序列是否真的单调？
- [ ] DXY 方向与货币对方向是否一致？不一致是否已解释？
- [ ] 10Y 收益率方向是否支持当前判断？
- [ ] 央行路径差是否与交易方向一致？
- [ ] VIX 水平是否支持当前风险偏好假设？
- [ ] 当前价格是否已经贴近最近阻力/支撑，导致盈亏比不足 1.5？
- [ ] SL 锚定哪个结构位？什么时候形成的？
- [ ] TP1/TP2/TP3 各锚定哪个结构位？
- [ ] 入场价、SL、TP1/TP2/TP3 的盈利/亏损百分比、加权盈亏比、仓位示例是否已逐项复核算术一致？
- [ ] 失效条件是否客观可观察？
- [ ] 当前是否处于央行决议 / NFP / CPI 数据窗口期？如是，宏观权重大于技术面
- [ ] 当前是否周末？DXY 和美债收益率是否只是前收参考？
- [ ] 新闻是否是硬新闻，而不是评论稿/技术分析文章/标题党？
- [ ] 仓位在风控范围内（2%）？
- [ ] 已检查货币对专属逻辑（见第九节）
- [ ] 🆕 利率环境判断：real rate regime + 2s10s slope？
- [ ] 🆕 FOMC/CPI/NFP 事件窗口已标注？

---

## 七、常见错误（禁止清单）

| 错误 | 正确做法 |
|------|---------|
| ❌ 用 24h 高/低点做 SL/TP | ✅ 用独立的结构摆点（前高/前低、趋势线、颈线） |
| ❌ 「跌 30 pips 止损」统一套用 | ✅ 止损锚定最近结构低点下方 0.15-0.25%，各货币对波动率不同 |
| ❌ 给两个方向让用户选 | ✅ 只给一个方向（做多/做空/观望） |
| ❌ 不确定时硬说一个方向 | ✅ 诚实输出「观望」并说明分歧在哪 |
| ❌ SL 太近被扫掉 | ✅ 留 0.15-0.25% 缓冲，放在结构位外侧 |
| ❌ TP 设得太远不切实际 | ✅ 每个 TP 都有明确的结构依据 |
| ❌ 把「美元走强」直接等同于做多 USDXXX | ✅ 先看对手货币的驱动：USDJPY 受美债收益率主导，AUDUSD 受风险偏好主导 |
| ❌ 忽略央行路径只看 K 线 | ✅ K 线 + 利率/美元方向 = 完整判断 |
| ❌ 所有货币对用同样的止损宽度 | ✅ GBPUSD 波动 > EURUSD，USDCNH 有管理波动，各自调整 |
| ❌ 用采样价格拼接假 K 线后精确卡止损 | ✅ 日内执行优先读取 Yahoo Finance 1H 真实 OHLC |
| ❌ 只看当前截面，不复盘最近 30 日轨迹 | ✅ 先判断这个货币对平时怎么走，再解释今天的波动 |
| ❌ 在重大数据公布前追单 | ✅ 数据前 30 分钟自动降级为观望 |
| ❌ 把周末 DXY 前收当实时盘中联动 | ✅ 明确标注休市，只把宏观块当背景过滤 |
| ❌ 在主要阻力前追多 / 主要支撑前追空 | ✅ 等回踩/反抽；盈亏比不够就观望 |
| ❌ 把评论稿/技术分析文章当成事件驱动 | ✅ 优先使用有明确时间、事件主体、来源的硬新闻 |
| ❌ 把未收盘 K 线写成已确认的 4H/1H 摆点或形态 | ✅ 未收盘只能写「临时高/低」 |
| ❌ 把不单调的价格序列写成「连续 lower highs / higher lows」 | ✅ 逐个核对摆点；序列不干净就改写 |
| ❌ 做 USDJPY 不看美债收益率 | ✅ USDJPY 第一驱动是美债收益率，第二才是 BOJ |
| ❌ 做 USDCNH 不看中美利差和政策管理 | ✅ 人民币有管理浮动，政策干预风险不可忽略 |
| ❌ TP%、SL%、加权 RR、仓位示例算数互相打架 | ✅ 发布前逐项复核百分比与仓位公式 |

---

## 八、货币对差异

| 维度 | EURUSD | USDJPY | GBPUSD | AUDUSD | USDCNH | DXY |
|------|--------|--------|--------|--------|--------|-----|
| 日均波动 | 中 (~0.5%) | 中高 (~0.7%) | 高 (~0.7%) | 中高 (~0.7%) | 低 (~0.3%) | 低 (~0.4%) |
| 第一驱动 | Fed vs ECB | 美债收益率 | BOE + 通胀 | 中国/风险偏好 | 中美利差 | Fed 路径 |
| 止损缓冲 | 0.15-0.20% | 0.20-0.25% | 0.20-0.30% | 0.20-0.25% | 0.10-0.15% | 0.10-0.15% |
| 结构周期 | 4H/日线为主 | 4H/日线为主 | 4H/1H 为主 | 4H/1H 为主 | 日线为主 | 日线为主 |
| 宏观事件敏感 | FOMC + ECB + NFP | FOMC + BOJ + NFP | BOE + UK CPI + FOMC | RBA + 中国数据 | PBOC + 中美事件 | FOMC + NFP + CPI |
| 操纵/干预风险 | 低 | 中（BOJ 干预） | 低 | 低 | 高（PBOC 管理） | 极低 |
| 交易风格 | 日内+波段 | 日内+波段 | 日内为主 | 日内+波段 | 波段为主 | 波段/宏观 |
| 避险属性 | 中性 | 日元避险 | 中性 | 风险货币 | 管理货币 | 避险+宏观 |

---

## 九、货币对专属逻辑

### EURUSD
- **核心驱动**：Fed 路径 vs ECB 路径的相对预期差
- **关键变量**：美德利差（10Y Bund vs 10Y UST）、DXY、欧元区政治风险（如法德选举、意大利预算）
- **主导逻辑**：Fed 鹰 + ECB 鸽 = EURUSD ↓；Fed 鸽 + ECB 鹰 = EURUSD ↑
- **需要关注的交叉盘**：EURGBP、EURJPY、EURCHF
- **关键数据**：欧元区 CPI、德国 IFO/ZEW、美国 NFP/CPI、FOMC + ECB 会议
- **特别注意**：EURUSD 在 1.05-1.10 之间经常形成长期区间，突破需要强宏观驱动

### USDJPY
- **核心驱动**：美债 10Y 收益率（第一驱动），BOJ 政策与干预风险（第二驱动）
- **关键变量**：10Y UST 收益率、美日利差、日本央行收益率曲线控制（YCC）政策
- **主导逻辑**：10Y ↑ + BOJ 鸽 = USDJPY ↑；10Y ↓ + BOJ 鹰/干预 = USDJPY ↓
- **需要关注的交叉盘**：EURJPY、GBPJPY、AUDJPY
- **关键数据**：日本 CPI、BOJ 会议、日本 GDP、美国 NFP/CPI
- **特别注意**：150 以上有 BOJ 口头/实际干预风险；140 以下市场关注 BOJ 是否转向
- **避险逻辑**：全球 risk-off → JPY 走强 → USDJPY 下跌（即使美元也强，日元避险属性更强）

### GBPUSD
- **核心驱动**：英国通胀路径 + BOE 利率政策 vs Fed
- **关键变量**：UK CPI、BOE 投票比、英国 GDP、脱欧后续/政治风险
- **主导逻辑**：UK CPI 顽固 + BOE 鹰 = GBPUSD ↑；UK 衰退 + BOE 鸽 = GBPUSD ↓
- **需要关注的交叉盘**：EURGBP（反映英镑相对欧元强弱）
- **关键数据**：UK CPI、UK GDP、BOE 会议、UK 零售销售
- **特别注意**：GBPUSD 波动率在主要货币对中最高，止损必须适当放宽
- **政治风险**：英国政治变动（首相更迭、预算案）可引发单日 1%+ 波动

### AUDUSD
- **核心驱动**：中国需求 + 全球风险偏好 + 大宗商品
- **关键变量**：铁矿石/铜价、中国 PMI/GDP、RBA 政策、全球股市
- **主导逻辑**：中国刺激 + risk-on + 大宗涨 = AUDUSD ↑；中国疲软 + risk-off = AUDUSD ↓
- **需要关注的交叉盘**：AUDJPY、AUDNZD、NZDUSD
- **关键数据**：中国 PMI/GDP/贸易数据、澳洲就业/CPI、RBA 会议
- **特别注意**：AUD 是典型的「风险货币」，VIX 升高时 AUDUSD 倾向下跌
- **套利**：AUD 相对高息，在低波动环境下有套利资金流入；高波动时套利平仓

### USDCNH
- **核心驱动**：中美利差 + PBOC 管理意图
- **关键变量**：USDCNY 中间价、CFETS 人民币指数、中美 10Y 利差
- **主导逻辑**：中美利差扩大 + PBOC 容忍贬值 = USDCNH ↑；利差收窄 + PBOC 捍卫 = USDCNH ↓
- **需要关注的交叉盘**：USDCNY（在岸）、EURCNH、JPYCNH
- **关键数据**：PBOC LPR/MLF 操作、中国贸易数据/外汇储备、美国对华政策
- **特别注意**：
  - USDCNH 有管理浮动特征，单边趋势可能被 PBOC 干预打断
  - CNH 中间价偏离前收超过 500 pips 时，关注政策信号
  - 中美关系/关税事件可引发快速波动
  - CNH 流动性在亚洲时段最好，纽约时段流动性下降

### DXY（美元指数）
- **核心驱动**：Fed 利率路径 + 全球风险偏好
- **关键变量**：FOMC 点阵图、美国经济数据 vs 预期、全球避险需求
- **主导逻辑**：Fed 鹰 + 美国经济强 = DXY ↑；Fed 鸽 + 美国经济弱 + 全球 risk-on = DXY ↓
- **关键成分权重**：EUR 57.6%、JPY 13.6%、GBP 11.9%、CAD 9.1%、SEK 4.2%、CHF 3.6%
- **关键数据**：FOMC、NFP、CPI、GDP、ISM PMI
- **特别注意**：
  - DXY 受 EUR 影响最大（近 58%），EURUSD 走势与 DXY 高度负相关
  - 避险时期美元和日元同时走强，DXY 上升
  - DXY 突破 105/107/110 整数关口往往触发趋势加速
  - 分析 DXY 不适合做日内短线，更适合做宏观方向判断

---

## 十、数据采集可靠性（必读）

**核心问题：** 技能中 `curl | python3 -c "..."` 的数据块在 Hermes `terminal()` 执行时，f-string 内的特殊字符（引号 `'"`、花括号 `{}`、冒号 `:`、emoji）会被 shell 错误转义，导致约 40% 的数据块首次运行失败（`SyntaxError: f-string: invalid syntax`、`unterminated string literal`）。

**可靠做法（按优先级）：**
1. **首选**：当环境支持 `execute_code` 时，用 Python 原生 `urllib.request` 替代 `curl | python3 -c`，彻底避开 shell 转义。示例：
   ```python
   from hermes_tools import terminal
   r = terminal("""python3 -c "
   import json, urllib.request
   d = json.load(urllib.request.urlopen('https://query1.finance.yahoo.com/v8/finance/chart/EURUSD=X?interval=1d&range=5d'))
   print(d['chart']['result'][0]['meta']['regularMarketPrice'])
   " """)
   ```
2. **次选**：如果必须用 `curl | python3 -c`，f-string 中避免使用 emoji、花括号格式化、嵌套引号。用 `+` 拼接或 `%` 格式化代替。
3. **重试策略**：数据块失败时，先降级为更简单的 Python（去掉格式化，只打原始值），不要反复用同一段会失败的代码重试。补拉时用独立 `python3` 脚本而非 bash 管道。
4. **并行执行**：独立的数据块用多个并行 `execute_code` 调用同时拉取，不要串行等待。

**已知脆弱的块：** 块 1.2（30D 4H 轨迹，f-string 含 `%m-%d %H:%M`）、块 1.5（4H/1H 蜡烛聚合）、块 5（Yahoo Finance 偶发 429/空响应）。这些块首次失败率高，优先用 Python 原生方案重试。

**Yahoo Finance 特殊注意：**
- `query1.finance.yahoo.com` 可能返回 429（频率限制）。解决：4 符号 + 0.5s 延迟；触发 429 时停止补抓，用上一交易日数据参考（频率限制），此时减少请求频率或加大间隔
- 外汇对在周末可能返回 `null` 或最后交易日的 stale 数据——这是正常的
- `regularMarketPrice` 在美股休市期间可能不是实时价，需要标注

---

## 十一、与 crypto-market-analysis 的主要差异

| 维度 | 加密货币 | 外汇 |
|------|---------|------|
| 核心驱动 | 庄家合力（OI+费率） | 央行路径+利率差 |
| 技术面权重 | 40% | 30% |
| 宏观权重 | 15% | 35% |
| 情绪指标 | 恐惧贪婪指数 | VIX |
| 市场结构 | 链上数据 | DXY+利差 |
| 交叉验证 | 多交易所比价 | DXY+交叉盘+关联资产 |
| 庄家行为 | OI+多空比+费率 | CFTC 持仓（如有） |
| 数据源优先级 | CoinGecko/Binance | Yahoo Finance |
| 交易时间 | 24/7 | 24/5（周末休市） |
| 波动特征 | 极高 | 中低（相对） |
| 止损间距 | 0.2-0.3% | 0.15-0.30%（因货币对而异） |

---

## 附：快速参考卡片

### 货币对 → Yahoo Finance 代码
| 货币对 | Yahoo 代码 | 
|--------|-----------|
| EURUSD | `EURUSD=X` |
| USDJPY | `JPY=X` |
| GBPUSD | `GBPUSD=X` |
| AUDUSD | `AUDUSD=X` |
| NZDUSD | `NZDUSD=X` |
| USDCHF | `CHF=X` |
| USDCAD | `CAD=X` |
| USDCNH | `CNH=X` |
| DXY | `DX-Y.NYB` |

### 代理/关联资产 → Yahoo 代码
| 资产 | Yahoo 代码 |
|------|-----------|
| 10Y UST | `^TNX` |
| 5Y UST | `^FVX` |
| VIX | `^VIX` |
| 黄金期货 | `GC=F` |
| 原油期货 | `CL=F` |
| 标普500 | `^GSPC` |
| 纳斯达克 | `^IXIC` |
| 道琼斯 | `^DJI` |

### 仓位公式速算
```
$10,000 账户，2% 风险 = $200
仓位 = $200 / |entry - SL|

示例（EURUSD）：
入场 1.08500，SL 1.08200（结构低点下方 0.2%）
风险 = 0.00300 = 30 pips
仓位 = 200 / 0.00300 = 66,667 单位 ≈ 0.67 标准手
```

### 货币对专属止损参考（最小缓冲，仍需结构位调整）
| 货币对 | 最小缓冲 | 典型 pips |
|--------|---------|----------|
| EURUSD | 0.15% | 15-18 |
| USDJPY | 0.20% | 25-35 |
| GBPUSD | 0.25% | 25-35 |
| AUDUSD | 0.20% | 12-18 |
| USDCNH | 0.12% | 80-120 |
| DXY | 0.10% | 10-12 |
