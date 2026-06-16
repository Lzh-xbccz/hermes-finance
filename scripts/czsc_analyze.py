#!/usr/bin/env python3
"""
缠论全栈分析 v4.0 — czsc v1.0.0rc8
  Multi-freq CZSC + Signals + Dark Charts + Auto Report

用法:
  python czsc_analyze.py BTCUSDT                    # 默认 4H+15min 联立
  python czsc_analyze.py BTCUSDT --freqs 4h,1h,15m  # 自定义多级别
  python czsc_analyze.py BTCUSDT --signals --chart --report
"""

import sys, os, json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

from czsc.connectors.ccxt_connector import get_raw_bars
from czsc import CZSC, format_standard_kline, Freq, RawBar
from czsc._native.signals import call_signal

# ══════════════════════════════════════════════════
# CONFIG
# ══════════════════════════════════════════════════

FREQ_MAP: Dict[str, Freq] = {
    '1m': Freq.F1, '5m': Freq.F5, '15m': Freq.F15, '30m': Freq.F30,
    '1h': Freq.F60, '2h': Freq.F120, '4h': Freq.F240,
    '1d': Freq.D, '1w': Freq.W,
}

PERIOD_MAP: Dict[str, str] = {
    '1m': '1m', '5m': '5m', '15m': '15m', '30m': '30m',
    '1h': '1h', '2h': '2h', '4h': '4h',
    '1d': '1d', '1w': '1w',
}

SIGNAL_NAMES = {
    '一买': 'cxt_first_buy_V221126',
    '综合决策': 'cxt_decision_V240614',
    '笔结束': 'cxt_bi_end_V230104',
}

DEFAULT_FREQS = ['4h', '15m']
LOOKBACK_DAYS = 90


# ══════════════════════════════════════════════════
# 数据获取
# ══════════════════════════════════════════════════

def fetch_bars(symbol: str, freq_key: str) -> tuple:
    """拉取 K 线并转换为 czsc RawBar"""
    period = PERIOD_MAP[freq_key]
    freq = FREQ_MAP[freq_key]
    edt = datetime.now().strftime('%Y%m%d')
    sdt = (datetime.now() - timedelta(days=LOOKBACK_DAYS)).strftime('%Y%m%d')
    
    df = get_raw_bars(symbol, period, sdt=sdt, edt=edt)
    bars = format_standard_kline(df, freq)
    return bars, freq, len(df)


# ══════════════════════════════════════════════════
# CZSC 分析
# ══════════════════════════════════════════════════

class FreqAnalysis:
    """单级别缠论分析"""
    def __init__(self, symbol: str, freq_key: str):
        self.symbol = symbol
        self.freq_key = freq_key
        self.freq = FREQ_MAP[freq_key]
        
        bars, freq_val, n_klines = fetch_bars(symbol, freq_key)
        self.bars: List[RawBar] = bars
        self.n_klines = n_klines
        self.c = CZSC(bars, max_bi_num=50)
        
        # 统计
        self.n_bi = len(self.c.bi_list)
        self.n_fx = len(self.c.fx_list)
        self.n_ubi_fx = len(self.c.ubi_fxs)
        self.n_ubi = len(self.c.ubi)
        self.zs_fxs = [f for f in self.c.ubi_fxs if f.has_zs]
        
        # 当前价
        self.cur_price = bars[-1].close if bars else 0
        
        # 信号
        self.signals: Dict[str, List[Any]] = {}
        for name, sig_name in SIGNAL_NAMES.items():
            try:
                res = call_signal(sig_name, self.c)
                if res:
                    self.signals[name] = res
            except Exception:
                pass
        
        # 中枢位置
        self.zs_position: str = '无中枢'
        if self.zs_fxs:
            z = self.zs_fxs[-1]
            if self.cur_price > z.high:
                self.zs_position = '上方 🟢'
            elif self.cur_price >= z.low:
                self.zs_position = '内部 ⚪'
            else:
                self.zs_position = '下方 🔴'
            self.zs_low = z.low
            self.zs_high = z.high
            self.zs_power = z.power_str
        else:
            self.zs_low = self.zs_high = 0
            self.zs_power = 'N/A'
    
    @property
    def last_bi_dir(self) -> str:
        if self.c.bi_list:
            return self.c.bi_list[-1].direction.value
        return 'N/A'
    
    @property
    def last_bi_power(self) -> float:
        if self.c.bi_list:
            return self.c.bi_list[-1].power
        return 0.0
    
    def summary(self) -> str:
        """单行摘要"""
        bi = self.c.bi_list[-1] if self.c.bi_list else None
        bi_str = f"BI#{self.n_bi} {self.last_bi_dir} {bi.power:+.0f}%" if bi else "无笔"
        zs_str = f"ZS ${self.zs_low:.2f}-${self.zs_high:.2f} {self.zs_position}" if self.zs_fxs else "无中枢"
        return f"{self.freq_key:>4s}: {self.n_klines}K {self.n_bi}笔 | {bi_str} | {zs_str}"


# ══════════════════════════════════════════════════
# 多级别联立分析
# ══════════════════════════════════════════════════

class MultiFreqAnalysis:
    """多级别缠论联立分析"""
    def __init__(self, symbol: str, freq_keys: List[str]):
        self.symbol = symbol
        self.freq_keys = freq_keys
        self.analyses: Dict[str, FreqAnalysis] = {}
        
        for fk in freq_keys:
            self.analyses[fk] = FreqAnalysis(symbol, fk)
    
    def resonance_check(self) -> str:
        """检查多级别共振"""
        dirs = []
        for fk in self.freq_keys:
            fa = self.analyses[fk]
            dirs.append(fa.last_bi_dir)
        
        if len(set(dirs)) == 1:
            d = dirs[0]
            return f"同向{'上涨 📈' if d == '向上' else '下跌 📉'}（共振确认）"
        else:
            return f"分歧 ⚠️: {'/'.join(f'{fk}={fa.last_bi_dir}' for fk, fa in self.analyses.items())}"
    
    def buy_signal_summary(self) -> str:
        """汇总所有级别的买入信号"""
        results = []
        for fk, fa in self.analyses.items():
            if fa.signals:
                sig_str = ', '.join(fa.signals.keys())
                results.append(f"{fk}: {sig_str}")
        return ' | '.join(results) if results else '无买入信号'
    
    def generate_charts(self, outdir: str = '/tmp', theme: str = 'dark', localize: bool = True) -> List[str]:
        """生成所有级别的 lightweight-charts，默认中文化"""
        from czsc.utils.plotting.lightweight import plot_czsc
        import subprocess
        
        localizer = os.path.join(os.path.dirname(__file__), 'localize_chart.py')
        files = []
        for fk, fa in self.analyses.items():
            outfile = os.path.join(outdir, f'czsc_{self.symbol}_{fk}.html')
            plot_czsc(fa.c, path=outfile, theme=theme, title=f'{self.symbol} {fk}')
            
            if localize and os.path.exists(localizer):
                try:
                    out_cn = os.path.join(outdir, f'czsc_{self.symbol}_{fk}_cn.html')
                    subprocess.run(
                        ['python3', localizer, outfile, '-o', out_cn],
                        capture_output=True, timeout=10
                    )
                    files.append(out_cn)
                except Exception:
                    files.append(outfile)
            else:
                files.append(outfile)
        return files
    
    def generate_report(self, outfile: Optional[str] = None) -> str:
        """生成 Markdown 分析报告"""
        if outfile is None:
            outfile = f'/tmp/czsc_{self.symbol}_report.md'
        
        lines = []
        lines.append(f"# {self.symbol} 缠论多级别分析报告")
        lines.append(f"**时间**: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        lines.append(f"**数据范围**: 近{LOOKBACK_DAYS}天")
        lines.append("")
        
        # 摘要
        primary = self.analyses.get('4h') or list(self.analyses.values())[0]
        lines.append("## 📊 摘要")
        lines.append(f"- **当前价**: ${primary.cur_price:.4f}")
        lines.append(f"- **共振判断**: {self.resonance_check()}")
        lines.append(f"- **买入信号**: {self.buy_signal_summary()}")
        lines.append("")
        
        # 各级别详解
        for fk in self.freq_keys:
            fa = self.analyses[fk]
            lines.append(f"## {fk} 级别")
            lines.append(f"- K 线: {fa.n_klines} | 分型: {fa.n_fx} | 笔: {fa.n_bi} | UBI: {fa.n_ubi}")
            
            if fa.zs_fxs:
                lines.append(f"- **中枢**: ${fa.zs_low:.2f} — ${fa.zs_high:.2f} | 力度: {fa.zs_power} | 位置: {fa.zs_position}")
            else:
                lines.append(f"- **中枢**: 无")
            
            if fa.signals:
                lines.append("- **信号**:")
                for name, sigs in fa.signals.items():
                    sig_strs = [str(s) for s in sigs]
                    lines.append(f"  - 【{name}】✅ {' | '.join(sig_strs)}")
            
            # 笔序列（最近5笔）
            bi_list = fa.c.bi_list[-5:]
            if bi_list:
                lines.append("\n| 笔 | 方向 | 起点 | 终点 | 力度 |")
                lines.append("|-----|------|------|------|------|")
                for bi in bi_list:
                    idx = fa.c.bi_list.index(bi) + 1
                    lines.append(
                        f"| BI#{idx} | {bi.direction.value} | "
                        f"${bi.fx_a.fx:.2f} | ${bi.fx_b.fx:.2f} | "
                        f"{bi.power:+.1f}% |"
                    )
            lines.append("")
        
        # 交易建议
        lines.append("## 🎯 交易建议")
        lines.append(f"- 方向判断: _根据共振+信号综合判断_")
        lines.append(f"- 关键支撑: _中枢下沿_")
        lines.append(f"- 关键阻力: _中枢上沿_")
        lines.append(f"- 风险提示: 本报告由 czsc v1.0.0rc8 自动生成，仅供参考")
        
        content = '\n'.join(lines)
        if outfile:
            with open(outfile, 'w', encoding='utf-8') as f:
                f.write(content)
        return content
    
    def print_summary(self):
        """终端输出摘要"""
        primary = self.analyses.get('4h') or list(self.analyses.values())[0]
        
        print(f"\n{'='*60}")
        print(f"  {self.symbol} 缠论多级别联立分析")
        print(f"  时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        print(f"{'='*60}")
        print(f"  当前价: ${primary.cur_price:.4f}")
        print(f"  共振: {self.resonance_check()}")
        print(f"  信号: {self.buy_signal_summary()}")
        
        for fk in self.freq_keys:
            fa = self.analyses[fk]
            print(f"\n  ── {fk} ──")
            print(f"  {fa.summary()}")
            
            if fa.signals:
                for name, sigs in fa.signals.items():
                    print(f"  【{name}】✅")
        
        print(f"\n{'='*60}")


# ══════════════════════════════════════════════════
# CLI
# ══════════════════════════════════════════════════

def parse_args():
    symbol = 'BTCUSDT'
    freqs = DEFAULT_FREQS[:]
    do_chart = False
    do_signals = False
    do_report = False
    
    for arg in sys.argv[1:]:
        if arg == '--chart':
            do_chart = True
        elif arg == '--signals':
            do_signals = True  # Always on for multi-freq
        elif arg == '--report':
            do_report = True
        elif arg.startswith('--freqs='):
            freqs = arg.split('=', 1)[1].split(',')
        elif arg in ('--help', '-h'):
            print(__doc__)
            sys.exit(0)
        elif not arg.startswith('--'):
            if '/' in arg:
                symbol = arg.replace('/', '')
            elif arg.upper().endswith(('USDT', 'USDC', 'BTC')):
                symbol = arg.upper()
            elif arg in FREQ_MAP:
                freqs = [arg]
            else:
                symbol = arg.upper()
    
    return symbol, freqs, do_chart, do_report


def main():
    symbol, freqs, do_chart, do_report = parse_args()
    
    # 验证 Freq
    for fk in freqs:
        if fk not in FREQ_MAP:
            print(f"❌ 不支持的周期: {fk}")
            print(f"   支持: {list(FREQ_MAP.keys())}")
            sys.exit(1)
    
    # 数据
    print(f"标的: {symbol} | 级别: {', '.join(freqs)}")
    
    for fk in freqs:
        bars, freq, n = fetch_bars(symbol, fk)
        print(f"  {fk}: {n} 条 K 线")
    
    # 分析
    mfa = MultiFreqAnalysis(symbol, freqs)
    mfa.print_summary()
    
    # 图表
    if do_chart:
        print(f"\n📈 生成 dark theme 图表...")
        files = mfa.generate_charts(theme='dark')
        for f in files:
            size_kb = os.path.getsize(f) // 1024
            print(f"  ✅ {f} ({size_kb}KB)")
    
    # 报告
    if do_report:
        report_path = mfa.generate_report()
        print(f"\n📝 报告: {report_path}")
    
    return mfa


if __name__ == '__main__':
    mfa = main()
