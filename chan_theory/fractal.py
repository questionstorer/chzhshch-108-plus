"""
Fractal detection (分型识别).
Based on Lessons 62, 77, 82 of 缠中说禅.

Top Fractal (顶分型): k2.high = max(k1.high, k2.high, k3.high)
                                            AND k2.low = max(k1.low, k2.low, k3.low)

Bottom Fractal (底分型): k2.low = min(k1.low, k2.low, k3.low)
                                                 AND k2.high = min(k1.high, k2.high, k3.high)

Lesson 77 further clarifies that adjacent valid fractals must satisfy
combination law (结合律): they cannot share K-lines.

Fractal Strength (Lesson 82):
    Analyze K-line patterns within fractal to judge reversal vs continuation.
    Strong fractal = likely reversal; Weak fractal = likely continuation.
"""

from __future__ import annotations

from .data_types import Fractal, FractalStrength, FractalType, KLine


def detect_fractals(klines: list[KLine]) -> list[Fractal]:
    """
    Detect and normalize top/bottom fractals from processed K-lines.

    Rules:
    1. Three consecutive processed K-lines form a local fractal candidate.
    2. Adjacent valid fractals cannot share K-lines (Lesson 77).
    3. Consecutive same-type fractals are normalized by keeping the later one
       only when it extends the same extreme; otherwise both are retained for
       later stroke construction.
    """
    if len(klines) < 3:
        return []

    fractals: list[Fractal] = []

    for i in range(1, len(klines) - 1):
        k1, k2, k3 = klines[i - 1], klines[i], klines[i + 1]
        fractal_type = _detect_local_fractal(k1, k2, k3)
        if fractal_type is None:
            continue

        candidate = Fractal(
            type=fractal_type,
            k1=k1,
            k2=k2,
            k3=k3,
            index=len(fractals),
        )
        _append_normalized_fractal(fractals, candidate)

    # Re-index
    for i, f in enumerate(fractals):
        f.index = i

    return fractals


def _detect_local_fractal(
    k1: KLine,
    k2: KLine,
    k3: KLine,
) -> FractalType | None:
    """Return the local fractal type for three processed K-lines."""
    if (k2.high >= k1.high and k2.high >= k3.high and
            k2.low >= k1.low and k2.low >= k3.low):
        return FractalType.TOP

    if (k2.low <= k1.low and k2.low <= k3.low and
            k2.high <= k1.high and k2.high <= k3.high):
        return FractalType.BOTTOM

    return None


def _append_normalized_fractal(
    fractals: list[Fractal],
    candidate: Fractal,
) -> None:
    """
    Normalize a local fractal candidate into the running fractal sequence.

    The cleanup mirrors Lessons 77/65 at the fractal level:
    - adjacent valid fractals cannot share K-lines;
    - a later higher top replaces an earlier lower top;
    - a later lower bottom replaces an earlier higher bottom.
    """
    if not fractals:
        fractals.append(candidate)
        return

    prev = fractals[-1]

    if _shares_kline(prev, candidate):
        if candidate.type == prev.type:
            if _is_more_extreme(candidate, prev):
                fractals[-1] = candidate
        else:
            fractals[-1] = candidate
        return

    if candidate.type == prev.type and _is_more_extreme(candidate, prev):
        fractals[-1] = candidate
        return

    fractals.append(candidate)


def _shares_kline(left: Fractal, right: Fractal) -> bool:
    """Adjacent valid fractals must not reuse any processed K-line."""
    return right.k1.index <= left.k3.index


def _is_more_extreme(current: Fractal, previous: Fractal) -> bool:
    """Check whether a same-type fractal extends the relevant extreme."""
    if current.type != previous.type:
        return False

    if current.type == FractalType.TOP:
        return current.value > previous.value

    return current.value < previous.value


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
