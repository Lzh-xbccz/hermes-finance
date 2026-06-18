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
