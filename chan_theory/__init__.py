"""
缠中说禅技术分析系统 (Chan Theory Technical Analysis System)
Based on the 108 lessons of "教你炒股票" by 缠中说禅

Core Principles:
  - 走势必完美 (Trend Must Be Perfect) - Lesson 17
  - 任何级别的走势都可分解为盘整、下跌与上涨 - Lesson 17
  - 任何走势类型至少由三段次级别走势类型构成 - Lesson 17

Modules:
  data_types    - Core data structures (KLine, Fractal, Bi, Segment, Hub, Signal)
  kline_processor - K-line inclusion handling (包含处理)
  fractal       - Fractal detection with strength analysis (分型识别)
  bi            - Bi/Stroke construction (笔的构建)
  segment       - Segment construction with Case 1/2 (线段构建)
  hub           - Hub detection, extension, expansion, migration (中枢识别)
  divergence    - MACD divergence detection (背驰)
  signals       - Three classes of buy/sell points (三类买卖点)
  indicators    - Bollinger Bands, MA kisses, gap analysis (辅助指标)
  strategies    - Trading strategies and trend monitoring (操作策略)
  multi_level   - Multi-level analysis and interval nesting (多级别联立/区间套)
  data_source   - Tushare data integration (数据接口)
  visualize     - Chart generation (可视化)
  chan          - Main analyzer orchestrator (主分析器)
"""

from .data_types import (
    Direction, FractalType, FractalStrength, SignalType,
    TrendType, TrendStatus, PostDivergenceOutcome,
    MAKissType, GapType,
    KLine, RawKLine, Fractal, Bi, Segment, Hub, Signal,
    TrendMonitor, Gap,
)
from .chan import ChanAnalyzer
from .multi_level import MultiLevelAnalyzer
