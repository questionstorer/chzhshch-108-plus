"""
K-line preprocessing: Inclusion handling (包含处理).
Based on Lesson 62 of 缠中说禅.

When two adjacent K-lines have an inclusion relationship (one contains the other),
they must be merged before fractal detection:
  - Inclusion: (k1.high >= k2.high AND k1.low <= k2.low) or vice versa
  - In an upward context: take max(high), max(low)
  - In a downward context: take min(high), min(low)
"""

from __future__ import annotations

from .data_types import KLine, RawKLine


def _has_inclusion(k1: KLine, k2: KLine) -> bool:
    """Check if two K-lines have an inclusion relationship."""
    return (k1.high >= k2.high and k1.low <= k2.low) or \
           (k2.high >= k1.high and k2.low <= k1.low)


def _merge_klines(k1: KLine, k2: KLine, direction_up: bool) -> KLine:
    """
    Merge two K-lines with inclusion relationship.
    direction_up=True:  take max(high), max(low) - upward context
    direction_up=False: take min(high), min(low) - downward context
    """
    if direction_up:
        new_high = max(k1.high, k2.high)
        new_low = max(k1.low, k2.low)
    else:
        new_high = min(k1.high, k2.high)
        new_low = min(k1.low, k2.low)

    merged = KLine(
        index=k1.index,
        dt=k2.dt,
        high=new_high,
        low=new_low,
        elements=k1.elements + k2.elements,
    )
    return merged


def process_inclusion(raw_klines: list[RawKLine]) -> list[KLine]:
    """
    Process raw K-lines by handling inclusion relationships.

    Returns a list of processed KLines with inclusions merged.
    """
    if len(raw_klines) < 2:
        return [
            KLine(index=k.index, dt=k.dt, high=k.high, low=k.low, elements=[k])
            for k in raw_klines
        ]

    result: list[KLine] = []

    # Initialize first K-line
    first = raw_klines[0]
    result.append(KLine(index=first.index, dt=first.dt,
                        high=first.high, low=first.low, elements=[first]))

    for i in range(1, len(raw_klines)):
        raw = raw_klines[i]
        current = KLine(index=raw.index, dt=raw.dt,
                        high=raw.high, low=raw.low, elements=[raw])

        prev = result[-1]

        if _has_inclusion(prev, current):
            # Determine direction context from the two most recent non-included K-lines
            if len(result) >= 2:
                direction_up = result[-2].high < prev.high
            else:
                direction_up = prev.high < current.high

            merged = _merge_klines(prev, current, direction_up)
            result[-1] = merged
        else:
            current.index = len(result)
            result.append(current)

    # Re-index
    for i, k in enumerate(result):
        k.index = i

    return result
