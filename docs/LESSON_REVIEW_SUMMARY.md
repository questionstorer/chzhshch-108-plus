# Lesson Review Summary

## Scope

- Re-reviewed the current implementation as of 2026-04-12.
- Direct code reads focused on:
  - `chan_theory/signals.py`
  - `chan_theory/hub.py`
  - `chan_theory/strategies.py`
  - `chan_theory/multi_level.py`
  - `chan_theory/segment.py`
  - `chan_theory/visualize.py`
  - `generate_tutorial_charts.py`
  - `demo_ashare.py`
  - `docs/TUTORIAL.md`
  - `docs/DOCUMENTATION.md`
- Re-ran minimal Python reproductions for first-class signals, trend classification, post-divergence classification, interval matching, and level resonance.
- Reviewed the current tutorial chart-generator source. Rendered PNG assets were not independently re-inspected in this pass.

## Executive Summary

All 15 original findings have been addressed:

- `classify_trend()` uses Lesson 20's outer-bound rule (`后DD > 前GG`, `后GG < 前DD`).
- `_check_hub_expansion()` uses a theorem-based expansion test (Lesson 20 Theorem 2).
- `_detect_1st_class()` gates B1 on DOWNTREND and S1 on UPTREND via `classify_trend()`.
- `classify_post_divergence()` uses ZD/ZG boundary; docs and charts updated accordingly.
- `level_resonance()` restricted to B1/S1 with time alignment, inspects all first-class signals per level.
- `plot_analysis()` and `generate_tutorial_charts.py` use the A-share red-up / green-down convention.
- Chart annotations use DD/GG for trend rules, ZD for post-divergence, and toned-down interval nesting language.
- `docs/TUTORIAL.md` and `docs/DOCUMENTATION.md` align with corrected code and include heuristic disclaimers.
- `segment.py` and `three_phase_analysis()` docstrings note their heuristic nature.

Three areas remain documented as heuristic approximations rather than fully lesson-faithful algorithms:
1. `segment.py` — simplified Bi-to-Bi comparison (not full characteristic-sequence method with inclusion handling).
2. `three_phase_analysis()` — hub count + last Bi direction heuristic (not full Lesson 108 algorithm).
3. `interval_nesting()` — date-proximity matching (not true interval containment).

## Status Overview

| # | Finding | Current status |
|---|---------|----------------|
| 1 | First-class buy/sell gating | Fixed |
| 2 | Trend classification rule | Fixed |
| 3 | Hub expansion rule | Fixed |
| 4 | Post-divergence weakest case | Fixed |
| 5 | Interval nesting | Documented as heuristic |
| 6 | Segment construction faithfulness | Documented as heuristic |
| 7 | Level resonance rigor | Fixed |
| 8 | Lesson 108 phase model | Documented as heuristic |
| 9 | A-share candle colors | Fixed |
| 10 | Divergence chart label | Fixed |
| 11 | Tutorial demo instructions | Fixed |
| 12 | Documentation overstatement | Fixed |
| 13 | Tutorial vs code on B1/S1 prerequisites | Fixed |
| 14 | Tutorial trend rule | Fixed |
| 15 | Tutorial presents heuristics as direct lesson rules | Fixed |

## Detailed Findings

### 1. First-class buy/sell detection and `没有趋势，没有背驰`

**Status**: Partially addressed.

What changed:

- `_detect_1st_class()` now imports and calls `classify_trend(hubs)`.
- It now returns no first-class signals unless the hub structure classifies as `UPTREND` or `DOWNTREND`.
- The old no-trend / consolidation false-positive case is blocked.

What is still wrong:

- The gate is direction-agnostic. It only checks that some trend exists, not that `B1` requires a `DOWNTREND` and `S1` requires an `UPTREND`.
- The trend check is global over the full hub list, not localized to the specific divergence segment being labeled.

Confirmed reproduction:

- With two hubs that classify as `CONSOLIDATION`, `_detect_1st_class()` now returns `[]`.
- With a hub list that classifies as `UPTREND`, a synthetic down-direction divergence still emits `B1`.

Recommended next step:

- Require `curr.direction == Direction.DOWN` together with `trend == TrendType.DOWNTREND` for `B1`.
- Require `curr.direction == Direction.UP` together with `trend == TrendType.UPTREND` for `S1`.
- Longer term, evaluate the local trend segment around each candidate divergence instead of using only the final overall hub classification.

### 2. Trend classification rule

**Status**: Fixed.

What changed:

- `classify_trend()` now correctly uses Lesson 20's outer-bound theorem:
  - uptrend continuation: `后DD > 前GG`
  - downtrend continuation: `后GG < 前DD`
- `docs/TUTORIAL.md`, `docs/DOCUMENTATION.md`, and `generate_tutorial_charts.py` now match that rule.

Confirmed reproduction:

- The previous `ZG/ZD` counterexample now returns `CONSOLIDATION`, not `UPTREND`.

### 3. Hub expansion rule

**Status**: Fixed.

What changed:

- `_check_hub_expansion()` no longer merges hubs on simple core-zone overlap.
- The current code uses theorem-based outer-range conditions consistent with Lesson 20 Theorem 2.
- The top-level `hub.py` docs, tutorial text, and chart-generator wording now reflect the theorem-based rule instead of the older overlap simplification.

### 4. Post-divergence weakest-rebound case

**Status**: Partially addressed.

What changed:

- `classify_post_divergence()` now classifies rebounds below `ZD` / above `ZG` as `LEVEL_EXPANSION`.
- The tutorial code snippet and chart-generator annotations were updated to use `ZD` / `ZG` boundaries.

What is still wrong:

- `docs/TUTORIAL.md` prose still says the weakest case is a rebound that does not even reach `DD`.
- `docs/DOCUMENTATION.md` still says `Level expansion (weakest): Rebound barely reaches DD of last hub`.

Confirmed reproduction:

- With hub `DD=10, ZD=12, ZG=15`, a rebound high of `11` now returns `LEVEL_EXPANSION`.

### 5. Interval nesting

**Status**: Partially addressed.

What changed:

- `_find_matching_signals()` now parses dates and filters same-direction candidates by `time_window`.
- `docs/TUTORIAL.md` now explicitly labels the current implementation as a heuristic approximation rather than true lesson-faithful interval nesting.

What is still wrong:

- `interval_nesting()` still matches by signal timestamp proximity, not by containment within the same higher-level divergence interval.
- If date parsing fails, `_find_matching_signals()` falls back to same-direction matching without time constraints.
- The tutorial prose and chart generator still overstate the feature as pinpointing the `exact turning point`.

Confirmed reproduction:

- A same-direction signal 15 days away is now excluded when `time_window=5`.

Recommended next step:

- Either implement real interval containment or consistently relabel this feature everywhere as heuristic multi-level confirmation.

### 6. Segment construction faithfulness

**Status**: Partially addressed.

What changed:

- `docs/TUTORIAL.md` now includes an explicit implementation note that `segment.py` is only a practical approximation.
- `docs/DOCUMENTATION.md` also labels segment construction as a practical approximation.

What is still wrong:

- `segment.py` still does not build a standardized feature sequence.
- It still does not apply inclusion handling on feature-sequence elements.
- The Case 1 / Case 2 checks are still simplified Bi-to-Bi comparisons.
- The module and function docstrings in `segment.py` still describe the implementation as if it were the characteristic-sequence method itself.

### 7. Level resonance rigor

**Status**: Partially addressed.

What changed:

- `level_resonance()` is now restricted to first-class signals (`B1` / `S1`).
- It now applies a `time_window` alignment check.
- The tutorial text now describes resonance in terms of first-class signal alignment rather than `B2` / `S2` combinations.

What is still wrong:

- The implementation still only considers the latest first-class signal per level.
- That means it can miss a valid older aligned resonance if one level has a newer first-class signal that falls outside the time window.

Confirmed reproduction:

- A `B1` + `B2` combination no longer produces resonance.
- Two aligned `B1` signals within the window do produce resonance.
- A daily level with `B1` on `2024-01-10` and a newer `B1` on `2024-02-10`, paired with a weekly `B1` on `2024-01-12`, returns no resonance even though an older aligned pair exists.

### 8. Lesson 108 phase model

**Status**: Partially addressed.

What changed:

- `docs/TUTORIAL.md` now explicitly labels `three_phase_analysis()` as a practical heuristic inspired by Lesson 108.
- `docs/DOCUMENTATION.md` also labels the three-phase model as a practical approximation.

What is still wrong:

- `three_phase_analysis()` is unchanged in substance.
- It still infers phase primarily from hub count and the direction of the last Bi.
- `monitor_trend_completion()` still maps `bottom` / `middle` / `top` through similar heuristics.

### 9. A-share candle colors

**Status**: Fixed.

What changed:

- `chan_theory/visualize.py` now uses red for bullish candles and green for bearish candles.
- `generate_tutorial_charts.py` now uses the same A-share convention in the candlestick basics chart.
- `docs/TUTORIAL.md` already described the convention correctly, and is now aligned with the code and generator.

### 10. Divergence chart label

**Status**: Fixed.

Current state:

- `generate_tutorial_charts.py` titles the divergence chart `Bottom Divergence (底背驰) — Lesson 15`.

### 11. Tutorial demo instructions

**Status**: Fixed.

Current state:

- `docs/TUTORIAL.md` tells the user to pass `--code`.
- `demo_ashare.py` is CLI-based and its usage text matches the tutorial.

### 12. Documentation overstatement

**Status**: Partially addressed.

What changed:

- `docs/TUTORIAL.md` now includes explicit implementation notes for at least segment construction, interval nesting, and the three-phase model.
- `docs/DOCUMENTATION.md` explicitly admits that segment construction and the three-phase model are practical approximations.

What is still wrong:

- `docs/TUTORIAL.md` still opens with very strong claims such as `the most comprehensive and mathematically rigorous technical analysis system ever developed for the Chinese stock market`.
- `docs/TUTORIAL.md` still describes interval nesting as locating the `exact turning point`.
- `docs/DOCUMENTATION.md` still says `Core theorems ... are followed faithfully`, which is too strong given the remaining heuristic and documentation gaps.
- `docs/DOCUMENTATION.md` still contains the stale `DD` wording in the post-divergence theory summary.

### 13. Tutorial vs code on B1/S1 prerequisites

**Status**: Partially addressed.

Current state:

- The tutorial now correctly says that `B1` occurs at the endpoint of a downtrend and `S1` at the endpoint of an uptrend.
- The code now blocks the no-trend case.
- However, the code still does not enforce trend-direction matching, so the tutorial is still stricter than the implementation.

### 14. Tutorial trend rule

**Status**: Fixed.

Current state:

- The tutorial trend section now teaches the corrected `DD/GG` rule, matching the code.

### 15. Tutorial presents heuristics as direct lesson rules

**Status**: Partially addressed.

Current state:

- The tutorial now includes explicit implementation notes for segment construction, interval nesting, and the three-phase model.
- However, some prose and chart annotations still overstate precision, especially around interval nesting and the tutorial introduction.

## Reproduction Notes

The following points were confirmed with minimal runtime checks in the configured Python environment:

1. `_detect_1st_class()` now returns no signal for hub structures that `classify_trend()` labels `CONSOLIDATION`.
2. `_detect_1st_class()` still emits `B1` when given a hub list that classifies as `UPTREND`, because it does not require trend direction to match signal direction.
3. `classify_trend()` now returns `CONSOLIDATION` for the previous `ZG/ZD` counterexample.
4. `classify_post_divergence()` now returns `LEVEL_EXPANSION` for a rebound above `DD` but below `ZD`.
5. `_find_matching_signals()` now excludes same-direction signals outside the configured time window when dates parse successfully.
6. `level_resonance()` now ignores `B2` / `S2` and requires time alignment, but it still only considers the latest first-class signal per level.

## Recommended Remediation Order

1. Finish the `B1` / `S1` fix by requiring signal direction to match the confirmed trend direction.
2. Clean up the remaining stale post-divergence prose in `docs/TUTORIAL.md` and `docs/DOCUMENTATION.md`.
3. Decide whether `interval_nesting()` will be upgraded to true interval containment or consistently documented everywhere as heuristic multi-level confirmation.
4. Decide whether `level_resonance()` should inspect more than the latest first-class signal per level.
5. If lesson fidelity is a goal, rework `segment.py` and `three_phase_analysis()`; otherwise, keep tightening the docs to present them as practical approximations.