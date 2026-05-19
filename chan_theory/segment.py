"""
Segment construction (线段构建).
Based on Lessons 62, 65, 67, 71, 77, 78 of 缠中说禅.

A segment is composed of at least 3 consecutive Bi (strokes).
A segment is terminated when a sub-level structure breaks its direction:
  - An UP segment ends when a descending Bi's low breaks below the
    previous ascending Bi's low
  - A DOWN segment ends when an ascending Bi's high breaks above the
    previous descending Bi's high

Segment = 线段 = a movement with no internal hub structure (Lesson 65).

Termination Cases (Lessons 65, 67, 71, 77):
  Case 1 (第一种情况): Characteristic sequence gap filled → segment broken.
  Case 2 (第二种情况): Gap not filled but the next same-direction
    characteristic element itself breaks → original segment also broken.

Implementation note:
  The current implementation uses simplified Bi-to-Bi comparisons as a
  practical approximation.  A fully lesson-faithful implementation would
  build a standardized feature sequence with inclusion handling on the
  feature-sequence elements themselves (Lesson 67).
"""

from __future__ import annotations

from .data_types import Bi, Direction, Segment


def construct_segments(bis: list[Bi]) -> list[Segment]:
    """
    Construct segments from a sequence of Bi (strokes).

    Uses a simplified approximation of the characteristic sequence method
    (特征序列) from Lesson 67:
    - For an UP segment, examine descending Bi as the characteristic sequence
    - For a DOWN segment, examine ascending Bi as the characteristic sequence
    - A segment ends when the characteristic sequence forms a fractal
      in the opposite direction

    Note: this does not build a fully standardized feature sequence with
    inclusion handling on the feature-sequence elements.
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

            # Check Case 1 & Case 2 termination
            terminated, case_type = _check_segment_termination(seg_bis, direction)
            if terminated:
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
        if segments and start_idx <= segments[-1].end_bi.index:
            start_idx = segments[-1].end_bi.index + 1

    # Standardize segment endpoints (Lesson 78)
    segments = _standardize_segments(segments)

    return segments


def _check_segment_termination(
    bis: list[Bi], direction: Direction
) -> tuple[bool, int]:
    """
    Check if segment should terminate — implements both Case 1 and Case 2.

    Returns: (should_terminate, case_type)
        case_type: 0=no, 1=Case 1, 2=Case 2

    Case 1 (Lesson 65): The characteristic sequence directly forms a
      top/bottom fractal → segment breaks.
    Case 2 (Lesson 67): Gap in characteristic sequence not filled, but
      the next element going with original direction is itself broken.
    """
    if len(bis) < 5:
        return False, 0

    if direction == Direction.UP:
        # Characteristic sequence = descending Bi
        char_seq = [b for b in bis if b.direction == Direction.DOWN]
        if len(char_seq) < 2:
            return False, 0

        latest = char_seq[-1]
        prev = char_seq[-2]

        # Case 1: Top fractal in characteristic sequence
        # = latest down Bi breaks below previous down Bi
        if latest.low < prev.low and latest.high < prev.high:
            return True, 1

        # Case 2: Gap exists (latest.high < prev.low), but check if
        # the next ascending Bi fails to make new high
        if len(char_seq) >= 3 and latest.high < prev.low:
            # Gap not filled - check if the ascending Bi between them
            # fails to exceed the previous ascending Bi's high
            asc_bis = [b for b in bis if b.direction == Direction.UP]
            if len(asc_bis) >= 2:
                if asc_bis[-1].high < asc_bis[-2].high:
                    return True, 2

    else:  # DOWN segment
        char_seq = [b for b in bis if b.direction == Direction.UP]
        if len(char_seq) < 2:
            return False, 0

        latest = char_seq[-1]
        prev = char_seq[-2]

        # Case 1: Bottom fractal in characteristic sequence
        if latest.high > prev.high and latest.low > prev.low:
            return True, 1

        # Case 2: Gap with failed continuation
        if len(char_seq) >= 3 and latest.low > prev.high:
            desc_bis = [b for b in bis if b.direction == Direction.DOWN]
            if len(desc_bis) >= 2:
                if desc_bis[-1].low > desc_bis[-2].low:
                    return True, 2

    return False, 0


def _standardize_segments(segments: list[Segment]) -> list[Segment]:
    """
    Standardize segment endpoints (Lesson 78).

    When a segment's highest/lowest point isn't at its endpoint,
    adjust so the extreme Bi is used as the effective endpoint.
    This creates a normalized zigzag for hub/trend analysis.
    """
    for seg in segments:
        if not seg.bis:
            continue

        if seg.direction == Direction.UP:
            # Endpoint should be the highest point
            max_bi = max(seg.bis, key=lambda b: b.high)
            if max_bi.high > seg.end_bi.high:
                seg.end_bi = max_bi
            # Start should be the lowest point
            min_bi = min(seg.bis, key=lambda b: b.low)
            if min_bi.low < seg.start_bi.low:
                seg.start_bi = min_bi
        else:
            # Endpoint should be the lowest point
            min_bi = min(seg.bis, key=lambda b: b.low)
            if min_bi.low < seg.end_bi.low:
                seg.end_bi = min_bi
            # Start should be the highest point
            max_bi = max(seg.bis, key=lambda b: b.high)
            if max_bi.high > seg.start_bi.high:
                seg.start_bi = max_bi

    return segments
