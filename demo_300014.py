#!/usr/bin/env python3
from __future__ import annotations
"""
Demo: 缠论分析 — 300014.SZ 亿纬锂能

Tries to fetch real data from tushare first.
Falls back to synthetic data if tushare is unavailable.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from chan_theory import ChanAnalyzer, MultiLevelAnalyzer, RawKLine
from chan_theory.visualize import plot_analysis

# ── Configure matplotlib for Chinese characters ──────────────────────
import matplotlib
import matplotlib.pyplot as plt

# Try to use a font that supports CJK characters
for font_name in ['SimHei', 'Microsoft YaHei', 'STSong', 'Arial Unicode MS']:
    try:
        matplotlib.rcParams['font.sans-serif'] = [font_name] + matplotlib.rcParams['font.sans-serif']
        break
    except Exception:
        pass
matplotlib.rcParams['axes.unicode_minus'] = False


# ── Token ─────────────────────────────────────────────────────────────
TOKEN_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tushare_token.txt")

def read_token():
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, "r") as f:
            return f.read().strip()
    return os.environ.get("TUSHARE_TOKEN", "")


# ── Try fetching real data ────────────────────────────────────────────
def fetch_real_data(ts_code, start, end, token):
    """Attempt to fetch real daily K-line data via tushare."""
    try:
        from chan_theory.data_source import TushareDataSource
        ds = TushareDataSource(token=token)
        klines = ds.get_daily(ts_code, start, end, adj="")
        if klines and len(klines) > 50:
            return klines, "daily"
        # If adj="" fails, try without calling pro_bar
        klines = ds.get_daily(ts_code, start, end, adj="qfq")
        if klines and len(klines) > 50:
            return klines, "daily"
    except Exception as e:
        print(f"  tushare fetch failed: {e}")
    return None, None


def fetch_real_weekly(ts_code, start, end, token):
    """Attempt to fetch real weekly K-line data via tushare."""
    try:
        from chan_theory.data_source import TushareDataSource
        ds = TushareDataSource(token=token)
        return ds.get_weekly(ts_code, start, end, adj="")
    except Exception:
        return None


# ── Synthetic fallback ────────────────────────────────────────────────
def generate_300014_synthetic(n=500, seed=300014):
    """
    Generate synthetic data resembling 300014.SZ (亿纬锂能) price behaviour.
    Base price ~35 CNY, with realistic A-share daily patterns.
    """
    import math
    import random

    random.seed(seed)
    klines = []
    price = 35.0

    for i in range(n):
        drift = 0.0008 * price
        cycle1 = 1.0 * math.sin(2 * math.pi * i / 55)
        cycle2 = 0.5 * math.sin(2 * math.pi * i / 22)
        cycle3 = 0.25 * math.sin(2 * math.pi * i / 10)
        noise = random.gauss(0, 0.35)

        change = drift + (cycle1 + cycle2 + cycle3) * 0.18 + noise * 0.12
        price = max(price + change, 5.0)

        vol = 0.02 * price
        high = price + abs(random.gauss(0, vol))
        low = price - abs(random.gauss(0, vol))
        open_p = price + random.gauss(0, vol * 0.5)
        close_p = price + random.gauss(0, vol * 0.5)
        high = max(high, open_p, close_p)
        low = min(low, open_p, close_p)

        vol_base = 8_000_000
        volume = max(vol_base + random.gauss(0, vol_base * 0.3)
                     + abs(change) / price * vol_base * 8, 200_000)

        year = 2024 + i // 250
        day_of_year = (i % 250) + 1
        month = min((day_of_year - 1) // 21 + 1, 12)
        day = ((day_of_year - 1) % 21) + 1

        klines.append(RawKLine(
            index=i,
            dt="{}{:02d}{:02d}".format(year, month, day),
            open=round(open_p, 2),
            close=round(close_p, 2),
            high=round(high, 2),
            low=round(low, 2),
            volume=round(volume, 0),
        ))
    return klines


def generate_300014_weekly_synthetic(n=100, seed=300015):
    """Generate synthetic weekly data for multi-level analysis."""
    import math
    import random

    random.seed(seed)
    klines = []
    price = 35.0

    for i in range(n):
        drift = 0.004 * price
        cycle1 = 2.0 * math.sin(2 * math.pi * i / 20)
        cycle2 = 1.0 * math.sin(2 * math.pi * i / 8)
        noise = random.gauss(0, 0.6)

        change = drift + (cycle1 + cycle2) * 0.2 + noise * 0.15
        price = max(price + change, 5.0)

        vol = 0.035 * price
        high = price + abs(random.gauss(0, vol))
        low = price - abs(random.gauss(0, vol))
        open_p = price + random.gauss(0, vol * 0.5)
        close_p = price + random.gauss(0, vol * 0.5)
        high = max(high, open_p, close_p)
        low = min(low, open_p, close_p)
        volume = max(30_000_000 + random.gauss(0, 10_000_000), 1_000_000)

        year = 2024 + i // 52
        week = (i % 52) + 1
        month = min((week - 1) // 4 + 1, 12)
        day = min(((week - 1) % 4) * 7 + 1, 28)

        klines.append(RawKLine(
            index=i,
            dt="{}{:02d}{:02d}".format(year, month, day),
            open=round(open_p, 2),
            close=round(close_p, 2),
            high=round(high, 2),
            low=round(low, 2),
            volume=round(volume, 0),
        ))
    return klines


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
    return analyzer


# ── Main ──────────────────────────────────────────────────────────────
def main():
    ts_code = "300014.SZ"
    start = "20240101"
    end = "20260331"
    token = read_token()

    print("=" * 70)
    print("  Chan Theory Analysis Demo  --  300014.SZ (Yi Wei Li Neng)")
    print("=" * 70)

    # ── Try real data first ───────────────────────────────────────────
    klines = None
    data_source = "synthetic"

    if token:
        print("\nTushare token found. Attempting to fetch real data...")
        klines, freq = fetch_real_data(ts_code, start, end, token)
        if klines:
            data_source = "tushare"
            print("  Loaded {} real daily K-lines from tushare".format(len(klines)))

    if klines is None:
        print("\nUsing synthetic data (tushare unavailable or returned no data).")
        print("To use real data, ensure tushare API is accessible and token is valid.")
        klines = generate_300014_synthetic(n=500)
        print("  Generated {} synthetic daily K-lines".format(len(klines)))

    # ── Single-level analysis ─────────────────────────────────────────
    analyzer = ChanAnalyzer()
    analyzer.load(klines)
    analyzer.analyze()

    label = "real" if data_source == "tushare" else "synthetic"
    print_report(analyzer, "{} Daily Analysis ({} data)".format(ts_code, label))

    chart_path = "chan_analysis_300014_SZ.png"
    plot_analysis(
        analyzer,
        title="{} Chan Theory Analysis ({})".format(ts_code, label),
        save_path=chart_path,
    )
    print("\nChart saved to {}".format(chart_path))

    # ── Multi-level analysis ──────────────────────────────────────────
    print("\n\n" + "=" * 70)
    print("  Multi-Level Analysis (Daily + Weekly)")
    print("=" * 70)

    weekly = None
    if data_source == "tushare" and token:
        weekly = fetch_real_weekly(ts_code, start, end, token)
    if weekly is None:
        weekly = generate_300014_weekly_synthetic(n=100)
        print("  Using synthetic weekly data ({} bars)".format(len(weekly)))

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
