---
name: futures-market-analysis
description: "商品期货、贵金属、能源、股指期货八维分析：1-7维先形成主判断，第8维用CZSC缠论确认/冲突/不足；覆盖 CL/BZ/GC/SI/HG/NG/PL/PA/ES/NQ/YM/RTY，并识别 Binance TradFi 商品永续 CLUSDT/BZUSDT/XAUUSDT/XAGUSDT/COPPERUSDT/NATGASUSDT/XPTUSDT/XPDUSDT 的K线、资金费率、OI、多空比。"
---

# 期货市场八维分析全流程

> ⛔ 铁律：你不是在写行情播报，你是在做法医解剖。每句话必须回答"为什么"。禁止"可能""或许""值得关注"。每个数据必须有对比基准。每个判断必须有因果链。

> **核心理念：期货价格由宏观驱动 + 供需基本面 + 市场结构共同决定。**
> 地缘政治和库存数据可在瞬间覆盖所有技术位。技术分析在期货中的权重远低于加密货币——不可颠倒。

---


> **⛔ 禁止调用 mcp_yfinance 系列工具**：Yahoo Finance 频繁 429。所有数据通过 `scripts/` 目录下的 fetch 脚本获取（内置延迟+重试）。模型不要额外调 `mcp_yfinance_get_historical_stock_prices` 等 MCP 工具。

## 一、铁律（不可违反）

### 1. 只输出一个方向
- 🟢 做多 或 🔴 做空 或 ⚪ 观望
- **禁止**给「如果…则做多，如果…则做空」
- 观望也是合法的输出——当地缘/事件风险主导且方向质量差时，诚实说「观望」

### 2. 止盈止损必须锚定客观技术结构
- ✅ 允许参考的结构：前高/前低（独立摆点）、形态颈线、趋势线交点、斐波那契回撤位、密集成交区上沿/下沿、EMA21/EMA55
- ❌ **禁止**使用：24h 最高/最低点、今日开盘价、「跌 2% 就走」等固定百分比、任何以时间为边界而非结构为边界的价位
- 每一个 SL/TP 价位必须在报告中标注「结构依据」——具体说明这是哪个结构、什么时候形成的

### 3. 止损幅度由结构决定
- 做多止损：放在最近关键结构低点下方 0.2%-0.3%
- 做空止损：放在最近关键结构高点上方 0.2%-0.3%
- 期货跳空风险高于加密——止损可适当放宽 0.1%-0.2%（共 0.3%-0.5%），但仍必须锚定结构位
- 止损幅度不由百分比决定（但如果结构决定的幅度超过账户风控上限，需特别标注风险，建议减小仓位而非放宽止损）

### 4. 必须带失效条件
- 至少 2 个明确的「不等止损、立即手动平仓」的条件
- 失效条件必须是客观可观察的（K 线收盘、OVX/VIX 异动、关键新闻事件升级、关联市场破位等）

### 5. 数据缺口必须降级处理
- 报告开头必须标注**分析时间（UTC）**
- 若 Yahoo Finance 返回 429、4xx、空数据或结构变更，先减少请求并复用已拉取数据；仍失败则停止补抓，**绝不编造**
- 技术结构、波动率代理、交叉验证三项里只要缺 1 项，默认降级为 ⚪ 观望
- 新闻、库存等非关键块缺失时，可继续分析，但必须明确写出「数据缺口」
- 若处于周末或美国节假日，期货电子盘虽仍在交易但流动性极低，宏观块仅以最近收盘作背景参考
- COT 报告数据天然滞后 3 天，仅作中长期背景参考，**不得**用于日内决策

### 6. 先复盘轨迹，再谈方向
- 每做一个品种，必须先看它最近 `30D` 日线和 `4H` 轨迹是怎么走出来的，再看当前截面
- 必须回答：这个品种最近更像 `趋势推进 / 箱体洗盘 / 冲高派发 / 跌破回收 / 阴跌磨人` 里的哪一种
- 如果你连最近主导手法都说不清，就不能把当前波动解读为高置信度机会

### 7. 事件面前，技术面自动降权
- 一级事件（海峡关闭/全面战争）：技术面完全无效，强制 ⚪ 观望
- 二级事件（军事冲突升级/停火破裂）：技术面权重降至 10%，以事件方向为主
- 三级事件（停火谈判/库存数据/EIA/OPEC）：技术面权重降至 30%，等数据落地后确认
- 四级事件（常规供需/评论）：技术面保持正常权重

### 8. OVX 与价格背离 = 方向不可靠 ⚠️ CL 专属铁律

> 地缘危机中常见：价格暴跌后反弹 7-10%，但 OVX 纹丝不动。这种情况必须识破。

**经典陷阱：crash-and-bounce**
- 价格 3 小时跌 -12% → 随后反弹 +7%
- 但 OVX 仍停在 70+，完全未跟随回落
- **这不是利好驱动的趋势反转**——是空头回补 + 短线抄底的超卖修复
- **真正的趋势反转必须伴随 OVX 同步崩塌**（如 75→45 以下）
- 如果 OVX 不跌，恐慌未解除，不可据此做多

**OVX-价格背离速查：**
| 价格 | OVX | 真实含义 | 操作 |
|------|-----|---------|------|
| ↑ +7% | → 不动 | 🟡 超卖修复 | ⚪ 观望 |
| ↑ +7% | ↓ -20% | 🟢 恐慌消退 | 可考虑做多 |
| ↓ -10% | ↑ +15% | 🔴 恐慌加速 | 可考虑做空 |
| ↓ -10% | → 不动 | ⚪ 有序下跌 | 等 OVX 给出方向 |

### 10. 必须区分品种专属逻辑
- 不同品种的核心驱动完全不同：CL 看地缘和库存，GC 看实际利率和美元，股指看 Fed 和风险偏好
- 不能把原油的分析框架套到黄金上，也不能把股指的逻辑套到铜上
- 每个品种必须按「品种专属逻辑」一节中的优先级顺序排列驱动因素

### 11. 单交易所风险必须注明
- 期货主要在单一交易所（NYMEX/CME/COMEX）交易，没有多交易所交叉验证
- 必须在报告中标注「单交易所风险」，流动性异常时（如节假日前、重大事件前）降低仓位

---

## 二、八维分析框架

| # | 维度 | 期货对应项 | 核心关注 |
|---|------|-----------|---------|
| 1 | 📈 技术结构 | K线趋势、量价关系、支撑阻力、形态识别 | 90D/30D/24H 结构、摆点序列 |
| 2 | ⛓️ 可执行合约层 | Binance TradFi 永续 K线/OI/资金费率/多空比 | 交易层是否拥挤？可执行价格是否偏离指数？ |
| 3 | 🏛️ 传统期货结构 | 近月代理、CFTC、EIA、库存与基差背景 | 供需、套保、投机仓位是否支持方向？ |
| 4 | 🐋 主导力量 | OVX/VIX、ETF资金流、DXY、COT滞后参考 | 谁在定价？恐慌、供需还是宏观？ |
| 5 | 😱 情绪/波动率 | OVX/VIX、挤仓情绪、事件恐慌 | 波动率是否确认价格方向？ |
| 6 | 🌍 宏观与事件 | 地缘、利率、美元、EIA/OPEC/Fed | 地缘/库存/美元是否覆盖技术位？ |
| 7 | 🔍 交叉验证 | ETF、相关资产、美元、美债、现货代理 | 关联市场是否确认方向？ |
| 8 | 🧭 缠论结构 | CZSC 中枢、笔、背驰、买卖点候补 | 只做确认/冲突/不足，不能覆盖1-7维主判断 |

**强制输出规则**：
1. 先给 `七维主判断`，只基于第 1-7 维。
2. 再给 `缠论确认`，说明 CZSC 是确认、冲突还是不足。
3. 最终方向只能在主判断和第 8 维关系明确后输出；冲突或不足时降级为观望/等待触发。
4. 使用 `python3 -m hermes_finance analyze futures <SYMBOL>` 或 MCP `analyze_futures`，默认会尽量用采集器 K 线跑 CZSC。

---

## 三、决策流程（从数据到方向）

### 第零步：确认标的 + 执行前检查 ⚠️ 必做

```text
1. 记录分析时间（UTC）
2. 确认标的符号（CL=F / BZ=F / GC=F / SI=F / HG=F / NG=F / PL=F / PA=F / ES=F / NQ=F / YM=F / RTY=F）
3. 确认合约月份假设（默认近月代理，特别标注）
4. 检查是否处于重大事件窗口（EIA 库存日、OPEC 会议、FOMC、非农等）
```

**执行规则：**
- 用户给精确合约月份时，按用户给定
- 用户只给简称时，用近月代理 `{SYM}=F`，但要写明假设
- 用户给 Binance TradFi 商品永续时，先映射到期货 root：`CLUSDT -> CL`、`BZUSDT -> BZ`、`XAUUSDT -> GC`、`XAGUSDT -> SI`、`COPPERUSDT -> HG`、`NATGASUSDT -> NG`、`XPTUSDT -> PL`、`XPDUSDT -> PA`
- Binance TradFi 商品永续可作为可执行 K 线/资金费率/OI/多空比层；传统近月代理、CFTC、EIA、OVX/DXY 仍作为供需、宏观和传统期货验证层
- 如果当前处于一级或二级事件窗口，先判断是否需要强制观望
- 若当前价格已经贴近最近主阻力/主支撑，导致首个止盈空间过小、盈亏比低于 1.5，则不追价，等待回踩/反抽或直接观望

### 第一步：复盘这个品种最近的操盘手法（决定值不值得做）

**三层复盘窗口：**
```text
90D 日线轮廓 → 看大环境
30D 4H 轨迹 → 看主导手法
24H 1H 节奏 → 看今天是在延续、回踩还是诱多/诱空
```

**常见操盘手法分类：**
- `趋势推进`：higher highs + higher lows，回调浅，放量突破后缩量整理
- `箱体洗盘`：长时间区间震荡，上下插针多，真假突破反复出现
- `冲高派发`：急拉后高位横盘，长上影增多，放量却不再创新高
- `跌破回收`：先破关键位触发恐慌，再快速收回区间内部
- `阴跌磨人`：lower highs 持续，反弹弱，量能难以跟上

**执行规则：**
- 今天的判断必须和最近 `30D 4H` 主导手法对照，说明当前是**延续**还是**反着来收割**
- 若今天的短线信号和最近主导手法明显冲突，优先怀疑是假突破/假跌破
- 期货尤其注意：周末或节假日后的跳空开盘经常是「假突破」，等第一根 1H K 线收盘确认

### 第二步：判断趋势结构（决定能不能做）

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

### 第三步：判断主导力量（决定跟不跟）

**期货的主导力量判断逻辑（替代加密的 OI+费率）：**

| 主导力量信号 | 含义 | 操作 |
|-------------|------|------|
| OVX/VIX 下降 + 价格上升 | 恐慌消退 + 趋势健康 | 🟢 坚定做多 |
| OVX/VIX 上升 + 价格下降 | 恐慌定价 + 趋势加速 | 🔴 坚定做空 |
| OVX/VIX 上升 + 价格横盘 | 多空博弈加剧 | ⚠️ 观望，等突破确认 |
| ETF 资金净流入 + 价格上升 | 机构资金推动 | 🟢 趋势可信 |
| ETF 资金净流出 + 价格下降 | 机构资金撤离 | 🔴 趋势可信 |
| DXY 走强 + 商品价格走弱 | 美元压制（标准负相关） | 🔴 商品承压 |
| DXY 走弱 + 商品价格走强 | 美元支撑 | 🟢 商品受益 |

**COT 报告参考（仅中长期背景，不用于日内）：**
- 商业头寸（Commercials）通常正确
- 大型投机客（Large Specs）极度拥挤的方向 = 可能反转
- COT 数据天然滞后 3 天，**不得用于日内决策**

### 第四步：量价验证（决定时机对不对）

- 上涨放量 + 回调缩量 = 健康 → 可以进场
- 上涨缩量 + 下跌放量 = 危险 → 缓一缓
- 天量长上影/下影 = 反转预警 → 禁止进场
- 缩量至极（近 5 日均量的 50% 以下）= 变盘前兆 → 可进场但要快进快出

### 第五步：精算止盈止损位

**做多场景：**
```
SL  = 最近结构低点 × (1 - 0.5%)   ← 必须是独立的4H/1H摆低点（期货放宽至0.5%以应对跳空）
TP1 = 最近的结构阻力              ← 前高、趋势线上轨、形态颈线
TP2 = 下一级结构阻力              ← 更远的独立结构峰
TP3 = 形态理论目标                ← 旗杆高度投影、斐波那契延伸
```

**做空场景：**
```
SL  = 最近结构高点 × (1 + 0.5%)
TP1 = 最近的结构支撑
TP2 = 下一级结构支撑
TP3 = 形态理论目标
```

---

## 四、数据采集（按顺序执行以下数据块）

### ⚠️ 强制规则：一键脚本采集（禁止手动 curl Yahoo）

**唯一允许的数据采集方式：**

```bash
# 一键采集所有数据（内置429重试+并行+Yahoo串行限速）
python3 /root/.hermes/skills/research/futures-market-analysis/scripts/futures_fetch.py GC --compact
# 替换 GC 为: CL / BZ / GC / SI / HG / NG / PL / PA / ES / NQ / YM / RTY
# 也可直接传 Binance TradFi 商品永续: CLUSDT / BZUSDT / XAUUSDT / XAGUSDT / COPPERUSDT / NATGASUSDT / XPTUSDT / XPDUSDT
```

脚本输出完整 JSON，包含：daily_90d、hourly_10d、agg_4h_10d、proxies(DXY/VIX/ETF)、news、cftc；若 Binance TradFi 商品永续可用，还包含 `structured_drivers.binance_tradfi_perp` 的 1H/4H/1D K线、24h ticker、mark/index、资金费率、OI、OI历史、多空账户/仓位比。

**Binance TradFi 商品永续优先级**：
- `CL -> CLUSDT`
- `BZ -> BZUSDT`
- `GC -> XAUUSDT`
- `SI -> XAGUSDT`
- `HG -> COPPERUSDT`
- `NG -> NATGASUSDT`
- `PL -> XPTUSDT`
- `PA -> XPDUSDT`

这些 Binance 符号代表可交易的 USDT 永续层，优先用于可执行 K 线、资金费率、OI 和多空比；`CL=F` / `GC=F` 等传统近月代理、CFTC、EIA、OVX/DXY 用于传统期货、供需和宏观验证。不要把 `CLUSDT`、`XAUUSDT` 这类 TradFi 商品永续误路由到 crypto skill。

**⚠️ Yahoo 429 降级路径（2026-05-20 实测验证）**：

若 fetch 脚本返回 `"yahoo_chart": "error"` 且 `"errors": {"yahoo": "HTTP Error 429"}`：

1. **不要**手动 curl Yahoo（会被再限流）
2. **立即切换**到 Tavily 搜索补关键缺口：

```bash
# 并行搜索 — 价格 + DXY + VIX + 10Y 四个关键数据
# 使用 mcp_tavily_tavily_search，每条 query 独立调用
queries = [
    "gold price today COMEX GC=F per ounce 2026-05-20",     # 品种价格
    "DXY dollar index today May 20 2026",                    # 美元
    "VIX volatility index today May 20 2026",                # 恐慌
    "US 10 year treasury yield today May 20 2026 ^TNX",     # 利率
]
```

3. **Tavily 数据可用来源**（已验证）：
   - 价格：Stooq (stooq.com)、TradingEconomics、TEchi、Fortune
   - DXY：MarketWatch、TradingEconomics、Barchart
   - VIX：Investing.com (历史表)、CBOE 官方
   - 10Y：YCharts、Treasury.gov 官方数据、Investing.com

4. **GC 最后兜底 K 线补充方案**：当 GC=F 被 Yahoo 429 阻断且 `XAUUSDT` TradFi 永续不可用时，才通过 **PAXG/USDT（Binance spot）** 获取黄金技术结构代理：
   ```python
   # PAXG ≈ 1 troy oz gold，与 GC=F 偏差 <0.1%
   # Binance API 无需鉴权，无频率限制问题
   url = "https://api.binance.com/api/v3/klines?symbol=PAXGUSDT&interval=1d&limit=90"
   
   # 用于4H聚合
   url = "https://api.binance.com/api/v3/klines?symbol=PAXGUSDT&interval=1h&limit=720"
   ```
   - ⚠️ PAXG 流动性远低于 COMEX（日均仅 3K-7K 手），结构位有效但止损滑点风险需注意
   - ⚠️ 建议用 PAXG 看图、COMEX 下单
   - 价格完美同步（实测 PAXG $4,527 ≈ TradingEconomics $4,528）

5. **精度说明**：Tavily 数据来自网页爬取，非实时 API。期货价格可能有 CFD vs COMEX 差异（TradingEconomics 报价常比 Stooq 高 $50-70）。优先使用 Stooq/CBOE/Treasury.gov 等官方源。

5. **新闻 + CFTC 仍然可用**：fetch 脚本即使 Yahoo 429，news 和 cftc 块通常成功（独立数据源）。

6. **降级标记**：报告中必须写「⚠️ 技术面数据缺口：Yahoo 429，价格/DXY/VIX/10Y 来自 Tavily 搜索」。SL/TP 精度下降一档。

### 🔶 Binance PAXG 最后兜底方案（黄金 GC 专属，2026-05-21 实测）

> 当 Yahoo 429 导致 K 线数据缺失，且 `XAUUSDT` Binance TradFi 黄金永续不可用时，**PAXG/USDT（币安现货）** 才可作为黄金 COMEX 期货的技术结构代理。
> PAXG = Paxos Gold，1 token ≈ 1 盎司黄金，与 GC=F 偏差 <0.1%。

**使用条件**：
- 仅限 GC（黄金）。白银/原油/股指不适用此方法
- 优先级低于 `XAUUSDT` TradFi 永续；不要在 `XAUUSDT` 可用时优先使用 PAXG
- PAXG 在币安的流动性远低于 COMEX（日均 3K-7K 手），**结构位有效但下单应以 COMEX 合约为准**
- 当前日成交量不足 500 时标注「超低流动性警告」

**数据采集命令**（Python，无需 API Key）：

```python
import json, urllib.request

def fetch_binance(symbol, interval, limit):
    url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    raw = json.load(urllib.request.urlopen(req, timeout=15))
    return [{'t': k[0]//1000, 'o': float(k[1]), 'h': float(k[2]),
             'l': float(k[3]), 'c': float(k[4]), 'v': float(k[5])} for k in raw]

# 90日线、30日4H聚合、近16根1H —— 三个窗口同时拉
daily = fetch_binance("PAXGUSDT", "1d", 90)
hourly_30d = fetch_binance("PAXGUSDT", "1h", 720)  # 30d * 24h → 聚合4H
hourly_5d = fetch_binance("PAXGUSDT", "1h", 120)  # 5d → 近16根1H

# 4H 聚合（每4根1H合成一根）
agg_4h = []
for i in range(0, len(hourly_30d)-3, 4):
    chunk = hourly_30d[i:i+4]
    agg_4h.append({'t': chunk[0]['t'], 'o': chunk[0]['o'],
        'h': max(r['h'] for r in chunk), 'l': min(r['l'] for r in chunk),
        'c': chunk[-1]['c'], 'v': sum(r['v'] for r in chunk)})
```

**报告中标注**：
- 「技术结构代理：PAXG/USDT（Binance，1 PAXG ≈ 1 oz 黄金，偏差 <0.1%）」
- 「⚠️ PAXG 流动性低：当前日成交 X 手，建议用 PAXG 看图、用 COMEX 下单」
- SL/TP 精度保持，但标注「数据源偏差风险」

**宏观数据（OVX/VIX/DXY/10Y）通过 fetch 脚本获取，禁止调 mcp_yfinance。**




```

**❌ 绝对禁止：**
- 直接 `curl https://query1.finance.yahoo.com/...`
- 手写 `urllib.request` 调 Yahoo
- 任何绕过脚本的 Yahoo 直连

下面的代码块仅作参考文档保留，**不要复制执行**。

### 块 0：执行前检查 ⚠️ 必做

> 先确认分析时间和标的。标的都没对齐，后面的数据越多越危险。

```bash
# 记录分析时间（报告中必须回填）
date -u '+分析时间(UTC): %Y-%m-%d %H:%M'

# 确认标的符号（把 CL 替换成你的标的）
echo "=== 标的确认 ==="
echo "标的: CL=F (WTI 原油近月合约)"
echo "合约假设: 近月代理，滚动规则下可能与实际持仓月份有差异"
echo "波动率代理: ^OVX"
echo "主力ETF代理: USO"

# 检查是否处于重大事件窗口
echo ""
echo "=== 事件窗口检查 ==="
echo "今天星期几: $(date -u '+%A')"
echo "检查: EIA 原油库存日(周三) / OPEC会议 / FOMC / 非农 / 合约到期日"
```

**执行规则：**
- 非 CL 标的需替换波动率代理（股指用 ^VIX，黄金/白银无专用波动率指数，用 VIX 替代参考）
- 若处于重大事件窗口前 2 小时内，标注「事件窗口期」，方向置信度至少降一档
- Yahoo Finance 请求头必须带 `User-Agent: Mozilla/5.0` 否则可能返回 429

### 块 1：实时行情 + 30日历史

```bash
# 30日价格走势（以 CL=F 为例，替换 SYMBOL 为你的标的）
SYMBOL="CL=F"
curl -s -H "User-Agent: Mozilla/5.0" "https://query1.finance.yahoo.com/v8/finance/chart/${SYMBOL}?interval=1d&range=30d" | python3 -c "
import json, sys
from datetime import datetime, timezone
d = json.load(sys.stdin)['chart']['result'][0]
meta = d['meta']
quotes = d['indicators']['quote'][0]
idx = d['timestamp']
print(f'=== {meta.get(\"symbol\",\"?\")} 近30日价格 ===')
print(f'币种: {meta.get(\"currency\",\"USD\")} | 交易所: {meta.get(\"exchangeName\",\"?\")}')
for i in range(len(idx)):
    dt = datetime.fromtimestamp(idx[i], tz=timezone.utc).strftime('%m-%d')
    o = quotes['open'][i]
    c = quotes['close'][i]
    h = quotes['high'][i]
    l = quotes['low'][i]
    v = quotes['volume'][i]
    if o and c:
        chg = (c-o)/o*100 if o else 0
        clr = '🟢' if chg>=0 else '🔴'
        print(f'{dt} {clr} O:{o:,.2f} H:{h:,.2f} L:{l:,.2f} C:{c:,.2f} | {chg:+.2f}% | vol:{v:,.0f}')
prev = meta.get('chartPreviousClose', 0)
cur = meta.get('regularMarketPrice', 0)
print(f'前收盘: {prev:,.2f} | 当前: {cur:,.2f} | 变动: {(cur-prev)/prev*100:+.2f}%' if prev else '实时价格获取中...')
"

# 实时行情快照
curl -s -H "User-Agent: Mozilla/5.0" "https://query1.finance.yahoo.com/v8/finance/chart/${SYMBOL}?interval=1d&range=1d" | python3 -c "
import json, sys
d = json.load(sys.stdin)['chart']['result'][0]
meta = d['meta']
q = d['indicators']['quote'][0]
cur = meta.get('regularMarketPrice', 0)
prev = meta.get('chartPreviousClose', 0)
hi = meta.get('regularMarketDayHigh', cur)
lo = meta.get('regularMarketDayLow', cur)
vol = meta.get('regularMarketVolume', 0)
print(f'=== 实时行情快照 ===')
print(f'当前: {cur:,.2f}')
print(f'前收: {prev:,.2f}')
print(f'日内高: {hi:,.2f}')
print(f'日内低: {lo:,.2f}')
print(f'日内变动: {(cur-prev)/prev*100:+.2f}%' if prev else '')
print(f'成交量: {vol:,.0f}')
print(f'52周高: {meta.get(\"fiftyTwoWeekHigh\",\"?\"):,.2f}')
print(f'52周低: {meta.get(\"fiftyTwoWeekLow\",\"?\"):,.2f}')
"
```

**所有可分析标的符号表：**

| 品种 | Yahoo 代码 | Binance TradFi 永续 | 波动率代理 | ETF 代理 | 类别 |
|------|-----------|----------------------|-----------|---------|------|
| WTI 原油 | `CL=F` | `CLUSDT` | `^OVX` | `USO` | 能源 |
| Brent 原油 | `BZ=F` | `BZUSDT` | `^OVX` | `BNO` | 能源 |
| 黄金 | `GC=F` | `XAUUSDT` | `^VIX`（替代） | `GLD` | 贵金属 |
| 白银 | `SI=F` | `XAGUSDT` | `^VIX`（替代） | `SLV` | 贵金属 |
| 铜 | `HG=F` | `COPPERUSDT` | `^VIX`（替代） | `COPX` | 工业金属 |
| 天然气 | `NG=F` | `NATGASUSDT` | `^OVX`（部分参考） | `UNG` | 能源 |
| 铂金 | `PL=F` | `XPTUSDT` | `^VIX`（替代） | `PPLT` | 贵金属 |
| 钯金 | `PA=F` | `XPDUSDT` | `^VIX`（替代） | `PALL` | 贵金属 |
| 标普500 | `ES=F` | — | `^VIX` | `SPY` | 股指 |
| 纳斯达克100 | `NQ=F` | — | `^VIX` | `QQQ` | 股指 |
| 道琼斯 | `YM=F` | — | `^VIX` | `DIA` | 股指 |
| 罗素2000 | `RTY=F` | — | `^VIX` | `IWM` | 股指 |

### 块 1.2：历史轨迹复盘 — 30D 4H 聚合 ⚠️ 必做

> Yahoo Finance 不提供原生 4H K 线，从 1H 聚合。拉取 30 天 1H 数据，每 4 根聚合成一根 4H K 线。
>
> ⚠️ **已知截断问题**：`interval=1h&range=30d` 的 JSON 响应在 ~50KB 处经常截断（`Expecting ',' delimiter`），导致 4H 聚合失败。**可靠替代方案**：
> 1. 块 1.2 的「30D 4H 轨迹 + 大波动 K 线」改用 **30D 日线做摆点识别和波动扫描**（日线响应小，不截断）
> 2. 块 1.5 的「4H K 线」改用 **5d 1H 聚合 4H**（数据量可控，不截断），取最近 12 根 4H 即可覆盖 2 天短线结构
> 3. 两者互补：日线看轮廓 + 4H 看精度，不依赖单一截断源

```bash
# 30日 4H 轨迹复盘（1H 聚合 → 4H）
SYMBOL="CL=F"
curl -s -H "User-Agent: Mozilla/5.0" "https://query1.finance.yahoo.com/v8/finance/chart/${SYMBOL}?interval=1h&range=30d" | python3 -c "
import json, sys
from datetime import datetime, timezone
d = json.load(sys.stdin)['chart']['result'][0]
quotes = d['indicators']['quote'][0]
idx = d['timestamp']

# 构建1H蜡烛
candles = []
for i in range(len(idx)):
    o = quotes['open'][i]; h = quotes['high'][i]
    l = quotes['low'][i]; c = quotes['close'][i]; v = quotes['volume'][i]
    if o and c:
        candles.append({'t':idx[i],'o':o,'h':h,'l':l,'c':c,'v':(v or 0)})

# 聚合4H
agg_4h = []
for i in range(0, len(candles)-3, 4):
    chunk = candles[i:i+4]
    if chunk:
        agg_4h.append({
            't': chunk[0]['t'],
            'o': chunk[0]['o'],
            'h': max(x['h'] for x in chunk),
            'l': min(x['l'] for x in chunk),
            'c': chunk[-1]['c'],
            'v': sum(x['v'] for x in chunk)
        })

print('=== 🧭 30日 4H 轨迹复盘（聚合）===')
if agg_4h:
    hi = max(agg_4h, key=lambda r: r['h'])
    lo = min(agg_4h, key=lambda r: r['l'])
    n = len(agg_4h)
    print(f'K线数: {n} 根 4H')
    print(f'区间低点: {lo[\"l\"]:,.2f} @ {datetime.fromtimestamp(lo[\"t\"], tz=timezone.utc).strftime(\"%m-%d %H:%M\")}')
    print(f'区间高点: {hi[\"h\"]:,.2f} @ {datetime.fromtimestamp(hi[\"t\"], tz=timezone.utc).strftime(\"%m-%d %H:%M\")}')
    print(f'区间涨跌: {(agg_4h[-1][\"c\"]/agg_4h[0][\"o\"]-1)*100:+.1f}%')

    # 识别摆点
    ph, pl = [], []
    for i in range(2, len(agg_4h)-2):
        if agg_4h[i]['h'] > agg_4h[i-1]['h'] and agg_4h[i]['h'] > agg_4h[i-2]['h'] and agg_4h[i]['h'] > agg_4h[i+1]['h'] and agg_4h[i]['h'] > agg_4h[i+2]['h']:
            ph.append(agg_4h[i])
        if agg_4h[i]['l'] < agg_4h[i-1]['l'] and agg_4h[i]['l'] < agg_4h[i-2]['l'] and agg_4h[i]['l'] < agg_4h[i+1]['l'] and agg_4h[i]['l'] < agg_4h[i+2]['l']:
            pl.append(agg_4h[i])

    print(f'最近摆高:')
    for r in ph[-4:]:
        print(f'  {datetime.fromtimestamp(r[\"t\"], tz=timezone.utc).strftime(\"%m-%d %H:%M\")}  {r[\"h\"]:,.2f}')
    print(f'最近摆低:')
    for r in pl[-4:]:
        print(f'  {datetime.fromtimestamp(r[\"t\"], tz=timezone.utc).strftime(\"%m-%d %H:%M\")}  {r[\"l\"]:,.2f}')

    # 大波动K线
    events = []
    for r in agg_4h:
        body = (r['c'] - r['o']) / r['o'] * 100 if r['o'] else 0
        rng = (r['h'] - r['l']) / r['o'] * 100 if r['o'] else 0
        if abs(body) >= 1.5 or rng >= 2.5:
            events.append((abs(body), body, rng, r))
    print(f'大波动K线（帮助识别急拉/急砸/洗盘）:')
    for _, body, rng, r in sorted(events, reverse=True)[:6]:
        dt = datetime.fromtimestamp(r['t'], tz=timezone.utc).strftime('%m-%d %H:%M')
        print(f'  {dt} body:{body:+.2f}% range:{rng:.2f}% O:{r[\"o\"]:,.2f} C:{r[\"c\"]:,.2f}')
else:
    print('数据不足，无法聚合4H')
"

# 90日 日线轮廓（大环境）
curl -s -H "User-Agent: Mozilla/5.0" "https://query1.finance.yahoo.com/v8/finance/chart/${SYMBOL}?interval=1d&range=90d" | python3 -c "
import json, sys
d = json.load(sys.stdin)['chart']['result'][0]
quotes = d['indicators']['quote'][0]
idx = d['timestamp']
valid = [(i, quotes['open'][i], quotes['close'][i]) for i in range(len(idx)) if quotes['open'][i] and quotes['close'][i]]
if len(valid) >= 7:
    o0 = valid[0][1]; c0 = valid[-1][2]
    c20 = valid[-20][2] if len(valid) >= 20 else valid[0][2]
    c7 = valid[-7][2] if len(valid) >= 7 else valid[0][2]
    print(f'=== 🗺️ 90日 日线轮廓 ===')
    print(f'数据点数: {len(valid)} 个交易日')
    print(f'90日涨跌: {(c0/o0-1)*100:+.1f}%')
    print(f'20日涨跌: {(c0/c20-1)*100:+.1f}%')
    print(f'7日涨跌: {(c0/c7-1)*100:+.1f}%')
else:
    print('数据不足，无法计算轮廓')
"
```

**复盘后必须输出：**
- 最近 `30D 4H` 主导手法是什么
- 最近 `2-3` 次关键动作是什么（急拉、急砸、假突破、回收、派发）
- 今天看到的信号属于 `延续 / 回踩 / 诱多 / 诱空 / 纯噪音`

### 块 1.5：日内短线 — 4H/1H K 线 ⚠️ 日内交易者必看

```bash
# 4H K线（聚合）+ 1H K线（近5日）
SYMBOL="CL=F"
curl -s -H "User-Agent: Mozilla/5.0" "https://query1.finance.yahoo.com/v8/finance/chart/${SYMBOL}?interval=1h&range=5d" | python3 -c "
import json, sys
from datetime import datetime, timezone
d = json.load(sys.stdin)['chart']['result'][0]
quotes = d['indicators']['quote'][0]
idx = d['timestamp']

# 构建1H蜡烛
candles = []
for i in range(len(idx)):
    o = quotes['open'][i]; h = quotes['high'][i]
    l = quotes['low'][i]; c = quotes['close'][i]; v = quotes['volume'][i]
    if o and c:
        candles.append({'t':idx[i],'o':o,'h':h,'l':l,'c':c,'v':(v or 0)})

# 聚合4H
agg_4h = []
for i in range(0, len(candles)-3, 4):
    chunk = candles[i:i+4]
    if chunk:
        agg_4h.append({
            't': chunk[0]['t'],
            'o': chunk[0]['o'],
            'h': max(x['h'] for x in chunk),
            'l': min(x['l'] for x in chunk),
            'c': chunk[-1]['c'],
            'v': sum(x['v'] for x in chunk)
        })

print(f'=== 📊 4H K线（近5日聚合，{len(agg_4h)}根）===')
for r in agg_4h[-12:]:
    dt = datetime.fromtimestamp(r['t'], tz=timezone.utc).strftime('%m-%d %H:%M')
    body = abs(r['c'] - r['o']) / r['o'] * 100 if r['o'] else 0
    wick_up = (r['h'] - max(r['o'], r['c'])) / r['o'] * 100 if r['o'] else 0
    wick_down = (min(r['o'], r['c']) - r['l']) / r['o'] * 100 if r['o'] else 0
    clr = '🟢' if r['c'] >= r['o'] else '🔴'
    print(f'{dt} {clr} O:{r[\"o\"]:,.2f} H:{r[\"h\"]:,.2f} L:{r[\"l\"]:,.2f} C:{r[\"c\"]:,.2f} | 实体:{body:.1f}% 上影:{wick_up:.1f}% 下影:{wick_down:.1f}%')

# 1H K线（最近16根）
print(f'=== 📊 1H K线（近16h）===')
for r in candles[-16:]:
    dt = datetime.fromtimestamp(r['t'], tz=timezone.utc).strftime('%m-%d %H:%M')
    body = abs(r['c'] - r['o']) / r['o'] * 100 if r['o'] else 0
    clr = '🟢' if r['c'] >= r['o'] else '🔴'
    print(f'{dt} {clr} O:{r[\"o\"]:,.2f} H:{r[\"h\"]:,.2f} L:{r[\"l\"]:,.2f} C:{r[\"c\"]:,.2f} | body:{body:.2f}% vol:{r[\"v\"]:,.0f}')
"
```

### 块 2：市场结构 — 期限结构、Contango/Backwardation 代理、库存

> 期货的核心市场结构是期限结构（term structure）。这里使用近月-远月价差作为 contango/backwardation 代理。

```bash
# 期限结构代理：近月 vs 远月（以CL为例：CL=F 近月，CL=F + 6个月后的合约）
# 通过连续合约与 ETF 表现对比推断结构
SYMBOL="CL=F"
ETF_PROXY="USO"

echo "=== ⛓️ 市场结构 ==="

# 近月合约价格与表现
curl -s -H "User-Agent: Mozilla/5.0" "https://query1.finance.yahoo.com/v8/finance/chart/${SYMBOL}?interval=1d&range=90d" | python3 -c "
import json, sys
d = json.load(sys.stdin)['chart']['result'][0]
meta = d['meta']
quotes = d['indicators']['quote'][0]
idx = d['timestamp']
valid = [(quotes['close'][i], quotes['volume'][i]) for i in range(len(idx)) if quotes['close'][i]]
print(f'近月合约: {meta.get(\"symbol\",\"?\")} | 当前: {meta.get(\"regularMarketPrice\",\"?\"):,.2f}')
if len(valid) >= 30:
    print(f'30日涨跌: {(valid[-1][0]/valid[-30][0]-1)*100:+.1f}%')
    print(f'7日涨跌: {(valid[-1][0]/valid[-7][0]-1)*100:+.1f}%')
"

# ETF代理（USO/GLD/SLV）近30日表现
echo ""
curl -s -H "User-Agent: Mozilla/5.0" "https://query1.finance.yahoo.com/v8/finance/chart/${ETF_PROXY}?interval=1d&range=30d" | python3 -c "
import json, sys
d = json.load(sys.stdin)['chart']['result'][0]
meta = d['meta']
quotes = d['indicators']['quote'][0]
idx = d['timestamp']
valid = [(quotes['close'][i],) for i in range(len(idx)) if quotes['close'][i]]
print(f'ETF({meta.get(\"symbol\",\"?\")}) 当前: {meta.get(\"regularMarketPrice\",\"?\"):,.2f}')
if len(valid) >= 30:
    print(f'ETF 30日涨跌: {(valid[-1][0]/valid[-30][0]-1)*100:+.1f}%')
# ETF表现落后近月 → 可能contango（期货升水，滚动成本高）
# ETF表现领先近月 → 可能backwardation（期货贴水，滚动收益）
"

# 库存背景（针对能源品种）
echo ""
echo "=== 🛢️ 库存背景 ==="
echo "数据源: EIA 每周三公布原油/天然气库存（免费公开）"
echo "注意: 如果今天是EIA公布日，请单独查询最新库存数据"
echo "替代参考: Google News搜索 'EIA crude oil inventory' 获取最新头条"
```

**市场结构解读规则：**
- **Contango（期货升水）**：远月 > 近月。供应充足/需求偏弱 → ETF 长期持有者滚动成本高 → 轻微偏空背景
- **Backwardation（期货贴水）**：近月 > 远月。供应紧张/需求强劲 → ETF 持有者获得滚动收益 → 轻微偏多背景
- **库存趋势**：库存连续增加 → 供应宽松 → 偏空；库存连续减少 → 供应紧张 → 偏多

### 块 2.5：主导力量 — 波动率代理 + ETF 资金流 + DXY

> 替代加密的 OI + 费率 + 多空比。OVX 和 VIX 是期货最重要的情绪/恐慌指标。

```bash
SYMBOL="CL=F"
# 自动选择波动率代理：CL/NG → OVX；ES/NQ/YM/RTY → VIX；GC/SI/HG → VIX（参考）

# === 波动率代理 ===
# OVX（原油波动率指数）
echo "=== 😱 OVX 原油波动率指数 ==="
curl -s -H "User-Agent: Mozilla/5.0" "https://query1.finance.yahoo.com/v8/finance/chart/%5EOVX?interval=1d&range=30d" | python3 -c "
import json, sys
from datetime import datetime, timezone
d = json.load(sys.stdin)['chart']['result'][0]
meta = d['meta']
quotes = d['indicators']['quote'][0]
idx = d['timestamp']
cur = meta.get('regularMarketPrice', 0)
prev = meta.get('chartPreviousClose', 0)
print(f'OVX 当前: {cur:.1f} | 前收: {prev:.1f} | 变动: {(cur-prev)/prev*100:+.1f}%' if prev else f'OVX 当前: {cur:.1f}')
# OVX 解读
if cur < 25: print('状态: 🟢 低波动安逸 → 可按技术面正常交易')
elif cur < 35: print('状态: 🟡 正常 → 正常仓位')
elif cur < 45: print('状态: 🟠 偏高/供应担忧 → 仓位减半')
elif cur < 75: print('状态: 🔴 地缘危机 → 仓位降至1/4，止损放宽')
else: print('状态: 🚨 极端恐慌/战争模式 → 建议观望')
# 日均预期波幅
import math
daily_move = cur / math.sqrt(252) if cur > 0 else 0
print(f'日均预期波幅(OVX/√252): ±{daily_move:.2f}')
# 近5日OVX走势
valid = [(idx[i], quotes['close'][i]) for i in range(len(idx)) if quotes['close'][i]]
print(f'近5日OVX:')
for t, v in valid[-5:]:
    print(f'  {datetime.fromtimestamp(t, tz=timezone.utc).strftime(\"%m-%d\")}: {v:.1f}')
"

# VIX（股指恐慌指数，所有品种都参考）
echo ""
echo "=== 😨 VIX 恐慌指数 ==="
curl -s -H "User-Agent: Mozilla/5.0" "https://query1.finance.yahoo.com/v8/finance/chart/%5EVIX?interval=1d&range=30d" | python3 -c "
import json, sys
d = json.load(sys.stdin)['chart']['result'][0]
meta = d['meta']
cur = meta.get('regularMarketPrice', 0)
prev = meta.get('chartPreviousClose', 0)
print(f'VIX 当前: {cur:.1f} | 前收: {prev:.1f} | 变动: {(cur-prev)/prev*100:+.1f}%' if prev else f'VIX 当前: {cur:.1f}')
if cur < 15: print('状态: 🟢 安逸 (风险偏好高)')
elif cur < 20: print('状态: 🟡 正常')
elif cur < 30: print('状态: 🟠 担忧 (风险偏好降)')
else: print('状态: 🔴 恐慌 (避险情绪)')
"

# === ETF 资金流代理 ===
echo ""
echo "=== 💰 USO 原油ETF ==="
curl -s -H "User-Agent: Mozilla/5.0" "https://query1.finance.yahoo.com/v8/finance/chart/USO?interval=1d&range=5d" | python3 -c "
import json, sys
d = json.load(sys.stdin)['chart']['result'][0]
meta = d['meta']
cur = meta.get('regularMarketPrice', 0)
prev = meta.get('chartPreviousClose', 0)
vol = meta.get('regularMarketVolume', 0)
avg_vol = meta.get('averageDailyVolume3Month', 0)
print(f'USO 当前: {cur:,.2f} | 变动: {(cur-prev)/prev*100:+.3f}%' if prev else f'USO 当前: {cur:,.2f}')
print(f'成交量: {vol:,.0f} | 3月均量: {avg_vol:,.0f}')
vol_ratio = vol/avg_vol if avg_vol else 0
if vol_ratio > 1.5: print(f'⚠️ 量比 {vol_ratio:.1f}x → 异常放量，大资金可能在进出')
elif vol_ratio > 1.2: print(f'🟡 量比 {vol_ratio:.1f}x → 略放量')
else: print(f'⚪ 量比 {vol_ratio:.1f}x → 正常')
"

# === DXY 美元指数 ===
echo ""
echo "=== 💵 美元指数 DXY ==="
curl -s -H "User-Agent: Mozilla/5.0" "https://query1.finance.yahoo.com/v8/finance/chart/DX-Y.NYB?interval=1d&range=5d" | python3 -c "
import json, sys
d = json.load(sys.stdin)['chart']['result'][0]
meta = d['meta']
cur = meta.get('regularMarketPrice', 0)
prev = meta.get('chartPreviousClose', 0)
print(f'DXY 当前: {cur:,.2f} | 变动: {(cur-prev)/prev*100:+.3f}%' if prev else f'DXY 当前: {cur:,.2f}')
if cur > 105: print(f'🟠 美元 >105 → 商品普遍承压')
elif cur > 100: print(f'🟡 美元 100-105 → 中性偏强')
else: print(f'🟢 美元 <100 → 商品受益')
"

# === COT 报告提示 ===
echo ""
echo "=== 📋 COT 持仓报告 ==="
echo "COT 数据天然滞后 3 天（每周五公布截至周二的持仓）"
echo "仅作中长期背景参考，不用于日内决策"
echo "查询入口: https://www.cftc.gov/dea/futures/deacmesf.htm"
```

### 块 2.7：增强宏观仪表盘 ⚠️ 新增（macro-rates-monitor 精简版）

> 期货的宏观定价核心：GC看实际利率，CL看美元+地缘，ES/NQ看利率路径+VIX。
> 与块5并行拉取，不增加等待时间。

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

real_10y = tnx - 2.8
dxy_dir = 'STRONG' if dxy>105 else 'WEAK' if dxy<100 else 'NEUTRAL'
print(f'\n10Y: {tnx:.1f}% | Real(est): {real_10y:.1f}% | DXY: {dxy:.1f}({dxy_dir}) | VIX: {vix:.1f}')
print('GC: Real rate UP -> Gold DOWN / CL: DXY UP -> Oil DOWN / ES: VIX>30 -> risk-off')
print('FOMC: Jun 17-18, 2026 | Rate: 4.25-4.50%')
```

**块2.7 品种专属解读：**
| 品种 | 宏观信号 | 方向 |
|------|---------|------|
| GC | 实际利率 ↓ + 美元 ↓ | 🟢 看涨 |
| GC | 实际利率 ↑ + 美元 ↑ | 🔴 看跌 |
| CL | 美元 ↓ + VIX 不涨 | 🟢 看涨 |
| ES/NQ | VIX<20 + 10Y不涨 | 🟢 看涨 |
| ES/NQ | VIX>25 | 🔴 看跌 |

---

### 块 3：交叉验证 — 关联资产 + 美元 + 收益率

```bash
# 交叉验证：关联资产群表现
# 不同品种的关联资产不同，此处以CL原油为例
# CL关联: DXY, GC=F(黄金同向避险), ^GSPC(风险偏好), ^TNX(利率)
# GC关联: DXY, ^TNX, ^VIX, ^GSPC
# ES关联: ^VIX, ^TNX, DXY, ^IXIC

SYMBOL="CL=F"

echo "=== 🔍 交叉验证（关联资产群）==="

# 美元指数
echo "--- DXY ---"
curl -s -H "User-Agent: Mozilla/5.0" "https://query1.finance.yahoo.com/v8/finance/chart/DX-Y.NYB?interval=1d&range=5d" | python3 -c "
import json, sys
d = json.load(sys.stdin)['chart']['result'][0]
m = d['meta']
cur = m.get('regularMarketPrice',0); prev = m.get('chartPreviousClose',0)
print(f'{cur:,.2f} ({(cur-prev)/prev*100:+.2f}%)' if prev else f'{cur:,.2f}')
"

# 10年期美债收益率
echo "--- 10Y 美债收益率 ---"
curl -s -H "User-Agent: Mozilla/5.0" "https://query1.finance.yahoo.com/v8/finance/chart/%5ETNX?interval=1d&range=5d" | python3 -c "
import json, sys
d = json.load(sys.stdin)['chart']['result'][0]
m = d['meta']
cur = m.get('regularMarketPrice',0); prev = m.get('chartPreviousClose',0)
print(f'{cur:.2f}% ({(cur-prev)/prev*100:+.2f}%)' if prev else f'{cur:.2f}%')
"

# 黄金（同向避险参考）
echo "--- 黄金 ---"
curl -s -H "User-Agent: Mozilla/5.0" "https://query1.finance.yahoo.com/v8/finance/chart/GC=F?interval=1d&range=5d" | python3 -c "
import json, sys
d = json.load(sys.stdin)['chart']['result'][0]
m = d['meta']
cur = m.get('regularMarketPrice',0); prev = m.get('chartPreviousClose',0)
print(f'{cur:,.2f} ({(cur-prev)/prev*100:+.2f}%)' if prev else f'{cur:,.2f}')
"

# 标普500（风险偏好）
echo "--- 标普500 ---"
curl -s -H "User-Agent: Mozilla/5.0" "https://query1.finance.yahoo.com/v8/finance/chart/%5EGSPC?interval=1d&range=5d" | python3 -c "
import json, sys
d = json.load(sys.stdin)['chart']['result'][0]
m = d['meta']
cur = m.get('regularMarketPrice',0); prev = m.get('chartPreviousClose',0)
print(f'{cur:,.0f} ({(cur-prev)/prev*100:+.2f}%)' if prev else f'{cur:,.0f}')
"

echo ""
echo "--- 交叉验证结论 ---"
echo "检查清单:"
echo "  □ 美元方向是否与标的方向一致（美元↑ → 商品↓）？"
echo "  □ 收益率方向是否确认宏观逻辑？"
echo "  □ 关联资产群是否同向确认（如原油与黄金同向=避险驱动；原油与标普同向=需求驱动）？"
echo "  □ 如有明显背离（如美元走弱但商品不涨），标注为'分歧信号'，降低置信度"
```

### 块 4：情绪面 — OVX/VIX 深度解读

```bash
# 情绪面已经在块2.5中拉取了OVX和VIX
# 这里做深度解读

echo "=== 🎭 情绪面综合解读 ==="

echo "--- OVX 解读（原油专属）---"
echo "OVX < 25: 安逸 → 技术面权重正常"
echo "OVX 25-35: 正常 → 正常操作"
echo "OVX 35-45: 供应担忧 → 仓位减半，止损放宽"
echo "OVX 45-75: 地缘危机 → 仓位降至1/4，优先事件驱动"
echo "OVX > 75: 战争模式 → 强制观望"

echo ""
echo "--- VIX 解读（适用于所有品种）---"
echo "VIX < 15: 安逸 → 风险偏好高（股指利好，避险资产可能承压）"
echo "VIX 15-20: 正常"
echo "VIX 20-30: 担忧 → 仓位减半"
echo "VIX > 30: 恐慌 → 股指强制观望或大幅减仓"

echo ""
echo "--- 情绪综合判断 ---"
echo "规则: 当 VIX > 30 且 OVX > 45 时 → 全市场恐慌，强制观望"
echo "规则: 当 VIX < 15 且 OVX < 25 时 → 全市场安逸，技术面权重最高"
echo "规则: VIX 与 OVX 方向分歧时 → 按标的专属波动率代理为准"
```

### 块 5：宏观基本面 — EIA/OPEC/Fed/地缘新闻

```bash
# 新闻采集：Google News RSS 多路搜索
SYMBOL_NAME="crude oil"

echo "=== 📰 市场级新闻（Google News RSS）==="
curl -s "https://news.google.com/rss/search?q=${SYMBOL_NAME}+price+when:1d&hl=en-US&gl=US&ceid=US:en" | python3 -c "
import sys, html, xml.etree.ElementTree as ET
root = ET.fromstring(sys.stdin.read())
items = root.findall('./channel/item')
for i, item in enumerate(items[:4], 1):
    title = html.unescape(item.findtext('title', '')).strip()
    pub = item.findtext('pubDate', '').strip()
    print(f'{i}. {title}')
    if pub: print(f'   {pub}')
"

echo ""
echo "=== 🏛️ 地缘/OPEC/政策新闻（Google News RSS）==="
curl -s "https://news.google.com/rss/search?q=OPEC+OR+crude+inventory+OR+geopolitical+oil+when:3d&hl=en-US&gl=US&ceid=US:en" | python3 -c "
import sys, html, xml.etree.ElementTree as ET
root = ET.fromstring(sys.stdin.read())
items = root.findall('./channel/item')
for i, item in enumerate(items[:4], 1):
    title = html.unescape(item.findtext('title', '')).strip()
    pub = item.findtext('pubDate', '').strip()
    print(f'{i}. {title}')
    if pub: print(f'   {pub}')
"

echo ""
echo "=== 🏦 Fed/利率新闻（Google News RSS）==="
curl -s "https://news.google.com/rss/search?q=Federal+Reserve+OR+FOMC+interest+rate+when:7d&hl=en-US&gl=US&ceid=US:en" | python3 -c "
import sys, html, xml.etree.ElementTree as ET
root = ET.fromstring(sys.stdin.read())
items = root.findall('./channel/item')
for i, item in enumerate(items[:3], 1):
    title = html.unescape(item.findtext('title', '')).strip()
    pub = item.findtext('pubDate', '').strip()
    print(f'{i}. {title}')
    if pub: print(f'   {pub}')
"

echo ""
echo "=== 📊 EIA 库存数据 ==="
echo "EIA 每周三 10:30 AM ET 公布原油库存"
echo "查询: https://www.eia.gov/petroleum/supply/weekly/"
echo "如果今天是周三且数据已出，额外搜索 'EIA crude inventory weekly'"

echo ""
echo "=== ⚠️ 事件风险等级评估 ==="
echo "请根据新闻内容手动评估:"
echo "  🚨 一级: 海峡关闭/全面战争 → 强制观望"
echo "  🔴 二级: 军事冲突升级/停火破裂 → 技术面权重降至10%"
echo "  🟡 三级: 停火谈判/EIA库存/OPEC会议 → 技术面权重降至30%"
echo "  ⚪ 四级: 常规供需/评论 → 技术面正常权重"
```

**新闻块执行规则：**
- 默认从 3 路 RSS 中提炼 `2-4` 条真正影响交易判断的新闻，不要把整屏标题搬进最终报告
- `price today / current price / prediction / technical analysis / opinion / recap` 这类标题默认降权
- `OPEC / EIA / inventory / supply disruption / sanctions / Fed / FOMC / geopolitical / pipeline / export ban` 这类带明确事件主体的标题优先保留
- 同一事件若被多家媒体重复转载，只保留最接近原始事件的一条
- 如果没有筛出明确硬新闻，就写「新闻面无强驱动，主要是价格播报/观点稿」，不要硬凑事件
- 地缘新闻必须按事件等级分类（一级/二级/三级/四级）

---

## 五、严格输出模板（不可偏离）

```markdown
## 🎯 [标的名称] 期货交易决策

**分析时间（UTC）**：[YYYY-MM-DD HH:MM]
**合约**：[CL=F / GC=F / ES=F 等，近月代理假设；若可用，注明 Binance TradFi 永续如 CLUSDT/XAUUSDT 为可执行层]
**数据完整性**：[完整 / 缺少哪几块；若关键块缺失则只能观望]
**事件权重**：[技术主导 / 事件主导 / 混合] — 当前事件等级：⚪/🟡/🔴/🚨

### 方向：🟢 做多 / 🔴 做空 / ⚪ 观望

**一句话理由**：[最核心的结构依据 + 主导驱动，一句话说清楚]
**宏观时效性**：[美股开市可视作实时参考 / 周末或休市仅以前收作背景过滤 / 流动性正常/偏低]

### 历史轨迹复盘
- 最近 `30D 4H` 主导手法：[趋势推进 / 箱体洗盘 / 冲高派发 / 跌破回收 / 阴跌磨人]
- 最近关键动作：[列出 2-3 次关键轨迹动作 + 时间]
- 今天更像：[延续 / 回踩 / 诱多 / 诱空 / 纯噪音]

### 结构依据
- 最近结构摆点：[higher low / lower high，具体价位和形成时间]
- 当前形态：[楔形/旗形/双底/头肩/三角收敛等]
- 量价状态：[放量/缩量 + 方向 → 健康/危险]

### 📐 增强宏观
- 利率：10Y X.X% | 实际利率 X.X% | FOMC X月X日
- DXY：XX.X（强势/中性/弱势）| VIX：XX.X

### 八维判断
- 📈 技术面：[结论 — 趋势方向 + 关键结构位]
- ⛓️ 可执行合约层：[Binance TradFi 永续/OI/资金费率/多空比]
- 🏛️ 传统期货结构：[contango/backwardation 倾向 + 库存/CFTC背景]
- 🐋 主导力量：[OVX/VIX 状态 + ETF 资金流 + DXY 方向]
- 😱 情绪/波动率：[波动率区间 + 恐慌/贪婪判断]
- 🌍 宏观与事件：[地缘/政策/库存/利率核心驱动]
- 🔍 交叉验证：[关联资产是否确认 / 是否有背离]
- 🧭 缠论结构：[CZSC 确认/冲突/不足 + 中枢/笔/背驰]

### 💰 止盈止损计划

| 项目 | 价位 | 结构依据 |
|------|------|---------|
| **入场** | $XX.XX | [当前区间 + 结构位支撑/阻力] |
| **🔴 SL** | $XX.XX（-X.X%） | [**锚定的结构位名称 + 形成时间**] |

| 级别 | 平仓% | 触发价 | 盈利% | 结构依据 |
|------|-------|--------|-------|---------|
| 🔴 SL | 全部 | $XX.XX | -X.X% | [结构位名称] |
| 🟡 TP1 | 30% | $XX.XX | +X.X% | [结构位名称] |
| 🟠 TP2 | 30% | $XX.XX | +X.X% | [结构位名称] |
| 🟢 TP3 | 40% | $XX.XX | +X.X% | [结构位名称] |

### 移动止损
- 到 TP1 → 移损至开仓价
- 到 TP2 → 移损至 TP1
- 创新高/低 → 跟踪最近 2 根 4H K 线的结构摆点

### 仓位
- 风险金额 ÷ |入场价 - SL| = 可开仓位（合约数）
- 以 $10,000 账户 2% 风险为例：**X.XX 手/合约**

### 失效条件（不等止损，手动离场）
1. [客观条件 1 — 如：OVX 单日飙升超过 15%]
2. [客观条件 2 — 如：相关资产（DXY/黄金/标普）明确反向突破关键位]
3. [客观条件 3 — 如：一级/二级地缘事件突发]

### 风险提示
- ⚠️ **单交易所风险**：期货主要在单一交易所（NYMEX/CME/COMEX）交易
- ⚠️ **跳空风险**：期货周末/节假日后开盘常见跳空，止损可能滑点
- ⚠️ **合约到期风险**：近月合约临近到期时流动性下降，注意移仓换月

### 禁止事项
- ❌ 止损后立即反向开仓
- ❌ 浮盈加仓（除非趋势非常明确且有结构支撑）
- ❌ 在重大事件（EIA/FOMC/OPEC）公布前 30 分钟内开新仓
- ❌ 一天超过 3 笔交易

**免责声明**：本分析不构成投资建议。期货交易风险极高，可能导致超过本金的损失。
```

---

## 六、决策检查清单

- [ ] 已标注分析时间（UTC）与数据缺口
- [ ] 已确认标的符号和合约月份假设
- [ ] 已检查是否处于重大事件窗口（EIA/OPEC/FOMC/非农）
- [ ] 已评估事件风险等级（🚨/🔴/🟡/⚪）并相应调整技术面权重
- [ ] 已复盘最近 `30D 4H` 主导手法
- [ ] 已说明今天更像延续、回踩还是陷阱
- [ ] 最近结构摆点是 higher low 还是 lower high？
- [ ] 引用的 `4H/1H` 结构位是否都来自**已收盘 K 线**？未收盘 K 线只能写「临时高/低」，不得写成已确认摆点
- [ ] 如果写了「连续 lower highs / higher lows」，对应价位序列是否真的单调？
- [ ] OVX/VIX 处于什么区间？对仓位和操作有什么约束？
- [ ] DXY 方向是否与标的方向一致？（商品期货：DXY↑ → 价格↓）
- [ ] ETF 资金流代理（USO/GLD/SLV/SPY）是否有异常放量？
- [ ] COT 数据是否被错误地用于日内决策？（如果是 → 删除该引用）
- [ ] 期限结构倾向 contango 还是 backwardation？
- [ ] 量是放还是缩？方向对不对？
- [ ] 当前价格是否已经贴近最近阻力/支撑，导致盈亏比不足 1.5？
- [ ] SL 锚定哪个结构位？什么时候形成的？（期货 SL 放宽至 0.3%-0.5% 应对跳空）
- [ ] TP1/TP2/TP3 各锚定哪个结构位？
- [ ] 入场价、SL、TP1/TP2/TP3 的盈利/亏损百分比、加权盈亏比、仓位示例是否算术一致？
- [ ] 失效条件是否客观可观察？（必须包含 OVX/VIX 异动条件）
- [ ] 当前是否周末/节假日？流动性是否偏低？
- [ ] 新闻是否是硬新闻，而不是评论稿/技术分析文章/标题党？
- [ ] 新闻是否按事件等级（🚨/🔴/🟡/⚪）分类？
- [ ] 是否标注了「单交易所风险」和「跳空风险」？
- [ ] 品种专属逻辑是否正确应用？
- [ ] 🆕 利率/DXY 方向是否支持交易方向（GC看实际利率，CL看美元）？
- [ ] 🆕 FOMC/CPI/EIA 事件窗口已标注？（不能用原油框架分析黄金，不能用黄金框架分析股指）
- [ ] 仓位在风控范围内（2%）？

---

## 七、常见错误（禁止清单）

| 错误 | 正确做法 |
|------|---------|
| ❌ 用 24h 高/低点做 SL/TP | ✅ 用独立的结构摆点（前高/前低、趋势线、颈线） |
| ❌ 「跌 2% 止损」 | ✅ 止损锚定最近结构低点下方 0.3%-0.5% |
| ❌ 给两个方向让用户选 | ✅ 只给一个方向（做多/做空/观望） |
| ❌ 不确定时硬说一个方向 | ✅ 诚实输出「观望」并说明分歧在哪 |
| ❌ 在一级/二级事件面前坚持技术分析 | ✅ 一级事件强制观望，二级事件将技术面权重降至 10% |
| ❌ SL 太近被扫掉（忽略期货跳空风险） | ✅ 期货 SL 放宽至 0.3%-0.5%，放在结构位外侧 |
| ❌ TP 设得太远不切实际 | ✅ 每个 TP 都有明确的结构依据 |
| ❌ 忽略 OVX/VIX 只看 K 线 | ✅ K 线 + 波动率 + 事件 = 完整判断 |
| ❌ 把 COT 报告（滞后 3 天）用于日内决策 | ✅ COT 仅作中长期背景，不用于日内分析 |
| ❌ 用原油分析框架套到黄金/股指上 | ✅ 每个品种按「品种专属逻辑」中的驱动优先级分析 |
| ❌ 只看当前截面，不复盘最近 30 日轨迹 | ✅ 先判断这个品种平时怎么走，再解释今天的波动 |
| ❌ 在主要阻力前追多 / 主要支撑前追空 | ✅ 等回踩/反抽；盈亏比不够就观望 |
| ❌ 把评论稿/技术分析文章当成事件驱动 | ✅ 优先使用有明确时间、事件主体、来源的硬新闻 |
| ❌ 把未收盘 K 线写成已确认的 4H/1H 摆点或形态 | ✅ 未收盘只能写「临时高/低」；摆点、形态结论必须等该周期收盘 |
| ❌ 把不单调的价格序列写成「连续 lower highs / higher lows」 | ✅ 逐个核对摆点；序列不干净就改写为「冲高回落 / 回踩后反抽」 |
| ❌ 忘记标注「单交易所风险」 | ✅ 期货缺乏多所对比，每次报告都要提醒 |
| ❌ 在 EIA/OPEC/FOMC 公布前 30 分钟开仓 | ✅ 重大数据公布前等待，公布后确认方向再进场 |
| ❌ 把 OVX/VIX 的绝对数值当作精确信号 | ✅ OVX/VIX 看区间和趋势，单点值只作区间判断 |
| ❌ 🆕 f-string 嵌套 `r["key"]` → SyntaxError（如 `f"${r["h"]}"` 中 `"` 破坏语法） | ✅ 先 `v = r["h"]` 再 `f"${v}"`，或用 `%` / `format()` |
| ❌ 同会话内先跑 BTC 再跑期货（如 GC）→ 429 配额耗尽，宏观/DXY/VIX 全部降级 | ✅ 多资产分析时从「最需要宏观数据的品种」开始（GC 比 BTC 更需要 DXY/VIX），或两品种之间间隔 ≥ 60s 等速率窗口重置。如果已经耗尽了，标注「宏观 429 降级，以新闻推断替代」即可，不影响技术结构判断 |
| TP%、SL%、加权 RR、仓位示例算术互相打架 | ✅ 发布前逐项复核百分比与仓位公式 |
| GC 分析中把 BTC 分析后的 429 限流错误原样搬入报告 | ✅ 429 降级后标注「数据缺口」即可，不要写 YAML 错误原文 |
| 多个数据块并行拉取时 Yahoo 429 频繁（BTC+GC 连续分析） | ✅ 串行拉取每块加 2s 延迟；宏观块与价格块之间留 3s 冷却 |

---

## 八、品种专属逻辑

### 🛢️ CL（WTI 原油）

**驱动优先级：地缘 > OPEC+ > 库存(EIA) > 美元 > 技术结构**

- **核心情绪代理**：`^OVX`（原油波动率指数）
- **ETF 代理**：`USO`
- **关键关联**：`DXY`（负相关）、`GC=F`（同向避险时）、`^GSPC`（需求预期）
- **EIA 库存**：每周三 10:30 AM ET 公布，是原油最重要的定期数据事件
- **OPEC+**：会议前后波动剧烈，技术面失效概率高
- **季节性**：夏季驾驶季（5-9月）需求偏强，秋季检修季（9-10月）需求偏弱
- **跳空风险**：周末地缘事件可导致周一开盘 $3-5 跳空
- **做多条件**：higher low + OVX 不上升 + 无利空新闻 + 盈亏比 >1.5
- **做空条件**：lower high + OVX 下降趋势 + 无升级信号 + 跌破关键支撑

### 🥇 GC（黄金）

**驱动优先级：实际利率/美债收益率 > 美元 > 避险需求 > 技术结构**

- **核心情绪代理**：`^VIX`（无专属波动率指数，VIX 替代参考）
- **ETF 代理**：`GLD`
- **关键关联**：`^TNX`（强负相关——实际利率↑ = 黄金↓）、`DXY`（负相关）、`^VIX`（正相关避险时）
- **核心逻辑**：黄金是「实际利率的反面」——实际利率下行 = 黄金涨；实际利率上行 = 黄金跌
- **避险逻辑**：地缘危机时黄金常与美元同涨（避险资金流入），这与商品的美元负相关逻辑不同
- **美联储**：FOMC 会议和点阵图是黄金最大的事件驱动
- **央行购金**：需关注各国央行购金动态（中长期背景，不用于日内）
- **做多条件**：higher low + 10Y 收益率下行/至少不升 + 美元不强 + 盈亏比 >1.5
- **做空条件**：lower high + 10Y 收益率上行 + 美元走强 + 跌破关键支撑

### 🥈 SI（白银）

**驱动优先级：黄金联动 > 工业需求 > 美元 > 技术结构**

- **核心情绪代理**：`^VIX`（替代参考）
- **ETF 代理**：`SLV`
- **双面属性**：白银兼具贵金属（避险）和工业金属（经济周期）双重属性
- **金银比**：金银比 > 85 = 白银相对便宜；金银比 < 65 = 白银相对贵
- **工业需求**：光伏、电子等工业需求是关键基本面变量
- **波动性**：白银波动通常为黄金的 1.5-2 倍，止损需相应放宽
- **做多条件**：黄金结构偏多 + 工业数据不差 + higher low 确认
- **做空条件**：黄金结构偏空 + 工业数据走弱 + lower high 确认

### 🔧 HG（铜）

**驱动优先级：中国宏观 > 库存 > 美元 > 技术结构**

- **核心情绪代理**：`^VIX`（替代参考）
- **ETF 代理**：无主流 ETF，可用 `COPX` 作弱参考
- **核心逻辑**：铜是「经济晴雨表」——全球经济预期直接影响铜价
- **中国经济**：中国占全球铜消费约 50%，中国 PMI/信贷数据/房地产是核心驱动
- **库存**：LME（伦敦金属交易所）和 SHFE（上海期货交易所）库存数据
- **美元**：标准负相关（DXY↑ → 铜价↓）
- **做多条件**：中国宏观数据改善 + 库存下降 + higher low + DXY 不强势
- **做空条件**：中国宏观数据恶化 + 库存上升 + lower high + DXY 走强

### 🔥 NG（天然气）

**驱动优先级：天气 > 库存(EIA) > 产量 > 技术结构**

- **核心情绪代理**：`^OVX`（部分参考，天然气无专属波动率指数）
- **ETF 代理**：`UNG`（但杠杆损耗严重，仅作弱参考）
- **天气**：天然气最核心的驱动——冬季取暖需求（11-3月）、夏季制冷需求（6-9月）
- **EIA 天然气库存**：每周四 10:30 AM ET 公布
- **季节性**：补库季（4-10月）通常价格承压，去库季（11-3月）通常价格支撑
- **极端波动**：天然气单日波动 5-10% 常见，止损要比其他品种更宽
- **做多条件**：天气预报告冷/热 + 库存低于 5 年均值 + higher low
- **做空条件**：天气温和 + 库存充裕 + lower high

### 📊 ES（标普500 期货）

**驱动优先级：利率/Fed > 市场风险偏好 > 财报季 > VIX > 技术结构**

- **核心情绪代理**：`^VIX`
- **ETF 代理**：`SPY`
- **核心逻辑**：Fed 政策预期是最核心驱动——鸽派 = 涨，鹰派 = 跌
- **FOMC**：会议前后是最大的事件风险
- **VIX**：<15 安逸看涨，>30 恐慌观望
- **财报季**：每年 1/4/7/10 月，个股财报可影响指数方向
- **经济数据**：非农、CPI、GDP 等关键数据影响 Fed 预期
- **做多条件**：higher low + VIX <20 且不上升 + Fed 预期偏鸽 + 盈亏比 >1.5
- **做空条件**：lower high + VIX 上升 + Fed 预期偏鹰 + 跌破关键支撑

### 🖥️ NQ（纳斯达克100 期货）

**驱动优先级：利率/Fed > 科技股风险偏好 > AI/科技催化剂 > VIX > 技术结构**

- **核心情绪代理**：`^VIX`
- **ETF 代理**：`QQQ`
- **利率敏感**：纳斯达克对利率更敏感（成长股估值依赖低利率）——10Y 收益率↑ = NQ 承压
- **VIX**：NQ 对 VIX 的敏感性高于 ES
- **集中度风险**：Mag7（AAPL/MSFT/NVDA/GOOGL/AMZN/META/TSLA）占 NQ 权重极高
- **做多条件**：higher low + VIX <20 + 10Y 收益率不上升 + 科技面无利空
- **做空条件**：lower high + VIX 上升 + 10Y 收益率上行 + 科技龙头破位

### 🏭 YM（道琼斯 期货）

**驱动优先级：利率/Fed > 价值/周期性板块 > 经济数据 > VIX > 技术结构**

- **核心情绪代理**：`^VIX`
- **ETF 代理**：`DIA`
- **特征**：相比 ES/NQ 更偏向价值股和周期性板块（金融、工业、消费品）
- **利率**：对利率的敏感度介于 ES 和 NQ 之间
- **经济数据**：对就业和工业产出数据更敏感
- **做多条件**：higher low + VIX 不上升 + 经济数据偏强 + 盈亏比 >1.5
- **做空条件**：lower high + VIX 上升 + 经济数据走弱

### 📐 RTY（罗素2000 期货）

**驱动优先级：利率/Fed > 美国国内经济 > 中小银行 > VIX > 技术结构**

- **核心情绪代理**：`^VIX`
- **ETF 代理**：`IWM`
- **国内聚焦**：RTY 是纯美国国内经济晴雨表（小盘股海外收入占比低）
- **利率敏感**：小盘股对利率最敏感（融资依赖高）——降息预期 = RTY 受益最大
- **中小银行**：区域银行危机时 RTY 暴跌（2023年3月 SVB 事件）
- **做多条件**：higher low + VIX <20 + 降息预期 + 无银行危机
- **做空条件**：lower high + VIX 上升 + 利率维持高位 + 银行业承压

---

## 九、非期货标的处理

当用户要求分析的品种不在 `CL/BZ/GC/SI/HG/NG/PL/PA/ES/NQ/YM/RTY` 范围内时：

1. **先判断是否可通过 Yahoo Finance `{SYM}=F` 格式覆盖**：如 `ZC=F`（玉米）、`ZS=F`（大豆）、`ZW=F`（小麦）等农产品期货
2. **若可覆盖**：沿用本框架，但需标注「品种专属逻辑缺失，按通用商品逻辑分析」
3. **若为现货/ETF**（如 `XAUUSD`、`SPY`）：降级分析——仅保留技术面 + 交叉验证 + 情绪面，标注「非期货标的，市场结构/期限结构维度缺失」
4. **若为外汇**：不适用本框架，建议使用专用外汇分析技能

---

## 注意事项

- Yahoo Finance chart API 偶发 429/空响应，请求间隔至少 1 秒；若连续失败，停止补抓并标注数据缺口
- 所有 Yahoo Finance 请求必须带 `User-Agent: Mozilla/5.0` 头
- 4H K 线通过 1H 数据聚合得到，非原生数据，标注「聚合4H」
- COT 报告天然滞后 3 天，**绝不**用于日内决策，仅在波段/中长期背景中提及
- 周末和节假日期货电子盘仍在交易但流动性极低，技术信号可靠性下降
- 近月合约临近到期（通常到期前 1-2 周）时流动性下降，注意移仓换月
- 预测必须标注「不构成投资建议」
- 数据缺失时明确标注缺口，**绝不编造**
- OVX 数据仅对原油/能源有直接意义；其他品种用 VIX 替代参考
- 新闻采集使用 Google News RSS（比直接搜索更稳定），但仍会混入评论稿和二手转载，需主动降噪
- 所有 curl 管道中的 Python 代码应避免嵌套引号和 emoji（避免 shell 转义错误），错误时先降级为简单脚本
- 独立数据块尽量并行执行，减少串行等待时间
