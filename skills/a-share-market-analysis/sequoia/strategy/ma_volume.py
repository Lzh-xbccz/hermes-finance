"""均线+成交量选股策略：5日均线上穿20日均线且成交量放大。"""

import pandas as pd

from sequoia.core.logger import get_logger
from sequoia.strategy.base import BaseStrategy

logger = get_logger(__name__)


class MaVolumeStrategy(BaseStrategy):
    """均线+成交量选股策略。

    选股条件（全部向量化，严禁 iterrows）：
    1. 5日收盘均线上穿20日收盘均线（金叉）
    2. 当日成交量 > 20日均量的 1.5 倍（放量确认）

    Attributes:
        webhook_key: 路由到 'ma_volume' 专属飞书机器人。
    """

    webhook_key: str = "ma_volume"

    def run(self) -> list[str]:
        """
        并行遍历全市场，返回满足均线金叉+放量条件的股票代码列表。
        """
        symbols = self.engine.get_local_symbols()

        def _check(symbol: str) -> str | None:
            try:
                df = self.engine.get_ohlcv(symbol)
                if len(df) < 20:
                    return None
                df["ma5"] = df["close"].rolling(5).mean()
                df["ma20"] = df["close"].rolling(20).mean()
                df["vol_ma20"] = df["volume"].rolling(20).mean()
                last = df.iloc[-1]
                prev = df.iloc[-2]
                if (prev["ma5"] < prev["ma20"] and last["ma5"] > last["ma20"]
                        and last["volume"] > last["vol_ma20"] * 1.5):
                    return symbol
            except Exception as exc:
                logger.warning(f"[{symbol}] 策略计算失败：{exc}")
            return None

        selected = self._run_parallel(symbols, _check)
        logger.info(f"MaVolumeStrategy 选出 {len(selected)} 只股票")
        return selected
