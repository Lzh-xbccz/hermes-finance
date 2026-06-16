#!/usr/bin/env python3
"""
中文化 czsc lightweight-charts HTML 工具提示标签
用法: python3 localize_chart.py in.html [-o out.html]
"""

import sys, os, re

REPLACEMENTS = [
    # tooltip 行标签
    ("<span class=\"tooltip__label\">Open</span>", "<span class=\"tooltip__label\">开</span>"),
    ("<span class=\"tooltip__label\">High</span>", "<span class=\"tooltip__label\">高</span>"),
    ("<span class=\"tooltip__label\">Low</span>", "<span class=\"tooltip__label\">低</span>"),
    ("<span class=\"tooltip__label\">Close</span>","<span class=\"tooltip__label\">收</span>"),
    
    # tooltip section 标题
    ("'VOLUME'", "'成交量'"),
    ("<span class=\"tooltip__label\">Change</span>", "<span class=\"tooltip__label\">涨跌</span>"),
    ("<span class=\"tooltip__label\">vol</span>", "<span class=\"tooltip__label\">量</span>"),
    ("<span class=\"tooltip__label\">ma_vol</span>", "<span class=\"tooltip__label\">均量</span>"),
    
    # 均线
    ("SMA5", "均线⑤"),
    ("SMA20", "均线⑳"),
    ("SMA 5", "均线⑤"),
    ("SMA 20", "均线⑳"),
    
    # 面板标题/其他
    ("PRICE · K + SMA + FX + BI", "价格 · K线+均线+分型+笔"),
    ("VOL · SMA 20", "成交量 · 均线⑳"),
    ("VOLUME", "成交量"),
    ("SIGNALS · @CURRENT BAR", "信号 · 当前K线"),
    ("Chg %", "涨跌%"),
    ("<span class=\"tooltip__label\">Vol</span>", "<span class=\"tooltip__label\">量</span>"),
    ("<span class=\"tooltip__label\">DIFF</span>", "<span class=\"tooltip__label\">差离值</span>"),
    ("<span class=\"tooltip__label\">DEA</span>", "<span class=\"tooltip__label\">信号线</span>"),
]


def localize_html(input_path: str, output_path: str = None) -> str:
    if output_path is None:
        base, ext = os.path.splitext(input_path)
        output_path = f"{base}_cn{ext}"
    
    with open(input_path, 'r', encoding='utf-8') as f:
        html = f.read()
    
    for old, new in REPLACEMENTS:
        if old != new:  # skip no-ops
            count = html.count(old)
            if count:
                html = html.replace(old, new)
                print(f"  {old[:50]:<50s} → {new:<20s} ({count})")
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)
    
    return output_path


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = None
    
    args = sys.argv[2:]
    i = 0
    while i < len(args):
        if args[i] == '-o' and i + 1 < len(args):
            output_file = args[i + 1]
            i += 2
        else:
            i += 1
    
    result = localize_html(input_file, output_file)
    size_kb = os.path.getsize(result) // 1024
    print(f"\n✅ {result} ({size_kb}KB)")
