"""
Fractal detection (分型识别).
Based on Lessons 62, 82 of 缠中说禅.

Top Fractal (顶分型): k2.high = max(k1.high, k2.high, k3.high)
                      AND k2.low = max(k1.low, k2.low, k3.low)

Bottom Fractal (底分型): k2.low = min(k1.low, k2.low, k3.low)
                         AND k2.high = min(k1.high, k2.high, k3.high)

Fractal Strength (Lesson 82):
  Analyze K-line patterns within fractal to judge reversal vs continuation.
  Strong fractal = likely reversal; Weak fractal = likely continuation.
"""

from __future__ import annotations

from .data_types import Fractal, FractalStrength, FractalType, KLine


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


def analyze_fractal_strength(fractal: Fractal) -> FractalStrength:
    """
    Analyze fractal strength (Lesson 82: 分型力度分析).

    Strong fractal (likely reversal):
      - Top: k3 has long body dropping far below k2's midpoint
      - Bottom: k3 has long body rising far above k2's midpoint

    Weak fractal (likely continuation):
      - Top: k3 barely drops, stays above k2's midpoint
      - Bottom: k3 barely rises, stays below k2's midpoint
    """
    k1, k2, k3 = fractal.k1, fractal.k2, fractal.k3
    k2_range = k2.high - k2.low
    if k2_range == 0:
        return FractalStrength.NORMAL

    k2_mid = k2.mid

    if fractal.type == FractalType.TOP:
        # How far did k3 drop relative to k2?
        drop_ratio = (k2.high - k3.low) / k2_range
        # Did k3 close below k2 midpoint?
        k3_close = k3.low  # approximate with low for processed klines
        if k3.elements:
            k3_close = k3.elements[-1].close

        if drop_ratio > 0.7 and k3_close < k2_mid:
            return FractalStrength.STRONG
        elif drop_ratio < 0.3 and k3_close > k2_mid:
            return FractalStrength.WEAK
        return FractalStrength.NORMAL

    else:  # BOTTOM
        rise_ratio = (k3.high - k2.low) / k2_range
        k3_close = k3.high
        if k3.elements:
            k3_close = k3.elements[-1].close

        if rise_ratio > 0.7 and k3_close > k2_mid:
            return FractalStrength.STRONG
        elif rise_ratio < 0.3 and k3_close < k2_mid:
            return FractalStrength.WEAK
        return FractalStrength.NORMAL
