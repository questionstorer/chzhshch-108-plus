"""
Buy/Sell point detection (买卖点识别).
Based on Lessons 15, 17, 20, 21 of 缠中说禅.

Three Classes of Buy Points:
  1st (第一类): After divergence in downtrend - Lesson 15
  2nd (第二类): Pullback low after 1st buy - Lesson 17
  3rd (第三类): Retest not breaking ZG after hub exit - Lesson 20

Three Classes of Sell Points (mirror of buy points):
  1st (第一类): After divergence in uptrend
  2nd (第二类): Rally high after 1st sell
  3rd (第三类): Retest not breaking ZD after hub exit

Completeness Theorem (Lesson 21):
  All up/down trends must start/end at some buy/sell points.
"""

from __future__ import annotations

from .data_types import Bi, Direction, Hub, Signal, SignalType
from .divergence import compute_macd, compute_macd_area


def detect_signals(
    bis: list[Bi],
    hubs: list[Hub],
    closes: list[float],
) -> list[Signal]:
    """
    Detect all three classes of buy and sell points.
    """
    signals: list[Signal] = []

    signals.extend(_detect_1st_class(bis, closes))
    signals.extend(_detect_2nd_class(bis, signals))
    signals.extend(_detect_3rd_class(bis, hubs))

    # Sort by time
    signals.sort(key=lambda s: s.dt)
    return signals


def _detect_1st_class(bis: list[Bi], closes: list[float]) -> list[Signal]:
    """
    Detect 1st class buy/sell points (第一类买卖点).

    1st Buy: Divergence at end of downtrend
      - Two consecutive down Bi where the 2nd has weaker MACD area
      - Price makes new low but MACD doesn't confirm

    1st Sell: Divergence at end of uptrend
      - Two consecutive up Bi where the 2nd has weaker MACD area
      - Price makes new high but MACD doesn't confirm
    """
    if len(bis) < 3 or len(closes) < 26:
        return []

    _, _, histogram = compute_macd(closes)
    signals: list[Signal] = []

    # Find pairs of same-direction Bi and check for divergence
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

        # Get K-line index ranges for MACD area comparison
        curr_start_idx = curr.start.k2.index
        curr_end_idx = curr.end.k2.index
        prev_start_idx = prev_same.start.k2.index
        prev_end_idx = prev_same.end.k2.index

        # Bounds check
        max_idx = len(histogram)
        curr_area = compute_macd_area(
            histogram,
            min(curr_start_idx, max_idx),
            min(curr_end_idx + 1, max_idx),
        )
        prev_area = compute_macd_area(
            histogram,
            min(prev_start_idx, max_idx),
            min(prev_end_idx + 1, max_idx),
        )

        if prev_area == 0:
            continue

        # 1st class BUY point: end of downtrend with divergence
        if curr.direction == Direction.DOWN:
            if curr.low <= prev_same.low and curr_area < prev_area:
                signals.append(Signal(
                    type=SignalType.BUY_1ST,
                    dt=curr.end_dt,
                    price=curr.low,
                    bi=curr,
                    description=(
                        f"第一类买点: 下跌背驰 "
                        f"(MACD面积比={curr_area / prev_area:.2f})"
                    ),
                ))

        # 1st class SELL point: end of uptrend with divergence
        elif curr.direction == Direction.UP:
            if curr.high >= prev_same.high and curr_area < prev_area:
                signals.append(Signal(
                    type=SignalType.SELL_1ST,
                    dt=curr.end_dt,
                    price=curr.high,
                    bi=curr,
                    description=(
                        f"第一类卖点: 上涨背驰 "
                        f"(MACD面积比={curr_area / prev_area:.2f})"
                    ),
                ))

    return signals


def _detect_2nd_class(
    bis: list[Bi],
    first_class_signals: list[Signal],
) -> list[Signal]:
    """
    Detect 2nd class buy/sell points (第二类买卖点).

    2nd Buy (Lesson 17):
      After a 1st buy point, the subsequent pullback's low = 2nd buy point.
      Must not break below the 1st buy point's low.

    2nd Sell:
      After a 1st sell point, the subsequent rally's high = 2nd sell point.
      Must not break above the 1st sell point's high.
    """
    signals: list[Signal] = []

    for sig in first_class_signals:
        if sig.bi is None:
            continue

        bi_idx = sig.bi.index

        if sig.type == SignalType.BUY_1ST:
            # Look for the next pullback (down Bi) after the up Bi that follows
            # Pattern: down(1st buy) -> up -> down(2nd buy)
            for k in range(bi_idx + 1, min(bi_idx + 4, len(bis))):
                if bis[k].direction == Direction.DOWN:
                    if bis[k].low > sig.price:
                        signals.append(Signal(
                            type=SignalType.BUY_2ND,
                            dt=bis[k].end_dt,
                            price=bis[k].low,
                            bi=bis[k],
                            description=f"第二类买点: 回抽不破第一类买点低点",
                        ))
                    break

        elif sig.type == SignalType.SELL_1ST:
            # Look for the next rally (up Bi) after the down Bi that follows
            for k in range(bi_idx + 1, min(bi_idx + 4, len(bis))):
                if bis[k].direction == Direction.UP:
                    if bis[k].high < sig.price:
                        signals.append(Signal(
                            type=SignalType.SELL_2ND,
                            dt=bis[k].end_dt,
                            price=bis[k].high,
                            bi=bis[k],
                            description=f"第二类卖点: 反弹不破第一类卖点高点",
                        ))
                    break

    return signals


def _detect_3rd_class(
    bis: list[Bi],
    hubs: list[Hub],
) -> list[Signal]:
    """
    Detect 3rd class buy/sell points (第三类买卖点).

    3rd Buy (Lesson 20):
      After leaving a hub upward, a pullback that doesn't break
      below ZG = 3rd buy point.

    3rd Sell:
      After leaving a hub downward, a rally that doesn't break
      above ZD = 3rd sell point.
    """
    signals: list[Signal] = []

    for hub in hubs:
        if not hub.elements:
            continue

        last_element = hub.elements[-1]
        # Find the Bi index after the hub
        if isinstance(last_element, Bi):
            hub_end_bi_idx = last_element.index
        else:
            continue

        # Look for movements after the hub
        for i in range(hub_end_bi_idx + 1, min(hub_end_bi_idx + 6, len(bis))):
            bi = bis[i]

            # 3rd Buy: up departure + down retest not breaking ZG
            if bi.direction == Direction.UP and bi.high > hub.ZG:
                # Found departure upward, look for retest
                for j in range(i + 1, min(i + 4, len(bis))):
                    if bis[j].direction == Direction.DOWN:
                        if bis[j].low >= hub.ZG:
                            signals.append(Signal(
                                type=SignalType.BUY_3RD,
                                dt=bis[j].end_dt,
                                price=bis[j].low,
                                bi=bis[j],
                                hub=hub,
                                description=(
                                    f"第三类买点: 离开中枢后回抽不破ZG"
                                    f"({hub.ZG:.2f})"
                                ),
                            ))
                        break
                break

            # 3rd Sell: down departure + up retest not breaking ZD
            if bi.direction == Direction.DOWN and bi.low < hub.ZD:
                # Found departure downward, look for retest
                for j in range(i + 1, min(i + 4, len(bis))):
                    if bis[j].direction == Direction.UP:
                        if bis[j].high <= hub.ZD:
                            signals.append(Signal(
                                type=SignalType.SELL_3RD,
                                dt=bis[j].end_dt,
                                price=bis[j].high,
                                bi=bis[j],
                                hub=hub,
                                description=(
                                    f"第三类卖点: 离开中枢后回抽不破ZD"
                                    f"({hub.ZD:.2f})"
                                ),
                            ))
                        break
                break

    return signals
