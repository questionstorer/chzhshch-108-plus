"""
Multi-level analysis (多级别联立) and interval nesting (区间套).
Based on Lessons 37, 52, 53, 60, 81 of 缠中说禅.

区间套 (Interval Nesting, Lesson 37):
  When a higher-level divergence segment is identified, zoom into sub-level
  charts to find the sub-level divergence, then zoom further, forming nested
  intervals that converge to the exact turning point.

多级别联立 (Multi-Level Joint Analysis, Lesson 81):
  Like simultaneous equations — a single level has many possible outcomes,
  but combining multiple levels drastically reduces possibilities.

级别共振 (Level Resonance, Lesson 53):
  When multiple levels simultaneously show buy/sell points, the resulting
  move is much more powerful.
"""

from __future__ import annotations

from typing import Optional

from .data_types import (
    Bi, Direction, Hub, RawKLine, Signal, SignalType, TrendType,
)


class MultiLevelAnalyzer:
    """
    Multi-level Chan Theory analysis engine.

    Manages multiple ChanAnalyzer instances at different timeframe levels
    and coordinates cross-level analysis.

    Typical level mapping for A-share daily analysis:
      Level 0: 1-min  (for precise entry/exit)
      Level 1: 5-min  (sub-segment level)
      Level 2: 30-min (segment level)
      Level 3: daily  (primary analysis level)
      Level 4: weekly (higher-level context)
    """

    def __init__(self) -> None:
        # Lazy import to avoid circular dependency
        from .chan import ChanAnalyzer

        self._analyzers: dict[str, ChanAnalyzer] = {}
        self._level_order: list[str] = []
        self._ChanAnalyzer = ChanAnalyzer

    def add_level(self, name: str, raw_klines: list[RawKLine]) -> None:
        """
        Add a timeframe level for analysis.

        Args:
            name: Level name, e.g. "1min", "5min", "30min", "daily", "weekly"
            raw_klines: K-line data for this level
        """
        analyzer = self._ChanAnalyzer()
        analyzer.load(raw_klines)
        analyzer.analyze()
        self._analyzers[name] = analyzer
        if name not in self._level_order:
            self._level_order.append(name)

    def get_analyzer(self, name: str):
        """Get ChanAnalyzer for a specific level."""
        return self._analyzers.get(name)

    @property
    def levels(self) -> list[str]:
        return list(self._level_order)

    def interval_nesting(
        self,
        levels: Optional[list[str]] = None,
    ) -> list[dict]:
        """
        Perform 区间套 (interval nesting) analysis (Lessons 37, 52, 60).

        Procedure:
          1. At the highest level, identify divergence zones
          2. Zoom to sub-level, find sub-level divergence within that zone
          3. Continue zooming until the smallest level pinpoints the exact
             turning point

        Returns list of nested signal detections with confidence scores.
        """
        if levels is None:
            levels = list(reversed(self._level_order))

        if len(levels) < 2:
            return []

        results = []

        # Start from highest level, find divergence signals
        top_level = levels[0]
        top_analyzer = self._analyzers.get(top_level)
        if not top_analyzer or not top_analyzer.signals:
            return results

        for signal in top_analyzer.signals:
            nested = {
                "origin_level": top_level,
                "origin_signal": signal,
                "nested_confirmations": [],
                "confidence": 0.0,
            }

            # Try to confirm at each sub-level
            confirmed_count = 0
            for sub_level in levels[1:]:
                sub_analyzer = self._analyzers.get(sub_level)
                if not sub_analyzer:
                    continue

                # Find sub-level signals in the same time window
                matching = _find_matching_signals(signal, sub_analyzer.signals)
                if matching:
                    nested["nested_confirmations"].append({
                        "level": sub_level,
                        "signals": matching,
                    })
                    confirmed_count += 1

            # Confidence = fraction of sub-levels that confirm
            total_sub = len(levels) - 1
            nested["confidence"] = confirmed_count / total_sub if total_sub > 0 else 0.0
            results.append(nested)

        return results

    def level_resonance(self, time_window: int = 5) -> list[dict]:
        """
        Detect 级别共振 (level resonance) per Lesson 53.

        When multiple levels simultaneously show first-type buy/sell points,
        the resulting move is much more powerful.

        Only first-class signals (B1/S1) are considered for resonance, and
        signals must fall within ``time_window`` days of each other.

        Returns list of resonance events.
        """
        from datetime import datetime

        events = []

        # Collect all first-class signals from each level
        level_signals: dict[str, list[Signal]] = {}
        for name, analyzer in self._analyzers.items():
            if not analyzer.signals:
                continue
            first_class = [
                s for s in analyzer.signals
                if s.type in (SignalType.BUY_1ST, SignalType.SELL_1ST)
            ]
            if first_class:
                level_signals[name] = first_class

        if len(level_signals) < 2:
            return events

        def _parse_dt(dt_str: str):
            for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%Y%m%d"):
                try:
                    return datetime.strptime(dt_str, fmt)
                except ValueError:
                    continue
            return None

        # Check for alignment of same-type first-class signals across levels.
        # For each pair of levels, check if any B1 (or S1) from one level
        # is time-aligned with a B1 (or S1) from the other level.
        level_names = list(level_signals.keys())

        def _signals_aligned(sigs_a, sigs_b, sig_type):
            """Check if any signal of sig_type in sigs_a aligns with one in sigs_b."""
            for sa in sigs_a:
                if sa.type != sig_type:
                    continue
                sa_dt = _parse_dt(sa.dt)
                for sb in sigs_b:
                    if sb.type != sig_type:
                        continue
                    sb_dt = _parse_dt(sb.dt)
                    if sa_dt is not None and sb_dt is not None:
                        if abs((sa_dt - sb_dt).days) <= time_window:
                            return True
                    elif sa_dt is None or sb_dt is None:
                        return True
            return False

        buy_aligned_levels: list[str] = []
        sell_aligned_levels: list[str] = []

        for i in range(len(level_names)):
            for j in range(i + 1, len(level_names)):
                na, nb = level_names[i], level_names[j]
                sigs_a, sigs_b = level_signals[na], level_signals[nb]
                if _signals_aligned(sigs_a, sigs_b, SignalType.BUY_1ST):
                    if na not in buy_aligned_levels:
                        buy_aligned_levels.append(na)
                    if nb not in buy_aligned_levels:
                        buy_aligned_levels.append(nb)
                if _signals_aligned(sigs_a, sigs_b, SignalType.SELL_1ST):
                    if na not in sell_aligned_levels:
                        sell_aligned_levels.append(na)
                    if nb not in sell_aligned_levels:
                        sell_aligned_levels.append(nb)

        if len(buy_aligned_levels) >= 2:
            events.append({
                "type": "buy_resonance",
                "levels": buy_aligned_levels,
                "strength": len(buy_aligned_levels),
                "description": f"买点共振: {', '.join(buy_aligned_levels)} 同时出现第一类买点信号",
            })

        if len(sell_aligned_levels) >= 2:
            events.append({
                "type": "sell_resonance",
                "levels": sell_aligned_levels,
                "strength": len(sell_aligned_levels),
                "description": f"卖点共振: {', '.join(sell_aligned_levels)} 同时出现第一类卖点信号",
            })

        return events

    def cross_level_trend_status(self) -> dict:
        """
        Cross-level trend growth monitoring (Lessons 45, 53).

        Track how a small-level move grows into larger levels.
        """
        status = {}

        for name in self._level_order:
            analyzer = self._analyzers.get(name)
            if not analyzer:
                continue

            status[name] = {
                "trend_type": analyzer.trend_type.name
                    if hasattr(analyzer.trend_type, "name")
                    else str(analyzer.trend_type),
                "bis": len(analyzer.bis),
                "segments": len(analyzer.segments),
                "hubs": len(analyzer.hubs),
                "signals": len(analyzer.signals),
                "latest_signal": (
                    analyzer.signals[-1].type.value
                    if analyzer.signals else None
                ),
            }

        return status

    def summary(self) -> dict:
        """Return comprehensive multi-level analysis summary."""
        return {
            "levels": self.levels,
            "cross_level_status": self.cross_level_trend_status(),
            "resonance": self.level_resonance(),
            "interval_nesting": self.interval_nesting(),
        }


def _find_matching_signals(
    target: Signal,
    candidates: list[Signal],
    time_window: int = 5,
) -> list[Signal]:
    """
    Find signals in candidates that match the target signal direction and
    fall within ``time_window`` days of the target signal's date.

    True 区间套 requires that sub-level signals occur during the higher-level
    divergence interval (i.e., are time-aligned with the target).  Without
    this filter the returned signals can come from completely unrelated dates,
    making the confidence score meaningless.

    Date strings are expected to be in ISO-8601 format (YYYY-MM-DD or
    YYYY-MM-DD HH:MM:SS).  If parsing fails, the time filter is skipped and
    all same-direction candidates are returned as a best-effort fallback.
    """
    from datetime import datetime

    is_buy = target.type.value.startswith("B")

    # Try to parse the target date
    target_dt = None
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%Y%m%d"):
        try:
            target_dt = datetime.strptime(target.dt, fmt)
            break
        except ValueError:
            continue

    matching = []
    for s in candidates:
        if s.type.value.startswith("B") != is_buy:
            continue

        if target_dt is not None:
            s_dt = None
            for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%Y%m%d"):
                try:
                    s_dt = datetime.strptime(s.dt, fmt)
                    break
                except ValueError:
                    continue

            if s_dt is not None and abs((s_dt - target_dt).days) > time_window:
                continue

        matching.append(s)

    return matching[-3:] if matching else []
