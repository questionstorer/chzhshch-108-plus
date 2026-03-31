"""
Main ChanAnalyzer - orchestrates all components of Chan Theory analysis.
Implements the complete 缠中说禅 technical analysis pipeline from
K-line preprocessing to signal detection, trend monitoring, and strategies.
"""

from __future__ import annotations

from .data_types import (
    Bi, Fractal, Hub, KLine, RawKLine, Segment, Signal,
    TrendMonitor, TrendType,
)
from .kline_processor import process_inclusion
from .fractal import detect_fractals, analyze_fractal_strength
from .bi import construct_bis
from .segment import construct_segments
from .hub import (
    detect_hubs_from_bis, detect_hubs_from_segments,
    classify_trend, detect_hub_migration,
)
from .divergence import compute_macd
from .signals import detect_signals
from .indicators import (
    compute_bollinger_bands, classify_ma_kisses, detect_gaps,
    detect_boll_contraction,
)
from .strategies import (
    monitor_trend_completion,
    hub_oscillation_signals,
    mechanical_trading_signals,
    three_phase_analysis,
    TradeSignal,
)


class ChanAnalyzer:
    """
    Complete 缠中说禅 technical analysis engine.

    Usage:
        analyzer = ChanAnalyzer()
        analyzer.load(raw_klines)
        analyzer.analyze()

        # Access results
        print(analyzer.signals)       # Buy/sell points
        print(analyzer.hubs)          # Central hubs
        print(analyzer.trend_type)    # Trend classification
        print(analyzer.trend_monitor) # Real-time trend status
        print(analyzer.trade_signals) # Strategy recommendations
    """

    def __init__(self) -> None:
        self.raw_klines: list[RawKLine] = []
        self.klines: list[KLine] = []
        self.fractals: list[Fractal] = []
        self.bis: list[Bi] = []
        self.segments: list[Segment] = []
        self.hubs_bi: list[Hub] = []
        self.hubs_seg: list[Hub] = []
        self.signals: list[Signal] = []
        self.trend_type: TrendType = TrendType.UNKNOWN
        self.macd_dif: list[float] = []
        self.macd_dea: list[float] = []
        self.macd_hist: list[float] = []

        # New: auxiliary indicators
        self.boll_upper: list[float] = []
        self.boll_middle: list[float] = []
        self.boll_lower: list[float] = []
        self.ma_kisses: list[dict] = []
        self.gaps: list = []
        self.boll_contractions: list[dict] = []
        self.hub_migrations: list[dict] = []

        # New: trend monitoring and strategies
        self.trend_monitor: TrendMonitor = TrendMonitor()
        self.trade_signals: list[TradeSignal] = []
        self.phase_info: dict = {}
        self.fractal_strengths: dict = {}

    @property
    def hubs(self) -> list[Hub]:
        """Return all detected hubs (Bi-level + Segment-level)."""
        return self.hubs_bi + self.hubs_seg

    def load(self, raw_klines: list[RawKLine]) -> None:
        """Load raw K-line data."""
        self.raw_klines = raw_klines

    def load_from_dicts(self, data: list[dict]) -> None:
        """
        Load from list of dicts with keys:
        dt, open, close, high, low, volume (optional)
        """
        self.raw_klines = [
            RawKLine(
                index=i,
                dt=d["dt"],
                open=d["open"],
                close=d["close"],
                high=d["high"],
                low=d["low"],
                volume=d.get("volume", 0.0),
            )
            for i, d in enumerate(data)
        ]

    def analyze(self) -> None:
        """
        Run the complete analysis pipeline:
        1. K-line inclusion processing (包含处理) - Lesson 62
        2. Fractal detection (分型识别) - Lesson 62
        3. Fractal strength analysis (分型力度) - Lesson 82
        4. Bi/Stroke construction (笔的构建) - Lesson 62
        5. Segment construction with Case 1/2 (线段构建) - Lessons 62,65,67
        6. Hub detection with extension/expansion (中枢识别) - Lessons 17,20,24
        7. Hub migration analysis - Lesson 70
        8. MACD computation - Lesson 25
        9. Auxiliary indicators (BOLL, MA kisses, gaps)
        10. Signal detection (买卖点识别) - Lessons 15,17,20
        11. Trend classification - Lesson 17
        12. Trend completion monitoring (走势必完美) - Lesson 17
        13. Strategy signals (trading recommendations)
        """
        if not self.raw_klines:
            return

        # Step 1: Process K-line inclusions
        self.klines = process_inclusion(self.raw_klines)

        # Step 2: Detect fractals
        self.fractals = detect_fractals(self.klines)

        # Step 3: Analyze fractal strength
        for f in self.fractals:
            self.fractal_strengths[f.index] = analyze_fractal_strength(f)

        # Step 4: Construct Bi
        self.bis = construct_bis(self.fractals, self.klines)

        # Step 5: Construct segments (with Case 1/2 termination)
        self.segments = construct_segments(self.bis)

        # Step 6: Detect hubs (with extension/expansion)
        self.hubs_bi = detect_hubs_from_bis(self.bis)
        if self.segments:
            self.hubs_seg = detect_hubs_from_segments(self.segments)

        # Step 7: Hub migration analysis
        self.hub_migrations = detect_hub_migration(self.hubs_bi)

        # Step 8: Compute MACD
        closes = self._get_closes()
        if closes:
            self.macd_dif, self.macd_dea, self.macd_hist = compute_macd(closes)

        # Step 9: Auxiliary indicators
        if closes and len(closes) >= 20:
            self.boll_upper, self.boll_middle, self.boll_lower = \
                compute_bollinger_bands(closes)
            self.boll_contractions = detect_boll_contraction(
                self.boll_upper, self.boll_lower
            )

        if closes and len(closes) >= 20:
            self.ma_kisses = classify_ma_kisses(closes)

        highs = [k.high for k in self.klines]
        lows = [k.low for k in self.klines]
        if highs and lows and closes:
            self.gaps = detect_gaps(highs, lows, closes)

        # Step 10: Detect buy/sell signals
        self.signals = detect_signals(self.bis, self.hubs_bi, closes)

        # Step 11: Classify trend
        self.trend_type = classify_trend(self.hubs_bi)

        # Step 12: Monitor trend completion
        has_divergence = any(
            s.type.value in ("B1", "S1") for s in self.signals
        )
        self.trend_monitor = monitor_trend_completion(
            self.bis, self.hubs_bi, self.trend_type, has_divergence
        )

        # Step 13: Generate strategy signals
        self._generate_strategy_signals(closes)

        # Step 14: Three-phase analysis
        self.phase_info = three_phase_analysis(
            self.hubs_bi, self.bis, self.trend_type
        )

    def _get_closes(self) -> list[float]:
        """Extract close prices from processed K-lines."""
        return [
            k.elements[0].close if k.elements else (k.high + k.low) / 2
            for k in self.klines
        ]

    def _generate_strategy_signals(self, closes: list[float]) -> None:
        """Generate trading strategy signals."""
        self.trade_signals = []

        # Mechanical trading signals (Lesson 38)
        mech = mechanical_trading_signals(self.bis, self.hubs_bi, closes)
        self.trade_signals.extend(mech)

        # Hub oscillation signals (Lesson 33) for each hub
        for hub in self.hubs_bi:
            osc = hub_oscillation_signals(self.bis, hub, closes)
            self.trade_signals.extend(osc)

        # Sort by time
        self.trade_signals.sort(key=lambda s: s.dt)

    def summary(self) -> dict:
        """Return a summary of the analysis results."""
        return {
            "raw_klines": len(self.raw_klines),
            "processed_klines": len(self.klines),
            "fractals": len(self.fractals),
            "bis": len(self.bis),
            "segments": len(self.segments),
            "hubs_bi_level": len(self.hubs_bi),
            "hubs_seg_level": len(self.hubs_seg),
            "signals": len(self.signals),
            "trend_type": self.trend_type.name
                if hasattr(self.trend_type, "name")
                else str(self.trend_type),
            "trend_status": self.trend_monitor.status.name
                if hasattr(self.trend_monitor.status, "name")
                else str(self.trend_monitor.status),
            "phase": self.phase_info.get("phase", "unknown"),
            "phase_action": self.phase_info.get("action", "wait"),
            "trade_signals_count": len(self.trade_signals),
            "signal_details": [
                {
                    "type": s.type.value,
                    "dt": s.dt,
                    "price": s.price,
                    "description": s.description,
                }
                for s in self.signals
            ],
            "hub_details": [
                {
                    "ZG": h.ZG,
                    "ZD": h.ZD,
                    "GG": h.GG,
                    "DD": h.DD,
                    "elements": len(h.elements),
                    "level": h.level,
                    "extended": h.is_extended,
                }
                for h in self.hubs
            ],
            "trade_recommendations": [
                {
                    "action": t.action.name,
                    "price": t.price,
                    "dt": t.dt,
                    "reason": t.reason,
                    "confidence": t.confidence,
                }
                for t in self.trade_signals[-5:]  # Last 5 recommendations
            ],
        }
