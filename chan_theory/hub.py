"""
Central Hub detection (中枢识别).
Based on Lessons 17, 20, 24, 25, 33, 36, 70 of 缠中说禅.

Definition (Lesson 17):
  The overlapping part of at least 3 consecutive sub-level trend types.

Hub zone formula (Lesson 20):
  For 3 consecutive sub-level movements with highs/lows:
  ZG = min(g1, g2) = top of overlap zone
  ZD = max(d1, d2) = bottom of overlap zone
  GG = max(all highs)
  DD = min(all lows)

Hub extension (Lesson 25):
  A hub extends when the next element's range overlaps with [ZD, ZG].
  When extension reaches 6+ elements → level upgrade.

Hub expansion (Lesson 36):
  Two adjacent same-level hubs with overlapping ranges merge into a
  higher-level hub.

Hub generation (Lesson 70):
  After a third-type buy/sell point, a new hub must eventually form.

Hub migration (Lesson 70):
  Sequence of hubs moving in one direction. Track centers for trend strength.

Types (Lesson 17):
  - Trend (趋势): 2+ hubs in same direction, non-overlapping
  - Consolidation (盘整): exactly 1 hub
"""

from __future__ import annotations

from .data_types import Bi, Direction, Hub, Segment, TrendType


def detect_hubs_from_bis(bis: list[Bi]) -> list[Hub]:
    """
    Detect central hubs from Bi (stroke) sequences.
    This is for sub-minimum level analysis where
    a hub = at least 3 consecutive Bi with overlapping ranges.

    Also detects hub extensions (Lesson 25).
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
            ZG = min(b1.high, b3.high)
            ZD = max(b1.low, b3.low)

            if ZG <= ZD:
                ZG = overlap_top
                ZD = overlap_bottom

            hub_elements = [b1, b2, b3]
            GG = max(b.high for b in hub_elements)
            DD = min(b.low for b in hub_elements)
            extension_count = 0

            # Try to extend the hub with subsequent Bi
            j = i + 3
            while j < len(bis):
                next_bi = bis[j]
                # Extension: next Bi's range overlaps with [ZD, ZG]
                if next_bi.high >= ZD and next_bi.low <= ZG:
                    hub_elements.append(next_bi)
                    GG = max(GG, next_bi.high)
                    DD = min(DD, next_bi.low)
                    extension_count += 1
                    j += 1
                else:
                    break

            # Hub extension detection (Lesson 25):
            # 6+ elements → could upgrade level
            is_extended = extension_count > 0
            level = 0
            if len(hub_elements) >= 9:
                level = 1  # Level upgrade when 9+ elements (Lesson 25)

            hub = Hub(
                index=len(hubs),
                elements=hub_elements,
                ZG=ZG,
                ZD=ZD,
                GG=GG,
                DD=DD,
                level=level,
                is_extended=is_extended,
                extension_count=extension_count,
            )
            hubs.append(hub)

            # Move past this hub
            i = j
        else:
            i += 1

    # Check for hub expansion (Lesson 36)
    hubs = _check_hub_expansion(hubs)

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
            extension_count = 0

            # Extend
            j = i + 3
            while j < len(segments):
                next_seg = segments[j]
                if next_seg.high >= ZD and next_seg.low <= ZG:
                    hub_elements.append(next_seg)
                    GG = max(GG, next_seg.high)
                    DD = min(DD, next_seg.low)
                    extension_count += 1
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
                level=1,
                is_extended=extension_count > 0,
                extension_count=extension_count,
            )
            hubs.append(hub)
            i = j
        else:
            i += 1

    hubs = _check_hub_expansion(hubs)
    return hubs


def _check_hub_expansion(hubs: list[Hub]) -> list[Hub]:
    """
    Check for hub expansion into a higher-level hub (Lesson 20 Theorem 2).

    Per 缠中说禅走势中枢中心定理二, two adjacent same-level hubs form a
    higher-level hub when their core zones [ZD, ZG] are NOT trend-separated
    but their outer oscillation ranges [DD, GG] DO overlap:
      - 后ZG < 前ZD 且 后GG >= 前DD  (curr core below prev core, outers overlap)
      - 后ZD > 前ZG 且 后DD <= 前GG  (curr core above prev core, outers overlap)
    Core-zone overlap by itself means the hub is extending, NOT expanding.
    """
    if len(hubs) < 2:
        return hubs

    result: list[Hub] = [hubs[0]]

    for i in range(1, len(hubs)):
        prev = result[-1]
        curr = hubs[i]

        # Theorem 2 conditions for higher-level hub formation
        cores_above = curr.ZD > prev.ZG   # curr core entirely above prev core
        cores_below = curr.ZG < prev.ZD   # curr core entirely below prev core

        if cores_above:
            # Trend would require curr.DD > prev.GG; otherwise higher-level hub
            should_expand = curr.DD <= prev.GG
        elif cores_below:
            # Trend would require curr.GG < prev.DD; otherwise higher-level hub
            should_expand = curr.GG >= prev.DD
        else:
            # Cores overlap — this is a hub extension, not expansion
            should_expand = False

        if should_expand:
            # Merge into higher-level hub.
            # New core zone = overlap of the two outer envelopes.
            merged_elements = prev.elements + curr.elements
            new_ZG = min(prev.GG, curr.GG)
            new_ZD = max(prev.DD, curr.DD)
            if new_ZG <= new_ZD:
                # Safety fallback: use union of core zones
                new_ZG = max(prev.ZG, curr.ZG)
                new_ZD = min(prev.ZD, curr.ZD)
            merged = Hub(
                index=prev.index,
                elements=merged_elements,
                ZG=new_ZG,
                ZD=new_ZD,
                GG=max(prev.GG, curr.GG),
                DD=min(prev.DD, curr.DD),
                level=max(prev.level, curr.level) + 1,
                is_extended=True,
                extension_count=prev.extension_count + curr.extension_count + 1,
            )
            result[-1] = merged
        else:
            result.append(curr)

    # Re-index
    for i, h in enumerate(result):
        h.index = i

    return result


def detect_hub_migration(hubs: list[Hub]) -> list[dict]:
    """
    Detect hub migration pattern (Lesson 70: 中枢移动).

    Track hub centers to determine if hubs are migrating
    in one direction, indicating strong trend.

    Returns list of migration events with direction and strength.
    """
    if len(hubs) < 2:
        return []

    migrations = []
    for i in range(1, len(hubs)):
        prev = hubs[i - 1]
        curr = hubs[i]

        center_diff = curr.center - prev.center
        if center_diff > 0:
            direction = Direction.UP
        elif center_diff < 0:
            direction = Direction.DOWN
        else:
            continue

        migrations.append({
            "from_hub": prev.index,
            "to_hub": curr.index,
            "direction": direction,
            "center_shift": abs(center_diff),
            "non_overlapping": not prev.overlaps(curr),
        })

    return migrations


def classify_trend(hubs: list[Hub]) -> TrendType:
    """
    Classify the overall trend type based on hub structure (Lesson 17).

    - 0 hubs: incomplete / too little data
    - 1 hub: 盘整 (consolidation)
    - 2+ same-direction non-overlapping hubs: 趋势 (trend) - up or down
    """
    if len(hubs) == 0:
        return TrendType.UNKNOWN

    if len(hubs) == 1:
        return TrendType.CONSOLIDATION

    # Check if hubs are in same direction, using Lesson 20 Theorem 2:
    # Uptrend continuation: 后DD > 前GG
    # Downtrend continuation: 后GG < 前DD
    ascending = all(
        hubs[i + 1].DD > hubs[i].GG for i in range(len(hubs) - 1)
    )
    descending = all(
        hubs[i + 1].GG < hubs[i].DD for i in range(len(hubs) - 1)
    )

    if ascending:
        return TrendType.UPTREND
    elif descending:
        return TrendType.DOWNTREND
    else:
        return TrendType.CONSOLIDATION
