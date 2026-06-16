"""策略基类模块：定义所有选股策略的抽象接口。"""

from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable

from sequoia.core.config import Settings
from sequoia.data.engine import DataEngine


class BaseStrategy(ABC):
    """选股策略抽象基类。

    所有具体策略必须继承此类并实现 run() 方法。

    Attributes:
        webhook_key: 策略对应的飞书 webhook 标识，用于路由到不同机器人。
            默认为 'default'，将使用 Settings.feishu_webhook_url。
            子类可覆盖此属性以路由到专属机器人，例如 'ma_volume'。
    """

    webhook_key: str = "default"
    _PARALLEL_WORKERS: int = 8       # 并行线程数
    _BATCH_SIZE: int = 500           # 每批处理股票数

    def __init__(self, engine: DataEngine, settings: Settings) -> None:
        """
        初始化策略。

        Args:
            engine: DataEngine 实例，用于读取行情数据。
            settings: Settings 实例，用于读取配置。
        """
        self.engine = engine
        self.settings = settings

    def _run_parallel(self, symbols: list[str], check_one: Callable[[str], str | None]) -> list[str]:
        """并行遍历股票列表，对每只调用 check_one(symbol)，收集非 None 结果。
        
        Args:
            symbols: 全市场股票代码列表。
            check_one: 单只股票检查函数，返回股票代码（通过）或 None（不通过）。
        
        Returns:
            通过检查的股票代码列表。
        """
        if len(symbols) < 100:
            # 少量股票直接串行，避免线程开销
            result = []
            for s in symbols:
                r = check_one(s)
                if r is not None:
                    result.append(r)
            return result
        
        selected: list[str] = []
        with ThreadPoolExecutor(max_workers=self._PARALLEL_WORKERS) as pool:
            futures = {pool.submit(check_one, s): s for s in symbols}
            for future in as_completed(futures):
                try:
                    r = future.result()
                    if r is not None:
                        selected.append(r)
                except Exception:
                    pass
        return selected

    @abstractmethod
    def run(self) -> list[str]:
        """
        执行选股逻辑，返回选中的股票代码列表。

        Returns:
            满足策略条件的股票代码列表，如 ['000001', '600519']。
            无选股结果时返回空列表。
        """
        ...
