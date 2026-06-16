# Deribit BTC Options API 实战指南

> 用途：为 crypto-market-analysis 增加期权波动率维度（VIX/OVX 的加密对应项）

## 核心 API

| 端点 | 用途 |
|------|------|
| `GET /api/v2/public/get_index_price?index_name=btc_usd` | BTC 指数价格 |
| `GET /api/v2/public/get_instruments?currency=BTC&kind=option&expired=false` | 所有未到期合约列表 |
| `GET /api/v2/public/ticker?instrument_name={NAME}` | 单合约 IV + Greeks |
| `GET /api/v2/public/get_book_summary_by_currency?currency=BTC&kind=option` | 24h 汇总（成交量、OI） |

## ⚠️ 已踩坑（必读）

### 坑 1：`mark_iv` 单位
- **Deribit 返回的 `mark_iv` 已经是百分比**：`0.2715` = 27.15%
- **不要乘以 100！** 直接使用即是百分比
- 错误示例：`iv = d.get('mark_iv', 0) * 100` → 返回 2715.0%（错误）
- 正确示例：`iv = d.get('mark_iv', 0)` → 0.2715，要打印时用 `f'{iv*100:.1f}%'` → "27.2%"

### 坑 2：到期日当天/次日合约
- 到期日当天（如 5 月 8 日分析 5 月 8 日到期的合约）：IV 可能返回 absurd 值
- Mark price 可能为 $0（时间价值归零）
- **跳过当日和次日到期的合约**，用至少 2 天后的到期日

### 坑 3：合约命名格式
- 格式：`BTC-DDMMMYY-STRIIKE-C` 或 `BTC-DDMMMYY-STRIIKE-P`
- 例：`BTC-10MAY26-79500-C`
- 月份缩写：JAN FEB MAR APR MAY JUN JUL AUG SEP OCT NOV DEC
- 如果 API 返回 400，可能是到期日格式或合约名不存在

## 推荐采集流程

```python
# Step 1: 获取 BTC 指数价
r = urlopen('https://www.deribit.com/api/v2/public/get_index_price?index_name=btc_usd')
btc_idx = json.load(r)['result']['index_price']

# Step 2: 获取所有未到期合约，按到期日分组
r = urlopen('https://www.deribit.com/api/v2/public/get_instruments?currency=BTC&kind=option&expired=false')
instruments = json.load(r)['result']

# Step 3: 选最近的非当日/次日到期日
from collections import Counter
expiries = sorted(set(i['expiration_timestamp'] for i in instruments))
# 跳过前 2 个（当日 + 次日）
target_ts = expiries[2]  # 至少 2 天后
target_insts = [i for i in instruments if i['expiration_timestamp'] == target_ts]

# Step 4: 找到 ATM 合约
atm = min(target_insts, key=lambda i: abs(i['strike'] - btc_idx))

# Step 5: 获取 IV（注意：不乘 100）
r = urlopen(f'https://www.deribit.com/api/v2/public/ticker?instrument_name={atm["instrument_name"]}')
iv = json.load(r)['result']['mark_iv']  # ← 直接就是百分比，如 0.2715 = 27.15%

# Step 6: 偏斜分析（OTM Put vs OTM Call）
put_inst = min(target_insts, key=lambda i: abs(i['strike'] - btc_idx * 0.85))
call_inst = min(target_insts, key=lambda i: abs(i['strike'] - btc_idx * 1.15))
put_iv = get_iv(put_inst)  # 同上，不乘 100
call_iv = get_iv(call_inst)
skew = put_iv - call_iv  # 正 = 看跌偏斜（puts 贵），负 = 看涨偏斜（calls 贵）

# Step 7: 24h Put/Call 流量比
r = urlopen('https://www.deribit.com/api/v2/public/get_book_summary_by_currency?currency=BTC&kind=option')
data = json.load(r)['result']
put_vol = sum(d['volume_usd'] for d in data if d['instrument_name'].endswith('-P'))
call_vol = sum(d['volume_usd'] for d in data if d['instrument_name'].endswith('-C'))
pcr = put_vol / call_vol if call_vol > 0 else 0
# PCR > 1.2 = bearish flow; < 0.8 = bullish flow
```

## 信号解读

| 指标 | 看涨信号 | 看跌信号 | 中性 |
|------|---------|---------|------|
| Put/Call 量比 | < 0.8 | > 1.2 | 0.8-1.2 |
| 偏斜 (Put IV - Call IV) | < -3% | > +3% | -3% ~ +3% |
| ATM IV 水平 | 极低 (<40%) → 压缩后可能爆发 | 极高 (>90%) → 恐慌定价 | 40-70% 正常 |

## ⚠️ 数据质量警告
- Deribit 公开 API 无频率限制（相对宽松），但不要并发 >5 个请求
- 24h Put/Call 量比在亚洲时段可能偏低（Deribit 主要流动性在欧美时段）
- 大到期日（月底/季末）后 IV 可能骤降（vol crush），不要误判为情绪改善
