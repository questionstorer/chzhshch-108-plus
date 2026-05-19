"""
Bi/Stroke construction (笔的构建).
Based on Lessons 62, 65, 77 of 缠中说禅.

A Bi connects two adjacent fractals:
    - Ascending Bi: Bottom Fractal → Top Fractal
    - Descending Bi: Top Fractal → Bottom Fractal

Rules clarified by Lessons 65/77:
    - The two endpoint fractals must be opposite types.
    - There must be at least one processed K-line that belongs to neither
        endpoint fractal.
    - When consecutive same-type fractals occur, use the structurally effective
        one as the stroke endpoint.
"""

from __future__ import annotations

from .data_types import Bi, Direction, Fractal, FractalType, KLine


def construct_bis(fractals: list[Fractal], klines: list[KLine]) -> list[Bi]:
    """
    Construct all valid Bi (strokes) from the normalized fractal sequence.

    Lessons 65 and 77 make the pairing rule stricter than simply connecting
    every adjacent alternating fractal. The implementation keeps a running
    anchor fractal and only emits a Bi when the opposite fractal forms a valid
    stroke with strict minimum separation.
    """
    if len(fractals) < 2:
        return []

    bis: list[Bi] = []
    anchor = fractals[0]

    for candidate in fractals[1:]:
        if candidate.type == anchor.type:
            if _is_more_extreme(candidate, anchor):
                anchor = candidate
            continue

        if not _can_form_bi(anchor, candidate):
            anchor = candidate
            continue

        direction = _bi_direction(anchor, candidate)
        start_idx = anchor.k2.index
        end_idx = candidate.k2.index
        bi_klines = [k for k in klines if start_idx <= k.index <= end_idx]

        bi = Bi(
            index=len(bis),
            direction=direction,
            start=anchor,
            end=candidate,
            klines=bi_klines,
        )
        bis.append(bi)
        anchor = candidate

    # Re-index
    for i, b in enumerate(bis):
        b.index = i

    return bis


def _bi_direction(start: Fractal, end: Fractal) -> Direction:
    if start.type == FractalType.BOTTOM and end.type == FractalType.TOP:
        return Direction.UP
    return Direction.DOWN


def _can_form_bi(start: Fractal, end: Fractal) -> bool:
    if start.type == end.type:
        return False

    if end.k2.index - start.k2.index < 4:
        return False

    if start.type == FractalType.TOP:
        return start.value > end.value

    return end.value > start.value


def _is_more_extreme(current: Fractal, previous: Fractal) -> bool:
    if current.type != previous.type:
        return False

    if current.type == FractalType.TOP:
        return current.value > previous.value

    return current.value < previous.value
