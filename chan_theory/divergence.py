"""
Divergence detection (背驰) and MACD analysis.
Based on Lessons 15, 25 of 缠中说禅.

Divergence (Lesson 15):
  Two consecutive same-direction trends where the 2nd trend's
  STRENGTH is WEAKER than the 1st.

Strength Measurement:
  - 趋势力度 = area between short MA and long MA between consecutive "kisses"
  - MACD histogram area as auxiliary confirmation

Critical Rule (Lesson 15):
  "没有趋势，没有背驰" = NO TREND, NO DIVERGENCE
  Divergence ONLY applies to trends, NOT consolidations.

MACD Parameters (Lesson 25): 12, 26, 9
"""

from __future__ import annotations

import math


def compute_ema(data: list[float], period: int) -> list[float]:
    """Compute Exponential Moving Average."""
    if not data:
        return []

    multiplier = 2.0 / (period + 1)
    ema = [data[0]]

    for i in range(1, len(data)):
        val = data[i] * multiplier + ema[-1] * (1 - multiplier)
        ema.append(val)

    return ema


def compute_macd(
    closes: list[float],
    fast: int = 12,
    slow: int = 26,
    signal: int = 9,
) -> tuple[list[float], list[float], list[float]]:
    """
    Compute MACD (Moving Average Convergence Divergence).
    Parameters: 12, 26, 9 as specified in Lesson 25.

    Returns: (dif, dea, histogram)
      dif = fast EMA - slow EMA
      dea = signal EMA of dif
      histogram = 2 * (dif - dea)  (the bar/column chart)
    """
    ema_fast = compute_ema(closes, fast)
    ema_slow = compute_ema(closes, slow)

    dif = [f - s for f, s in zip(ema_fast, ema_slow)]
    dea = compute_ema(dif, signal)
    histogram = [2.0 * (d - e) for d, e in zip(dif, dea)]

    return dif, dea, histogram


def compute_macd_area(histogram: list[float], start: int, end: int) -> float:
    """
    Compute the area of MACD histogram between two indices.
    This represents 趋势力度 (trend force) per Lesson 15.
    """
    if start < 0 or end > len(histogram) or start >= end:
        return 0.0

    return sum(abs(h) for h in histogram[start:end])


def detect_divergence(
    highs: list[float],
    lows: list[float],
    closes: list[float],
    bis_ranges: list[tuple[int, int, str]],
) -> list[dict]:
    """
    Detect divergence (背驰) in price-MACD relationship.

    Args:
        highs:  list of high prices
        lows:   list of low prices
        closes: list of close prices
        bis_ranges: list of (start_idx, end_idx, direction) for each Bi

    Returns:
        List of divergence signals with details.

    Per Lesson 15: Compare MACD area of consecutive same-direction movements.
    Divergence = price makes new extreme but MACD area is SMALLER.
    """
    if len(closes) < 26:
        return []

    _, _, histogram = compute_macd(closes)
    divergences = []

    # Group Bi by direction and check consecutive pairs
    for i in range(1, len(bis_ranges)):
        curr_start, curr_end, curr_dir = bis_ranges[i]
        prev_start, prev_end, prev_dir = bis_ranges[i - 1]

        # Find the previous same-direction movement
        j = i - 2
        while j >= 0 and bis_ranges[j][2] != curr_dir:
            j -= 1

        if j < 0:
            continue

        prev_same_start, prev_same_end, _ = bis_ranges[j]

        # Compute MACD areas
        curr_area = compute_macd_area(histogram, curr_start, min(curr_end + 1, len(histogram)))
        prev_area = compute_macd_area(histogram, prev_same_start, min(prev_same_end + 1, len(histogram)))

        if prev_area == 0:
            continue

        # Check divergence conditions
        if curr_dir == "up":
            # Price makes new high but MACD area smaller
            curr_high = max(highs[curr_start:curr_end + 1]) if curr_end < len(highs) else 0
            prev_high = max(highs[prev_same_start:prev_same_end + 1]) if prev_same_end < len(highs) else 0

            if curr_high >= prev_high and curr_area < prev_area:
                divergences.append({
                    "type": "top_divergence",
                    "index": curr_end,
                    "price": curr_high,
                    "curr_area": curr_area,
                    "prev_area": prev_area,
                    "ratio": curr_area / prev_area,
                })

        elif curr_dir == "down":
            # Price makes new low but MACD area smaller
            curr_low = min(lows[curr_start:curr_end + 1]) if curr_end < len(lows) else float('inf')
            prev_low = min(lows[prev_same_start:prev_same_end + 1]) if prev_same_end < len(lows) else float('inf')

            if curr_low <= prev_low and curr_area < prev_area:
                divergences.append({
                    "type": "bottom_divergence",
                    "index": curr_end,
                    "price": curr_low,
                    "curr_area": curr_area,
                    "prev_area": prev_area,
                    "ratio": curr_area / prev_area,
                })

    return divergences


def compute_trend_force(
    closes: list[float],
    short_period: int = 5,
    long_period: int = 10,
    start: int = 0,
    end: int | None = None,
) -> float:
    """
    Compute 趋势力度 (Trend Force) per Lesson 15.
    = Area between short MA and long MA between consecutive "kisses".

    A "kiss" is where the short MA crosses the long MA.
    """
    if end is None:
        end = len(closes)

    segment = closes[start:end]
    if len(segment) < long_period:
        return 0.0

    short_ma = compute_ema(segment, short_period)
    long_ma = compute_ema(segment, long_period)

    return sum(abs(s - l) for s, l in zip(short_ma, long_ma))


def compute_average_trend_force(
    closes: list[float],
    short_period: int = 5,
    long_period: int = 10,
    start: int = 0,
    end: int | None = None,
) -> float:
    """
    Compute 趋势平均力度 per Lesson 15.
    = Trend Force / Time between kisses.
    """
    if end is None:
        end = len(closes)

    duration = end - start
    if duration <= 0:
        return 0.0

    force = compute_trend_force(closes, short_period, long_period, start, end)
    return force / duration
