"""
Visualization for Chan Theory technical analysis.
Generates candlestick charts with fractals, Bi, segments, hubs, signals,
Bollinger bands, and MACD.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .chan import ChanAnalyzer

try:
    import matplotlib
    matplotlib.use("Agg")  # Non-interactive backend for server environments
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False


def plot_analysis(
    analyzer: ChanAnalyzer,
    title: str = "缠论技术分析",
    save_path: str = "chan_analysis.png",
    show_boll: bool = True,
    show_trade_signals: bool = True,
    figsize: tuple = (20, 14),
) -> None:
    """
    Plot the complete Chan Theory analysis.

    Displays:
    - K-line candlesticks
    - Fractals (top=red triangle down, bottom=green triangle up)
    - Bi/Strokes (connected lines)
    - Segments (thick lines)
    - Hubs (shaded rectangles)
    - Buy/Sell signals (arrows)
    - MACD subplot
    - Bollinger Bands (optional)
    - Trade signal annotations (optional)
    """
    if not HAS_MATPLOTLIB:
        raise ImportError(
            "matplotlib is required for visualization. "
            "Install it with: pip install matplotlib"
        )

    if not analyzer.klines:
        print("No data to plot. Run analyzer.analyze() first.")
        return

    num_subplots = 2
    height_ratios = [3, 1]
    if show_boll and analyzer.boll_upper:
        pass  # BOLL on main chart

    fig, axes = plt.subplots(
        num_subplots, 1, figsize=figsize,
        gridspec_kw={"height_ratios": height_ratios},
        sharex=True,
    )
    ax1, ax2 = axes[0], axes[1]

    klines = analyzer.klines
    n = len(klines)
    highs = [k.high for k in klines]
    lows = [k.low for k in klines]

    # --- Main chart: K-lines as bars ---
    for i, k in enumerate(klines):
        if k.elements:
            o = k.elements[0].open
            c = k.elements[-1].close
        else:
            o = c = k.mid

        # A-share convention: red = bullish (up), green = bearish (down)
        color = "#d32f2f" if c >= o else "#388e3c"
        ax1.plot([i, i], [k.low, k.high], color=color, linewidth=0.8)
        ax1.plot([i, i], [min(o, c), max(o, c)], color=color, linewidth=3.0)

    # --- Bollinger Bands ---
    if show_boll and analyzer.boll_upper:
        ax1.plot(analyzer.boll_upper, color="#2196f3", linewidth=0.6,
                 alpha=0.5, linestyle="--", label="BOLL Upper")
        ax1.plot(analyzer.boll_middle, color="#9e9e9e", linewidth=0.6,
                 alpha=0.5, linestyle="-", label="BOLL Mid")
        ax1.plot(analyzer.boll_lower, color="#2196f3", linewidth=0.6,
                 alpha=0.5, linestyle="--", label="BOLL Lower")
        ax1.fill_between(range(len(analyzer.boll_upper)),
                         analyzer.boll_upper, analyzer.boll_lower,
                         alpha=0.05, color="#2196f3")

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
        seg_plotted = False
        for seg in analyzer.segments:
            seg_x = [seg.start_bi.start.k2.index, seg.end_bi.end.k2.index]
            seg_y = [seg.start_bi.start.value, seg.end_bi.end.value]
            label = "线段 (Segment)" if not seg_plotted else None
            ax1.plot(seg_x, seg_y, "m-", linewidth=2.5, alpha=0.5, label=label)
            seg_plotted = True

    # --- Hubs ---
    for hub in analyzer.hubs:
        if not hub.elements:
            continue

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

        edge_color = "#ff9800" if hub.level == 0 else "#e91e63"
        face_color = "#fff3e0" if hub.level == 0 else "#fce4ec"

        rect = mpatches.Rectangle(
            (x_start, hub.ZD),
            x_end - x_start,
            hub.ZG - hub.ZD,
            linewidth=1.5,
            edgecolor=edge_color,
            facecolor=face_color,
            alpha=0.4,
        )
        ax1.add_patch(rect)

        mid_x = (x_start + x_end) / 2
        level_str = f"L{hub.level}" if hub.level > 0 else ""
        ext_str = " 延伸" if hub.is_extended else ""
        ax1.text(mid_x, hub.ZG,
                 f"中枢{level_str}[{hub.ZD:.1f},{hub.ZG:.1f}]{ext_str}",
                 fontsize=7, ha="center", va="bottom", color="#e65100")

    # --- Signals ---
    signal_colors = {
        "B1": ("#4caf50", "^", 14),
        "B2": ("#81c784", "^", 12),
        "B3": ("#a5d6a7", "^", 10),
        "S1": ("#f44336", "v", 14),
        "S2": ("#e57373", "v", 12),
        "S3": ("#ef9a9a", "v", 10),
    }

    for sig in analyzer.signals:
        style = signal_colors.get(sig.type.value, ("#999", "o", 8))
        color, marker, size = style

        sig_x = None
        if sig.bi:
            sig_x = sig.bi.end.k2.index

        if sig_x is not None:
            ax1.plot(sig_x, sig.price, marker=marker, color=color,
                     markersize=size, markeredgecolor="black",
                     markeredgewidth=0.5)
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

    # --- Trade Signal Annotations ---
    if show_trade_signals and analyzer.trade_signals:
        for ts in analyzer.trade_signals[-10:]:  # Last 10 trade signals
            ts_x = None
            # Try to find x position
            for bi in analyzer.bis:
                if bi.end_dt == ts.dt:
                    ts_x = bi.end.k2.index
                    break

            if ts_x is not None:
                if ts.action.name == "BUY":
                    ax1.axvline(x=ts_x, color="#4caf50", alpha=0.2,
                                linewidth=1)
                elif ts.action.name == "SELL":
                    ax1.axvline(x=ts_x, color="#f44336", alpha=0.2,
                                linewidth=1)

    # --- Title & Info ---
    trend_name = (analyzer.trend_type.name
                  if hasattr(analyzer.trend_type, "name")
                  else str(analyzer.trend_type))
    phase = analyzer.phase_info.get("phase", "")
    status = (analyzer.trend_monitor.status.name
              if hasattr(analyzer.trend_monitor.status, "name")
              else "")

    info_text = f"趋势: {trend_name} | 阶段: {phase} | 状态: {status}"
    ax1.set_title(f"{title}\n{info_text}", fontsize=13, fontweight="bold")
    ax1.set_ylabel("价格 (Price)")
    ax1.grid(True, alpha=0.3)

    # Deduplicate legend
    handles, labels = ax1.get_legend_handles_labels()
    seen = set()
    unique = [(h, l) for h, l in zip(handles, labels)
              if l not in seen and not seen.add(l)]
    if unique:
        ax1.legend(*zip(*unique), loc="upper left", fontsize=8)

    # --- MACD subplot ---
    if analyzer.macd_hist:
        hist = analyzer.macd_hist
        colors = ["#4caf50" if h >= 0 else "#f44336" for h in hist]
        ax2.bar(range(len(hist)), hist, color=colors, width=0.8, alpha=0.7)

        if analyzer.macd_dif:
            ax2.plot(analyzer.macd_dif, "b-", linewidth=0.8, label="DIF",
                     alpha=0.8)
        if analyzer.macd_dea:
            ax2.plot(analyzer.macd_dea, "r-", linewidth=0.8, label="DEA",
                     alpha=0.8)

        ax2.axhline(y=0, color="gray", linewidth=0.5)
        ax2.set_ylabel("MACD")
        ax2.legend(fontsize=8)
        ax2.grid(True, alpha=0.3)

    ax2.set_xlabel("K线序号")

    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches="tight")
    print(f"Chart saved to {save_path}")


def plot_multi_level(
    analyzers: dict,
    title: str = "缠论多级别分析",
    save_path: str = "chan_multi_level.png",
) -> None:
    """
    Plot multi-level analysis side by side.

    Args:
        analyzers: dict mapping level name to ChanAnalyzer
        title: Chart title
        save_path: Output file path
    """
    if not HAS_MATPLOTLIB:
        raise ImportError("matplotlib is required for visualization.")

    levels = list(analyzers.keys())
    n_levels = len(levels)

    if n_levels == 0:
        return

    fig, axes = plt.subplots(n_levels, 1, figsize=(20, 6 * n_levels),
                             sharex=False)
    if n_levels == 1:
        axes = [axes]

    for ax, level_name in zip(axes, levels):
        analyzer = analyzers[level_name]
        if not analyzer.klines:
            ax.set_title(f"{level_name} - No Data")
            continue

        klines = analyzer.klines

        # K-lines
        for i, k in enumerate(klines):
            if k.elements:
                o = k.elements[0].open
                c = k.elements[-1].close
            else:
                o = c = k.mid
            # A-share convention: red = bullish (up), green = bearish (down)
            color = "#d32f2f" if c >= o else "#388e3c"
            ax.plot([i, i], [k.low, k.high], color=color, linewidth=0.5)
            ax.plot([i, i], [min(o, c), max(o, c)], color=color, linewidth=2.0)

        # Bi
        if analyzer.bis:
            bi_x, bi_y = [], []
            for bi in analyzer.bis:
                bi_x.extend([bi.start.k2.index, bi.end.k2.index])
                bi_y.extend([bi.start.value, bi.end.value])
            ax.plot(bi_x, bi_y, "b-", linewidth=1.0, alpha=0.6)

        # Hubs
        for hub in analyzer.hubs:
            if not hub.elements:
                continue
            first_el = hub.elements[0]
            last_el = hub.elements[-1]
            x_start = (first_el.start.k2.index if hasattr(first_el, "start")
                       else first_el.start_bi.start.k2.index
                       if hasattr(first_el, "start_bi") else 0)
            x_end = (last_el.end.k2.index if hasattr(last_el, "end")
                     else last_el.end_bi.end.k2.index
                     if hasattr(last_el, "end_bi") else len(klines))
            rect = mpatches.Rectangle(
                (x_start, hub.ZD), x_end - x_start, hub.ZG - hub.ZD,
                linewidth=1.0, edgecolor="#ff9800", facecolor="#fff3e0",
                alpha=0.4)
            ax.add_patch(rect)

        # Signals
        for sig in analyzer.signals:
            if sig.bi:
                sx = sig.bi.end.k2.index
                color = "#4caf50" if "B" in sig.type.value else "#f44336"
                marker = "^" if "B" in sig.type.value else "v"
                ax.plot(sx, sig.price, marker=marker, color=color,
                        markersize=10, markeredgecolor="black",
                        markeredgewidth=0.5)

        trend_name = (analyzer.trend_type.name
                      if hasattr(analyzer.trend_type, "name")
                      else str(analyzer.trend_type))
        ax.set_title(f"{level_name} | 趋势: {trend_name} | "
                     f"中枢: {len(analyzer.hubs)} | "
                     f"信号: {len(analyzer.signals)}",
                     fontsize=11)
        ax.set_ylabel("Price")
        ax.grid(True, alpha=0.3)

    plt.suptitle(title, fontsize=14, fontweight="bold")
    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches="tight")
    print(f"Multi-level chart saved to {save_path}")
