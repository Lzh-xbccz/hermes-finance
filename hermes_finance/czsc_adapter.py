"""CZSC adapters for non-crypto market collector data."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


FREQ_ORDER = {"1d": 1, "4h": 2, "1h": 3, "15m": 4}
DEFAULT_MARKET_FREQS = ["4h", "1d"]
DEFAULT_FREQS_BY_MARKET = {
    "futures": ["1h", "15m"],
    "a_share": ["1d"],
}
MIN_BARS = 20

SIGNAL_DEFS = {
    "一买": "cxt_first_buy_V221126",
    "一卖": "cxt_first_sell_V221126",
    "二买二卖": "cxt_second_bs_V230320",
    "三买": "cxt_third_buy_V230228",
    "三买三卖": "cxt_third_bs_V230318",
    "综合决策": "cxt_decision_V240614",
    "笔结束": "cxt_bi_end_V230104",
}


def analyze_market_klines(
    data: dict[str, Any],
    *,
    market: str,
    symbol: str | None = None,
    freqs: str | list[str] | None = None,
) -> dict[str, Any]:
    """Run CZSC on K-lines already returned by a market collector.

    Crypto keeps using the ccxt connector path. This adapter is for markets where
    the collector already fetched Yahoo/Tencent/Binance rows and ccxt does not
    provide the instrument directly.
    """

    freq_list = _normalize_freqs(freqs, market=market)
    rows_by_freq, source = extract_market_rows(data, market=market)
    selected = {freq: rows_by_freq[freq] for freq in freq_list if rows_by_freq.get(freq)}
    if not selected:
        available = ", ".join(sorted(rows_by_freq)) or "none"
        return _unavailable(market, symbol, f"no requested CZSC K-lines; available={available}", source)

    try:
        from czsc import CZSC, Freq, RawBar
        from czsc._native.signals import call_signal
    except Exception as exc:  # pragma: no cover - depends on optional runtime
        return _unavailable(market, symbol, f"czsc import failed: {exc}", source)

    freq_map = {"15m": Freq.F15, "1h": Freq.F60, "4h": Freq.F240, "1d": Freq.D}
    analyses: dict[str, dict[str, Any]] = {}
    errors: dict[str, str] = {}
    target_symbol = symbol or str(data.get("symbol") or data.get("ticker") or market).upper()

    for freq, rows in selected.items():
        bars = _rows_to_raw_bars(rows, symbol=target_symbol, freq=freq_map[freq], RawBar=RawBar)
        if len(bars) < MIN_BARS:
            errors[freq] = f"insufficient bars: {len(bars)} < {MIN_BARS}"
            continue
        try:
            c = CZSC(bars, max_bi_num=50)
        except Exception as exc:
            errors[freq] = str(exc)
            continue
        analyses[freq] = _summarize_czsc(c, bars, freq=freq, call_signal=call_signal)

    if not analyses:
        reason = "; ".join(f"{k}={v}" for k, v in sorted(errors.items())) or "no analyzable CZSC frequency"
        return _unavailable(market, symbol, reason, source, errors)

    resonance = _resonance(analyses)
    summary = _summary_line(target_symbol, analyses, resonance)
    report_text = _report_text(target_symbol, market, source, analyses, resonance, errors)
    return {
        "ok": True,
        "mode": "collector_klines",
        "market": market,
        "symbol": target_symbol,
        "source": source,
        "freqs": list(analyses.keys()),
        "summary": summary,
        "resonance": resonance,
        "analyses": analyses,
        "errors": errors,
        "report_text": report_text,
    }


def extract_market_rows(data: dict[str, Any], *, market: str) -> tuple[dict[str, list[dict[str, Any]]], str]:
    """Extract normalized frequency rows from collector JSON."""

    if market == "futures":
        block = data.get("structured_drivers", {}).get("binance_tradfi_perp", {})
        if block.get("available") and isinstance(block.get("klines"), dict):
            klines = block["klines"]
            return {
                "15m": _clean_rows(klines.get("15m", [])),
                "1h": _clean_rows(klines.get("1h", [])),
                "4h": _clean_rows(klines.get("4h", [])),
                "1d": _clean_rows(klines.get("1d", [])),
            }, f"Binance {block.get('symbol', '')} TradFi Perp"
        return _standard_rows(data)

    if market in {"forex", "us_equity"}:
        return _standard_rows(data)

    if market == "a_share":
        rows: dict[str, list[dict[str, Any]]] = {}
        stock_rows = data.get("stock", {}).get("history_daily")
        if isinstance(stock_rows, list) and stock_rows:
            rows["1d"] = _clean_rows(stock_rows)
            source = data.get("stock", {}).get("tencent_code") or data.get("stock", {}).get("input") or "A-share stock"
            return rows, f"Tencent {source} daily K-lines"
        indices = data.get("indices_history_daily", {})
        if isinstance(indices, dict):
            sh_rows = indices.get("sh000001")
            if isinstance(sh_rows, list) and sh_rows:
                rows["1d"] = _clean_rows(sh_rows)
                return rows, "Tencent sh000001 daily K-lines"
        return rows, "A-share collector K-lines"

    return _standard_rows(data)


def _standard_rows(data: dict[str, Any]) -> tuple[dict[str, list[dict[str, Any]]], str]:
    return {
        "15m": _clean_rows(data.get("m15", []) or data.get("minute_15d", []) or data.get("intraday_15m", [])),
        "1h": _clean_rows(data.get("hourly_10d", [])),
        "4h": _clean_rows(data.get("agg_4h_10d", [])),
        "1d": _clean_rows(data.get("daily_90d", [])),
    }, f"{data.get('ticker') or data.get('symbol')} collector K-lines"


def _clean_rows(rows: Any) -> list[dict[str, Any]]:
    if not isinstance(rows, list):
        return []
    out = []
    for row in rows:
        if isinstance(row, dict) and all(key in row for key in ["open", "high", "low", "close"]):
            out.append(row)
    return out


def _normalize_freqs(freqs: str | list[str] | None, *, market: str | None = None) -> list[str]:
    default = DEFAULT_FREQS_BY_MARKET.get(str(market or ""), DEFAULT_MARKET_FREQS)
    if freqs is None:
        return default[:]
    raw = freqs.split(",") if isinstance(freqs, str) else freqs
    selected = []
    for item in raw:
        freq = str(item).strip().lower()
        if freq in FREQ_ORDER and freq not in selected:
            selected.append(freq)
    return selected or default[:]


def _rows_to_raw_bars(rows: list[dict[str, Any]], *, symbol: str, freq: Any, RawBar: Any) -> list[Any]:
    parsed = []
    for row in rows:
        dt = _row_dt(row)
        open_ = _to_float(row.get("open"))
        high = _to_float(row.get("high"))
        low = _to_float(row.get("low"))
        close = _to_float(row.get("close"))
        if dt is None or None in {open_, high, low, close}:
            continue
        vol = _to_float(row.get("volume")) or 0.0
        amount = _to_float(row.get("quote_volume") or row.get("amount") or row.get("amount_yuan")) or 0.0
        parsed.append((dt, open_, close, high, low, vol, amount))
    parsed.sort(key=lambda item: item[0])
    bars = []
    for idx, (dt, open_, close, high, low, vol, amount) in enumerate(parsed, start=1):
        bars.append(RawBar(symbol=symbol, dt=dt, freq=freq, open=open_, close=close, high=high, low=low, vol=vol, amount=amount, id=idx))
    return bars


def _row_dt(row: dict[str, Any]) -> datetime | None:
    ts = row.get("ts")
    if ts is not None:
        try:
            return datetime.fromtimestamp(float(ts), tz=timezone.utc).replace(tzinfo=None)
        except (TypeError, ValueError, OSError):
            pass
    time_utc = row.get("time_utc")
    if isinstance(time_utc, str) and time_utc:
        value = time_utc.replace("Z", "+00:00")
        try:
            dt = datetime.fromisoformat(value)
            if dt.tzinfo is not None:
                return dt.astimezone(timezone.utc).replace(tzinfo=None)
            return dt
        except ValueError:
            pass
        for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%d"):
            try:
                return datetime.strptime(time_utc, fmt)
            except ValueError:
                continue
    date = row.get("date")
    if isinstance(date, str) and date:
        try:
            return datetime.strptime(date[:10], "%Y-%m-%d")
        except ValueError:
            return None
    return None


def _summarize_czsc(c: Any, bars: list[Any], *, freq: str, call_signal: Any) -> dict[str, Any]:
    raw_signals: dict[str, list[str]] = {}
    active_signals: list[dict[str, str]] = []
    for label, signal_name in SIGNAL_DEFS.items():
        try:
            signals = call_signal(signal_name, c) or []
        except Exception:
            continue
        raw_signals[label] = [str(getattr(sig, "value", sig)) for sig in signals]
        for sig in signals:
            if _is_active_signal(sig):
                active_signals.append({
                    "label": label,
                    "direction": _signal_direction(sig),
                    "value": str(getattr(sig, "value", sig)),
                })

    z = _latest_center(c)
    last_bi = c.bi_list[-1] if c.bi_list else None
    last_bi_detail = {}
    if last_bi:
        start = float(last_bi.fx_a.fx)
        end = float(last_bi.fx_b.fx)
        current = float(bars[-1].close)
        pct = (end - start) / start * 100 if start else 0.0
        completion_direction = last_bi.direction.value
        live_direction = completion_direction
        broken = False
        if completion_direction == "向上" and current < start:
            live_direction = "向下"
            broken = True
        elif completion_direction == "向下" and current > start:
            live_direction = "向上"
            broken = True
        last_bi_detail = {
            "direction": completion_direction,
            "live_direction": live_direction,
            "start": start,
            "end": end,
            "change_pct": pct,
            "current_price": current,
            "broken_by_current_price": broken,
        }

    return {
        "freq": freq,
        "n_klines": len(bars),
        "n_bi": len(c.bi_list),
        "n_fx": len(c.fx_list),
        "current_price": float(bars[-1].close),
        "last_bi": last_bi_detail,
        "center": z,
        "active_signals": active_signals,
        "inactive_signal_count": sum(len(v) for v in raw_signals.values()) - len(active_signals),
        "divergence": _divergence(c),
        "pattern": _buy_sell_pattern(c),
    }


def _latest_center(c: Any) -> dict[str, Any] | None:
    centers = [fx for fx in getattr(c, "ubi_fxs", []) if getattr(fx, "has_zs", False)]
    if not centers:
        return None
    z = centers[-1]
    cur = float(c.bars_raw[-1].close)
    if cur > z.high:
        position = "上方"
    elif cur >= z.low:
        position = "内部"
    else:
        position = "下方"
    return {"low": float(z.low), "high": float(z.high), "position": position, "power": getattr(z, "power_str", "")}


def _is_active_signal(sig: Any) -> bool:
    v1 = str(getattr(sig, "v1", "") or "")
    return v1 not in {"", "其他", "任意", "无", "NA", "N/A"}


def _signal_direction(sig: Any) -> str:
    text = "_".join(str(getattr(sig, attr, "") or "") for attr in ("v1", "v2", "v3", "key", "value"))
    if any(token in text for token in ("开多", "做多", "看多", "买")):
        return "buy"
    if any(token in text for token in ("开空", "做空", "看空", "卖")):
        return "sell"
    return "neutral"


def _divergence(c: Any) -> str:
    if len(c.bi_list) < 3:
        return ""
    bi1, bi2 = c.bi_list[-3], c.bi_list[-1]
    if bi1.direction != bi2.direction:
        return ""
    amp1 = abs(float(bi1.fx_b.fx) - float(bi1.fx_a.fx))
    amp2 = abs(float(bi2.fx_b.fx) - float(bi2.fx_a.fx))
    ratio = amp2 / max(amp1, 0.01)
    direction = bi1.direction.value
    if direction == "向上" and bi2.fx_b.fx > bi1.fx_b.fx and amp2 < amp1 * 0.7:
        return f"上涨背驰: 新高 {float(bi2.fx_b.fx):.4f}>{float(bi1.fx_b.fx):.4f}, 力度 {ratio:.1%}"
    if direction == "向下" and bi2.fx_b.fx < bi1.fx_b.fx and amp2 < amp1 * 0.7:
        return f"下跌背驰: 新低 {float(bi2.fx_b.fx):.4f}<{float(bi1.fx_b.fx):.4f}, 力度 {ratio:.1%}"
    return ""


def _buy_sell_pattern(c: Any) -> str:
    if len(c.bi_list) < 3:
        return ""
    a, b, c_bi = c.bi_list[-3:]
    if a.direction.value == "向上" and b.direction.value == "向下" and c_bi.direction.value == "向上":
        pullback_low = float(c_bi.fx_a.fx)
        prev_up_start = float(a.fx_a.fx)
        if pullback_low > prev_up_start:
            return f"二买候补: 回调 {pullback_low:.4f} 不破前低 {prev_up_start:.4f}"
        return f"一买候补: 创新低 {pullback_low:.4f} 后转向上"
    if a.direction.value == "向下" and b.direction.value == "向上" and c_bi.direction.value == "向下":
        rebound_high = float(c_bi.fx_a.fx)
        prev_down_start = float(a.fx_a.fx)
        if rebound_high < prev_down_start:
            return f"二卖候补: 反弹 {rebound_high:.4f} 不过前高 {prev_down_start:.4f}"
        return f"一卖候补: 创新高 {rebound_high:.4f} 后转向下"
    return ""


def _resonance(analyses: dict[str, dict[str, Any]]) -> dict[str, Any]:
    score = 0
    dirs = {freq: item.get("last_bi", {}).get("live_direction") or item.get("last_bi", {}).get("direction") for freq, item in analyses.items() if item.get("last_bi")}
    unique_dirs = {d for d in dirs.values() if d}
    if len(unique_dirs) == 1:
        only = next(iter(unique_dirs))
        score += 2 if only == "向上" else -2

    for item in analyses.values():
        center = item.get("center")
        if center:
            if center.get("position") == "上方":
                score += 1
            elif center.get("position") == "下方":
                score -= 1
        last_bi = item.get("last_bi", {})
        if last_bi.get("broken_by_current_price"):
            if last_bi.get("live_direction") == "向上":
                score += 1
            elif last_bi.get("live_direction") == "向下":
                score -= 1
        for sig in item.get("active_signals", []):
            if sig["direction"] == "buy":
                score += 1
            elif sig["direction"] == "sell":
                score -= 1

    if score >= 4:
        verdict = "强做多"
    elif score >= 2:
        verdict = "偏多"
    elif score <= -4:
        verdict = "强做空"
    elif score <= -2:
        verdict = "偏空"
    else:
        verdict = "震荡观望"
    return {"score": score, "verdict": verdict, "last_bi_directions": dirs}


def _summary_line(symbol: str, analyses: dict[str, dict[str, Any]], resonance: dict[str, Any]) -> str:
    parts = []
    for freq, item in sorted(analyses.items(), key=lambda kv: FREQ_ORDER.get(kv[0], 99)):
        bi = item.get("last_bi", {})
        direction = bi.get("live_direction") or bi.get("direction", "无笔")
        if bi.get("broken_by_current_price"):
            direction = f"{direction}(完成笔{bi.get('direction')}已被当前价破坏)"
        center = item.get("center") or {}
        parts.append(
            f"{freq}: {item['n_klines']}K/{item['n_bi']}笔/"
            f"{direction}/中枢{center.get('position', '无')}"
        )
    return f"{symbol} CZSC {resonance['verdict']} score={resonance['score']} | " + " | ".join(parts)


def _report_text(
    symbol: str,
    market: str,
    source: str,
    analyses: dict[str, dict[str, Any]],
    resonance: dict[str, Any],
    errors: dict[str, str],
) -> str:
    lines = [
        f"# {symbol} 缠论结构确认",
        f"- 市场: {market}",
        f"- K线来源: {source}",
        f"- 综合判断: {resonance['verdict']} (score={resonance['score']})",
        f"- 笔方向: {resonance.get('last_bi_directions', {})}",
        "",
    ]
    for freq, item in sorted(analyses.items(), key=lambda kv: FREQ_ORDER.get(kv[0], 99)):
        bi = item.get("last_bi", {})
        live_direction = bi.get("live_direction") or bi.get("direction", "无")
        if bi.get("broken_by_current_price"):
            live_direction = f"{live_direction}（完成笔{bi.get('direction')}已被当前价破坏）"
        center = item.get("center")
        lines.extend([
            f"## {freq}",
            f"- K线/分型/笔: {item['n_klines']} / {item['n_fx']} / {item['n_bi']}",
            f"- 当前价: {item['current_price']:.4f}",
            f"- 最近完成笔: {bi.get('direction', '无')} {bi.get('start', 'n/a')} -> {bi.get('end', 'n/a')} ({bi.get('change_pct', 0):+.2f}%)",
            f"- 实时方向: {live_direction}",
            f"- 中枢: {_center_text(center)}",
            f"- 有效信号: {_signals_text(item.get('active_signals', []))}",
            f"- 背驰: {item.get('divergence') or '无'}",
            f"- 买卖点模式: {item.get('pattern') or '无'}",
            "",
        ])
    if errors:
        lines.append("## 不可用级别")
        lines.extend(f"- {freq}: {err}" for freq, err in sorted(errors.items()))
    return "\n".join(lines).rstrip()


def _center_text(center: dict[str, Any] | None) -> str:
    if not center:
        return "无"
    return f"{center['low']:.4f}-{center['high']:.4f}，位置={center['position']}，力度={center.get('power', '')}"


def _signals_text(signals: list[dict[str, str]]) -> str:
    if not signals:
        return "无（其他/任意已过滤）"
    return "；".join(f"{s['label']}:{s['direction']}:{s['value']}" for s in signals[:5])


def _unavailable(
    market: str,
    symbol: str | None,
    reason: str,
    source: str,
    errors: dict[str, str] | None = None,
) -> dict[str, Any]:
    return {
        "ok": False,
        "mode": "collector_klines",
        "market": market,
        "symbol": symbol,
        "source": source,
        "freqs": [],
        "summary": f"CZSC unavailable: {reason}",
        "reason": reason,
        "errors": errors or {},
        "report_text": f"# {symbol or market} 缠论结构确认\n- 状态: 不可用\n- 原因: {reason}\n- K线来源: {source}",
    }


def _to_float(value: Any) -> float | None:
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None
