"""
缠中说禅技术分析系统 (Chan Theory Technical Analysis System)
Based on the 108 lessons of "教你炒股票" by 缠中说禅

Core Principles:
  - 走势必完美 (Trend Must Be Perfect) - Lesson 17
  - 任何级别的走势都可分解为盘整、下跌与上涨 - Lesson 17
  - 任何走势类型至少由三段次级别走势类型构成 - Lesson 17
"""

from .data_types import (
    Direction, FractalType, KLine, RawKLine,
    Fractal, Bi, Segment, Hub, Signal, SignalType,
)
from .chan import ChanAnalyzer
