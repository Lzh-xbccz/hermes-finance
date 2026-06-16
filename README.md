# Hermes Finance — 缠论+多维度金融市场分析框架

> 基于 [czsc](https://github.com/waditu/czsc) v1.0 缠论库，覆盖加密货币/期货/外汇/A股/美股

## 分析维度

每个市场采用多维因果分析框架，集成缠论（czsc）作为核心技术分析维度：

| 市场 | 技能 | 维度数 |
|------|------|--------|
| 加密货币 | `crypto-market-analysis` | 八维（含缠论） |
| 商品期货 | `futures-market-analysis` | 六维 |
| 外汇 | `forex-market-analysis` | 六维 |
| A股 | `a-share-market-analysis` | 六维 |
| 美股 | `us-equity-market-analysis` | 六维 |
| 多市场路由 | `multi-market-analysis` | 自动识别 |

## 缠论集成 (czsc-ccxt-analysis)

- `CZSC` 对象：分型/笔/中枢自动识别
- 220+ 信号函数：一买/二买/三买/综合决策
- 多级别联立：4H + 15min 共振分析
- 可视化：plot_czsc_chart (Plotly) + kline_pro (ECharts)
- 数据源：CCXT (Binance) / 天勤 / Tushare

## 快速开始

```bash
pip install czsc ccxt pandas plotly
python scripts/czsc_analyze.py BTCUSDT 4h --signals --chart
```

## 项目结构

```
skills/          # 分析技能（SKILL.md + references）
  crypto-market-analysis/
  futures-market-analysis/
  forex-market-analysis/
  a-share-market-analysis/
  us-equity-market-analysis/
  multi-market-analysis/
  czsc-ccxt-analysis/
  microcap-pnd-system/
scripts/         # 可执行脚本
  czsc_analyze.py      # 缠论分析
  market_analyze.py    # 多市场分析
```

## 免责声明

本项目仅用于技术交流和学习研究，不构成任何投资建议。
