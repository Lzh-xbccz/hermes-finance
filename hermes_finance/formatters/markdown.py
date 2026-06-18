"""Markdown output helpers."""

from __future__ import annotations

from typing import Any


def format_market_result(result: dict[str, Any]) -> str:
    """Format a combined market result for CLI/MCP clients."""

    fetch = result.get("fetch") or {}
    data = fetch.get("data")
    lines = [
        f"# Hermes Finance Analysis: {result.get('market')} {result.get('symbol')}",
        "",
        f"- Fetch status: {'ok' if fetch.get('ok') else 'failed'}",
        f"- Collector: {fetch.get('collector') or 'n/a'}",
        f"- CZSC: {_czsc_status(result.get('czsc'))}",
        "",
    ]
    lines.extend(_analysis_contract(result))
    if fetch.get("stderr"):
        lines.extend(["## Collector Stderr", _clip(fetch["stderr"], 1500), ""])
    if isinstance(data, dict):
        lines.extend(_source_status(data))
        lines.extend(_json_summary(data))
    elif fetch.get("output_text"):
        lines.extend(["## Collector Output", "```text", _clip(fetch["output_text"], 12000), "```", ""])
    czsc = result.get("czsc") or {}
    if czsc.get("report_text"):
        lines.extend(["## CZSC Report", _clip(czsc["report_text"], 12000), ""])
    elif czsc.get("output_text"):
        lines.extend(["## CZSC Output", "```text", _clip(czsc["output_text"], 12000), "```", ""])
    notes = result.get("notes") or []
    if notes:
        lines.append("## Notes")
        lines.extend(f"- {note}" for note in notes)
    return "\n".join(lines).rstrip() + "\n"


def _analysis_contract(result: dict[str, Any]) -> list[str]:
    """Return the required synthesis contract for market analysis outputs."""

    market = result.get("market")
    czsc = result.get("czsc")
    if czsc is None:
        czsc_line = "CZSC is missing. Mark dimension 8 as unavailable and downgrade confidence."
    elif czsc.get("ok"):
        czsc_line = "CZSC evidence is available. Use it only as dimension 8 confirmation."
    else:
        czsc_line = "CZSC failed. Mark dimension 8 as unavailable and downgrade final confidence."
    dimensions = _dimension_names(str(market))
    title = "Crypto Analysis Contract" if market == "crypto" else "Eight-Dimension Analysis Contract"

    return [
        f"## {title}",
        f"This is a {market} analysis result. Do not compress it into a quick market summary.",
        "",
        "Before writing the final answer, synthesize the evidence into this exact structure:",
        "",
        "1. 数据完整性",
        "2. 七维主判断（只基于 1-7 维，并写明各维度权重/主导因素；不允许用 CZSC 覆盖）",
        "3. 缠论确认（第 8 维，只做确认/冲突/不足；不得把 CZSC score 当最终方向）",
        "4. 最终方向（必须由七维主判断得出，再说明 CZSC 是确认、冲突还是降级原因）",
        "5. 因果叙事",
        "6. 八维深挖：" + "、".join(dimensions),
        "7. 情景推演（概率合计 100%）",
        "8. 交易计划和失效条件",
        "",
        f"- Strictness: {czsc_line}",
        "- Decision rule: final direction must be driven by dimensions 1-7. CZSC can refine entry/exit timing, confirm, conflict, or downgrade confidence, but it must not be the dominant reason for the trade.",
        "- For non-crypto markets, if a dimension has no direct equivalent, use the market-specific proxy and state the limitation.",
        "- Missing sections must be explicitly marked as unavailable; do not silently skip a dimension.",
        "",
    ]


def _dimension_names(market: str) -> list[str]:
    mapping = {
        "crypto": ["技术结构", "链上真相", "庄家博弈/合约结构", "情绪反指", "宏观驱动", "交易所交叉验证", "期权暗语", "缠论结构"],
        "futures": ["技术结构", "可执行合约层/OI/资金费率", "传统期货结构/CFTC/EIA", "主导力量", "情绪/波动率", "宏观与事件", "交叉验证", "缠论结构"],
        "forex": ["技术结构", "利差与美元结构", "央行/主导力量", "风险情绪", "宏观事件", "交叉验证", "仓位/CFTC", "缠论结构"],
        "us_equity": ["技术结构", "市场/行业结构", "公司事件/机构主导", "情绪与期权代理", "宏观利率", "同业/ETF交叉验证", "流动性与缺口风险", "缠论结构"],
        "a_share": ["技术结构", "资金面/北向", "市场结构/涨跌家数", "情绪量能", "宏观政策", "板块轮动", "量化/Sequoia信号", "缠论结构"],
    }
    return mapping.get(market, mapping["crypto"])


def _czsc_status(czsc: dict[str, Any] | None) -> str:
    if czsc is None:
        return "not requested or not applicable"
    return "ok" if czsc.get("ok") else "failed"


def _source_status(data: dict[str, Any]) -> list[str]:
    status = data.get("source_status")
    if not isinstance(status, dict) or not status:
        return []
    lines = ["## Source Status"]
    for key, value in sorted(status.items()):
        lines.append(f"- {key}: {value}")
    lines.append("")
    return lines


def _json_summary(data: dict[str, Any]) -> list[str]:
    keys = [
        "analysis_time_utc",
        "fetched_at_utc",
        "fetched_at_bjt",
        "symbol",
        "ticker",
        "label",
        "kind",
        "instrument_type",
    ]
    lines = ["## Data Summary"]
    for key in keys:
        if key in data:
            lines.append(f"- {key}: {data[key]}")
    for list_key in ["daily_90d", "hourly_10d", "agg_4h_10d", "news", "macro_events", "upcoming_macro_events"]:
        value = data.get(list_key)
        if isinstance(value, list):
            lines.append(f"- {list_key}: {len(value)} items")
    for dict_key in ["proxies", "structured_drivers", "errors", "availability"]:
        value = data.get(dict_key)
        if isinstance(value, dict):
            lines.append(f"- {dict_key}: {len(value)} keys")
    lines.extend(["", "Full structured data is available in the JSON result."])
    return lines


def _clip(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text.rstrip()
    return text[:limit].rstrip() + "\n...[truncated]..."
