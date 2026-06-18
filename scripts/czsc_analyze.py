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
from czsc.signals import cxt_first_buy_V221126, cxt_second_bs_V230320, cxt_third_buy_V230228, cxt_decision_V240614, cxt_bi_end_V230104

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

SIGNAL_FUNCS = {
    '一买': cxt_first_buy_V221126,
    '二买': cxt_second_bs_V230320,
    '三买': cxt_third_buy_V230228,
    '综合决策': cxt_decision_V240614,
    '笔结束': cxt_bi_end_V230104,
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
        
        # 信号（直接调用公开的 czsc.signals 函数）
        self.signals: Dict[str, List[Any]] = {}
        for name, sig_func in SIGNAL_FUNCS.items():
            try:
                res = sig_func(self.c)
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
    
    def divergence_check(self) -> str:
        """背驰分析 — 比较同方向相邻笔的振幅（源自 czsc_skills by zengbin93）"""
        if len(self.c.bi_list) < 3:
            return ""
        recent = self.c.bi_list[-3:]
        bi1, bi2 = recent[-2], recent[-1]
        amp1 = abs(bi1.fx_b.fx - bi1.fx_a.fx)
        amp2 = abs(bi2.fx_b.fx - bi2.fx_a.fx)
        
        if bi1.direction != bi2.direction:
            return ""
        
        d = bi1.direction.value
        amp_ratio = amp2 / max(amp1, 0.01)
        
        if d == '向上' and bi2.fx_b.fx > bi1.fx_b.fx and amp2 < amp1 * 0.7:
            return f"⚠️ 上涨背驰: 价格创新高${bi2.fx_b.fx:.1f}>{bi1.fx_b.fx:.1f} 但力度衰减 {amp_ratio:.1%} → 关注一卖"
        elif d == '向下' and bi2.fx_b.fx < bi1.fx_b.fx and amp2 < amp1 * 0.7:
            return f"🟢 下跌背驰: 价格创新低${bi2.fx_b.fx:.1f}<{bi1.fx_b.fx:.1f} 但力度衰减 {amp_ratio:.1%} → 关注一买"
        return ""
    
    def buy_sell_pattern(self) -> str:
        """买卖点模式识别 — 基于分型回调判断（源自 czsc_skills by zengbin93）"""
        if len(self.c.bi_list) < 4:
            return ""
        recent = self.c.bi_list[-5:]
        last = recent[-1]
        parts = []
        
        # 识别买点：回调不破前低=二买，创新低反弹=一买
        for i in range(1, len(recent)):
            bi = recent[i]
            if bi.direction.value == '向上' and recent[i-1].direction.value == '向下':
                if i >= 2:
                    prev_up = recent[i-2]
                    if prev_up.direction.value == '向上':
                        if bi.fx_a.fx > prev_up.fx_a.fx:
                            parts.append(f"二买候补: 回调${bi.fx_a.fx:.1f}不破前低${prev_up.fx_a.fx:.1f}")
                        elif bi.fx_a.fx < prev_up.fx_a.fx:
                            parts.append(f"一买候补: 创新低${bi.fx_a.fx:.1f}后转向上")
        
        # 识别卖点
        for i in range(1, len(recent)):
            bi = recent[i]
            if bi.direction.value == '向下' and recent[i-1].direction.value == '向上':
                if i >= 2:
                    prev_down = recent[i-2]
                    if prev_down.direction.value == '向下':
                        if bi.fx_a.fx < prev_down.fx_a.fx:
                            parts.append(f"二卖候补: 反弹${bi.fx_a.fx:.1f}不过前高${prev_down.fx_a.fx}")
                        elif bi.fx_a.fx > prev_down.fx_a.fx:
                            parts.append(f"一卖候补: 创新高${bi.fx_a.fx:.1f}后转向下")
        
        return ' | '.join(parts[-3:]) if parts else ""
    
    def summary(self) -> str:
        """单行摘要"""
        bi = self.c.bi_list[-1] if self.c.bi_list else None
        bi_str = f"BI#{self.n_bi} {self.last_bi_dir} {bi.power*100:+.0f}%" if bi else "无笔"
        zs_str = f"ZS ${self.zs_low:.4f}-${self.zs_high:.4f} {self.zs_position}" if self.zs_fxs else "无中枢"
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
        """检查多级别共振 — 笔方向 + 中枢位置 + 嵌套关系"""
        lines = []
        
        # ── 1. 笔方向共振 ──
        dirs = {fk: fa.last_bi_dir for fk, fa in self.analyses.items()}
        unique_dirs = set(dirs.values())
        if len(unique_dirs) == 1:
            d = list(unique_dirs)[0]
            lines.append(f"笔方向: {'🟢 一致上涨' if d == '向上' else '🔴 一致下跌'}（同向共振 ✓）")
        else:
            lines.append(f"笔方向: ⚠️ 分歧 — {' | '.join(f'{fk}={d}' for fk, d in dirs.items())}")
        
        # ── 2. 中枢位置共振 ──
        zs_positions = {}
        for fk, fa in self.analyses.items():
            if fa.zs_fxs:
                zs_positions[fk] = fa.zs_position
        if zs_positions:
            above = [fk for fk, p in zs_positions.items() if '上方' in p]
            inside = [fk for fk, p in zs_positions.items() if '内部' in p]
            below = [fk for fk, p in zs_positions.items() if '下方' in p]
            pos_parts = []
            if above: pos_parts.append(f"{','.join(above)} 在中枢上方 🟢")
            if inside: pos_parts.append(f"{','.join(inside)} 在中枢内部 ⚪")
            if below: pos_parts.append(f"{','.join(below)} 在中枢下方 🔴")
            lines.append(f"中枢位置: {' | '.join(pos_parts)}")
        else:
            lines.append(f"中枢位置: 无中枢参考")
        
        # ── 3. 嵌套关系（小级别中枢 vs 大级别中枢） ──
        sorted_keys = sorted(self.freq_keys, key=lambda k: FREQ_MAP[k].value, reverse=True)
        if len(sorted_keys) >= 2:
            big = self.analyses[sorted_keys[0]]
            small = self.analyses[sorted_keys[-1]]
            if big.zs_fxs and small.zs_fxs:
                big_zs = big.zs_fxs[-1]
                small_zs = small.zs_fxs[-1]
                if small_zs.low >= big_zs.low and small_zs.high <= big_zs.high:
                    lines.append(f"嵌套: {sorted_keys[-1]} 中枢在 {sorted_keys[0]} 中枢内部 → 标准震荡 ⚪")
                elif small_zs.low > big_zs.high:
                    lines.append(f"嵌套: {sorted_keys[-1]} 中枢在 {sorted_keys[0]} 中枢上方 → 强势离开 🟢")
                elif small_zs.high < big_zs.low:
                    lines.append(f"嵌套: {sorted_keys[-1]} 中枢在 {sorted_keys[0]} 中枢下方 → 弱势离开 🔴")
        
        # ── 4. 综合评分 ──
        score = 0
        # 笔方向一致 +2/-2
        if len(unique_dirs) == 1:
            d = list(unique_dirs)[0]
            score += 2 if d == '向上' else -2
        # 中枢位置
        if zs_positions:
            n_above = sum(1 for p in zs_positions.values() if '上方' in p)
            n_below = sum(1 for p in zs_positions.values() if '下方' in p)
            score += n_above - n_below
        # 嵌套
        if len(sorted_keys) >= 2 and big.zs_fxs and small.zs_fxs:
            if small_zs.low > big_zs.high:
                score += 2
            elif small_zs.high < big_zs.low:
                score -= 2
        
        if score >= 4:
            verdict = '🟢 强做多（笔+中枢+嵌套三重共振）'
        elif score >= 2:
            verdict = '🟢 偏多（至少两项共振）'
        elif score <= -4:
            verdict = '🔴 强做空（笔+中枢+嵌套三重共振）'
        elif score <= -2:
            verdict = '🔴 偏空（至少两项共振）'
        else:
            verdict = '⚪ 震荡观望（信号不足，等方向确认）'
        
        lines.append(f"综合评分: {score:+d} → {verdict}")
        
        return '\n'.join(lines)
    
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
        resonance = self.resonance_check().replace('\n', '\n  ')
        lines.append(f"- **共振判断**:\n  {resonance}")
        lines.append(f"- **买入信号**: {self.buy_signal_summary()}")
        lines.append("")
        
        # 各级别详解
        for fk in self.freq_keys:
            fa = self.analyses[fk]
            lines.append(f"## {fk} 级别")
            lines.append(f"- K 线: {fa.n_klines} | 分型: {fa.n_fx} | 笔: {fa.n_bi} | UBI: {fa.n_ubi}")
            
            if fa.zs_fxs:
                lines.append(f"- **中枢**: ${fa.zs_low:.4f} — ${fa.zs_high:.4f} | 力度: {fa.zs_power} | 位置: {fa.zs_position}")
            else:
                lines.append(f"- **中枢**: 无")
            
            if fa.signals:
                lines.append("- **信号**:")
                for name, sigs in fa.signals.items():
                    sig_strs = [str(s) for s in sigs]
                    lines.append(f"  - 【{name}】✅ {' | '.join(sig_strs)}")
            
            # 背驰 + 买卖点模式
            div = fa.divergence_check()
            bsp = fa.buy_sell_pattern()
            if div:
                lines.append(f"- **背驰**: {div}")
            if bsp:
                lines.append(f"- **买卖点模式**: {bsp}")
            
            # 笔序列（最近5笔）
            bi_list = fa.c.bi_list[-5:]
            if bi_list:
                lines.append("\n| 笔 | 方向 | 起点 | 终点 | 力度 |")
                lines.append("|-----|------|------|------|------|")
                for bi in bi_list:
                    idx = fa.c.bi_list.index(bi) + 1
                    lines.append(
                        f"| BI#{idx} | {bi.direction.value} | "
                        f"${bi.fx_a.fx:.4f} | ${bi.fx_b.fx:.4f} | "
                        f"{bi.power*100:+.1f}% |"
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
    
    def print_summary(self, show_signals=False):
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
            
            if show_signals and fa.signals:
                for name, sigs in fa.signals.items():
                    print(f"  【{name}】✅")
            
            div = fa.divergence_check()
            if div:
                print(f"  背驰: {div}")
            bsp = fa.buy_sell_pattern()
            if bsp:
                print(f"  模式: {bsp}")
        
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
    
    i = 1
    while i < len(sys.argv):
        arg = sys.argv[i]
        if arg == '--chart':
            do_chart = True
        elif arg == '--signals':
            do_signals = True
        elif arg == '--report':
            do_report = True
        elif arg == '--freqs' and i + 1 < len(sys.argv):
            freqs = sys.argv[i + 1].split(',')
            i += 1  # 跳过值
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
        i += 1
    
    return symbol, freqs, do_chart, do_signals, do_report


def main():
    symbol, freqs, do_chart, do_signals, do_report = parse_args()
    
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
    mfa.print_summary(show_signals=do_signals)
    
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
