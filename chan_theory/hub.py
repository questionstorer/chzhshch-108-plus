"""
Central Hub detection (中枢识别).
Based on Lessons 17, 20, 24 of 缠中说禅.

Definition (Lesson 17):
  The overlapping part of at least 3 consecutive sub-level trend types.

Hub zone formula (Lesson 20):
  For 3 consecutive sub-level movements with highs/lows:
  ZG = min(g1, g2) = top of overlap zone
  ZD = max(d1, d2) = bottom of overlap zone
  GG = max(all highs)
  DD = min(all lows)

Hub extension (Lesson 20):
  A hub extends when the next segment's range overlaps with [ZD, ZG].
  If the overlap zone with a new segment forms a NEW hub at a higher level.

Types (Lesson 17):
  - Trend (趋势): 2+ hubs in same direction, non-overlapping
  - Consolidation (盘整): exactly 1 hub
"""

from __future__ import annotations

from .data_types import Bi, Direction, Hub, Segment


def detect_hubs_from_bis(bis: list[Bi]) -> list[Hub]:
    """
    Detect central hubs from Bi (stroke) sequences.
    This is for sub-minimum level analysis where
    a hub = at least 3 consecutive Bi with overlapping ranges.
    """
    if len(bis) < 3:
        return []

    hubs: list[Hub] = []
    i = 0

    while i < len(bis) - 2:
        b1, b2, b3 = bis[i], bis[i + 1], bis[i + 2]

        # Check overlap of first three Bi
        overlap_top = min(b1.high, b2.high, b3.high)
        overlap_bottom = max(b1.low, b2.low, b3.low)

        if overlap_top > overlap_bottom:
            # Valid hub found
            # ZG = min(g1, g2) from the defining segments
            # ZD = max(d1, d2) from the defining segments
            ZG = min(b1.high, b3.high)
            ZD = max(b1.low, b3.low)

            if ZG <= ZD:
                # Use the broader overlap
                ZG = overlap_top
                ZD = overlap_bottom

            hub_elements = [b1, b2, b3]
            GG = max(b.high for b in hub_elements)
            DD = min(b.low for b in hub_elements)

            # Try to extend the hub with subsequent Bi
            j = i + 3
            while j < len(bis):
                next_bi = bis[j]
                # Extension: next Bi's range overlaps with [ZD, ZG]
                if next_bi.high >= ZD and next_bi.low <= ZG:
                    hub_elements.append(next_bi)
                    GG = max(GG, next_bi.high)
                    DD = min(DD, next_bi.low)
                    j += 1
                else:
                    break

            hub = Hub(
                index=len(hubs),
                elements=hub_elements,
                ZG=ZG,
                ZD=ZD,
                GG=GG,
                DD=DD,
            )
            hubs.append(hub)

            # Move past this hub
            i = j
        else:
            i += 1

    return hubs


def detect_hubs_from_segments(segments: list[Segment]) -> list[Hub]:
    """
    Detect central hubs from Segment sequences.
    This is for higher-level analysis.
    """
    if len(segments) < 3:
        return []

    hubs: list[Hub] = []
    i = 0

    while i < len(segments) - 2:
        s1, s2, s3 = segments[i], segments[i + 1], segments[i + 2]

        overlap_top = min(s1.high, s2.high, s3.high)
        overlap_bottom = max(s1.low, s2.low, s3.low)

        if overlap_top > overlap_bottom:
            ZG = min(s1.high, s3.high)
            ZD = max(s1.low, s3.low)

            if ZG <= ZD:
                ZG = overlap_top
                ZD = overlap_bottom

            hub_elements = [s1, s2, s3]
            GG = max(s.high for s in hub_elements)
            DD = min(s.low for s in hub_elements)

            # Extend
            j = i + 3
            while j < len(segments):
                next_seg = segments[j]
                if next_seg.high >= ZD and next_seg.low <= ZG:
                    hub_elements.append(next_seg)
                    GG = max(GG, next_seg.high)
                    DD = min(DD, next_seg.low)
                    j += 1
                else:
                    break

            hub = Hub(
                index=len(hubs),
                elements=hub_elements,
                ZG=ZG,
                ZD=ZD,
                GG=GG,
                DD=DD,
            )
            hubs.append(hub)
            i = j
        else:
            i += 1

    return hubs


def classify_trend(hubs: list[Hub]) -> str:
    """
    Classify the overall trend type based on hub structure (Lesson 17).

    - 0 hubs: incomplete / too little data
    - 1 hub: 盘整 (consolidation)
    - 2+ same-direction hubs: 趋势 (trend) - up or down
    """
    if len(hubs) == 0:
        return "insufficient_data"

    if len(hubs) == 1:
        return "consolidation"  # 盘整

    # Check if hubs are in same direction (non-overlapping, progressing)
    ascending = all(
        hubs[i + 1].ZD > hubs[i].ZG for i in range(len(hubs) - 1)
    )
    descending = all(
        hubs[i + 1].ZG < hubs[i].ZD for i in range(len(hubs) - 1)
    )

    if ascending:
        return "uptrend"   # 上涨趋势
    elif descending:
        return "downtrend"  # 下跌趋势
    else:
        return "consolidation"  # 盘整 with overlapping hubs
