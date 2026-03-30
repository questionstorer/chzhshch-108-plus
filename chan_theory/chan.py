"""
Main ChanAnalyzer - orchestrates all components of Chan Theory analysis.
"""

from __future__ import annotations

from .data_types import (
    Bi, Fractal, Hub, KLine, RawKLine, Segment, Signal,
)
from .kline_processor import process_inclusion
from .fractal import detect_fractals
from .bi import construct_bis
from .segment import construct_segments
from .hub import detect_hubs_from_bis, detect_hubs_from_segments, classify_trend
from .divergence import compute_macd
from .signals import detect_signals


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
        self.trend_type: str = ""
        self.macd_dif: list[float] = []
        self.macd_dea: list[float] = []
        self.macd_hist: list[float] = []

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
        1. K-line inclusion processing (包含处理)
        2. Fractal detection (分型识别)
        3. Bi/Stroke construction (笔的构建)
        4. Segment construction (线段构建)
        5. Hub detection (中枢识别)
        6. MACD computation
        7. Signal detection (买卖点识别)
        8. Trend classification
        """
        if not self.raw_klines:
            return

        # Step 1: Process K-line inclusions (Lesson 62)
        self.klines = process_inclusion(self.raw_klines)

        # Step 2: Detect fractals (Lesson 62)
        self.fractals = detect_fractals(self.klines)

        # Step 3: Construct Bi (Lesson 62)
        self.bis = construct_bis(self.fractals, self.klines)

        # Step 4: Construct segments (Lessons 62, 65)
        self.segments = construct_segments(self.bis)

        # Step 5: Detect hubs (Lessons 17, 20, 24)
        self.hubs_bi = detect_hubs_from_bis(self.bis)
        if self.segments:
            self.hubs_seg = detect_hubs_from_segments(self.segments)

        # Step 6: Compute MACD (Lesson 25)
        closes = [k.elements[0].close if k.elements else (k.high + k.low) / 2
                  for k in self.klines]
        if closes:
            self.macd_dif, self.macd_dea, self.macd_hist = compute_macd(closes)

        # Step 7: Detect buy/sell signals (Lessons 15, 17, 20)
        self.signals = detect_signals(self.bis, self.hubs_bi, closes)

        # Step 8: Classify trend (Lesson 17)
        self.trend_type = classify_trend(self.hubs_bi)

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
            "trend_type": self.trend_type,
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
                }
                for h in self.hubs
            ],
        }
