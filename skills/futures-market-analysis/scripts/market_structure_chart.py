#!/usr/bin/env python3
"""Render futures 4H market structure as a standalone lightweight-charts HTML."""

from __future__ import annotations

import argparse
import html
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
# 复用 crypto skill 的 K 线架构识别函数（_crypto_market_architecture 等）。
# 这些函数是图表渲染的核心逻辑，两市场共享同一套架构识别算法。
CRYPTO_SCRIPT_DIR = SCRIPT_DIR.parents[1] / "crypto-market-analysis" / "scripts"
for path in (SCRIPT_DIR, CRYPTO_SCRIPT_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from fetch_data import (  # noqa: E402
    _close,
    _crypto_market_architecture,
    _fmt_level,
    _high,
    _low,
    _open,
    _volume,
    _line_value_at_idx,
    _truncate_line_to_idx,
)
from futures_fetch import (  # noqa: E402
    BINANCE_TRADFI_SYMBOLS,
    SYMBOL_MAP,
    fetch_binance_json,
    normalize_binance_kline_rows,
)


LWC_SCRIPT = "https://unpkg.com/lightweight-charts@4.2.3/dist/lightweight-charts.standalone.production.js"


def _row_timestamp(row, fallback_idx):
    ts = row.get("ts")
    if ts is None:
        return 1_700_000_000 + fallback_idx * 14_400
    try:
        ts = float(ts)
    except (TypeError, ValueError):
        return 1_700_000_000 + fallback_idx * 14_400
    if ts > 10_000_000_000:
        ts = ts / 1000
    return int(ts)


def _time_at(rows, idx):
    if not rows:
        return 1_700_000_000
    idx = max(0, min(int(idx), len(rows) - 1))
    return _row_timestamp(rows[idx], idx)


def _utc_text_at(rows, idx):
    if idx is None:
        return ""
    return datetime.fromtimestamp(_time_at(rows, idx), timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


def _line_to_series(line, rows):
    return [
        {"time": _time_at(rows, point.get("idx", 0)), "value": float(point.get("price", 0.0))}
        for point in line.get("points", [])
    ]


def _interval_seconds(interval):
    text = str(interval or "").strip().lower()
    if not text:
        return 0
    unit = text[-1]
    try:
        value = int(text[:-1])
    except ValueError:
        return 0
    if unit == "m":
        return value * 60
    if unit == "h":
        return value * 3600
    if unit == "d":
        return value * 86400
    return 0


def _last_closed_idx(rows, interval):
    if not rows:
        return -1
    last_idx = len(rows) - 1
    seconds = _interval_seconds(interval)
    if seconds <= 0:
        return last_idx
    last_open = _time_at(rows, last_idx)
    now_ts = int(datetime.now(timezone.utc).timestamp())
    return last_idx - 1 if now_ts < last_open + seconds else last_idx


def _confirmed_break_side(rows, upper_line, lower_line, idx, break_buffer):
    upper = _line_value_at_idx(upper_line, idx)
    lower = _line_value_at_idx(lower_line, idx)
    if upper is None or lower is None:
        return ""
    close = _close(rows[idx])
    if close > upper + break_buffer:
        return "up"
    if close < lower - break_buffer:
        return "down"
    return ""


def _first_parent_break_idx(rows, upper_line, lower_line, start_idx, end_idx, break_buffer, channel_kind, confirm_bars=2):
    start = max(0, int(start_idx))
    end = int(end_idx)
    if end - start + 1 < confirm_bars:
        return None, ""
    for idx in range(start, end - confirm_bars + 2):
        side = _confirmed_break_side(rows, upper_line, lower_line, idx, break_buffer)
        if not side:
            continue
        confirmed = True
        for offset in range(1, confirm_bars):
            if _confirmed_break_side(rows, upper_line, lower_line, idx + offset, break_buffer) != side:
                confirmed = False
                break
        if not confirmed:
            continue
        if side == "up":
            return idx, f"上破{channel_kind}上轨"
        return idx, f"下破{channel_kind}下轨"
    return None, ""


def _latest_parent_rail_test(rows, upper_line, lower_line, start_idx, end_idx, break_buffer):
    for idx in range(int(end_idx), max(0, int(start_idx)) - 1, -1):
        upper = _line_value_at_idx(upper_line, idx)
        lower = _line_value_at_idx(lower_line, idx)
        if upper is None or lower is None:
            continue
        row = rows[idx]
        if _close(row) > upper + break_buffer:
            return idx, "上轨测试未确认"
        if _high(row) > upper + break_buffer and _close(row) <= upper + break_buffer:
            return idx, "上轨刺破未确认"
        if _close(row) < lower - break_buffer:
            return idx, "下轨测试未确认"
        if _low(row) < lower - break_buffer and _close(row) >= lower - break_buffer:
            return idx, "下轨刺破未确认"
    return None, ""


def _unconfirmed_arch_position(position):
    if "上破" in position:
        return "上轨测试未确认"
    if "下破" in position:
        return "下轨测试未确认"
    return position


def _fmt_optional_level(value):
    if value is None:
        return "-"
    return _fmt_level(value)


def _unconfirmed_reason(kind, status, lower, upper):
    if "未确认" not in status:
        return ""
    side = "上轨" if "上轨" in status else "下轨" if "下轨" in status else "轨道边缘"
    return (
        f"市场架构={kind}，{side}测试未确认，"
        f"下轨/支撑 {_fmt_optional_level(lower)}，上轨/阻力 {_fmt_optional_level(upper)}；"
        "需连续已收盘K线确认，或收回通道内。"
    )


def _last_anchor_idx(line):
    anchors = line.get("anchors", [])
    return max((int(p.get("idx", 0)) for p in anchors), default=None)


def _structure_markers(upper_line, lower_line, rows, break_idx, break_position, rail_test_idx=None, rail_test_position=""):
    markers = []
    for anchor in upper_line.get("anchors", []):
        markers.append({
            "time": _time_at(rows, anchor.get("idx", 0)),
            "position": "aboveBar",
            "color": "#B45309",
            "shape": "circle",
            "text": "通道高点",
        })
    for anchor in lower_line.get("anchors", []):
        markers.append({
            "time": _time_at(rows, anchor.get("idx", 0)),
            "position": "belowBar",
            "color": "#047857",
            "shape": "circle",
            "text": "通道低点",
        })
    if break_idx is not None:
        is_up_break = "上破" in break_position
        markers.append({
            "time": _time_at(rows, break_idx),
            "position": "belowBar" if is_up_break else "aboveBar",
            "color": "#059669" if is_up_break else "#DC2626",
            "shape": "arrowUp" if is_up_break else "arrowDown",
            "text": break_position,
        })
    elif rail_test_idx is not None:
        is_upper_test = "上轨" in rail_test_position
        markers.append({
            "time": _time_at(rows, rail_test_idx),
            "position": "aboveBar" if is_upper_test else "belowBar",
            "color": "#F59E0B",
            "shape": "circle",
            "text": rail_test_position,
        })
    return sorted(markers, key=lambda x: x["time"])


def fetch_binance_tradfi_klines(symbol, interval="4h", limit=180):
    root = symbol.upper()
    binance_symbol = BINANCE_TRADFI_SYMBOLS.get(root, root)
    rows = fetch_binance_json("/fapi/v1/klines", {"symbol": binance_symbol, "interval": interval, "limit": limit})
    return binance_symbol, normalize_binance_kline_rows(rows)


def build_futures_structure_payload(symbol, rows, binance_symbol=None, interval="4h"):
    rows = [r for r in rows if None not in {_open(r), _high(r), _low(r), _close(r)}]
    if not rows:
        raise ValueError("no kline rows")

    root = symbol.upper()
    label = SYMBOL_MAP.get(root, {}).get("label", root)
    binance_symbol = binance_symbol or BINANCE_TRADFI_SYMBOLS.get(root, root)
    arch = _crypto_market_architecture(rows)
    upper_line = arch.get("upper_line", {})
    lower_line = arch.get("lower_line", {})
    break_idx = None
    break_position = ""
    rail_test_idx = None
    rail_test_position = ""
    break_buffer = float(arch.get("break_buffer", 0.0))
    end_idx = len(rows) - 1
    confirmed_end_idx = _last_closed_idx(rows, interval)
    latest_upper = _line_value_at_idx(upper_line, end_idx)
    latest_lower = _line_value_at_idx(lower_line, end_idx)
    anchor_idxs = [idx for idx in [_last_anchor_idx(upper_line), _last_anchor_idx(lower_line)] if idx is not None]
    last_anchor = max(anchor_idxs) if anchor_idxs else None
    if arch.get("kind") in {"下降通道", "上升通道"}:
        scan_start = (last_anchor + 1) if last_anchor is not None else 0
        break_idx, break_position = _first_parent_break_idx(
            rows,
            upper_line,
            lower_line,
            scan_start,
            confirmed_end_idx,
            break_buffer,
            arch.get("kind", "通道"),
        )
        if break_idx is None:
            rail_test_idx, rail_test_position = _latest_parent_rail_test(
                rows,
                upper_line,
                lower_line,
                scan_start,
                end_idx,
                break_buffer,
            )
    if break_idx is not None:
        upper_line = _truncate_line_to_idx(upper_line, break_idx)
        lower_line = _truncate_line_to_idx(lower_line, break_idx)

    candles = []
    for idx, row in enumerate(rows):
        candles.append({
            "time": _row_timestamp(row, idx),
            "open": float(_open(row)),
            "high": float(_high(row)),
            "low": float(_low(row)),
            "close": float(_close(row)),
        })

    recent_after = rows[break_idx:] if break_idx is not None else rows[-12:]
    retest_low = min(_low(r) for r in recent_after)
    post_high = max(_high(r) for r in recent_after)
    last = float(_close(rows[-1]))
    status = break_position or rail_test_position or _unconfirmed_arch_position(arch["position"])
    stance = "观望" if "未确认" in status else arch["stance"]
    reason = _unconfirmed_reason(arch["kind"], status, latest_lower, latest_upper) or arch["reason"]
    if break_idx is not None and "上破" in break_position:
        summary_note = "旧通道已在首次上破处截断；后续按上破后回踩/延续观察，不再把过期通道延伸到最新K线。"
        post_high_title = "上破后高点"
        retest_low_title = "上破后回踩低点"
    elif break_idx is not None and "下破" in break_position:
        summary_note = "旧通道已在首次下破处截断；后续按下破后反抽/延续观察，不再把过期通道延伸到最新K线。"
        post_high_title = "下破后反抽高点"
        retest_low_title = "下破后低点"
    else:
        summary_note = "未出现确认上破/下破，结构通道延伸到最新K线。"
        post_high_title = "近期高点"
        retest_low_title = "近期低点"

    return {
        "symbol": f"{root} / {label}",
        "binance_symbol": binance_symbol,
        "interval": interval.upper(),
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "last_price": last,
        "last_price_text": _fmt_level(last),
        "candles": candles,
        "markers": _structure_markers(upper_line, lower_line, rows, break_idx, break_position, rail_test_idx, rail_test_position),
        "lines": {
            "upper": _line_to_series(upper_line, rows),
            "lower": _line_to_series(lower_line, rows),
        },
        "price_lines": [
            {"price": float(post_high), "title": post_high_title, "color": "#B45309"},
            {"price": float(retest_low), "title": retest_low_title, "color": "#047857"},
        ] if break_idx is not None else [],
        "architecture": {
            "kind": arch["kind"],
            "stance": stance,
            "position": status,
            "break_idx": break_idx,
            "break_time_text": _utc_text_at(rows, break_idx) if break_idx is not None else "",
            "rail_test_idx": rail_test_idx,
            "rail_test_time_text": _utc_text_at(rows, rail_test_idx) if rail_test_idx is not None else "",
            "event_time_text": (
                _utc_text_at(rows, break_idx)
                if break_idx is not None
                else _utc_text_at(rows, rail_test_idx) if rail_test_idx is not None else ""
            ),
            "old_upper": float(upper_line.get("points", [{}])[-1].get("price", 0.0)),
            "old_lower": float(lower_line.get("points", [{}])[-1].get("price", 0.0)),
            "post_high": float(post_high),
            "retest_low": float(retest_low),
            "reason": reason,
            "logic": arch.get("logic", []),
            "note": summary_note,
        },
    }


def render_futures_structure_html(payload):
    payload_json = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    title = html.escape(f"{payload['symbol']} {payload['interval']} 结构图")
    return HTML_TEMPLATE.replace("__TITLE__", title).replace("__PAYLOAD_JSON__", payload_json).replace("__LWC_SCRIPT__", LWC_SCRIPT)


def write_futures_structure_chart(symbol, output=None, interval="4h", limit=180):
    binance_symbol, rows = fetch_binance_tradfi_klines(symbol, interval, limit)
    payload = build_futures_structure_payload(symbol, rows, binance_symbol, interval)
    out = Path(output) if output else Path("/tmp") / f"hermes_{symbol.upper()}_futures_structure.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render_futures_structure_html(payload), encoding="utf-8")
    return out, payload


HTML_TEMPLATE = """<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>__TITLE__</title>
  <script src="__LWC_SCRIPT__"></script>
  <style>
    * { box-sizing: border-box; }
    body {
      margin: 0;
      background: #F7F8FA;
      color: #111827;
      font-family: Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", sans-serif;
      letter-spacing: 0;
    }
    header {
      display: grid;
      grid-template-columns: 1fr auto;
      gap: 16px;
      padding: 18px 24px;
      background: #FFFFFF;
      border-bottom: 1px solid #E5E7EB;
    }
    h1 { margin: 0; font-size: 22px; line-height: 1.2; }
    .sub { color: #6B7280; font-size: 12px; margin-top: 4px; }
    main {
      display: grid;
      grid-template-columns: minmax(0, 1fr) 340px;
      gap: 16px;
      padding: 16px;
    }
    .chart, .side {
      background: #FFFFFF;
      border: 1px solid #E5E7EB;
      border-radius: 8px;
      box-shadow: 0 10px 28px rgba(15, 23, 42, 0.08);
      min-width: 0;
    }
    #chart { height: 640px; }
    .side { padding: 16px; }
    .badge {
      display: inline-flex;
      border: 1px solid #E5E7EB;
      border-radius: 999px;
      padding: 7px 10px;
      background: #F9FAFB;
      font-size: 13px;
      margin-bottom: 12px;
    }
    .grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 8px;
    }
    .metric {
      border: 1px solid #E5E7EB;
      border-radius: 6px;
      padding: 10px;
      min-width: 0;
    }
    .label { font-size: 12px; color: #6B7280; }
    .value {
      margin-top: 4px;
      font-family: "SFMono-Regular", Consolas, monospace;
      overflow-wrap: anywhere;
    }
    h2 {
      font-size: 13px;
      color: #6B7280;
      margin: 18px 0 8px;
      text-transform: uppercase;
    }
    p { font-size: 13px; line-height: 1.55; }
    @media (max-width: 900px) {
      header, main { grid-template-columns: 1fr; }
      #chart { height: 520px; }
    }
  </style>
</head>
<body>
  <header>
    <div>
      <h1 id="title"></h1>
      <div id="subtitle" class="sub"></div>
    </div>
    <div id="last" class="sub"></div>
  </header>
  <main>
    <section class="chart"><div id="chart"></div></section>
    <aside class="side">
      <div id="badge" class="badge"></div>
      <div class="grid">
        <div class="metric"><div class="label">Last</div><div id="last-price" class="value"></div></div>
        <div class="metric"><div class="label">Break Time</div><div id="break-time" class="value"></div></div>
        <div class="metric"><div class="label">Old Upper</div><div id="old-upper" class="value"></div></div>
        <div class="metric"><div class="label">Retest Low</div><div id="retest-low" class="value"></div></div>
        <div class="metric"><div class="label">Post High</div><div id="post-high" class="value"></div></div>
        <div class="metric"><div class="label">Old Lower</div><div id="old-lower" class="value"></div></div>
      </div>
      <h2>Structure</h2>
      <p id="note"></p>
      <p id="reason"></p>
    </aside>
  </main>
  <script>
  (function () {
    const payload = __PAYLOAD_JSON__;
    const arch = payload.architecture;
    const fmt = (value) => Number(value).toLocaleString(undefined, { maximumFractionDigits: Math.abs(value) >= 1000 ? 0 : 4 });
    const byId = (id) => document.getElementById(id);
    byId("title").textContent = payload.symbol + " " + payload.interval + " 结构图";
    byId("subtitle").textContent = payload.binance_symbol + " TradFi Perp · 无成交量背景 · " + payload.generated_at;
    byId("last").textContent = "Last " + payload.last_price_text;
    byId("badge").textContent = arch.position;
    byId("last-price").textContent = payload.last_price_text;
    byId("break-time").textContent = arch.event_time_text || arch.break_time_text || arch.rail_test_time_text || "-";
    byId("old-upper").textContent = fmt(arch.old_upper);
    byId("old-lower").textContent = fmt(arch.old_lower);
    byId("post-high").textContent = fmt(arch.post_high);
    byId("retest-low").textContent = fmt(arch.retest_low);
    byId("note").textContent = arch.note;
    byId("reason").textContent = arch.reason;

    const chart = LightweightCharts.createChart(byId("chart"), {
      height: byId("chart").clientHeight,
      layout: { background: { type: "solid", color: "#FFFFFF" }, textColor: "#111827" },
      grid: { vertLines: { color: "#EEF2F7" }, horzLines: { color: "#EEF2F7" } },
      rightPriceScale: { borderColor: "#E5E7EB" },
      timeScale: { borderColor: "#E5E7EB", timeVisible: true, secondsVisible: false }
    });
    const candle = chart.addCandlestickSeries({
      upColor: "#059669",
      downColor: "#DC2626",
      borderUpColor: "#047857",
      borderDownColor: "#B91C1C",
      wickUpColor: "#047857",
      wickDownColor: "#B91C1C"
    });
    candle.setData(payload.candles);
    candle.setMarkers(payload.markers);

    function addLine(data, color) {
      if (!data || data.length < 2) return;
      const line = chart.addLineSeries({
        color: color,
        lineWidth: 3,
        lineStyle: LightweightCharts.LineStyle.Dashed,
        priceLineVisible: false,
        lastValueVisible: false
      });
      line.setData(data);
    }
    addLine(payload.lines.upper, "#9333EA");
    addLine(payload.lines.lower, "#0891B2");
    payload.price_lines.forEach((item) => {
      candle.createPriceLine({
        price: item.price,
        color: item.color,
        lineWidth: 1,
        lineStyle: LightweightCharts.LineStyle.Dashed,
        axisLabelVisible: true,
        title: item.title
      });
    });
    chart.timeScale().fitContent();
    window.addEventListener("resize", () => {
      chart.applyOptions({ width: byId("chart").clientWidth, height: byId("chart").clientHeight });
      chart.timeScale().fitContent();
    });
  })();
  </script>
</body>
</html>
"""


def main(argv=None):
    parser = argparse.ArgumentParser(description="Generate a futures market-structure HTML chart.")
    parser.add_argument("symbol", help="Futures symbol, e.g. CL, GC, ES, NQ")
    parser.add_argument("--interval", default="4h", help="Binance interval, default: 4h")
    parser.add_argument("--limit", type=int, default=180, help="Number of candles, default: 180")
    parser.add_argument("--output", "-o", help="Output HTML path")
    args = parser.parse_args(argv)

    out, payload = write_futures_structure_chart(args.symbol, args.output, args.interval, args.limit)
    print(f"HTML: {out}")
    print(
        "结构: "
        f"{payload['architecture']['kind']} | {payload['architecture']['position']} | "
        f"last {payload['last_price_text']}"
    )


if __name__ == "__main__":
    main()
