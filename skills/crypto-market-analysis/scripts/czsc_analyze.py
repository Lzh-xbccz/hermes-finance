#!/usr/bin/env python3
"""
czsc 缠论多级别分析 — 薄封装，核心逻辑在 ../../../../scripts/czsc_analyze.py

用法:
    python3 czsc_analyze.py BTCUSDT                    # 默认 4H+15min 联立
    python3 czsc_analyze.py BTCUSDT 4h,1h,15m          # 自定义多级别
    python3 czsc_analyze.py BTCUSDT --signals --chart --report

⚠️ 核心实现在 ../../../../scripts/czsc_analyze.py — 修改请去那边，本文件只做路由。
"""

import sys, os

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
_MAIN_SCRIPTS = os.path.join(_PROJECT_ROOT, 'scripts')
sys.path.insert(0, _MAIN_SCRIPTS)

if __name__ == '__main__':
    try:
        from czsc_analyze import main
        main()
    except ImportError as e:
        print(f"⚠️  无法加载主脚本: {e}")
        print(f"   路径: {_MAIN_SCRIPTS}/czsc_analyze.py")
        print(f"   请确认 czsc (含 ccxt_connector) 已安装: pip install git+https://github.com/waditu/czsc.git")
        sys.exit(1)
