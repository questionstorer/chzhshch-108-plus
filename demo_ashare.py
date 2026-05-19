#!/usr/bin/env python3
from __future__ import annotations
"""
Demo: 缠论分析 using Ashare (free Sina/Tencent data, no token needed)

Fetches real A-share data via Ashare package and runs Chan Theory analysis.

Usage:
    python demo_ashare.py                           # Default: 300014.SZ daily
    python demo_ashare.py --code sz300014 --count 500
    python demo_ashare.py --code sh600519 --count 300
    python demo_ashare.py --code 000001.SZ --count 400

Code formats:
    sz300014 / sh600519        - Prefix format
    300014.SZ / 600519.SH      - Tushare format
    300014.XSHE / 600519.XSHG  - JoinQuant format
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from chan_theory import ChanAnalyzer, MultiLevelAnalyzer
from chan_theory.data_source import AshareDataSource
from chan_theory.visualize import plot_analysis

# ── Configure matplotlib for Chinese characters ──────────────────────
import matplotlib
import matplotlib.pyplot as plt

for font_name in ['SimHei', 'Microsoft YaHei', 'STSong', 'Arial Unicode MS',
                   'WenQuanYi Micro Hei', 'Noto Sans CJK SC', 'DejaVu Sans']:
    try:
        matplotlib.rcParams['font.sans-serif'] = [font_name] + matplotlib.rcParams['font.sans-serif']
        break
    except Exception:
        pass
matplotlib.rcParams['axes.unicode_minus'] = False


# ── Pretty print analysis ────────────────────────────────────────────
def print_report(analyzer, title):
    """Print a comprehensive Chan Theory analysis report."""
    print("\n" + "=" * 70)
    print("  {}".format(title))
    print("=" * 70)

    s = analyzer.summary()

    print("\n  Data Summary:")
    print("   Raw K-lines:       {}".format(s['raw_klines']))
    print("   Processed K-lines: {} (after inclusion merge)".format(s['processed_klines']))
    print("   Fractals:          {}".format(s['fractals']))
    print("   Bi (strokes):      {}".format(s['bis']))
    print("   Segments:          {}".format(s['segments']))

    print("\n  Trend:")
    print("   Type:   {}".format(s['trend_type']))
    print("   Status: {}".format(s['trend_status']))
    print("   Phase:  {}".format(s['phase']))
    print("   Action: {}".format(s['phase_action']))

    print("\n  Hubs ({} bi-level, {} seg-level):".format(
        s['hubs_bi_level'], s['hubs_seg_level']))
    for i, h in enumerate(s['hub_details']):
        ext = " [extended]" if h['extended'] else ""
        print("   Hub {}{}: ZD={:.2f} ZG={:.2f}  range=[{:.2f}, {:.2f}]  elements={}".format(
            i + 1, ext, h['ZD'], h['ZG'], h['DD'], h['GG'], h['elements']))

    print("\n  Signals ({} total):".format(s['signals']))
    if s['signal_details']:
        for sig in s['signal_details']:
            tag = "BUY " if "B" in sig['type'] else "SELL"
            print("   [{}] {} @ {} price={:.2f} -- {}".format(
                tag, sig['type'], sig['dt'], sig['price'], sig['description']))
    else:
        print("   (none)")

    print("\n  Strategy Recommendations ({} total):".format(len(s['trade_recommendations'])))
    for rec in s['trade_recommendations']:
        print("   {} @ {} price={:.2f} confidence={:.0%} -- {}".format(
            rec['action'], rec['dt'], rec['price'],
            rec['confidence'], rec['reason']))

    if analyzer.ma_kisses:
        kiss_counts = {}
        for k in analyzer.ma_kisses:
            name = k['type'].name
            kiss_counts[name] = kiss_counts.get(name, 0) + 1
        print("\n  MA Kiss Classification:")
        for ktype, count in kiss_counts.items():
            print("   {}: {} times".format(ktype, count))

    if analyzer.gaps:
        gap_counts = {}
        for g in analyzer.gaps:
            name = g.gap_type.name
            gap_counts[name] = gap_counts.get(name, 0) + 1
        print("\n  Gap Analysis:")
        for gtype, count in gap_counts.items():
            print("   {}: {}".format(gtype, count))

    if analyzer.boll_contractions:
        print("\n  Bollinger Band Contractions: {} events".format(
            len(analyzer.boll_contractions)))

    print("\n" + "=" * 70)


# ── Main ──────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description="缠论分析 Demo — Ashare free data (Sina/Tencent)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python demo_ashare.py                                   # 300014.SZ 500 bars
  python demo_ashare.py --code sh600519 --count 300       # 贵州茅台
  python demo_ashare.py --code sz000001 --count 400       # 平安银行
  python demo_ashare.py --code 000001.SZ --end 2025-06-30 # with end date
        """,
    )
    parser.add_argument("--code", type=str, default="300014.SZ",
                        help="Stock code (default: 300014.SZ 亿纬锂能)")
    parser.add_argument("--count", type=int, default=500,
                        help="Number of daily bars (default: 500)")
    parser.add_argument("--weekly-count", type=int, default=200,
                        help="Number of weekly bars (default: 200)")
    parser.add_argument("--end", type=str, default="",
                        help="End date YYYY-MM-DD or YYYYMMDD (default: today)")

    args = parser.parse_args()

    code = args.code
    display_code = code.upper()

    print("=" * 70)
    print("  Chan Theory Analysis Demo — {} (Ashare free data)".format(display_code))
    print("=" * 70)

    # ── Initialize Ashare data source ─────────────────────────────────
    ds = AshareDataSource()

    # ── Fetch daily data ──────────────────────────────────────────────
    print("\nFetching {} daily K-lines for {}...".format(args.count, display_code))
    klines = ds.get_daily(code, count=args.count, end_date=args.end)
    if not klines:
        print("ERROR: No data returned for {}".format(display_code))
        print("Check that the code is valid (e.g., sz300014, sh600519, 000001.SZ)")
        sys.exit(1)
    print("  Loaded {} daily K-lines  [{} ~ {}]".format(
        len(klines), klines[0].dt, klines[-1].dt))

    # ── Single-level analysis ─────────────────────────────────────────
    analyzer = ChanAnalyzer()
    analyzer.load(klines)
    analyzer.analyze()

    print_report(analyzer, "{} Daily Analysis (real data)".format(display_code))

    safe_code = display_code.replace(".", "_")
    chart_path = "chan_analysis_{}.png".format(safe_code)
    plot_analysis(
        analyzer,
        title="{} Chan Theory Analysis (daily)".format(display_code),
        save_path=chart_path,
    )
    print("\nChart saved to {}".format(chart_path))

    # ── Fetch weekly data for multi-level analysis ────────────────────
    print("\n\n" + "=" * 70)
    print("  Multi-Level Analysis (Daily + Weekly)")
    print("=" * 70)

    print("\nFetching {} weekly K-lines for {}...".format(
        args.weekly_count, display_code))
    weekly = ds.get_weekly(code, count=args.weekly_count, end_date=args.end)

    if not weekly:
        print("  WARNING: No weekly data returned, skipping multi-level analysis.")
    else:
        print("  Loaded {} weekly K-lines  [{} ~ {}]".format(
            len(weekly), weekly[0].dt, weekly[-1].dt))

        mla = MultiLevelAnalyzer()
        mla.add_level("daily", klines)
        mla.add_level("weekly", weekly)

        # Cross-level status
        status = mla.cross_level_trend_status()
        print("\n  Cross-Level Trend Status:")
        for level, info in status.items():
            print("   {}: trend={}, bis={}, hubs={}, signals={}".format(
                level, info['trend_type'], info['bis'],
                info['hubs'], info['signals']))

        # Level resonance
        resonance = mla.level_resonance()
        if resonance:
            print("\n  Level Resonance:")
            for event in resonance:
                print("   {}".format(event['description']))
        else:
            print("\n  Level Resonance: no multi-level resonance signals")

        # Interval nesting
        nesting = mla.interval_nesting()
        if nesting:
            print("\n  Interval Nesting ({} signals):".format(len(nesting)))
            for item in nesting[:5]:
                sig = item['origin_signal']
                print("   {} @ {}: confidence={:.0%}, origin={}".format(
                    sig.type.value, sig.dt,
                    item['confidence'], item['origin_level']))
        else:
            print("\n  Interval Nesting: no nested signals detected")

    print("\n" + "=" * 70)
    print("  Done! Open {} to see the chart.".format(chart_path))
    print("=" * 70)


if __name__ == "__main__":
    main()
