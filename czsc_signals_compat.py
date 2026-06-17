"""
czsc.signals 兼容层 — 适配 czsc v1.0.0rc8 (Rust 核心)

v1.0.0rc8 将信号函数编译为 Rust 原生代码，通过 czsc._native.call_signal 调用。
此模块将旧的 Python 风格 import（如 from czsc.signals import cxt_first_buy_V221126）
映射到新的 call_signal API，确保现有脚本无需修改即可运行。

⚠️ 安装方式：install.sh 会将此文件复制到 czsc 包目录下。
   升级 czsc 后需重新运行 install.sh 或手动重新复制。
   未来计划改为独立 pip 包，避免污染 site-packages。

用法:
    from czsc.signals import cxt_first_buy_V221126, cxt_second_bs_V230320
    result = cxt_first_buy_V221126(c)  # c = CZSC 对象
"""

import warnings
from czsc._native import call_signal as _call_signal
from typing import Any, Dict, List, Optional
from czsc import CZSC

# ─── 版本检查 ───
try:
    import czsc
    _czsc_version = getattr(czsc, '__version__', 'unknown')
    if not _czsc_version.startswith('1.0.0'):
        warnings.warn(
            f"czsc_signals_compat.py 是为 czsc 1.0.0rc8 编写的，"
            f"当前 czsc 版本为 {_czsc_version}，可能存在兼容性问题。",
            UserWarning,
            stacklevel=2,
        )
except Exception:
    pass

# ─── 工厂函数：为每个信号名生成调用函数 ───

def _make_signal_func(name: str):
    """创建一个闭包函数，调用 call_signal(name, c)"""
    def _signal_wrapper(c: CZSC) -> List[Any]:
        return _call_signal(name, c)
    _signal_wrapper.__name__ = name
    _signal_wrapper.__doc__ = f"信号: {name}\n调用 call_signal('{name}', c) — czsc v1.0.0rc8"
    return _signal_wrapper

# ─── 一买 / 一卖 ───
cxt_first_buy_V221126 = _make_signal_func('cxt_first_buy_V221126')
cxt_first_sell_V221126 = _make_signal_func('cxt_first_sell_V221126')

# ─── 二买 / 二卖 ───
cxt_second_bs_V230320 = _make_signal_func('cxt_second_bs_V230320')
cxt_second_bs_V240524 = _make_signal_func('cxt_second_bs_V240524')

# ─── 三买 / 三卖 ───
cxt_third_buy_V230228 = _make_signal_func('cxt_third_buy_V230228')
cxt_third_bs_V230318 = _make_signal_func('cxt_third_bs_V230318')
cxt_third_bs_V230319 = _make_signal_func('cxt_third_bs_V230319')

# ─── 综合决策 ───
cxt_decision_V240614 = _make_signal_func('cxt_decision_V240614')

# ─── 笔结束 ───
cxt_bi_end_V230104 = _make_signal_func('cxt_bi_end_V230104')

# ─── 动态代理：未定义的信号名自动映射 ───
# 从 czsc._native.list_signal_names() 获取完整列表 (222个信号)
_SIGNAL_NAMES: Optional[List[str]] = None

def _get_signal_names() -> List[str]:
    global _SIGNAL_NAMES
    if _SIGNAL_NAMES is None:
        try:
            from czsc._native import list_signal_names
            _SIGNAL_NAMES = list_signal_names()
        except Exception:
            _SIGNAL_NAMES = []
    return _SIGNAL_NAMES

def __getattr__(name: str):
    """动态代理：任何未显式定义的信号名都自动映射到 call_signal"""
    # 跳过私有属性
    if name.startswith('_'):
        raise AttributeError(name)
    
    # 检查是否为已知信号名
    known = _get_signal_names()
    if not known or name in known:
        return _make_signal_func(name)
    
    raise AttributeError(f"未知信号: {name}")

# ─── 元信息 ───
__all__ = [
    'cxt_first_buy_V221126',
    'cxt_first_sell_V221126', 
    'cxt_second_bs_V230320',
    'cxt_second_bs_V240524',
    'cxt_third_buy_V230228',
    'cxt_third_bs_V230318',
    'cxt_third_bs_V230319',
    'cxt_decision_V240614',
    'cxt_bi_end_V230104',
]
