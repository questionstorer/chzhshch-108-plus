#!/usr/bin/env python3
"""
Demo: 缠论技术分析系统 (Chan Theory Technical Analysis)

This demo shows how to use the Chan Theory implementation to analyze
a stock. It supports three modes:

1. TUSHARE MODE: Fetch real stock data via tushare API
   - Set TUSHARE_TOKEN environment variable or pass --token
   - Example: python demo.py --token YOUR_TOKEN --code 000001.SZ

2. CSV MODE: Load data from a CSV file
   - Example: python demo.py --csv your_data.csv

3. DEMO MODE (default): Generate realistic synthetic data
   - Example: python demo.py

Usage:
    python demo.py                              # Synthetic demo
    python demo.py --token TOKEN --code 000001.SZ  # Tushare
    python demo.py --csv data.csv               # CSV file
"""

import argparse
import json
import math
import os
import random
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from chan_theory import ChanAnalyzer, MultiLevelAnalyzer, RawKLine
from chan_theory.visualize import plot_analysis


def generate_realistic_stock_data(
    n: int = 500,
    seed: int = 42,
    base_price: float = 15.0,
    ticker: str = "DEMO",
) -> list[RawKLine]:
    """
    Generate realistic synthetic stock data that mimics A-share price action.

    Includes:
    - Long-term trend (slowly rising)
    - Cyclical patterns (simulating hub oscillations)
    - Short-term noise (daily volatility)
    - Volume correlation with price movement
    """
    random.seed(seed)
    klines = []
    price = base_price

    for i in range(n):
        # Long-term upward drift
        drift = 0.001 * price

        # Cyclical component (simulates hub oscillation)
        cycle1 = 0.8 * math.sin(2 * math.pi * i / 60)
        cycle2 = 0.4 * math.sin(2 * math.pi * i / 25)
        cycle3 = 0.2 * math.sin(2 * math.pi * i / 12)

        # Mean-reverting noise
        noise = random.gauss(0, 0.3)

        # Price change
        change = drift + (cycle1 + cycle2 + cycle3) * 0.15 + noise * 0.1
        price = max(price + change, 1.0)

        # OHLCV generation
        volatility = 0.02 * price
        high = price + abs(random.gauss(0, volatility))
        low = price - abs(random.gauss(0, volatility))
        open_p = price + random.gauss(0, volatility * 0.5)
        close_p = price + random.gauss(0, volatility * 0.5)

        # Ensure OHLC consistency
        high = max(high, open_p, close_p)
        low = min(low, open_p, close_p)

        # Volume inversely related to price stability
        vol_base = 5000000
        vol_noise = random.gauss(0, vol_base * 0.3)
        vol_move = abs(change) / price * vol_base * 10
        volume = max(vol_base + vol_noise + vol_move, 100000)

        # Date generation (trading days only, ~250 per year)
        year = 2023 + i // 250
        day_of_year = (i % 250) + 1
        month = min((day_of_year - 1) // 21 + 1, 12)
        day = ((day_of_year - 1) % 21) + 1

        klines.append(RawKLine(
            index=i,
            dt=f"{year}{month:02d}{day:02d}",
            open=round(open_p, 2),
            close=round(close_p, 2),
            high=round(high, 2),
            low=round(low, 2),
            volume=round(volume, 0),
        ))

    return klines


def run_analysis(klines: list[RawKLine], title: str) -> ChanAnalyzer:
    """Run Chan Theory analysis and print results."""
    analyzer = ChanAnalyzer()
    analyzer.load(klines)
    analyzer.analyze()

    # ──────────────────────────────────────────────────────────
    # Print comprehensive analysis report
    # ──────────────────────────────────────────────────────────

    print("\n" + "=" * 70)
    print(f"  缠论技术分析报告 — {title}")
    print("=" * 70)

    summary = analyzer.summary()

    print(f"\n📊 数据统计:")
    print(f"   原始K线:   {summary['raw_klines']}")
    print(f"   处理后K线: {summary['processed_klines']} (合并包含关系后)")
    print(f"   分型数量:  {summary['fractals']}")
    print(f"   笔数量:    {summary['bis']}")
    print(f"   线段数量:  {summary['segments']}")

    print(f"\n📈 趋势判断:")
    print(f"   趋势类型:  {summary['trend_type']}")
    print(f"   趋势状态:  {summary['trend_status']}")
    print(f"   当前阶段:  {summary['phase']}")
    print(f"   建议操作:  {summary['phase_action']}")

    if summary.get('phase_action') == 'oscillation_buy':
        print(f"   ➡ 底部构筑阶段, 以中枢震荡方式逢低买入")
    elif summary.get('phase_action') == 'oscillation_sell':
        print(f"   ➡ 顶部构筑阶段, 以中枢震荡方式逢高卖出")
    elif summary.get('phase_action') == 'hold':
        print(f"   ➡ 中间连接段, 持有等待")

    print(f"\n🏗️  中枢 ({summary['hubs_bi_level']} bi-level, "
          f"{summary['hubs_seg_level']} seg-level):")
    for i, h in enumerate(summary['hub_details']):
        level_str = f"级别{h['level']}" if h['level'] > 0 else "笔级别"
        ext_str = " [延伸]" if h['extended'] else ""
        print(f"   中枢{i+1} ({level_str}{ext_str}): "
              f"ZD={h['ZD']:.2f}, ZG={h['ZG']:.2f}, "
              f"范围=[{h['DD']:.2f}, {h['GG']:.2f}], "
              f"元素={h['elements']}")

    print(f"\n🎯 买卖点信号 ({summary['signals']} total):")
    if summary['signal_details']:
        for sig in summary['signal_details']:
            emoji = "🟢" if "B" in sig['type'] else "🔴"
            print(f"   {emoji} {sig['type']} @ {sig['dt']} "
                  f"价格={sig['price']:.2f} — {sig['description']}")
    else:
        print("   (暂无信号)")

    print(f"\n💡 策略建议 (最近 {len(summary['trade_recommendations'])} 条):")
    for rec in summary['trade_recommendations']:
        emoji = {"BUY": "🟢", "SELL": "🔴", "HOLD": "🟡",
                 "REDUCE": "🟠"}.get(rec['action'], "⚪")
        print(f"   {emoji} {rec['action']} @ {rec['dt']} "
              f"价格={rec['price']:.2f} "
              f"信心={rec['confidence']:.0%} — {rec['reason']}")

    # Auxiliary indicators summary
    if analyzer.ma_kisses:
        kiss_types = {}
        for k in analyzer.ma_kisses:
            name = k['type'].name
            kiss_types[name] = kiss_types.get(name, 0) + 1
        print(f"\n📉 MA均线吻分类:")
        for ktype, count in kiss_types.items():
            print(f"   {ktype}: {count}次")

    if analyzer.boll_contractions:
        print(f"\n📏 布林带收缩事件: {len(analyzer.boll_contractions)}次")

    if analyzer.gaps:
        gap_types = {}
        for g in analyzer.gaps:
            name = g.gap_type.name
            gap_types[name] = gap_types.get(name, 0) + 1
        print(f"\n🔲 缺口分析:")
        for gtype, count in gap_types.items():
            print(f"   {gtype}: {count}个")

    print("\n" + "=" * 70)

    return analyzer


def demo_tushare(token: str, ts_code: str, start: str, end: str):
    """Run demo with tushare data."""
    from chan_theory.data_source import TushareDataSource

    print(f"Fetching data for {ts_code} from {start} to {end}...")
    ds = TushareDataSource(token=token)

    # Single-level analysis
    klines = ds.get_daily(ts_code, start, end)
    if not klines:
        print(f"ERROR: No data returned for {ts_code}")
        return

    print(f"Loaded {len(klines)} daily K-lines")
    analyzer = run_analysis(klines, f"{ts_code} 日线分析")

    # Generate chart
    chart_path = f"chan_analysis_{ts_code.replace('.', '_')}.png"
    plot_analysis(analyzer, title=f"{ts_code} 缠论技术分析",
                  save_path=chart_path)

    # Multi-level analysis
    print("\n\n" + "=" * 70)
    print("  多级别联立分析 (Multi-Level Analysis)")
    print("=" * 70)

    weekly = ds.get_weekly(ts_code, start, end)
    if weekly:
        mla = MultiLevelAnalyzer()
        mla.add_level("daily", klines)
        mla.add_level("weekly", weekly)

        # Level resonance
        resonance = mla.level_resonance()
        if resonance:
            print("\n⚡ 级别共振:")
            for event in resonance:
                print(f"   {event['description']}")
        else:
            print("\n⚡ 级别共振: 暂无多级别共振信号")

        # Cross-level status
        status = mla.cross_level_trend_status()
        print("\n📊 各级别状态:")
        for level, info in status.items():
            print(f"   {level}: 趋势={info['trend_type']}, "
                  f"中枢={info['hubs']}, 信号={info['signals']}")

        # Interval nesting
        nesting = mla.interval_nesting()
        if nesting:
            print(f"\n🎯 区间套分析 ({len(nesting)} signals):")
            for n_item in nesting[:5]:
                conf = n_item['confidence']
                origin = n_item['origin_level']
                sig = n_item['origin_signal']
                print(f"   {sig.type.value} from {origin}: "
                      f"confidence={conf:.0%}")


def demo_csv(csv_path: str):
    """Run demo with CSV data."""
    from chan_theory.data_source import TushareDataSource

    print(f"Loading data from {csv_path}...")
    klines = TushareDataSource.from_csv(csv_path)
    if not klines:
        print(f"ERROR: No data loaded from {csv_path}")
        return

    print(f"Loaded {len(klines)} K-lines")
    analyzer = run_analysis(klines, f"CSV数据分析: {csv_path}")
    plot_analysis(analyzer, title=f"缠论分析: {csv_path}",
                  save_path="chan_analysis_csv.png")


def demo_synthetic():
    """Run demo with realistic synthetic data."""
    print("Generating realistic synthetic stock data...")
    print("(Use --token and --code for real data via tushare)")
    print()

    klines = generate_realistic_stock_data(n=500, seed=42, base_price=15.0)
    print(f"Generated {len(klines)} synthetic K-lines")

    # Single-level analysis
    analyzer = run_analysis(klines, "模拟股票 DEMO.SZ 日线分析")

    # Generate chart
    plot_analysis(
        analyzer,
        title="缠论分析 — 模拟股票 DEMO.SZ",
        save_path="chan_analysis_demo.png",
    )

    # Multi-level analysis with synthetic weekly data
    print("\n\n" + "=" * 70)
    print("  多级别联立分析 Demo (Multi-Level Analysis)")
    print("=" * 70)

    # Generate weekly-like data (every 5th kline, broader range)
    weekly_klines = generate_realistic_stock_data(
        n=100, seed=42, base_price=15.0
    )

    mla = MultiLevelAnalyzer()
    mla.add_level("daily", klines)
    mla.add_level("weekly", weekly_klines)

    # Cross-level status
    status = mla.cross_level_trend_status()
    print("\n📊 各级别状态:")
    for level, info in status.items():
        print(f"   {level}: 趋势={info['trend_type']}, "
              f"笔={info['bis']}, 中枢={info['hubs']}, "
              f"信号={info['signals']}")

    # Level resonance
    resonance = mla.level_resonance()
    if resonance:
        print("\n⚡ 级别共振:")
        for event in resonance:
            print(f"   {event['description']}")
    else:
        print("\n⚡ 暂无多级别共振")

    # Interval nesting
    nesting = mla.interval_nesting()
    if nesting:
        print(f"\n🎯 区间套分析 ({len(nesting)} signals):")
        for n_item in nesting[:5]:
            sig = n_item['origin_signal']
            print(f"   {sig.type.value} @ {sig.dt}: "
                  f"confidence={n_item['confidence']:.0%}, "
                  f"confirmations={len(n_item['nested_confirmations'])}")

    print("\n" + "=" * 70)
    print("  Demo complete! Chart saved to chan_analysis_demo.png")
    print("=" * 70)


def main():
    parser = argparse.ArgumentParser(
        description="缠论技术分析 Demo (Chan Theory Analysis Demo)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python demo.py                                    # Synthetic data demo
  python demo.py --token YOUR_TOKEN --code 000001.SZ  # Real stock data
  python demo.py --csv stock_data.csv               # From CSV file
  python demo.py --token YOUR_TOKEN --code 600519.SH --start 20230101 --end 20241231
        """,
    )

    parser.add_argument("--token", type=str, default=None,
                        help="Tushare API token")
    parser.add_argument("--code", type=str, default="000001.SZ",
                        help="Stock code (default: 000001.SZ)")
    parser.add_argument("--start", type=str, default="20240101",
                        help="Start date YYYYMMDD (default: 20240101)")
    parser.add_argument("--end", type=str, default="20251231",
                        help="End date YYYYMMDD (default: 20251231)")
    parser.add_argument("--csv", type=str, default=None,
                        help="Path to CSV file with OHLCV data")

    args = parser.parse_args()

    # Check for token in environment
    token = args.token or os.environ.get("TUSHARE_TOKEN")

    if args.csv:
        demo_csv(args.csv)
    elif token:
        demo_tushare(token, args.code, args.start, args.end)
    else:
        demo_synthetic()


if __name__ == "__main__":
    main()
