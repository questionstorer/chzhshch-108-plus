"""
Visualization for Chan Theory technical analysis.
Generates candlestick charts with fractals, Bi, segments, hubs, and signals.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .chan import ChanAnalyzer

try:
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    from matplotlib.collections import LineCollection
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False


def plot_analysis(analyzer: ChanAnalyzer, title: str = "缠论技术分析") -> None:
    """
    Plot the complete Chan Theory analysis on a candlestick-style chart.

    Displays:
    - K-line candlesticks
    - Fractals (top=red triangle down, bottom=green triangle up)
    - Bi/Strokes (connected lines)
    - Hubs (shaded rectangles)
    - Buy/Sell signals (arrows)
    - MACD subplot
    """
    if not HAS_MATPLOTLIB:
        raise ImportError(
            "matplotlib is required for visualization. "
            "Install it with: pip install matplotlib"
        )

    if not analyzer.klines:
        print("No data to plot. Run analyzer.analyze() first.")
        return

    fig, (ax1, ax2) = plt.subplots(
        2, 1, figsize=(18, 10),
        gridspec_kw={"height_ratios": [3, 1]},
        sharex=True,
    )

    klines = analyzer.klines
    n = len(klines)
    x = list(range(n))
    highs = [k.high for k in klines]
    lows = [k.low for k in klines]
    mids = [k.mid for k in klines]

    # --- Main chart: K-lines as bars ---
    for i, k in enumerate(klines):
        if k.elements:
            o = k.elements[0].open
            c = k.elements[-1].close
        else:
            o = c = k.mid

        color = "#d32f2f" if c < o else "#388e3c"
        ax1.plot([i, i], [k.low, k.high], color=color, linewidth=0.8)
        ax1.plot([i, i], [min(o, c), max(o, c)], color=color, linewidth=3.0)

    # --- Fractals ---
    for f in analyzer.fractals:
        idx = f.k2.index
        if f.type.name == "TOP":
            ax1.plot(idx, f.value, "rv", markersize=8, alpha=0.7)
        else:
            ax1.plot(idx, f.value, "g^", markersize=8, alpha=0.7)

    # --- Bi / Strokes ---
    if analyzer.bis:
        bi_x = []
        bi_y = []
        for bi in analyzer.bis:
            start_idx = bi.start.k2.index
            end_idx = bi.end.k2.index
            bi_x.extend([start_idx, end_idx])
            bi_y.extend([bi.start.value, bi.end.value])

        ax1.plot(bi_x, bi_y, "b-", linewidth=1.2, alpha=0.6, label="笔 (Bi)")

    # --- Segments ---
    if analyzer.segments:
        for seg in analyzer.segments:
            seg_x = [seg.start_bi.start.k2.index, seg.end_bi.end.k2.index]
            seg_y = [
                seg.start_bi.start.value,
                seg.end_bi.end.value,
            ]
            ax1.plot(seg_x, seg_y, "m-", linewidth=2.5, alpha=0.5, label="线段 (Segment)")

    # --- Hubs ---
    for hub in analyzer.hubs:
        if not hub.elements:
            continue

        # Determine x range
        first_el = hub.elements[0]
        last_el = hub.elements[-1]

        if hasattr(first_el, "start"):
            x_start = first_el.start.k2.index
        elif hasattr(first_el, "start_bi"):
            x_start = first_el.start_bi.start.k2.index
        else:
            continue

        if hasattr(last_el, "end"):
            x_end = last_el.end.k2.index
        elif hasattr(last_el, "end_bi"):
            x_end = last_el.end_bi.end.k2.index
        else:
            continue

        rect = mpatches.Rectangle(
            (x_start, hub.ZD),
            x_end - x_start,
            hub.ZG - hub.ZD,
            linewidth=1.5,
            edgecolor="#ff9800",
            facecolor="#fff3e0",
            alpha=0.4,
        )
        ax1.add_patch(rect)

        # Label hub zone
        mid_x = (x_start + x_end) / 2
        ax1.text(mid_x, hub.ZG, f"中枢[{hub.ZD:.1f},{hub.ZG:.1f}]",
                 fontsize=7, ha="center", va="bottom", color="#e65100")

    # --- Signals ---
    signal_colors = {
        "B1": ("#4caf50", "^", 14),  # 1st buy
        "B2": ("#81c784", "^", 12),  # 2nd buy
        "B3": ("#a5d6a7", "^", 10),  # 3rd buy
        "S1": ("#f44336", "v", 14),  # 1st sell
        "S2": ("#e57373", "v", 12),  # 2nd sell
        "S3": ("#ef9a9a", "v", 10),  # 3rd sell
    }

    for sig in analyzer.signals:
        style = signal_colors.get(sig.type.value, ("#999", "o", 8))
        color, marker, size = style

        # Find the x position from Bi
        sig_x = None
        if sig.bi:
            sig_x = sig.bi.end.k2.index

        if sig_x is not None:
            ax1.plot(sig_x, sig.price, marker=marker, color=color,
                     markersize=size, markeredgecolor="black", markeredgewidth=0.5)
            offset = -0.03 * (max(highs) - min(lows)) if "S" in sig.type.value \
                else 0.03 * (max(highs) - min(lows))
            ax1.annotate(
                sig.type.value,
                xy=(sig_x, sig.price),
                xytext=(sig_x, sig.price + offset),
                fontsize=8,
                fontweight="bold",
                color=color,
                ha="center",
            )

    ax1.set_title(title, fontsize=14, fontweight="bold")
    ax1.set_ylabel("价格 (Price)")
    ax1.grid(True, alpha=0.3)

    # Deduplicate legend
    handles, labels = ax1.get_legend_handles_labels()
    seen = set()
    unique = [(h, l) for h, l in zip(handles, labels) if l not in seen and not seen.add(l)]
    if unique:
        ax1.legend(*zip(*unique), loc="upper left", fontsize=8)

    # --- MACD subplot ---
    if analyzer.macd_hist:
        hist = analyzer.macd_hist
        colors = ["#4caf50" if h >= 0 else "#f44336" for h in hist]
        ax2.bar(range(len(hist)), hist, color=colors, width=0.8, alpha=0.7)

        if analyzer.macd_dif:
            ax2.plot(analyzer.macd_dif, "b-", linewidth=0.8, label="DIF", alpha=0.8)
        if analyzer.macd_dea:
            ax2.plot(analyzer.macd_dea, "r-", linewidth=0.8, label="DEA", alpha=0.8)

        ax2.axhline(y=0, color="gray", linewidth=0.5)
        ax2.set_ylabel("MACD")
        ax2.legend(fontsize=8)
        ax2.grid(True, alpha=0.3)

    ax2.set_xlabel("K线序号")

    plt.tight_layout()
    plt.savefig("chan_analysis.png", dpi=150, bbox_inches="tight")
    plt.show()
    print("Chart saved to chan_analysis.png")
