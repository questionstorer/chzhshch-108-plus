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

    def level_resonance(self) -> list[dict]:
        """
        Detect 级别共振 (level resonance) per Lesson 53.

        When multiple levels simultaneously show first-type buy/sell points,
        the resulting move is much more powerful.

        Returns list of resonance events.
        """
        events = []

        # Collect latest signals from each level
        level_signals: dict[str, list[Signal]] = {}
        for name, analyzer in self._analyzers.items():
            if analyzer.signals:
                level_signals[name] = analyzer.signals

        if len(level_signals) < 2:
            return events

        # Check for alignment of same-type signals across levels
        # Focus on 1st class signals (strongest)
        buy_levels = []
        sell_levels = []

        for name, signals in level_signals.items():
            latest = signals[-1]
            if latest.type in (SignalType.BUY_1ST, SignalType.BUY_2ND):
                buy_levels.append(name)
            elif latest.type in (SignalType.SELL_1ST, SignalType.SELL_2ND):
                sell_levels.append(name)

        if len(buy_levels) >= 2:
            events.append({
                "type": "buy_resonance",
                "levels": buy_levels,
                "strength": len(buy_levels),
                "description": f"买点共振: {', '.join(buy_levels)} 同时出现买点信号",
            })

        if len(sell_levels) >= 2:
            events.append({
                "type": "sell_resonance",
                "levels": sell_levels,
                "strength": len(sell_levels),
                "description": f"卖点共振: {', '.join(sell_levels)} 同时出现卖点信号",
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
    Find signals in candidates that match the target signal type direction.

    A match means: same buy/sell direction within a reasonable time window.
    """
    is_buy = target.type.value.startswith("B")

    matching = []
    for s in candidates:
        same_direction = s.type.value.startswith("B") == is_buy
        if same_direction:
            matching.append(s)

    # Return the last few matching signals (most recent)
    return matching[-3:] if matching else []
