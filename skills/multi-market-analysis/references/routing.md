# Market Routing

总路由的目标只有一个：把请求送到正确 skill。

## 1. 先跑分类脚本

```bash
python3 scripts/route_market.py "CL"
python3 scripts/route_market.py "EURUSD"
python3 scripts/route_market.py "600519"
```

返回值：
- `crypto`
- `a_share`
- `futures`
- `forex`
- `us_equity`
- `ambiguous`

## 2. 分类后的固定跳转

| 分类结果 | 跳转 skill |
|---------|------------|
| `crypto` | `crypto-market-analysis` |
| `a_share` | `a-share-market-analysis` |
| `futures` | `futures-market-analysis` |
| `forex` | `forex-market-analysis` |
| `us_equity` | `us-equity-market-analysis` |

## 3. 常见默认映射

| 输入 | 默认市场 | 备注 |
|------|---------|------|
| `BTC` `ETH` `SOL` | `crypto` | |
| `CL` `BZ` `GC` `SI` `HG` `NG` `PL` `PA` | `futures` | 若用户只说“黄金/原油”，仍需警惕歧义 |
| `CLUSDT` `BZUSDT` `XAUUSDT` `XAGUSDT` `COPPERUSDT` `NATGASUSDT` `XPTUSDT` `XPDUSDT` | `futures` | Binance TradFi 商品永续，不要按 `USDT` 误路由到 crypto |
| `ES` `NQ` `YM` `RTY` | `futures` | 默认股指期货 |
| `EURUSD` `USDJPY` `GBPUSD` `DXY` | `forex` | |
| `AAPL` `MSFT` `NVDA` `SPY` `QQQ` | `us_equity` | |
| `A股` `上证` `深证` `创业板` `600519` | `a_share` | |

## 4. 必须先确认的歧义

这些词不能直接强行分类：

- `黄金`
  - 可能是 `GC`、`XAUUSD`、`GLD`、A股黄金股
- `原油`
  - 可能是 `CL`、Brent、`USO`、`SC`
- `纳指`
  - 可能是 `NQ`、`QQQ`、`^IXIC`

如果上下文不能消歧，就先问。

## 5. 总路由不做的事

- 不在这里直接写完整交易报告
- 不在这里定义每个市场的详细指标
- 不在这里拍板 `做多 / 做空`

这些都留给目标 skill 完成。
