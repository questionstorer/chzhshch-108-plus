"""
Bi/Stroke construction (笔的构建).
Based on Lesson 62 of 缠中说禅.

A Bi connects two adjacent fractals:
  - Ascending Bi: Bottom Fractal → Top Fractal
  - Descending Bi: Top Fractal → Bottom Fractal

Rules:
  - At least 1 independent K-line must exist between the two fractals
    (the K-lines shared by the two fractals don't count)
  - Only adjacent fractals form valid Bi
"""

from __future__ import annotations

from .data_types import Bi, Direction, Fractal, FractalType, KLine


def construct_bis(fractals: list[Fractal], klines: list[KLine]) -> list[Bi]:
    """
    Construct all valid Bi (strokes) from the fractal sequence.

    Each Bi connects two adjacent alternating fractals with at least
    one K-line gap between the fractal K-line groups.
    """
    if len(fractals) < 2:
        return []

    bis: list[Bi] = []

    for i in range(len(fractals) - 1):
        f_start = fractals[i]
        f_end = fractals[i + 1]

        # Determine direction
        if f_start.type == FractalType.BOTTOM and f_end.type == FractalType.TOP:
            direction = Direction.UP
        elif f_start.type == FractalType.TOP and f_end.type == FractalType.BOTTOM:
            direction = Direction.DOWN
        else:
            continue  # Should not happen after alternation enforcement

        # Validate: need at least 1 independent K-line between fractals
        # The fractals share the middle K-line (k2), so we need
        # f_end.k1.index > f_start.k3.index OR at minimum
        # f_end.k2.index - f_start.k2.index >= 4 (strict) or >= 3 (relaxed)
        # We use the relaxed standard: at least 1 K-line between k2 of both
        gap = f_end.k2.index - f_start.k2.index
        if gap < 3:
            continue  # Not enough K-lines for a valid Bi

        # Collect the K-lines that belong to this Bi
        start_idx = f_start.k2.index
        end_idx = f_end.k2.index
        bi_klines = [k for k in klines if start_idx <= k.index <= end_idx]

        bi = Bi(
            index=len(bis),
            direction=direction,
            start=f_start,
            end=f_end,
            klines=bi_klines,
        )
        bis.append(bi)

    # Validate Bi sequence - ensure proper structure
    bis = _validate_bi_sequence(bis)

    # Re-index
    for i, b in enumerate(bis):
        b.index = i

    return bis


def _validate_bi_sequence(bis: list[Bi]) -> list[Bi]:
    """
    Validate and clean Bi sequence:
    - Adjacent Bi must alternate direction (UP, DOWN, UP, DOWN...)
    - When conflicts arise, keep the more significant stroke
    """
    if len(bis) < 2:
        return bis

    result: list[Bi] = [bis[0]]

    for bi in bis[1:]:
        prev = result[-1]

        if bi.direction == prev.direction:
            # Same direction: keep the one with larger range
            if bi.change > prev.change:
                result[-1] = bi
        else:
            result.append(bi)

    return result
