"""
Trading strategies based on Chan Theory (操作策略).
Based on Lessons 33, 38, 45, 48, 53, 68, 108 of 缠中说禅.

Hub Oscillation Trading (中枢震荡交易, Lesson 33):
  Buy at bottom divergence of each downward departure;
  sell at top divergence of each upward departure.

Mechanical Same-Level Operation (同级别分解机械化操作, Lesson 38):
  Fully mechanical: buy at down-divergence, sell at up-divergence.

Piecewise Function Model (分段函数操作模型, Lesson 68):
  Define boundary conditions and pre-assign actions for each segment.

Three-Phase Model (三段走势分类, Lesson 108):
  Bottom construction → middle connection → top construction.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional

from .data_types import (
    Bi, Direction, Hub, PostDivergenceOutcome, Signal, SignalType,
    TrendMonitor, TrendStatus, TrendType,
)


class PositionAction(Enum):
    BUY = auto()
    SELL = auto()
    HOLD = auto()
    REDUCE = auto()   # Partial sell


@dataclass
class TradeSignal:
    """A concrete trading action recommendation."""
    action: PositionAction
    price: float
    dt: str
    signal_source: Optional[Signal] = None
    reason: str = ""
    confidence: float = 0.0   # 0.0 to 1.0
    position_pct: float = 0.0  # suggested position % change


# ── Trend Completion Monitor (走势必完美, Lesson 17) ─────────────────


def monitor_trend_completion(
    bis: list[Bi],
    hubs: list[Hub],
    trend_type: TrendType,
    has_divergence: bool = False,
) -> TrendMonitor:
    """
    Monitor real-time trend growth/completion status (Lessons 17, 45).

    Tracks:
    - Has minimum structure (one hub) formed?
    - Is the hub extending?
    - Has a 3rd-type point appeared?
    - Is the divergence segment developing?
    """
    monitor = TrendMonitor(trend_type=trend_type)

    if not hubs:
        monitor.status = TrendStatus.FORMING
        monitor.phase = "unknown"
        return monitor

    monitor.hubs_formed = len(hubs)
    monitor.current_segment_count = len(bis)

    last_hub = hubs[-1]

    # Check hub status
    if last_hub.is_extended:
        monitor.status = TrendStatus.EXTENDING
    else:
        monitor.status = TrendStatus.HUB_FORMED

    # Check for divergence segments
    if has_divergence:
        monitor.has_divergence = True
        monitor.status = TrendStatus.DIVERGING

    # Determine phase (Lesson 108)
    if trend_type == TrendType.UPTREND:
        if len(hubs) == 1 and not has_divergence:
            monitor.phase = "bottom"
        elif has_divergence:
            monitor.phase = "top"
        else:
            monitor.phase = "middle"
    elif trend_type == TrendType.DOWNTREND:
        if len(hubs) == 1 and not has_divergence:
            monitor.phase = "top"
        elif has_divergence:
            monitor.phase = "bottom"
        else:
            monitor.phase = "middle"
    else:
        monitor.phase = "consolidation"

    return monitor


# ── Post-Divergence Outcome Classification (Lesson 29) ──────────────


def classify_post_divergence(
    current_bi: Bi,
    last_hub: Hub,
) -> PostDivergenceOutcome:
    """
    Classify the outcome after divergence (Lesson 29).

    After divergence in a+A+b+B+c pattern, exactly 3 possible outcomes:
      1. Level expansion (weakest): rebound reaches DD/GG of last hub but does
         NOT re-enter the core hub zone [ZD, ZG]. Per Lesson 29, the minimum
         valid rebound is one that at least reaches DD/GG; if it can't even
         reach DD/GG a new hub is forming below/above.
      2. Higher-level consolidation: re-enters last hub core [ZD, ZG]
      3. Reverse trend (strongest): breaks through last hub to the other side

    The key threshold between outcomes 1 and 2 is whether the first sub-level
    rebound re-enters the core hub zone [ZD, ZG], not the outer DD/GG bounds.
    """
    if current_bi.direction == Direction.UP:
        # After a bottom divergence, checking the upward rebound
        if current_bi.high < last_hub.ZD:
            # Rebound didn't reach hub core zone → level expansion (weakest)
            return PostDivergenceOutcome.LEVEL_EXPANSION
        elif current_bi.high <= last_hub.ZG:
            # Re-entered hub core zone [ZD, ZG] → higher-level consolidation
            return PostDivergenceOutcome.CONSOLIDATION
        else:
            # Broke through hub zone above ZG → reverse trend (uptrend)
            return PostDivergenceOutcome.REVERSE_TREND
    else:
        # After a top divergence, checking the downward decline
        if current_bi.low > last_hub.ZG:
            # Decline didn't reach hub core zone → level expansion (weakest)
            return PostDivergenceOutcome.LEVEL_EXPANSION
        elif current_bi.low >= last_hub.ZD:
            # Re-entered hub core zone [ZD, ZG] → higher-level consolidation
            return PostDivergenceOutcome.CONSOLIDATION
        else:
            # Broke through hub zone below ZD → reverse trend (downtrend)
            return PostDivergenceOutcome.REVERSE_TREND


# ── Hub Oscillation Trading (Lesson 33) ──────────────────────────────


def hub_oscillation_signals(
    bis: list[Bi],
    hub: Hub,
    closes: list[float],
) -> list[TradeSignal]:
    """
    Generate hub oscillation trading signals (Lesson 33: 中枢震荡交易).

    Strategy:
    - Buy at bottom: when price leaves hub downward and shows divergence
    - Sell at top: when price leaves hub upward and shows divergence
    - If 3rd-type buy appears after sell, re-enter immediately.
    """
    from .divergence import compute_macd, compute_macd_area

    signals: list[TradeSignal] = []

    if not bis or not closes or len(closes) < 26:
        return signals

    _, _, histogram = compute_macd(closes)

    for i, bi in enumerate(bis):
        # Check if Bi leaves the hub
        if bi.direction == Direction.DOWN and bi.low < hub.ZD:
            # Left hub downward - potential buy on divergence
            if i >= 2:
                prev_down = None
                for j in range(i - 2, -1, -1):
                    if bis[j].direction == Direction.DOWN:
                        prev_down = bis[j]
                        break

                if prev_down is not None:
                    curr_area = _safe_macd_area(histogram, bi)
                    prev_area = _safe_macd_area(histogram, prev_down)

                    if prev_area > 0 and curr_area < prev_area:
                        signals.append(TradeSignal(
                            action=PositionAction.BUY,
                            price=bi.low,
                            dt=bi.end_dt,
                            reason=f"中枢震荡买入: 下方背驰 (力度比={curr_area/prev_area:.2f})",
                            confidence=min(1.0, prev_area / max(curr_area, 0.01)),
                            position_pct=0.5,
                        ))

        elif bi.direction == Direction.UP and bi.high > hub.ZG:
            # Left hub upward - potential sell on divergence
            if i >= 2:
                prev_up = None
                for j in range(i - 2, -1, -1):
                    if bis[j].direction == Direction.UP:
                        prev_up = bis[j]
                        break

                if prev_up is not None:
                    curr_area = _safe_macd_area(histogram, bi)
                    prev_area = _safe_macd_area(histogram, prev_up)

                    if prev_area > 0 and curr_area < prev_area:
                        signals.append(TradeSignal(
                            action=PositionAction.SELL,
                            price=bi.high,
                            dt=bi.end_dt,
                            reason=f"中枢震荡卖出: 上方背驰 (力度比={curr_area/prev_area:.2f})",
                            confidence=min(1.0, prev_area / max(curr_area, 0.01)),
                            position_pct=0.5,
                        ))

    return signals


# ── Mechanical Same-Level Trading (Lesson 38) ───────────────────────


def mechanical_trading_signals(
    bis: list[Bi],
    hubs: list[Hub],
    closes: list[float],
) -> list[TradeSignal]:
    """
    Generate fully mechanical same-level trading signals (Lesson 38).

    Rules:
    1. After down-divergence → BUY
    2. If next up-segment shows no divergence vs previous → HOLD
    3. If up-divergence or no new high → SELL
    4. Continuously repeat like a machine

    This is the most mechanical and reliable strategy in Chan Theory.
    """
    from .divergence import compute_macd, compute_macd_area

    signals: list[TradeSignal] = []

    if not bis or len(closes) < 26:
        return signals

    _, _, histogram = compute_macd(closes)
    position_held = False

    for i in range(2, len(bis)):
        curr = bis[i]

        # Find previous same-direction Bi
        prev_same = None
        for j in range(i - 2, -1, -1):
            if bis[j].direction == curr.direction:
                prev_same = bis[j]
                break

        if prev_same is None:
            continue

        curr_area = _safe_macd_area(histogram, curr)
        prev_area = _safe_macd_area(histogram, prev_same)

        if prev_area == 0:
            continue

        has_divergence = curr_area < prev_area

        if curr.direction == Direction.DOWN and has_divergence:
            # Down divergence → BUY
            if not position_held:
                signals.append(TradeSignal(
                    action=PositionAction.BUY,
                    price=curr.low,
                    dt=curr.end_dt,
                    reason=f"机械买入: 下跌背驰 (力度比={curr_area/prev_area:.2f})",
                    confidence=0.7,
                    position_pct=1.0,
                ))
                position_held = True

        elif curr.direction == Direction.UP and has_divergence:
            # Up divergence → SELL
            if position_held:
                signals.append(TradeSignal(
                    action=PositionAction.SELL,
                    price=curr.high,
                    dt=curr.end_dt,
                    reason=f"机械卖出: 上涨背驰 (力度比={curr_area/prev_area:.2f})",
                    confidence=0.7,
                    position_pct=1.0,
                ))
                position_held = False

        elif curr.direction == Direction.UP and not has_divergence:
            # Up with no divergence → HOLD (trend continues)
            if position_held:
                signals.append(TradeSignal(
                    action=PositionAction.HOLD,
                    price=curr.high,
                    dt=curr.end_dt,
                    reason="持有: 上涨无背驰, 趋势延续",
                    confidence=0.6,
                    position_pct=0.0,
                ))

    return signals


# ── Three-Phase Analysis (Lesson 108) ────────────────────────────────


def three_phase_analysis(
    hubs: list[Hub],
    bis: list[Bi],
    trend_type: TrendType,
) -> dict:
    """
    Determine current phase of the three-phase model (Lesson 108).

    Any trend has 3 phases:
      Bottom construction → Middle connection → Top construction

    At bottom/top: trade like hub oscillation
    Middle: hold position and ride the trend
    """
    if not hubs:
        return {"phase": "insufficient_data", "action": "wait"}

    if trend_type == TrendType.UPTREND:
        if len(hubs) == 1:
            return {
                "phase": "bottom_construction",
                "action": "oscillation_buy",
                "description": "底部构筑阶段: 以中枢震荡方式买入为主",
            }
        elif len(hubs) >= 2:
            last_hub = hubs[-1]
            # Check if we might be in top construction
            if bis and bis[-1].direction == Direction.UP:
                return {
                    "phase": "middle_connection",
                    "action": "hold",
                    "description": "中间连接段: 持有, 等待上涨背驰",
                }
            else:
                return {
                    "phase": "top_construction",
                    "action": "oscillation_sell",
                    "description": "顶部构筑阶段: 以中枢震荡方式卖出为主",
                }

    elif trend_type == TrendType.DOWNTREND:
        if len(hubs) == 1:
            return {
                "phase": "top_construction",
                "action": "oscillation_sell",
                "description": "顶部构筑阶段: 以中枢震荡方式卖出为主",
            }
        elif len(hubs) >= 2:
            return {
                "phase": "bottom_construction",
                "action": "oscillation_buy",
                "description": "底部构筑阶段: 以中枢震荡方式买入为主",
            }

    return {
        "phase": "consolidation",
        "action": "oscillation",
        "description": "盘整阶段: 高抛低吸",
    }


# ── Helper ───────────────────────────────────────────────────────────


def _safe_macd_area(histogram: list[float], bi: Bi) -> float:
    """Safely compute MACD area for a Bi's index range."""
    from .divergence import compute_macd_area

    start = bi.start.k2.index
    end = bi.end.k2.index
    return compute_macd_area(histogram, min(start, len(histogram)),
                             min(end + 1, len(histogram)))
