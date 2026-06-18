#!/usr/bin/env python3
"""
A股东方财富数据采集脚本
用于从东方财富网页抓取 A 股关键数据返回结构化 JSON。
配合 Hermes browser 工具使用：先通过 browser_navigate + browser_console 提取原始数据，
再传给本脚本做解析和标准化。

数据页面：
  1. 北向资金：https://data.eastmoney.com/hsgt/index.html
  2. 板块排行：https://data.eastmoney.com/bkzj/hy.html  
  3. 大盘资金流向：https://data.eastmoney.com/cjsj/hqtzcj.html

作者：李小白菜吃猪 + Hermes
"""

import json
import sys
from datetime import datetime, timezone, timedelta


def parse_number(s: str) -> float:
    """从带中文单位的字符串中提取纯数字，如 '101.34亿元' → 101.34"""
    if not s:
        return 0.0
    s = s.strip().replace('亿元', '').replace('万', '').replace('%', '').replace(',', '')
    try:
        return float(s)
    except ValueError:
        return 0.0


def parse_northbound(raw_table_data: list) -> dict:
    """
    解析北向资金页面表格数据
    raw_table_data: browser_console 提取的 document.querySelectorAll 结果
    页面结构：第一个表格是港股通，第二个是陆股通（北向）
    """
    result = {
        "hgt": {},   # 沪股通
        "sgt": {},   # 深股通
        "total_net": 0.0,
        "status": "收盘"
    }

    for row in raw_table_data:
        board = row.get("board", "")
        net_buy = row.get("netBuy", "")

        if "港>沪" in board:
            result["hgt"] = {
                "net_buy": parse_number(net_buy),
                "total_vol": parse_number(row.get("totalVol", "0")),
                "balance": row.get("balance", ""),
                "up": int(parse_number(row.get("up", "0"))),
                "flat": int(parse_number(row.get("flat", "0"))),
                "down": int(parse_number(row.get("down", "0"))),
            }
            result["status"] = row.get("status", "收盘")
        elif "港>深" in board:
            result["sgt"] = {
                "net_buy": parse_number(net_buy),
                "total_vol": parse_number(row.get("totalVol", "0")),
                "balance": row.get("balance", ""),
                "up": int(parse_number(row.get("up", "0"))),
                "flat": int(parse_number(row.get("flat", "0"))),
                "down": int(parse_number(row.get("down", "0"))),
            }

    result["total_net"] = result["hgt"].get("net_buy", 0) + result["sgt"].get("net_buy", 0)
    return result


def parse_sectors(raw_table_data: list) -> dict:
    """解析板块排行数据，提取行业板块涨跌幅和资金流向"""
    sectors = []
    for row in raw_table_data:
        name = row.get("board", "")
        change_str = row.get("netBuy", "")
        flow_str = row.get("totalVol", "")
        if not name or name.isdigit():
            continue
        change = parse_number(change_str)
        flow = parse_number(flow_str) if flow_str else 0
        sectors.append({"name": name, "change_pct": change, "net_flow_yi": flow})
    sectors.sort(key=lambda x: x["change_pct"], reverse=True)
    return {"top_gainers": sectors[:10], "top_losers": sectors[-10:][::-1] if len(sectors) >= 10 else []}


def parse_capital_flow(raw_table_data: list) -> dict:
    """解析大盘资金流向，提取主力/超大单/大单/中单/小单净流入"""
    result = {"super_large": 0.0, "large": 0.0, "medium": 0.0, "small": 0.0, "main_net": 0.0}
    for row in raw_table_data:
        board = row.get("board", "")
        net = parse_number(row.get("netBuy", "0"))
        if "超大单" in board:
            result["super_large"] = net
        elif "大单" in board:
            result["large"] = net
        elif "中单" in board:
            result["medium"] = net
        elif "小单" in board:
            result["small"] = net
    result["main_net"] = result["super_large"] + result["large"]
    return result


def parse_market_breadth(raw_table_data: list) -> dict:
    """解析涨跌家数"""
    for row in raw_table_data:
        board = row.get("board", "")
        up = int(parse_number(row.get("up", "0")))
        down = int(parse_number(row.get("down", "0")))
        flat = int(parse_number(row.get("flat", "0")))
        if up + down + flat > 10:
            return {"up": up, "down": down, "flat": flat}
    return {"up": 0, "down": 0, "flat": 0}


def get_beijing_time() -> str:
    bjt = timezone(timedelta(hours=8))
    return datetime.now(bjt).strftime("%Y-%m-%dT%H:%M:%S+08:00")


def get_session_state() -> str:
    """
    仅根据北京时间时钟判断 A 股会话状态。
    注意：这里不覆盖法定节假日，调用方仍需结合行情时间戳二次确认。
    """
    bjt = timezone(timedelta(hours=8))
    now = datetime.now(bjt)
    if now.weekday() >= 5:
        return "weekend"
    t = now.hour * 60 + now.minute
    if 570 <= t < 690:      # 09:30-11:30
        return "morning"
    if 690 <= t < 780:      # 11:30-13:00
        return "lunch_break"
    if 780 <= t <= 900:     # 13:00-15:00
        return "afternoon"
    return "closed"


def is_trading_time() -> bool:
    """判断当前是否为 A 股连续竞价时段（不含午间休市，且不含法定节假日校验）"""
    return get_session_state() in {"morning", "afternoon"}


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({
            "error": "用法: python a_share_data.py <data_type> [json_data]",
            "types": ["northbound", "sectors", "capital_flow", "breadth"]
        }, ensure_ascii=False, indent=2))
        sys.exit(1)

    data_type = sys.argv[1]
    raw = []
    if len(sys.argv) >= 3:
        raw_text = sys.argv[2]
    else:
        raw_text = sys.stdin.read()

    try:
        raw = json.loads(raw_text)
    except json.JSONDecodeError:
        print(json.dumps({"error": "无效的 JSON 输入"}, ensure_ascii=False))
        sys.exit(1)

    parsers = {
        "northbound": parse_northbound,
        "sectors": parse_sectors,
        "capital_flow": parse_capital_flow,
        "breadth": parse_market_breadth,
    }

    parser = parsers.get(data_type)
    if not parser:
        print(json.dumps({"error": f"未知数据类型: {data_type}"}, ensure_ascii=False))
        sys.exit(1)

    output = parser(raw)
    output["timestamp"] = get_beijing_time()
    output["is_trading_time"] = is_trading_time()
    output["session_state"] = get_session_state()
    output["calendar_note"] = "仅基于北京时间时钟判断，不含法定节假日；需结合指数/北向资金时间戳二次确认"
    print(json.dumps(output, ensure_ascii=False, indent=2))
