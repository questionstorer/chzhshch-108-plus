# 缠论技术分析系统 (Chan Theory Technical Analysis System)

Implementation of the "缠中说禅" (Chan Zhong Shuo Chan) technical analysis system based on the 108 lessons of "教你炒股票" (Teaching You Stock Trading).

## Table of Contents

- [Overview](#overview)
- [Installation & Setup](#installation--setup)
- [Quick Start](#quick-start)
- [Architecture](#architecture)
- [Module Reference](#module-reference)
- [Tushare Integration](#tushare-integration)
- [Multi-Level Analysis](#multi-level-analysis)
- [Trading Strategies](#trading-strategies)
- [Theory Summary](#theory-summary)
- [FAQ](#faq)

---

## Overview

This system implements a comprehensive Chan Theory (缠论) framework based on the 108 lessons of 缠中说禅. Core theorems (Lessons 17, 20, 29, 62) are followed closely; higher-level constructs such as segment construction, interval nesting, and the three-phase model are practical approximations that cover the common cases.

| Feature | Lessons | Module |
|---------|---------|--------|
| K-line inclusion processing (包含处理) | 62 | `kline_processor.py` |
| Fractal detection + strength (分型识别) | 62, 82 | `fractal.py` |
| Bi/Stroke construction (笔) | 62 | `bi.py` |
| Segment construction - Case 1 & 2 (线段) | 62, 65, 67, 77, 78 | `segment.py` |
| Hub detection, extension, expansion (中枢) | 17, 20, 24, 25, 33, 36, 70 | `hub.py` |
| MACD divergence (背驰) | 15, 25 | `divergence.py` |
| Three classes of buy/sell points (三类买卖点) | 15, 17, 20, 21 | `signals.py` |
| Bollinger Bands, MA kisses, gap analysis | 15, 77, 90 | `indicators.py` |
| Trend monitoring (走势必完美) | 17, 45, 108 | `strategies.py` |
| Hub oscillation & mechanical trading | 33, 38, 68, 108 | `strategies.py` |
| Multi-level analysis & interval nesting | 37, 52, 53, 60, 81 | `multi_level.py` |
| Tushare data source | — | `data_source.py` |
| Visualization | — | `visualize.py` |

---

## Installation & Setup

### Prerequisites

- Python 3.10+
- pip

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd chzhshch-108-plus

# Install dependencies
pip install -r requirements.txt
```

### Dependencies

| Package | Purpose | Required? |
|---------|---------|-----------|
| `matplotlib` | Chart generation | Yes (for visualization) |
| `tushare` | Chinese A-share stock data | Yes (for live data) |
| `pandas` | Data manipulation (used by tushare) | Yes (for tushare) |

### Tushare Token Setup

To use live stock data, you need a Tushare API token:

1. Register at [https://tushare.pro/](https://tushare.pro/)
2. Get your API token from the user dashboard
3. Use it in your code:

```python
from chan_theory.data_source import TushareDataSource

ds = TushareDataSource(token='your_token_here')
```

> **Note:** Without a tushare token, you can still use the system with CSV files or any other data source by converting to `RawKLine` format.

---

## Quick Start

### Minimal Example (with synthetic data)

```python
from chan_theory import ChanAnalyzer, RawKLine

# Create some K-line data (replace with real data)
klines = [
    RawKLine(index=i, dt=f'2024-01-{i+1:02d}',
             open=10+i*0.1, close=10.5+i*0.1,
             high=11+i*0.1, low=9.5+i*0.1)
    for i in range(200)
]

analyzer = ChanAnalyzer()
analyzer.load(klines)
analyzer.analyze()

# Print summary
import json
print(json.dumps(analyzer.summary(), indent=2, ensure_ascii=False))
```

### With Tushare (Live Data)

```python
from chan_theory import ChanAnalyzer
from chan_theory.data_source import TushareDataSource
from chan_theory.visualize import plot_analysis

# Fetch data
ds = TushareDataSource(token='your_token')
klines = ds.get_daily('000001.SZ', '20240101', '20241231')

# Analyze
analyzer = ChanAnalyzer()
analyzer.load(klines)
analyzer.analyze()

# Visualize
plot_analysis(analyzer, title='平安银行 缠论分析')

# Get signals
for sig in analyzer.signals:
    print(f'{sig.type.value} @ {sig.dt} price={sig.price:.2f}')
```

### With CSV File (No Token Needed)

```python
from chan_theory import ChanAnalyzer
from chan_theory.data_source import TushareDataSource

klines = TushareDataSource.from_csv(
    'your_data.csv',
    dt_col='date',
    open_col='open',
    close_col='close',
    high_col='high',
    low_col='low',
    vol_col='volume',
)

analyzer = ChanAnalyzer()
analyzer.load(klines)
analyzer.analyze()
```

---

## Architecture

```
chan_theory/
├── __init__.py          # Package exports
├── data_types.py        # Core data structures (RawKLine, KLine, Fractal, Bi, Segment, Hub, Signal, etc.)
├── kline_processor.py   # K-line inclusion handling (包含处理)
├── fractal.py           # Fractal detection + strength analysis (分型)
├── bi.py                # Bi/Stroke construction (笔)
├── segment.py           # Segment construction with Case 1/2 (线段)
├── hub.py               # Hub detection, extension, expansion, migration (中枢)
├── divergence.py        # MACD computation, divergence detection (背驰)
├── signals.py           # Three classes of buy/sell points (买卖点)
├── indicators.py        # Bollinger Bands, MA kisses, gaps (辅助指标)
├── strategies.py        # Trading strategies, trend monitoring (操作策略)
├── multi_level.py       # Multi-level analysis, interval nesting (多级别联立)
├── data_source.py       # Tushare integration (数据接口)
├── visualize.py         # Chart generation (可视化)
└── chan.py              # Main ChanAnalyzer orchestrator (主分析器)
```

### Analysis Pipeline

```
Raw K-lines
    │
    ▼
┌─────────────────────┐
│ 1. Inclusion Process │  (包含处理, Lesson 62)
│    Merge overlapping │
│    K-lines           │
└──────────┬──────────┘
           ▼
┌─────────────────────┐
│ 2. Fractal Detection │  (分型识别, Lesson 62)
│    Top/Bottom fractals│
│    + strength analysis│
└──────────┬──────────┘
           ▼
┌─────────────────────┐
│ 3. Bi Construction   │  (笔的构建, Lesson 62)
│    Connect fractals  │
│    with direction    │
└──────────┬──────────┘
           ▼
┌─────────────────────┐
│ 4. Segment Building  │  (线段, Lessons 65/67)
│    Case 1 & 2 term.  │
│    + standardization │
└──────────┬──────────┘
           ▼
┌─────────────────────┐
│ 5. Hub Detection     │  (中枢, Lessons 17/20)
│    Extension/Expansion│
│    + Migration       │
└──────────┬──────────┘
           ▼
┌─────────────────────┐
│ 6. MACD + Indicators │  (Lessons 15/25/77/90)
│    Divergence, BOLL  │
│    MA kisses, Gaps   │
└──────────┬──────────┘
           ▼
┌─────────────────────┐
│ 7. Signal Detection  │  (买卖点, Lessons 15/17/20)
│    B1/B2/B3 S1/S2/S3 │
└──────────┬──────────┘
           ▼
┌─────────────────────┐
│ 8. Trend & Strategy  │  (Lessons 17/33/38/108)
│    Completeness      │
│    Phase analysis    │
│    Trade signals     │
└─────────────────────┘
```

---

## Module Reference

### `ChanAnalyzer` — Main Analysis Engine

```python
from chan_theory import ChanAnalyzer

analyzer = ChanAnalyzer()
analyzer.load(raw_klines)       # Load RawKLine list
analyzer.load_from_dicts(data)  # Or load from dicts
analyzer.analyze()              # Run full pipeline

# Results
analyzer.klines      # Processed K-lines (after inclusion)
analyzer.fractals    # Detected fractals
analyzer.bis         # Bi strokes
analyzer.segments    # Segments
analyzer.hubs        # All hubs (bi-level + segment-level)
analyzer.hubs_bi     # Bi-level hubs
analyzer.hubs_seg    # Segment-level hubs
analyzer.signals     # Buy/sell signals (B1, B2, B3, S1, S2, S3)
analyzer.trend_type  # TrendType enum: UPTREND, DOWNTREND, CONSOLIDATION
analyzer.trend_monitor  # TrendMonitor with status/phase
analyzer.trade_signals  # Strategy-generated trade recommendations
analyzer.phase_info     # Three-phase analysis result
analyzer.macd_dif/dea/hist  # MACD data
analyzer.boll_upper/middle/lower  # Bollinger Bands
analyzer.ma_kisses      # MA kiss events
analyzer.gaps           # Price gaps
analyzer.summary()      # Complete summary dict
```

### `MultiLevelAnalyzer` — Multi-Level Analysis

```python
from chan_theory import MultiLevelAnalyzer

mla = MultiLevelAnalyzer()
mla.add_level("daily", daily_klines)
mla.add_level("weekly", weekly_klines)

# Interval nesting (区间套)
nesting = mla.interval_nesting()

# Level resonance (级别共振)
resonance = mla.level_resonance()

# Cross-level status
status = mla.cross_level_trend_status()
```

### Signal Types

| Type | Name | Description |
|------|------|-------------|
| `B1` | 第一类买点 | Divergence at end of downtrend |
| `B2` | 第二类买点 | Pullback after B1 that doesn't break B1's low |
| `B3` | 第三类买点 | Retest after hub exit upward that doesn't break ZG |
| `S1` | 第一类卖点 | Divergence at end of uptrend |
| `S2` | 第二类卖点 | Rally after S1 that doesn't break S1's high |
| `S3` | 第三类卖点 | Retest after hub exit downward that doesn't break ZD |

### Trend Types

| Type | Chinese | Description |
|------|---------|-------------|
| `UPTREND` | 上涨趋势 | 2+ ascending hubs where Hub2.DD > Hub1.GG (Lesson 20) |
| `DOWNTREND` | 下跌趋势 | 2+ descending hubs where Hub2.GG < Hub1.DD (Lesson 20) |
| `CONSOLIDATION` | 盘整 | Single hub or hubs that don't meet the DD/GG trend condition |

---

## Tushare Integration

### Data Source Methods

```python
from chan_theory.data_source import TushareDataSource

ds = TushareDataSource(token='your_token')

# Single-level data
daily = ds.get_daily('600519.SH', '20240101', '20241231')
weekly = ds.get_weekly('600519.SH', '20240101', '20241231')
monthly = ds.get_monthly('600519.SH', '20240101', '20241231')
minutes = ds.get_minutes('600519.SH', '20240101', '20241231', freq='30min')

# Multi-level data (for multi-level analysis)
data = ds.get_multi_level_data(
    '600519.SH', '20240101', '20241231',
    levels=['daily', 'weekly']
)

# Search for stocks
results = ds.search_stock('贵州茅台')
```

### Offline Usage (CSV)

```python
# Load from CSV (no tushare token needed)
klines = TushareDataSource.from_csv('stock_data.csv')

# Load from any pandas DataFrame
import pandas as pd
df = pd.read_csv('data.csv')
klines = TushareDataSource.from_dataframe(df, dt_col='date')
```

### Common Stock Codes (A-Share)

| Code | Name | Exchange |
|------|------|----------|
| `000001.SZ` | 平安银行 | Shenzhen |
| `600519.SH` | 贵州茅台 | Shanghai |
| `000858.SZ` | 五粮液 | Shenzhen |
| `601318.SH` | 中国平安 | Shanghai |
| `000333.SZ` | 美的集团 | Shenzhen |

---

## Multi-Level Analysis

Multi-level analysis (多级别联立) is one of the most powerful concepts in Chan Theory. It combines signals from different timeframes to increase confidence.

### Interval Nesting (区间套)

```python
from chan_theory import MultiLevelAnalyzer
from chan_theory.data_source import TushareDataSource

ds = TushareDataSource(token='your_token')
data = ds.get_multi_level_data('600519.SH', '20230101', '20241231',
                                levels=['daily', 'weekly'])

mla = MultiLevelAnalyzer()
for level_name, klines in data.items():
    mla.add_level(level_name, klines)

# Find signals confirmed across levels
nesting = mla.interval_nesting()
for result in nesting:
    print(f"Signal from {result['origin_level']}: "
          f"confidence={result['confidence']:.0%}")
```

### Level Resonance (级别共振)

When multiple timeframes simultaneously show buy/sell signals, the resulting move is much more powerful.

```python
resonance = mla.level_resonance()
for event in resonance:
    print(f"{event['type']}: {event['description']}")
```

---

## Trading Strategies

### Hub Oscillation Trading (中枢震荡, Lesson 33)

Buy at bottom divergence of each downward departure from hub; sell at top divergence of each upward departure.

```python
# These are automatically generated in analyzer.trade_signals
for ts in analyzer.trade_signals:
    if '中枢震荡' in ts.reason:
        print(f"{ts.action.name} @ {ts.dt} price={ts.price:.2f}")
```

### Mechanical Trading (同级别分解, Lesson 38)

Fully mechanical: buy at down-divergence, sell at up-divergence, hold if no divergence in up-move.

```python
for ts in analyzer.trade_signals:
    if '机械' in ts.reason:
        print(f"{ts.action.name} @ {ts.dt} reason={ts.reason}")
```

### Three-Phase Model (Lesson 108)

```python
phase = analyzer.phase_info
print(f"Phase: {phase['phase']}")
print(f"Action: {phase['action']}")
print(f"Description: {phase['description']}")
```

---

## Theory Summary

### Core Axioms (from Lesson 17)

1. **走势必完美** — Every trend must complete. No trend lasts forever.
2. **走势分解** — Any trend decomposes into: consolidation + down + up.
3. **递归结构** — Any trend type consists of at least 3 sub-level trend types.

### Key Theorems

- **Divergence-Turning Theorem** (Lesson 29): Every divergence creates a buy/sell point at some level.
- **Trend Completeness** (Lesson 17): Once a trend type is confirmed, it must eventually transform.
- **Hub Formation** (Lesson 20): After any 3rd-type buy/sell point, a new hub must form.

### Post-Divergence Classification (Lesson 29)

After divergence in pattern `a + A + b + B + c`:
1. **Level expansion** (weakest): Rebound stays below ZD of last hub
2. **Consolidation**: Rebound re-enters last hub zone [ZD, ZG]
3. **Reverse trend** (strongest): Breaks through last hub entirely

### The Golden Rule

> "没有趋势，没有背驰" — No trend, no divergence.
>
> Divergence ONLY applies to trends (2+ hubs), NOT consolidations (1 hub).

---

## FAQ

**Q: Can I use this without tushare?**
A: Yes. Use `TushareDataSource.from_csv()` or `TushareDataSource.from_dataframe()` or manually create `RawKLine` objects from any data source.

**Q: What timeframe should I analyze?**
A: For A-share daily trading, the typical hierarchy is:
- 30min → daily → weekly
- For more precision: 5min → 30min → daily

**Q: Why does the analyzer find few signals in my data?**
A: Chan Theory requires sufficient data to form meaningful structures. Use at least 100+ K-lines for daily data, or 200+ for reliable results.

**Q: How do I get the most reliable signals?**
A: Use multi-level analysis. Signals confirmed at multiple levels (interval nesting) have the highest confidence.

**Q: What's the difference between `signals` and `trade_signals`?**
A: `signals` are raw Chan Theory buy/sell points (B1/B2/B3/S1/S2/S3). `trade_signals` are concrete trading recommendations generated by the strategy modules (with action, confidence, position sizing).
