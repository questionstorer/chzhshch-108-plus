"""
Auxiliary technical indicators for Chan Theory analysis.
Based on Lessons 15, 25, 77, 90 of 缠中说禅.

Includes:
  - Bollinger Bands (布林通道) per Lesson 90
  - MA Kiss Classification (均线吻分类) per Lesson 15
  - Gap Detection & Classification (缺口分类) per Lesson 77
  - Moving Averages
"""

from __future__ import annotations

from .data_types import Direction, Gap, GapType, MAKissType
from .divergence import compute_ema


# ── Moving Averages ──────────────────────────────────────────────────


def compute_sma(data: list[float], period: int) -> list[float]:
    """Compute Simple Moving Average."""
    if len(data) < period:
        return [sum(data[:i+1]) / (i+1) for i in range(len(data))]

    result = []
    for i in range(len(data)):
        if i < period - 1:
            result.append(sum(data[:i+1]) / (i+1))
        else:
            result.append(sum(data[i-period+1:i+1]) / period)
    return result


# ── Bollinger Bands (Lesson 90) ──────────────────────────────────────


def compute_bollinger_bands(
    closes: list[float],
    period: int = 20,
    num_std: float = 2.0,
) -> tuple[list[float], list[float], list[float]]:
    """
    Compute Bollinger Bands (布林通道) per Lesson 90.

    When BOLL channel contracts, signals end of hub consolidation (中阴阶段).
    First/second type buy/sell points often form at upper/lower rails.

    Returns: (upper, middle, lower) bands
    """
    middle = compute_sma(closes, period)
    upper = []
    lower = []

    for i in range(len(closes)):
        if i < period - 1:
            window = closes[:i+1]
        else:
            window = closes[i-period+1:i+1]

        mean = middle[i]
        variance = sum((x - mean) ** 2 for x in window) / len(window)
        std = variance ** 0.5

        upper.append(mean + num_std * std)
        lower.append(mean - num_std * std)

    return upper, middle, lower


def detect_boll_contraction(
    upper: list[float],
    lower: list[float],
    window: int = 10,
    threshold: float = 0.5,
) -> list[dict]:
    """
    Detect Bollinger Band contraction phases (中阴阶段 per Lesson 90).

    A contraction occurs when the bandwidth narrows significantly,
    signaling end of hub consolidation and impending breakout.
    """
    events = []
    if len(upper) < window + 1:
        return events

    for i in range(window, len(upper)):
        curr_width = upper[i] - lower[i]
        prev_width = upper[i - window] - lower[i - window]

        if prev_width == 0:
            continue

        ratio = curr_width / prev_width
        if ratio < threshold:
            events.append({
                "index": i,
                "curr_width": curr_width,
                "prev_width": prev_width,
                "contraction_ratio": ratio,
            })

    return events


# ── MA Kiss Classification (Lesson 15) ──────────────────────────────


def classify_ma_kisses(
    closes: list[float],
    short_period: int = 5,
    long_period: int = 20,
) -> list[dict]:
    """
    Classify MA "kisses" (均线吻) per Lesson 15.

    Three types:
      飞吻 (fly kiss): MAs barely approach, no actual cross.
      唇吻 (lip kiss): MAs touch briefly, 1-2 bar crossing.
      湿吻 (wet kiss): MAs intertwine for multiple bars.
        All major reversals start from 湿吻.
    """
    if len(closes) < long_period:
        return []

    short_ma = compute_ema(closes, short_period)
    long_ma = compute_ema(closes, long_period)

    kisses = []
    diff = [s - l for s, l in zip(short_ma, long_ma)]

    i = long_period
    while i < len(diff) - 1:
        # Detect cross (sign change)
        if diff[i] * diff[i - 1] < 0:
            cross_start = i

            # Count how many bars the MAs stay close
            intertwine_count = 0
            j = i
            threshold = abs(long_ma[i]) * 0.005  # 0.5% of price
            while j < len(diff) and abs(diff[j]) < threshold:
                intertwine_count += 1
                j += 1

            if intertwine_count >= 5:
                kiss_type = MAKissType.WET_KISS
            elif intertwine_count >= 2:
                kiss_type = MAKissType.LIP_KISS
            else:
                kiss_type = MAKissType.FLY_KISS

            kisses.append({
                "type": kiss_type,
                "index": cross_start,
                "duration": max(intertwine_count, 1),
                "short_ma": short_ma[cross_start],
                "long_ma": long_ma[cross_start],
            })

            i = max(j, i + 1)
        else:
            i += 1

    return kisses


# ── Gap Detection (Lesson 77) ────────────────────────────────────────


def detect_gaps(
    highs: list[float],
    lows: list[float],
    closes: list[float],
    min_gap_pct: float = 0.005,
) -> list[Gap]:
    """
    Detect price gaps (缺口) per Lesson 77.

    Gap types:
      突破缺口 (breakthrough): rarely filled, marks trend start
      中继缺口 (continuation): ~50% filled, mid-trend
      竭尽缺口 (exhaustion): filled + no new extreme = reversal
      普通缺口 (ordinary): hub oscillation gaps

    Classification is done post-hoc based on subsequent price action.
    Initially all gaps are classified as ORDINARY and upgraded later.
    """
    gaps: list[Gap] = []

    for i in range(1, len(highs)):
        # Up gap: today's low > yesterday's high
        if lows[i] > highs[i - 1]:
            gap_size = lows[i] - highs[i - 1]
            if gap_size / highs[i - 1] >= min_gap_pct:
                gaps.append(Gap(
                    gap_type=GapType.ORDINARY,
                    dt=str(i),
                    high=lows[i],
                    low=highs[i - 1],
                    direction=Direction.UP,
                ))

        # Down gap: today's high < yesterday's low
        elif highs[i] < lows[i - 1]:
            gap_size = lows[i - 1] - highs[i]
            if gap_size / lows[i - 1] >= min_gap_pct:
                gaps.append(Gap(
                    gap_type=GapType.ORDINARY,
                    dt=str(i),
                    high=lows[i - 1],
                    low=highs[i],
                    direction=Direction.DOWN,
                ))

    # Classify gaps based on subsequent price action
    gaps = _classify_gaps(gaps, highs, lows, closes)

    return gaps


def _classify_gaps(
    gaps: list[Gap],
    highs: list[float],
    lows: list[float],
    closes: list[float],
    lookback: int = 20,
) -> list[Gap]:
    """Classify gaps post-hoc based on subsequent price action."""
    for gap in gaps:
        idx = int(gap.dt)
        end_idx = min(idx + lookback, len(closes))

        # Check if gap is filled
        if gap.direction == Direction.UP:
            filled = any(lows[j] <= gap.low for j in range(idx + 1, end_idx))
        else:
            filled = any(highs[j] >= gap.high for j in range(idx + 1, end_idx))

        gap.is_filled = filled

        if not filled:
            # Unfilled gap = likely breakthrough
            gap.gap_type = GapType.BREAKTHROUGH
        elif filled:
            # Check if price made new extreme after fill
            if gap.direction == Direction.UP:
                new_high = max(highs[idx:end_idx]) > highs[idx]
                if not new_high:
                    gap.gap_type = GapType.EXHAUSTION
                else:
                    gap.gap_type = GapType.CONTINUATION
            else:
                new_low = min(lows[idx:end_idx]) < lows[idx]
                if not new_low:
                    gap.gap_type = GapType.EXHAUSTION
                else:
                    gap.gap_type = GapType.CONTINUATION

    return gaps
