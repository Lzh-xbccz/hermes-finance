#!/usr/bin/env python3
"""Render crypto 4H market architecture as a standalone lightweight-charts HTML."""

from __future__ import annotations

import argparse
import html
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from fetch_data import (  # noqa: E402
    _close,
    _crypto_market_architecture,
    _fmt_level,
    _high,
    _low,
    _normalize_kline_rows,
    _open,
    _volume,
    fetch,
    market_symbol,
)


LWC_SCRIPT = "https://unpkg.com/lightweight-charts@4.2.3/dist/lightweight-charts.standalone.production.js"


def _row_timestamp(row, fallback_idx):
    ts = None
    if isinstance(row, dict):
        ts = row.get("ts", row.get("t", row.get("time")))
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
    series = []
    for point in line.get("points", []):
        series.append({
            "time": _time_at(rows, point.get("idx", 0)),
            "value": float(point.get("price", 0.0)),
        })
    return series


def _line_value_at(line, idx):
    points = line.get("points", [])
    if len(points) < 2:
        return None
    first, last = points[0], points[-1]
    idx_delta = last.get("idx", 0) - first.get("idx", 0)
    if idx_delta == 0:
        return float(last.get("price", 0.0))
    slope = (last.get("price", 0.0) - first.get("price", 0.0)) / idx_delta
    return float(first.get("price", 0.0) + slope * (idx - first.get("idx", 0)))


def _midline_series(upper_line, lower_line, rows):
    upper_points = upper_line.get("points", [])
    lower_points = lower_line.get("points", [])
    if len(upper_points) < 2 or len(lower_points) < 2:
        return []
    start_idx = max(int(upper_points[0]["idx"]), int(lower_points[0]["idx"]))
    end_idx = min(int(upper_points[-1]["idx"]), int(lower_points[-1]["idx"]))
    if end_idx <= start_idx:
        end_idx = max(int(upper_points[-1]["idx"]), int(lower_points[-1]["idx"]))
    start_upper = _line_value_at(upper_line, start_idx)
    start_lower = _line_value_at(lower_line, start_idx)
    end_upper = _line_value_at(upper_line, end_idx)
    end_lower = _line_value_at(lower_line, end_idx)
    if None in {start_upper, start_lower, end_upper, end_lower}:
        return []
    return [
        {"time": _time_at(rows, start_idx), "value": (start_upper + start_lower) / 2},
        {"time": _time_at(rows, end_idx), "value": (end_upper + end_lower) / 2},
    ]


def _swing_markers(arch, rows):
    markers = []
    for anchor in arch.get("upper_line", {}).get("anchors", []):
        idx = anchor.get("idx", 0)
        markers.append({
            "time": _time_at(rows, idx),
            "position": "aboveBar",
            "color": "#B45309",
            "shape": "circle",
            "text": "摆高",
        })
    for anchor in arch.get("lower_line", {}).get("anchors", []):
        idx = anchor.get("idx", 0)
        markers.append({
            "time": _time_at(rows, idx),
            "position": "belowBar",
            "color": "#047857",
            "shape": "circle",
            "text": "摆低",
        })
    return sorted(markers, key=lambda x: x["time"])


def _subtrend_break_markers(sub, rows):
    if not sub:
        return []
    break_idx = sub.get("break_idx")
    if break_idx is None:
        return []
    position = sub.get("position", "")
    if "上破" in position:
        return [{
            "time": _time_at(rows, break_idx),
            "position": "belowBar",
            "color": "#059669",
            "shape": "arrowUp",
            "text": "子趋势上破",
        }]
    if "下破" in position:
        return [{
            "time": _time_at(rows, break_idx),
            "position": "aboveBar",
            "color": "#DC2626",
            "shape": "arrowDown",
            "text": "子趋势下破",
        }]
    return []


def fetch_binance_klines(coin_id, interval="4h", limit=180):
    symbol = market_symbol(coin_id)
    url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}"
    return _normalize_kline_rows(fetch(url, timeout=12))


def build_market_structure_payload(coin_id, rows, interval="4h"):
    rows = _normalize_kline_rows(rows)
    if not rows:
        raise ValueError("no kline rows")

    symbol = market_symbol(coin_id)
    arch = _crypto_market_architecture(rows)
    candles = []
    volume = []
    for idx, row in enumerate(rows):
        t = _row_timestamp(row, idx)
        open_price = float(_open(row))
        close_price = float(_close(row))
        candles.append({
            "time": t,
            "open": open_price,
            "high": float(_high(row)),
            "low": float(_low(row)),
            "close": close_price,
        })
        volume.append({
            "time": t,
            "value": float(_volume(row)),
            "color": "rgba(5, 150, 105, 0.28)" if close_price >= open_price else "rgba(220, 38, 38, 0.25)",
        })

    upper_line = arch.get("upper_line", {})
    lower_line = arch.get("lower_line", {})
    sub = arch.get("sub_structure") or {}
    sub_upper_line = sub.get("upper_line", {})
    sub_lower_line = sub.get("lower_line", {})
    upper = _line_to_series(upper_line, rows)
    lower = _line_to_series(lower_line, rows)
    mid = _midline_series(upper_line, lower_line, rows)
    sub_upper = _line_to_series(sub_upper_line, rows)
    sub_lower = _line_to_series(sub_lower_line, rows)
    markers = _swing_markers(arch, rows) + _subtrend_break_markers(sub, rows)

    return {
        "symbol": symbol,
        "interval": interval.upper(),
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "last_price": float(_close(rows[-1])),
        "last_price_text": _fmt_level(_close(rows[-1])),
        "candles": candles,
        "volume": volume,
        "lines": {
            "upper": upper,
            "lower": lower,
            "mid": mid,
            "subUpper": sub_upper,
            "subLower": sub_lower,
        },
        "markers": sorted(markers, key=lambda x: x["time"]),
        "architecture": {
            "kind": arch["kind"],
            "stance": arch["stance"],
            "position": arch["position"],
            "lower": arch["lower"],
            "upper": arch["upper"],
            "mid": arch["mid"],
            "break_buffer": arch["break_buffer"],
            "upper_breakout": arch["upper_breakout"],
            "lower_breakdown": arch["lower_breakdown"],
            "lower_text": _fmt_level(arch["lower"]),
            "upper_text": _fmt_level(arch["upper"]),
            "mid_text": _fmt_level(arch["mid"]),
            "upper_breakout_text": _fmt_level(arch["upper_breakout"]),
            "lower_breakdown_text": _fmt_level(arch["lower_breakdown"]),
            "high_slope_pct": arch.get("high_slope_pct", 0.0),
            "low_slope_pct": arch.get("low_slope_pct", 0.0),
            "reason": arch["reason"],
            "logic": arch.get("logic", []),
            "sub_structure": {
                "kind": sub.get("kind", ""),
                "stance": sub.get("stance", ""),
                "position": sub.get("position", ""),
                "break_idx": sub.get("break_idx"),
                "break_time_text": _utc_text_at(rows, sub.get("break_idx")) if sub.get("break_idx") is not None else "",
                "lower": sub.get("lower", 0.0),
                "upper": sub.get("upper", 0.0),
                "mid": sub.get("mid", 0.0),
                "lower_text": _fmt_level(sub.get("lower", 0.0)) if sub else "",
                "upper_text": _fmt_level(sub.get("upper", 0.0)) if sub else "",
                "reason": sub.get("reason", ""),
            } if sub else None,
        },
    }


def render_market_structure_html(payload):
    payload_json = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    title = html.escape(f"{payload['symbol']} {payload['interval']} 市场架构")
    return HTML_TEMPLATE.replace("__TITLE__", title).replace("__PAYLOAD_JSON__", payload_json).replace("__LWC_SCRIPT__", LWC_SCRIPT)


def write_market_structure_chart(coin_id, output=None, interval="4h", limit=180):
    rows = fetch_binance_klines(coin_id, interval=interval, limit=limit)
    payload = build_market_structure_payload(coin_id, rows, interval=interval)
    out = Path(output) if output else Path("/tmp") / f"hermes_{payload['symbol']}_market_structure.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render_market_structure_html(payload), encoding="utf-8")
    return out, payload


HTML_TEMPLATE = """<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>__TITLE__</title>
  <script src="__LWC_SCRIPT__"></script>
  <style>
    :root {
      --bg: #F7F8FA;
      --panel: #FFFFFF;
      --text: #111827;
      --muted: #6B7280;
      --grid: #E5E7EB;
      --rail-upper: #B45309;
      --rail-lower: #047857;
      --mid: #2563EB;
      --sub-upper: #9333EA;
      --sub-lower: #0891B2;
      --danger: #DC2626;
      --ok: #059669;
      --shadow: 0 10px 28px rgba(15, 23, 42, 0.08);
    }
    * { box-sizing: border-box; }
    html, body {
      margin: 0;
      background: var(--bg);
      color: var(--text);
      font-family: Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", sans-serif;
      letter-spacing: 0;
    }
    body { min-height: 100vh; }
    .shell {
      display: grid;
      grid-template-rows: auto 1fr;
      min-height: 100vh;
    }
    header {
      display: grid;
      grid-template-columns: minmax(180px, auto) 1fr auto;
      gap: 20px;
      align-items: end;
      padding: 20px 28px 16px;
      background: var(--panel);
      border-bottom: 1px solid var(--grid);
    }
    .symbol {
      font-family: "SFMono-Regular", Consolas, monospace;
      font-size: 28px;
      font-weight: 700;
      line-height: 1;
    }
    .sub, .stamp, .metric__label, .logic__step {
      color: var(--muted);
      font-size: 12px;
    }
    .status {
      display: flex;
      align-items: center;
      gap: 8px;
      justify-self: end;
      font-size: 13px;
      color: var(--muted);
      white-space: nowrap;
    }
    .dot {
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background: var(--mid);
    }
    main {
      display: grid;
      grid-template-columns: minmax(0, 1fr) 340px;
      gap: 16px;
      padding: 16px;
      min-height: 0;
    }
    .chart-wrap, aside {
      background: var(--panel);
      border: 1px solid var(--grid);
      border-radius: 8px;
      box-shadow: var(--shadow);
      min-width: 0;
    }
    .chart-wrap {
      position: relative;
      min-height: 620px;
      overflow: hidden;
    }
    #chart {
      width: 100%;
      height: 620px;
    }
    .tooltip {
      position: absolute;
      display: none;
      min-width: 188px;
      padding: 10px 12px;
      border: 1px solid var(--grid);
      border-radius: 6px;
      background: rgba(255,255,255,0.96);
      box-shadow: 0 8px 24px rgba(15, 23, 42, 0.12);
      pointer-events: none;
      z-index: 10;
      font-family: "SFMono-Regular", Consolas, monospace;
      font-size: 12px;
    }
    .tooltip__time {
      color: var(--muted);
      margin-bottom: 6px;
      padding-bottom: 6px;
      border-bottom: 1px solid var(--grid);
    }
    .tooltip__row {
      display: flex;
      justify-content: space-between;
      gap: 16px;
      line-height: 1.7;
    }
    aside {
      padding: 18px;
      overflow: auto;
    }
    .badge {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      border: 1px solid var(--grid);
      border-radius: 999px;
      padding: 7px 10px;
      font-size: 13px;
      margin-bottom: 14px;
      background: #F9FAFB;
    }
    .badge::before {
      content: "";
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background: var(--mid);
    }
    .badge--long::before { background: var(--ok); }
    .badge--short::before { background: var(--danger); }
    h1 {
      font-size: 20px;
      line-height: 1.25;
      margin: 0 0 4px;
    }
    h2 {
      font-size: 13px;
      margin: 18px 0 10px;
      color: var(--muted);
      text-transform: uppercase;
      font-weight: 700;
    }
    .metrics {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 8px;
    }
    .metric {
      border: 1px solid var(--grid);
      border-radius: 6px;
      padding: 10px;
      min-width: 0;
    }
    .metric__value {
      margin-top: 4px;
      font-family: "SFMono-Regular", Consolas, monospace;
      font-size: 15px;
      overflow-wrap: anywhere;
    }
    .subtrend {
      display: grid;
      gap: 8px;
      border: 1px solid var(--grid);
      border-radius: 6px;
      padding: 10px;
      font-size: 13px;
      line-height: 1.45;
      background: #F9FAFB;
    }
    .subtrend__title {
      font-weight: 700;
    }
    .subtrend__break {
      color: var(--ok);
      font-family: "SFMono-Regular", Consolas, monospace;
    }
    .subtrend__break--down { color: var(--danger); }
    .legend {
      display: grid;
      gap: 7px;
      font-size: 13px;
    }
    .legend__item {
      display: flex;
      align-items: center;
      gap: 8px;
    }
    .swatch {
      width: 26px;
      height: 3px;
      border-radius: 2px;
      flex: none;
    }
    .swatch--upper { background: var(--rail-upper); }
    .swatch--lower { background: var(--rail-lower); }
    .swatch--mid { background: var(--mid); }
    .swatch--sub-upper { background: repeating-linear-gradient(90deg, var(--sub-upper), var(--sub-upper) 6px, transparent 6px, transparent 10px); }
    .swatch--sub-lower { background: repeating-linear-gradient(90deg, var(--sub-lower), var(--sub-lower) 6px, transparent 6px, transparent 10px); }
    .logic {
      display: grid;
      gap: 8px;
      margin: 0;
      padding: 0;
      list-style: none;
    }
    .logic li {
      border-left: 3px solid var(--grid);
      padding-left: 10px;
      line-height: 1.45;
      font-size: 13px;
    }
    .logic__step {
      display: block;
      margin-bottom: 2px;
      font-weight: 700;
    }
    .error {
      padding: 24px;
      color: var(--danger);
      font-family: "SFMono-Regular", Consolas, monospace;
    }
    @media (max-width: 920px) {
      header {
        grid-template-columns: 1fr;
        align-items: start;
      }
      .status { justify-self: start; }
      main {
        grid-template-columns: 1fr;
      }
      .chart-wrap, #chart {
        min-height: 520px;
        height: 520px;
      }
    }
  </style>
</head>
<body>
  <div class="shell">
    <header>
      <div>
        <div id="symbol" class="symbol"></div>
        <div id="interval" class="sub"></div>
      </div>
      <div>
        <h1 id="headline"></h1>
        <div id="reason" class="sub"></div>
      </div>
      <div class="status"><span class="dot"></span><span id="generated"></span></div>
    </header>
    <main>
      <section class="chart-wrap">
        <div id="chart"></div>
        <div id="tooltip" class="tooltip"></div>
      </section>
      <aside>
        <div id="stance" class="badge"></div>
        <div class="metrics">
          <div class="metric">
            <div class="metric__label">Last</div>
            <div id="last-price" class="metric__value"></div>
          </div>
          <div class="metric">
            <div class="metric__label">Position</div>
            <div id="position" class="metric__value"></div>
          </div>
          <div class="metric">
            <div class="metric__label">Support</div>
            <div id="lower" class="metric__value"></div>
          </div>
          <div class="metric">
            <div class="metric__label">Resistance</div>
            <div id="upper" class="metric__value"></div>
          </div>
          <div class="metric">
            <div class="metric__label">Break Up</div>
            <div id="break-up" class="metric__value"></div>
          </div>
          <div class="metric">
            <div class="metric__label">Break Down</div>
            <div id="break-down" class="metric__value"></div>
          </div>
        </div>
        <h2>Sub Trend</h2>
        <div id="subtrend" class="subtrend"></div>
        <h2>Lines</h2>
        <div class="legend">
          <div class="legend__item"><span class="swatch swatch--upper"></span>上轨 / 阻力</div>
          <div class="legend__item"><span class="swatch swatch--lower"></span>下轨 / 支撑</div>
          <div class="legend__item"><span class="swatch swatch--mid"></span>中轨</div>
          <div class="legend__item"><span class="swatch swatch--sub-upper"></span>子趋势上轨</div>
          <div class="legend__item"><span class="swatch swatch--sub-lower"></span>子趋势下轨</div>
        </div>
        <h2>Logic</h2>
        <ul id="logic" class="logic"></ul>
      </aside>
    </main>
  </div>
  <script>
  (function () {
    const payload = __PAYLOAD_JSON__;
    const arch = payload.architecture;
    const fmt = (value) => Number(value).toLocaleString(undefined, { maximumFractionDigits: Math.abs(value) >= 1000 ? 0 : 4 });
    const byId = (id) => document.getElementById(id);

    byId("symbol").textContent = payload.symbol;
    byId("interval").textContent = payload.interval + " market architecture";
    byId("headline").textContent = arch.kind + " · " + arch.stance;
    byId("reason").textContent = arch.reason;
    byId("generated").textContent = payload.generated_at;
    byId("last-price").textContent = payload.last_price_text;
    byId("position").textContent = arch.position;
    byId("lower").textContent = arch.lower_text;
    byId("upper").textContent = arch.upper_text;
    byId("break-up").textContent = arch.upper_breakout_text;
    byId("break-down").textContent = arch.lower_breakdown_text;
    const sub = arch.sub_structure;
    const subtrend = byId("subtrend");
    if (sub) {
      const title = document.createElement("div");
      title.className = "subtrend__title";
      title.textContent = sub.kind + " / " + sub.position + " / " + sub.stance;
      subtrend.appendChild(title);
      const range = document.createElement("div");
      range.textContent = "子趋势下轨 " + sub.lower_text + " / 上轨 " + sub.upper_text;
      subtrend.appendChild(range);
      if (sub.break_idx !== null && sub.break_idx !== undefined) {
        const br = document.createElement("div");
        br.className = "subtrend__break" + (sub.position.indexOf("下破") >= 0 ? " subtrend__break--down" : "");
        br.textContent = sub.position + " · " + sub.break_time_text;
        subtrend.appendChild(br);
      }
    } else {
      subtrend.textContent = "无独立子趋势";
    }
    const stance = byId("stance");
    stance.textContent = arch.kind + " / " + arch.position + " / " + arch.stance;
    if (arch.stance === "做多") stance.classList.add("badge--long");
    if (arch.stance === "做空") stance.classList.add("badge--short");
    arch.logic.forEach((item) => {
      const li = document.createElement("li");
      const step = document.createElement("span");
      step.className = "logic__step";
      step.textContent = item.step;
      li.appendChild(step);
      li.appendChild(document.createTextNode(item.detail));
      byId("logic").appendChild(li);
    });

    const chartEl = byId("chart");
    if (typeof LightweightCharts === "undefined") {
      chartEl.innerHTML = '<div class="error">lightweight-charts JS 未加载，请联网后重新打开。</div>';
      return;
    }
    const chart = LightweightCharts.createChart(chartEl, {
      height: chartEl.clientHeight,
      layout: { background: { type: "solid", color: "#FFFFFF" }, textColor: "#111827" },
      grid: { vertLines: { color: "#EEF2F7" }, horzLines: { color: "#EEF2F7" } },
      rightPriceScale: { borderColor: "#E5E7EB" },
      timeScale: { borderColor: "#E5E7EB", timeVisible: true, secondsVisible: false },
      crosshair: { mode: LightweightCharts.CrosshairMode.Normal }
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

    const volume = chart.addHistogramSeries({
      priceFormat: { type: "volume" },
      priceScaleId: "",
      scaleMargins: { top: 0.82, bottom: 0 }
    });
    volume.setData(payload.volume);

    function addLine(data, color, width, style) {
      if (!data || data.length < 2) return null;
      const line = chart.addLineSeries({
        color: color,
        lineWidth: width,
        lineStyle: style,
        priceLineVisible: false,
        lastValueVisible: false
      });
      line.setData(data);
      return line;
    }
    addLine(payload.lines.upper, "#B45309", 3, LightweightCharts.LineStyle.Solid);
    addLine(payload.lines.lower, "#047857", 3, LightweightCharts.LineStyle.Solid);
    addLine(payload.lines.mid, "#2563EB", 2, LightweightCharts.LineStyle.Dashed);
    addLine(payload.lines.subUpper, "#9333EA", 2, LightweightCharts.LineStyle.Dotted);
    addLine(payload.lines.subLower, "#0891B2", 2, LightweightCharts.LineStyle.Dotted);

    candle.createPriceLine({
      price: arch.upper_breakout,
      color: "#B45309",
      lineWidth: 1,
      lineStyle: LightweightCharts.LineStyle.Dashed,
      axisLabelVisible: true,
      title: "上破"
    });
    candle.createPriceLine({
      price: arch.lower_breakdown,
      color: "#DC2626",
      lineWidth: 1,
      lineStyle: LightweightCharts.LineStyle.Dashed,
      axisLabelVisible: true,
      title: "下破"
    });

    const candleByTime = new Map(payload.candles.map((item) => [String(item.time), item]));
    const tooltip = byId("tooltip");
    chart.subscribeCrosshairMove((param) => {
      if (!param || !param.time || !param.point) {
        tooltip.style.display = "none";
        return;
      }
      const item = candleByTime.get(String(param.time));
      if (!item) {
        tooltip.style.display = "none";
        return;
      }
      const dt = new Date(Number(item.time) * 1000).toISOString().slice(0, 16).replace("T", " ");
      tooltip.innerHTML = [
        '<div class="tooltip__time">' + dt + ' UTC</div>',
        '<div class="tooltip__row"><span>O</span><span>' + fmt(item.open) + '</span></div>',
        '<div class="tooltip__row"><span>H</span><span>' + fmt(item.high) + '</span></div>',
        '<div class="tooltip__row"><span>L</span><span>' + fmt(item.low) + '</span></div>',
        '<div class="tooltip__row"><span>C</span><span>' + fmt(item.close) + '</span></div>'
      ].join("");
      tooltip.style.display = "block";
      const left = Math.min(param.point.x + 18, chartEl.clientWidth - tooltip.offsetWidth - 8);
      const top = Math.max(8, Math.min(param.point.y + 18, chartEl.clientHeight - tooltip.offsetHeight - 8));
      tooltip.style.left = left + "px";
      tooltip.style.top = top + "px";
    });

    chart.timeScale().fitContent();
    window.addEventListener("resize", () => {
      chart.applyOptions({ width: chartEl.clientWidth, height: chartEl.clientHeight });
      chart.timeScale().fitContent();
    });
  })();
  </script>
</body>
</html>
"""


def main(argv=None):
    parser = argparse.ArgumentParser(description="Generate a crypto market-structure HTML chart.")
    parser.add_argument("coin", help="Coin id or ticker, e.g. BTC, bitcoin, ZEC")
    parser.add_argument("--interval", default="4h", help="Binance interval, default: 4h")
    parser.add_argument("--limit", type=int, default=180, help="Number of candles, default: 180")
    parser.add_argument("--output", "-o", help="Output HTML path; default: /tmp/hermes_<SYMBOL>_market_structure.html")
    args = parser.parse_args(argv)

    out, payload = write_market_structure_chart(args.coin, args.output, args.interval, args.limit)
    print(f"HTML: {out}")
    print(
        "结构: "
        f"{payload['architecture']['kind']} | {payload['architecture']['position']} | "
        f"下轨/支撑 {payload['architecture']['lower_text']} | "
        f"上轨/阻力 {payload['architecture']['upper_text']} | "
        f"倾向 {payload['architecture']['stance']}"
    )


if __name__ == "__main__":
    main()
