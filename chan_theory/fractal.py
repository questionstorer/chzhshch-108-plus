"""
Fractal detection (分型识别).
Based on Lesson 62 of 缠中说禅.

Top Fractal (顶分型): k2.high = max(k1.high, k2.high, k3.high)
                      AND k2.low = max(k1.low, k2.low, k3.low)

Bottom Fractal (底分型): k2.low = min(k1.low, k2.low, k3.low)
                         AND k2.high = min(k1.high, k2.high, k3.high)
"""

from __future__ import annotations

from .data_types import Fractal, FractalType, KLine


def detect_fractals(klines: list[KLine]) -> list[Fractal]:
    """
    Detect all top and bottom fractals from processed K-lines.

    Rules:
    1. Three consecutive K-lines form a potential fractal
    2. Adjacent fractals must alternate (top-bottom-top-bottom...)
    3. When conflict: keep the more extreme one
    """
    if len(klines) < 3:
        return []

    raw_fractals: list[Fractal] = []

    for i in range(1, len(klines) - 1):
        k1, k2, k3 = klines[i - 1], klines[i], klines[i + 1]

        # Top fractal
        if (k2.high >= k1.high and k2.high >= k3.high and
                k2.low >= k1.low and k2.low >= k3.low):
            raw_fractals.append(Fractal(
                type=FractalType.TOP,
                k1=k1, k2=k2, k3=k3,
                index=len(raw_fractals),
            ))

        # Bottom fractal
        elif (k2.low <= k1.low and k2.low <= k3.low and
              k2.high <= k1.high and k2.high <= k3.high):
            raw_fractals.append(Fractal(
                type=FractalType.BOTTOM,
                k1=k1, k2=k2, k3=k3,
                index=len(raw_fractals),
            ))

    # Enforce alternation: top-bottom-top-bottom
    fractals = _enforce_alternation(raw_fractals)

    # Re-index
    for i, f in enumerate(fractals):
        f.index = i

    return fractals


def _enforce_alternation(fractals: list[Fractal]) -> list[Fractal]:
    """
    Ensure fractals strictly alternate between TOP and BOTTOM.
    When two consecutive same-type fractals occur, keep the more extreme one.
    """
    if not fractals:
        return []

    result: list[Fractal] = [fractals[0]]

    for f in fractals[1:]:
        prev = result[-1]

        if f.type == prev.type:
            # Same type: keep the more extreme one
            if f.type == FractalType.TOP:
                if f.value > prev.value:
                    result[-1] = f
            else:  # BOTTOM
                if f.value < prev.value:
                    result[-1] = f
        else:
            # Different type: check validity
            if prev.type == FractalType.TOP and f.type == FractalType.BOTTOM:
                if f.value < prev.value:
                    result.append(f)
            elif prev.type == FractalType.BOTTOM and f.type == FractalType.TOP:
                if f.value > prev.value:
                    result.append(f)

    return result
