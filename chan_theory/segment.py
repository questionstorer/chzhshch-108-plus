"""
Segment construction (线段构建).
Based on Lessons 62, 65, 67 of 缠中说禅.

A segment is composed of at least 3 consecutive Bi (strokes).
A segment is terminated when a sub-level structure breaks its direction:
  - An UP segment ends when a descending Bi's low breaks below the
    previous ascending Bi's low (characteristic sequence method)
  - A DOWN segment ends when an ascending Bi's high breaks above the
    previous descending Bi's high

Segment = 线段 = a movement with no internal hub structure (Lesson 65).
"""

from __future__ import annotations

from .data_types import Bi, Direction, Segment


def construct_segments(bis: list[Bi]) -> list[Segment]:
    """
    Construct segments from a sequence of Bi (strokes).

    Uses the characteristic sequence method (特征序列) from Lesson 67:
    - For an UP segment, examine descending Bi as the characteristic sequence
    - For a DOWN segment, examine ascending Bi as the characteristic sequence
    - A segment ends when the characteristic sequence forms a fractal
      in the opposite direction
    """
    if len(bis) < 3:
        return []

    segments: list[Segment] = []
    start_idx = 0

    while start_idx < len(bis) - 2:
        seg_bis = [bis[start_idx]]
        direction = bis[start_idx].direction
        end_idx = start_idx

        for i in range(start_idx + 1, len(bis)):
            seg_bis.append(bis[i])
            end_idx = i

            # Need at least 3 Bi for a segment
            if len(seg_bis) < 3:
                continue

            # Check if segment should terminate using characteristic sequence
            if _should_terminate_segment(seg_bis, direction):
                # The last Bi that breaks the pattern belongs to next segment
                # But the segment includes the Bi that caused termination
                break

        if len(seg_bis) >= 3:
            # Ensure segment has odd number of Bi (starts and ends same way)
            if len(seg_bis) % 2 == 0:
                seg_bis = seg_bis[:-1]
                end_idx -= 1

            seg = Segment(
                index=len(segments),
                direction=direction,
                start_bi=seg_bis[0],
                end_bi=seg_bis[-1],
                bis=list(seg_bis),
            )
            segments.append(seg)

        start_idx = end_idx
        if start_idx <= (segments[-1].end_bi.index if segments else start_idx):
            start_idx = (segments[-1].end_bi.index if segments else start_idx) + 1

    return segments


def _should_terminate_segment(bis: list[Bi], direction: Direction) -> bool:
    """
    Check if a segment should terminate based on characteristic sequence.

    For UP segment: check if descending Bi form a top fractal
      = current down Bi's high < previous down Bi's high
      AND current down Bi's low < previous down Bi's low
    For DOWN segment: check if ascending Bi form a bottom fractal
      = current up Bi's low > previous up Bi's low
      AND current up Bi's high > previous up Bi's high
    """
    if len(bis) < 5:
        return False

    if direction == Direction.UP:
        # Get the descending Bi (characteristic sequence for UP segment)
        desc_bis = [b for b in bis if b.direction == Direction.DOWN]
        if len(desc_bis) < 2:
            return False

        latest = desc_bis[-1]
        prev = desc_bis[-2]

        # Top fractal in characteristic sequence = segment end
        # The latest down Bi breaks below the previous down Bi
        return latest.low < prev.low and latest.high < prev.high

    else:  # DOWN segment
        # Get the ascending Bi (characteristic sequence for DOWN segment)
        asc_bis = [b for b in bis if b.direction == Direction.UP]
        if len(asc_bis) < 2:
            return False

        latest = asc_bis[-1]
        prev = asc_bis[-2]

        # Bottom fractal in characteristic sequence = segment end
        return latest.high > prev.high and latest.low > prev.low
