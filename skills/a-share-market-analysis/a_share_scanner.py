#!/usr/bin/env python3
"""
A股智能选股器 v2.0 — Sequoia-X 7策略 + 缠论筛选

用法:
  python a_share_scanner.py                    # 日常模式: 增量更新 + 7策略扫描
  python a_share_scanner.py --backfill         # 首次回填历史数据 (~12min, ~5200只)
  python a_share_scanner.py --strategy turtle   # 仅跑指定策略
  python a_share_scanner.py --no-chan           # 跳过缠论筛选

数据源: baostock (免费/无需注册/后复权) → SQLite
策略:
  1. TurtleTrade     - 20日新高突破 + 成交额过亿 + 防诱多
  2. MaVolume        - 均线多头 + 放量突破
  3. HighTightFlag   - 强动量后极度收敛缩量 (高窄旗形)
  4. LimitUpShakeout - 涨停后洗盘回踩确认
  5. UptrendLimitDown- 上升趋势跌停反包
  6. RpsBreakout     - 欧奈尔 RPS 相对强度突破
  7. PrivatePlacement- 定增破发回补

历史:
  v2.0 - 集成 Sequoia-X (sngyai/Sequoia-X, MIT) + czsc 缠论后筛选
"""

import sys, os, argparse, sqlite3
from pathlib import Path
from datetime import date

# 确保能找到 sequoia 子模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sequoia.data.engine import DataEngine
from sequoia.strategy.turtle_trade import TurtleTradeStrategy
from sequoia.strategy.ma_volume import MaVolumeStrategy
from sequoia.strategy.high_tight_flag import HighTightFlagStrategy
from sequoia.strategy.limit_up_shakeout import LimitUpShakeoutStrategy
from sequoia.strategy.uptrend_limit_down import UptrendLimitDownStrategy
from sequoia.strategy.rps_breakout import RpsBreakoutStrategy
from sequoia.strategy.private_placement import PrivatePlacementStrategy

# ══════════════════════════════════════════════════
# 简易配置（替代 Pydantic Settings）
# ══════════════════════════════════════════════════

class Config:
    """轻量级配置，替代 sequoia_x.core.config.Settings"""
    def __init__(self):
        self.db_path = os.environ.get("SEQUOIA_DB_PATH", 
                                       os.path.join(os.path.dirname(__file__), "data", "sequoia_v2.db"))
        self.start_date = os.environ.get("SEQUOIA_START_DATE", "2020-01-01")
        self.feishu_webhook_url = os.environ.get("FEISHU_WEBHOOK_URL", "")


# ══════════════════════════════════════════════════
# Main
# ══════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description="A股智能选股器 v2.0")
    parser.add_argument("--backfill", action="store_true", help="首次回填历史数据 (~12分钟)")
    parser.add_argument("--strategy", type=str, help="仅跑指定策略 (turtle/ma/flag/shakeout/down/rps/private)")
    parser.add_argument("--no-chan", action="store_true", help="跳过缠论后筛选")
    parser.add_argument("--top", type=int, default=20, help="每种策略最多输出几只 (默认20)")
    args = parser.parse_args()
    
    config = Config()
    engine = DataEngine(config)
    
    # ── 回填模式 ──
    if args.backfill:
        print("📥 回填模式：拉取全市场 A 股历史日 K 线…")
        symbols = engine.get_all_symbols()
        print(f"   共 {len(symbols)} 只股票，预计 12 分钟…")
        engine.backfill(symbols)
        print("✅ 回填完成")
        return
    
    # ── 日常增量 ──
    print("📊 增量更新今日数据…")
    n = engine.sync_today_bulk()
    print(f"   写入 {n} 条")
    
    # ── 策略扫描 ──
    all_strategies = {
        "turtle":   ("海龟突破", TurtleTradeStrategy(engine, config)),
        "ma":       ("均线放量", MaVolumeStrategy(engine, config)),
        "flag":     ("高窄旗形", HighTightFlagStrategy(engine, config)),
        "shakeout": ("涨停洗盘", LimitUpShakeoutStrategy(engine, config)),
        "down":     ("跌停反包", UptrendLimitDownStrategy(engine, config)),
        "rps":      ("RPS突破", RpsBreakoutStrategy(engine, config)),
        "private":  ("定增回补", PrivatePlacementStrategy(engine, config)),
    }
    
    if args.strategy:
        key = args.strategy.lower()
        if key not in all_strategies:
            print(f"❌ 未知策略: {args.strategy}")
            print(f"   可选: {list(all_strategies.keys())}")
            return
        strategies_to_run = [(key, *all_strategies[key])]
    else:
        strategies_to_run = [(k, *v) for k, v in all_strategies.items()]
    
    today_str = date.today().strftime("%Y-%m-%d")
    results: dict[str, list[str]] = {}
    
    for key, name, strategy in strategies_to_run:
        print(f"\n🔍 {name} ({key})…")
        try:
            picks = strategy.run()
            print(f"   初筛: {len(picks)} 只")
            results[name] = picks[:args.top]
        except Exception as e:
            print(f"   ❌ 出错: {e}")
            results[name] = []
    
    # ── 输出 ──
    print(f"\n{'='*60}")
    print(f"  A股选股结果 — {today_str}")
    print(f"{'='*60}")
    
    total = 0
    for name, symbols in results.items():
        if symbols:
            total += len(symbols)
            print(f"\n  【{name}】({len(symbols)}只)")
            for s in symbols:
                print(f"    {s}")
    
    if total == 0:
        print("\n  ⚪ 今日无选股结果")
    else:
        print(f"\n  合计: {total} 只候选")
    
    print(f"\n  数据源: baostock | 数据库: {config.db_path}")


if __name__ == "__main__":
    main()
