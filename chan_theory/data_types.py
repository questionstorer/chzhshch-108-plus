"""
Core data structures for Chan Theory technical analysis.
Based on Lessons 15, 17, 20, 24, 62 of 缠中说禅.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional


class Direction(Enum):
    UP = auto()
    DOWN = auto()


class FractalType(Enum):
    TOP = auto()     # 顶分型
    BOTTOM = auto()  # 底分型


class SignalType(Enum):
    """Three classes of buy/sell points (Lessons 15, 17, 20)."""
    BUY_1ST = "B1"   # 第一类买点 - after divergence in downtrend
    BUY_2ND = "B2"   # 第二类买点 - pullback low after 1st buy
    BUY_3RD = "B3"   # 第三类买点 - retest not breaking ZG
    SELL_1ST = "S1"   # 第一类卖点 - after divergence in uptrend
    SELL_2ND = "S2"   # 第二类卖点 - rally high after 1st sell
    SELL_3RD = "S3"   # 第三类卖点 - retest not breaking ZD


@dataclass
class RawKLine:
    """Raw K-line/candlestick data before inclusion processing."""

    index: int
    dt: str        # date/time string
    open: float
    close: float
    high: float
    low: float
    volume: float = 0.0


@dataclass
class KLine:
    """
    Processed K-line after inclusion handling (包含处理).
    Per Lesson 62: adjacent K-lines with inclusion relationships
    must be merged before fractal detection.
    """

    index: int
    dt: str
    high: float
    low: float
    elements: list[RawKLine] = field(default_factory=list)

    @property
    def mid(self) -> float:
        return (self.high + self.low) / 2.0


@dataclass
class Fractal:
    """
    Fractal pattern (分型) per Lesson 62.

    Top Fractal (顶分型): k2.high = max(k1.high, k2.high, k3.high)
                          AND k2.low = max(k1.low, k2.low, k3.low)
    Bottom Fractal (底分型): k2.low = min(k1.low, k2.low, k3.low)
                             AND k2.high = min(k1.high, k2.high, k3.high)
    """

    type: FractalType
    k1: KLine
    k2: KLine  # the middle/extreme K-line
    k3: KLine
    index: int  # sequential index among all fractals

    @property
    def value(self) -> float:
        """The extreme value: high for TOP, low for BOTTOM."""
        if self.type == FractalType.TOP:
            return self.k2.high
        return self.k2.low

    @property
    def dt(self) -> str:
        return self.k2.dt


@dataclass
class Bi:
    """
    Stroke/笔 per Lesson 62.

    A Bi connects two adjacent fractals (top→bottom or bottom→top).
    Must have at least one K-line between the top and bottom fractals.
    """

    index: int
    direction: Direction  # UP = bottom→top, DOWN = top→bottom
    start: Fractal
    end: Fractal
    klines: list[KLine] = field(default_factory=list)

    @property
    def high(self) -> float:
        if self.direction == Direction.UP:
            return self.end.value
        return self.start.value

    @property
    def low(self) -> float:
        if self.direction == Direction.UP:
            return self.start.value
        return self.end.value

    @property
    def start_dt(self) -> str:
        return self.start.dt

    @property
    def end_dt(self) -> str:
        return self.end.dt

    @property
    def length(self) -> int:
        return len(self.klines)

    @property
    def change(self) -> float:
        """Price change magnitude."""
        return abs(self.high - self.low)


@dataclass
class Segment:
    """
    Segment/线段 per Lessons 62, 65.

    A segment is composed of at least 3 Bi (strokes).
    It represents a trend movement without internal hub structure.
    """

    index: int
    direction: Direction
    start_bi: Bi
    end_bi: Bi
    bis: list[Bi] = field(default_factory=list)

    @property
    def high(self) -> float:
        return max(b.high for b in self.bis)

    @property
    def low(self) -> float:
        return min(b.low for b in self.bis)

    @property
    def start_dt(self) -> str:
        return self.start_bi.start_dt

    @property
    def end_dt(self) -> str:
        return self.end_bi.end_dt


@dataclass
class Hub:
    """
    Central Hub/走势中枢 per Lessons 17, 20, 24.

    The overlapping part of at least 3 consecutive sub-level trend types.
    Hub zone = [ZD, ZG] where:
      ZG = min(g1, g2) - top of hub range
      ZD = max(d1, d2) - bottom of hub range
      GG = max of all highs  - absolute high
      DD = min of all lows   - absolute low
    """

    index: int
    elements: list  # list of Bi or Segment that form this hub
    ZG: float       # top of overlap zone = min of first two highs
    ZD: float       # bottom of overlap zone = max of first two lows
    GG: float       # highest high of all elements
    DD: float       # lowest low of all elements

    @property
    def range(self) -> tuple[float, float]:
        """Hub zone [ZD, ZG]."""
        return (self.ZD, self.ZG)

    @property
    def width(self) -> float:
        return self.ZG - self.ZD

    def contains(self, price: float) -> bool:
        return self.ZD <= price <= self.ZG


@dataclass
class Signal:
    """
    Buy/Sell signal (买卖点) per Lessons 15, 17, 20.
    """

    type: SignalType
    dt: str
    price: float
    bi: Optional[Bi] = None
    hub: Optional[Hub] = None
    description: str = ""
