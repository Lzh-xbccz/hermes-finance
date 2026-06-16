# 增强宏观块：免费数据源方案

> 用于 crypto-market-analysis 块 5b。当 LSEG/Refinitiv MCP 不可用时，用 Yahoo Finance 免费 API 实现 macro-rates-monitor 级别的宏观分析。

## 数据源速查

> ⚠️ **首选 CNBC quotes**（2026-05-11 实测）：Yahoo Finance 429 频繁且被 `custom-model-providers` 铁律禁止调 `mcp_yfinance`。Tavily 对 VIX/DXY 常返回空。TradingView CSS 动态变化。**CNBC `/quotes/` 端点用 curl+grep 直接拿，最可靠**。

| 指标 | CNBC 端点 | 对 BTC 的含义 |
|------|-----------|-------------|
| 10Y 美债收益率 | `/quotes/US10Y` | 实际利率 ↑ = BTC 承压（机会成本） |
| 美元指数 | `/quotes/.DXY` | DXY ↓ = BTC ↑（历史负相关） |
| 标普 500 | `/quotes/.SPX` | 风险偏好，ρ≈0.6-0.8 与 BTC |
| VIX | `/quotes/VIX` | >30 = 恐慌 → BTC 承压 |

```bash
# 批量获取宏观测
for s in VIX .DXY US10Y .SPX; do
  echo -n "$s: "
  curl -s --max-time 10 "https://www.cnbc.com/quotes/$s" \
    -H "User-Agent: Mozilla/5.0" | grep -oP '"last":"[^"]*"'
done
```

## 增强分析清单

### 1. 利率环境
- 实际利率估算: 10Y - CPI(约2.8%) ≈ X.X%
- > 1.5% = 限制性 → BTC 中期承压
- < 0.5% = 宽松 → BTC 中期利好

### 2. 美元强弱
- DXY > 105：强势 → 风险资产承压
- DXY < 100：弱势 → BTC 受益
- 单日变动 > 1%：异常信号

### 3. 背离检测（最重要）
- SPX↑ + DXY↓ + BTC↓ → **BTC 内部弱势**（最强利空信号）
- SPX↓ + VIX↑ + BTC↓ → 系统性 risk-off（正常联动）
- SPX↑ + DXY↓ + BTC↑ → 美元弱 risk-on（正常联动）

### 4. Fed 日历
- 当前利率: 4.25-4.50%
- 下次 FOMC: 2026-06-17
- FOMC 前 48h → 宏观权重 > 技术面

## 拉取代码

直接用 CNBC curl（见上方），无需 Python。如需程序化处理：

```python
from hermes_tools import terminal

tickers = {"VIX": "VIX", "DXY": ".DXY", "10Y": "US10Y", "SPX": ".SPX"}
for name, ticker in tickers.items():
    cmd = f'curl -s --max-time 10 "https://www.cnbc.com/quotes/{ticker}" -H "User-Agent: Mozilla/5.0" | grep -oP \'"last":"[^"]*"\''
    r = terminal(cmd)
    print(f"{name}: {r.get('output','').strip()}")
```

## 429 / 失败降级

| 场景 | 处理 |
|------|------|
| CNBC 返回空 | 试 Google Finance → Tavily extract → 标注「宏观数据暂缺」 |
| 全部失败 | 标注「宏观数据暂缺」，不影响技术/庄家维度的决策 |
| 周末/节假日 | 只作前收背景参考，不作为实时触发 |
