#!/usr/bin/env python3
"""
Generate educational visualization charts for the Chan Theory tutorial.
Each chart illustrates a specific concept from the 108 lessons.
"""
from __future__ import annotations
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.patheffects as pe
import matplotlib.font_manager as fm
import numpy as np

# ── Rebuild font cache and pick a CJK font ───────────────────────────
def _setup_cjk_font():
    """Find a CJK-capable font and configure matplotlib to use it."""
    # Prefer fonts in this order
    candidates = [
        "Noto Sans CJK SC",
        "WenQuanYi Micro Hei",
        "WenQuanYi Zen Hei",
        "Noto Sans CJK JP",
        "Noto Serif CJK SC",
    ]
    available = {f.name for f in fm.fontManager.ttflist}
    for name in candidates:
        if name in available:
            return name
    # Not found in cache — rebuild and retry once
    fm._load_fontmanager(try_read_cache=False)
    available = {f.name for f in fm.fontManager.ttflist}
    for name in candidates:
        if name in available:
            return name
    return None  # fall back to default

_cjk_font = _setup_cjk_font()

OUT = "docs/images"
os.makedirs(OUT, exist_ok=True)

# ── Shared style ──────────────────────────────────────────────────────
_rc = {
    "figure.facecolor": "white",
    "axes.facecolor": "#fafafa",
    "axes.grid": True,
    "grid.alpha": 0.25,
    "font.size": 11,
    "axes.unicode_minus": False,
}
if _cjk_font:
    _rc["font.family"] = _cjk_font
    print(f"  using CJK font: {_cjk_font}")
else:
    print("  WARNING: no CJK font found; Chinese characters may not render")
plt.rcParams.update(_rc)


def save(fig, name):
    fig.savefig(f"{OUT}/{name}", dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  saved {OUT}/{name}")


# =====================================================================
# 1. K-line / Candlestick basics
# =====================================================================
def chart_kline_basics():
    fig, ax = plt.subplots(figsize=(10, 6))

    # Draw two example candles – bullish and bearish
    # Bullish (rising): close > open, colored green
    x = 1
    o, c, h, l = 10, 13, 14, 9.5
    ax.plot([x, x], [l, h], color="#388e3c", lw=2)
    ax.bar(x, c - o, bottom=o, width=0.5, color="#388e3c", edgecolor="#388e3c")
    # Labels
    ax.annotate("High (最高价)", xy=(x, h), xytext=(x + 0.8, h + 0.3),
                fontsize=10, arrowprops=dict(arrowstyle="->", color="gray"))
    ax.annotate("Close (收盘价)", xy=(x + 0.25, c), xytext=(x + 1.2, c + 0.5),
                fontsize=10, arrowprops=dict(arrowstyle="->", color="gray"))
    ax.annotate("Open (开盘价)", xy=(x + 0.25, o), xytext=(x + 1.2, o - 0.8),
                fontsize=10, arrowprops=dict(arrowstyle="->", color="gray"))
    ax.annotate("Low (最低价)", xy=(x, l), xytext=(x + 0.8, l - 0.7),
                fontsize=10, arrowprops=dict(arrowstyle="->", color="gray"))
    ax.text(x, h + 1.2, "Bullish (Yang/阳线)\nClose > Open", ha="center",
            fontsize=10, color="#388e3c", fontweight="bold")

    # Bearish (falling): close < open, colored red
    x = 4
    o, c, h, l = 13, 10, 14, 9.5
    ax.plot([x, x], [l, h], color="#d32f2f", lw=2)
    ax.bar(x, o - c, bottom=c, width=0.5, color="#d32f2f", edgecolor="#d32f2f")
    ax.annotate("Open (开盘价)", xy=(x - 0.25, o), xytext=(x - 1.8, o + 0.5),
                fontsize=10, arrowprops=dict(arrowstyle="->", color="gray"))
    ax.annotate("Close (收盘价)", xy=(x - 0.25, c), xytext=(x - 1.8, c - 0.8),
                fontsize=10, arrowprops=dict(arrowstyle="->", color="gray"))
    ax.text(x, h + 1.2, "Bearish (Yin/阴线)\nOpen > Close", ha="center",
            fontsize=10, color="#d32f2f", fontweight="bold")

    # Upper/lower shadow labels
    ax.annotate("Upper shadow\n(上影线)", xy=(1, 13.5), xytext=(-0.5, 14.5),
                fontsize=9, color="gray")
    ax.annotate("Lower shadow\n(下影线)", xy=(1, 9.75), xytext=(-0.5, 8.5),
                fontsize=9, color="gray")

    ax.set_xlim(-1, 6)
    ax.set_ylim(7, 16.5)
    ax.set_title("K-line (Candlestick) Anatomy / K线基础", fontsize=14, fontweight="bold")
    ax.set_xticks([])
    ax.set_ylabel("Price")
    save(fig, "01_kline_basics.png")


# =====================================================================
# 2. Inclusion relationship (包含关系)
# =====================================================================
def chart_inclusion():
    fig, axes = plt.subplots(1, 3, figsize=(16, 5))

    def draw_candle(ax, x, h, l, color="#555", width=0.4):
        mid = (h + l) / 2
        ax.bar(x, h - l, bottom=l, width=width, color=color, edgecolor=color, alpha=0.7)
        ax.plot([x, x], [l, h], color=color, lw=1.5)

    # Case A: No inclusion
    ax = axes[0]
    draw_candle(ax, 0, 12, 8, "#388e3c")
    draw_candle(ax, 1, 14, 10, "#388e3c")
    ax.set_title("No Inclusion\n(无包含关系)", fontweight="bold")
    ax.text(0.5, 6.5, "K2.high > K1.high\nK2.low > K1.low\n=> Independent", ha="center", fontsize=9)

    # Case B: Inclusion – K1 contains K2
    ax = axes[1]
    draw_candle(ax, 0, 14, 8, "#2196f3")
    draw_candle(ax, 1, 12, 9, "#ff9800")
    ax.annotate("", xy=(1, 12), xytext=(0, 14),
                arrowprops=dict(arrowstyle="<->", color="red", lw=2))
    ax.set_title("Inclusion: K1 contains K2\n(K1包含K2)", fontweight="bold")
    ax.text(0.5, 6.5, "K1.high >= K2.high\nAND K1.low <= K2.low\n=> Must merge!", ha="center", fontsize=9, color="red")

    # Case C: After merge (upward context)
    ax = axes[2]
    draw_candle(ax, 0, 14, 9, "#9c27b0")
    ax.set_title("After Merge (Upward)\n合并后 (向上)", fontweight="bold")
    ax.text(0, 6.5, "Up context: take\nmax(high), max(low)\n=> high=14, low=9", ha="center", fontsize=9, color="#9c27b0")

    for ax in axes:
        ax.set_ylim(5.5, 16)
        ax.set_xticks([0, 1])
        ax.set_xticklabels(["K1", "K2"])
        ax.set_ylabel("Price")
    axes[2].set_xticks([0])
    axes[2].set_xticklabels(["Merged"])

    fig.suptitle("Inclusion Handling (包含处理) — Lesson 62", fontsize=14, fontweight="bold")
    plt.tight_layout()
    save(fig, "02_inclusion.png")


# =====================================================================
# 3. Fractal patterns (分型)
# =====================================================================
def chart_fractals():
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    def draw_bar(ax, x, h, l, color):
        ax.bar(x, h - l, bottom=l, width=0.45, color=color, edgecolor=color, alpha=0.75)
        ax.plot([x, x], [l, h], color=color, lw=1.5)

    # Top fractal
    ax = axes[0]
    bars = [(0, 12, 8), (1, 15, 10), (2, 13, 9)]
    for x, h, l in bars:
        draw_bar(ax, x, h, l, "#d32f2f" if x == 1 else "#888")
    ax.plot(1, 15, "rv", markersize=18, zorder=5)
    ax.annotate("K2.high = max of three\nK2.low = max of three",
                xy=(1, 15), xytext=(1, 16.5), ha="center", fontsize=10,
                arrowprops=dict(arrowstyle="->", color="#d32f2f"),
                color="#d32f2f", fontweight="bold")
    ax.set_title("Top Fractal (顶分型)", fontsize=13, fontweight="bold", color="#d32f2f")
    ax.set_xticks([0, 1, 2])
    ax.set_xticklabels(["K1", "K2\n(peak)", "K3"])

    # Bottom fractal
    ax = axes[1]
    bars = [(0, 12, 8), (1, 10, 5), (2, 11, 7)]
    for x, h, l in bars:
        draw_bar(ax, x, h, l, "#388e3c" if x == 1 else "#888")
    ax.plot(1, 5, "g^", markersize=18, zorder=5)
    ax.annotate("K2.low = min of three\nK2.high = min of three",
                xy=(1, 5), xytext=(1, 3), ha="center", fontsize=10,
                arrowprops=dict(arrowstyle="->", color="#388e3c"),
                color="#388e3c", fontweight="bold")
    ax.set_title("Bottom Fractal (底分型)", fontsize=13, fontweight="bold", color="#388e3c")
    ax.set_xticks([0, 1, 2])
    ax.set_xticklabels(["K1", "K2\n(valley)", "K3"])

    for ax in axes:
        ax.set_ylim(2, 18)
        ax.set_ylabel("Price")

    fig.suptitle("Fractal Patterns (分型) — Lesson 62", fontsize=14, fontweight="bold")
    plt.tight_layout()
    save(fig, "03_fractals.png")


# =====================================================================
# 4. Bi / Stroke (笔)
# =====================================================================
def chart_bi():
    fig, ax = plt.subplots(figsize=(14, 7))

    # Simulated processed K-line highs/lows forming a zigzag
    prices_h = [10, 11, 12, 14, 13, 11, 9, 8, 9, 11, 13, 15, 14, 12, 10, 11, 13, 16]
    prices_l = [8,  9, 10, 12, 11,  9, 7, 6, 7,  9, 11, 13, 12, 10,  8,  9, 11, 14]
    n = len(prices_h)

    for i in range(n):
        o = prices_l[i] + 0.5
        c = prices_h[i] - 0.5
        color = "#388e3c" if c > o else "#d32f2f"
        ax.plot([i, i], [prices_l[i], prices_h[i]], color=color, lw=1)
        ax.bar(i, abs(c - o), bottom=min(o, c), width=0.4, color=color, alpha=0.6)

    # Mark fractals
    bottoms = [(0, prices_l[0]), (7, prices_l[7]), (14, prices_l[14])]
    tops    = [(3, prices_h[3]), (11, prices_h[11]), (17, prices_h[17])]

    for x, y in bottoms:
        ax.plot(x, y, "g^", markersize=14, zorder=5)
    for x, y in tops:
        ax.plot(x, y, "rv", markersize=14, zorder=5)

    # Draw Bi lines
    bi_points = [(0, prices_l[0]), (3, prices_h[3]), (7, prices_l[7]),
                 (11, prices_h[11]), (14, prices_l[14]), (17, prices_h[17])]
    bx = [p[0] for p in bi_points]
    by = [p[1] for p in bi_points]
    ax.plot(bx, by, "b-", lw=2.5, label="Bi (笔)", zorder=4)

    # Label each bi
    for i in range(len(bi_points) - 1):
        mx = (bi_points[i][0] + bi_points[i+1][0]) / 2
        my = (bi_points[i][1] + bi_points[i+1][1]) / 2
        direction = "UP ↑" if bi_points[i+1][1] > bi_points[i][1] else "DOWN ↓"
        color = "#388e3c" if "UP" in direction else "#d32f2f"
        ax.text(mx, my + 0.4, f"Bi {i+1}\n{direction}", ha="center",
                fontsize=9, color=color, fontweight="bold",
                bbox=dict(boxstyle="round,pad=0.2", facecolor="white", alpha=0.8))

    ax.text(0.5, -0.08,
            "Rule: Each Bi connects two adjacent alternating fractals (Top↔Bottom).\n"
            "There must be at least 1 independent K-line between the fractals of a valid Bi.",
            transform=ax.transAxes, ha="center", fontsize=10, style="italic",
            bbox=dict(boxstyle="round", facecolor="#e3f2fd"))

    ax.set_title("Bi / Stroke (笔) — Lesson 62\nThe fundamental building block of Chan Theory",
                 fontsize=14, fontweight="bold")
    ax.set_ylabel("Price")
    ax.set_xlabel("Processed K-line index (after inclusion merge)")
    ax.legend(fontsize=11)
    save(fig, "04_bi.png")


# =====================================================================
# 5. Segment (线段)
# =====================================================================
def chart_segment():
    fig, ax = plt.subplots(figsize=(14, 7))

    # Zigzag of Bi forming segments
    bi_points = [
        (0, 8), (3, 14), (5, 10), (8, 16), (10, 12),
        (13, 18), (16, 11), (19, 15), (21, 9), (24, 13), (26, 7)
    ]

    # Draw bi lines
    bx = [p[0] for p in bi_points]
    by = [p[1] for p in bi_points]
    ax.plot(bx, by, "b-", lw=1.2, alpha=0.5, label="Individual Bi (笔)")

    # Mark segment 1 (UP): Bi 1-5 (index 0-5)
    seg1_x = [bi_points[0][0], bi_points[5][0]]
    seg1_y = [bi_points[0][1], bi_points[5][1]]
    ax.plot(seg1_x, seg1_y, "m-", lw=4, alpha=0.6, label="Segment (线段)")
    ax.annotate("Segment 1 (UP)\n5 Bi, ascending",
                xy=(6, 15), fontsize=10, color="#9c27b0", fontweight="bold",
                bbox=dict(boxstyle="round", facecolor="#f3e5f5", alpha=0.8))

    # Mark segment 2 (DOWN): Bi 6-11 (index 5-10)
    seg2_x = [bi_points[5][0], bi_points[10][0]]
    seg2_y = [bi_points[5][1], bi_points[10][1]]
    ax.plot(seg2_x, seg2_y, "m-", lw=4, alpha=0.6)
    ax.annotate("Segment 2 (DOWN)\n5 Bi, descending",
                xy=(20, 9), fontsize=10, color="#9c27b0", fontweight="bold",
                bbox=dict(boxstyle="round", facecolor="#f3e5f5", alpha=0.8))

    # Mark fractals at bi endpoints
    for i, (x, y) in enumerate(bi_points):
        if i % 2 == 0:
            ax.plot(x, y, "g^", markersize=10, zorder=5)
        else:
            ax.plot(x, y, "rv", markersize=10, zorder=5)

    ax.text(0.5, -0.1,
            "A Segment must contain at least 3 Bi. It is terminated when the\n"
            "'characteristic sequence' (特征序列) forms an opposite fractal pattern.\n"
            "Case 1: direct fractal break | Case 2: gap + failed continuation (Lessons 65, 67)",
            transform=ax.transAxes, ha="center", fontsize=10, style="italic",
            bbox=dict(boxstyle="round", facecolor="#e3f2fd"))

    ax.set_title("Segments (线段) — Lessons 62, 65, 67\nA segment = at least 3 Bi in the same overall direction",
                 fontsize=14, fontweight="bold")
    ax.set_ylabel("Price")
    ax.legend(fontsize=10)
    save(fig, "05_segment.png")


# =====================================================================
# 6. Central Hub (中枢)
# =====================================================================
def chart_hub():
    fig, ax = plt.subplots(figsize=(14, 8))

    # Three Bi that overlap → forming a hub
    bi_points = [(0, 8), (3, 15), (5, 10), (8, 14), (10, 9), (13, 16)]
    bx = [p[0] for p in bi_points]
    by = [p[1] for p in bi_points]
    ax.plot(bx, by, "b-", lw=2, alpha=0.7, label="Bi sequence")

    for i, (x, y) in enumerate(bi_points):
        if i % 2 == 0:
            ax.plot(x, y, "g^", markersize=12, zorder=5)
        else:
            ax.plot(x, y, "rv", markersize=12, zorder=5)

    # Hub zone
    ZG = min(15, 14)  # = 14
    ZD = max(10, 9)   # = 10
    GG = max(15, 14, 16)  # = 16
    DD = min(8, 10, 9)    # = 8

    # Hub rectangle [ZD, ZG]
    rect = mpatches.Rectangle((0, ZD), 13, ZG - ZD,
                               linewidth=2.5, edgecolor="#ff9800",
                               facecolor="#fff3e0", alpha=0.5)
    ax.add_patch(rect)

    # Extended zone [DD, GG]
    rect2 = mpatches.Rectangle((0, DD), 13, GG - DD,
                                linewidth=1, edgecolor="#ff9800",
                                facecolor="none", linestyle="--", alpha=0.5)
    ax.add_patch(rect2)

    # Labels
    ax.annotate("ZG = min(g1, g2) = 14", xy=(13.5, ZG), fontsize=11, color="#e65100", fontweight="bold")
    ax.annotate("ZD = max(d1, d2) = 10", xy=(13.5, ZD), fontsize=11, color="#e65100", fontweight="bold")
    ax.annotate("GG = max(all highs) = 16", xy=(13.5, GG), fontsize=10, color="#999")
    ax.annotate("DD = min(all lows) = 8",  xy=(13.5, DD), fontsize=10, color="#999")

    ax.fill_between([0, 13], ZD, ZG, alpha=0.15, color="#ff9800")

    ax.text(6.5, 12, "Hub Zone (中枢)\n[ZD, ZG]", ha="center", fontsize=14,
            fontweight="bold", color="#e65100",
            bbox=dict(boxstyle="round", facecolor="white", alpha=0.9))

    ax.text(0.5, -0.12,
            "Central Hub = overlapping price range of at least 3 consecutive Bi.\n"
            "ZG = min(high of 1st entering, high of 1st leaving) — top of overlap zone\n"
            "ZD = max(low of 1st entering, low of 1st leaving) — bottom of overlap zone\n"
            "GG = highest point, DD = lowest point  (Lessons 17, 20, 24)",
            transform=ax.transAxes, ha="center", fontsize=10, style="italic",
            bbox=dict(boxstyle="round", facecolor="#fff3e0"))

    ax.set_title("Central Hub (中枢) — Lessons 17, 20, 24\nThe core structure of Chan Theory",
                 fontsize=14, fontweight="bold")
    ax.set_ylabel("Price")
    ax.set_ylim(5, 20)
    ax.legend()
    save(fig, "06_hub.png")


# =====================================================================
# 7. Trend vs Consolidation
# =====================================================================
def chart_trend_vs_consolidation():
    fig, axes = plt.subplots(1, 2, figsize=(16, 7))

    # Uptrend: 2 ascending hubs
    ax = axes[0]
    # Hub 1
    rect1 = mpatches.Rectangle((0, 10), 5, 3, lw=2, ec="#ff9800", fc="#fff3e0", alpha=0.5)
    ax.add_patch(rect1)
    ax.text(2.5, 11.5, "Hub 1", ha="center", fontsize=11, fontweight="bold", color="#e65100")

    # Hub 2 (higher)
    rect2 = mpatches.Rectangle((6, 15), 5, 3, lw=2, ec="#ff9800", fc="#fff3e0", alpha=0.5)
    ax.add_patch(rect2)
    ax.text(8.5, 16.5, "Hub 2", ha="center", fontsize=11, fontweight="bold", color="#e65100")

    # Zigzag through both
    pts = [(0, 10), (2, 13), (3.5, 11), (5.5, 15), (7, 14), (9, 18), (10.5, 15.5)]
    ax.plot([p[0] for p in pts], [p[1] for p in pts], "b-", lw=2)
    ax.annotate("Hub2.ZD > Hub1.ZG\n= Non-overlapping\n=> UPTREND",
                xy=(5.5, 14), fontsize=11, color="#388e3c", fontweight="bold",
                bbox=dict(boxstyle="round", facecolor="#e8f5e9"))
    ax.set_title("Uptrend (上涨趋势)\n2+ ascending, non-overlapping hubs", fontweight="bold", color="#388e3c")
    ax.set_ylim(7, 21)

    # Consolidation: single hub with oscillation
    ax = axes[1]
    rect = mpatches.Rectangle((0, 10), 10, 4, lw=2, ec="#ff9800", fc="#fff3e0", alpha=0.5)
    ax.add_patch(rect)
    ax.text(5, 12, "Single Hub", ha="center", fontsize=11, fontweight="bold", color="#e65100")

    pts = [(0, 11), (2, 14), (3.5, 10.5), (5.5, 13.5), (7, 10), (9, 14), (10, 11)]
    ax.plot([p[0] for p in pts], [p[1] for p in pts], "b-", lw=2)
    ax.annotate("Only 1 hub, price\noscillates within it\n=> CONSOLIDATION (盘整)",
                xy=(5, 8), fontsize=11, color="#ff9800", fontweight="bold",
                bbox=dict(boxstyle="round", facecolor="#fff3e0"))
    ax.set_title("Consolidation (盘整)\nSingle hub, no trend", fontweight="bold", color="#ff9800")
    ax.set_ylim(7, 18)

    for ax in axes:
        ax.set_ylabel("Price")
        ax.set_xlabel("Time")

    fig.suptitle("Trend vs Consolidation — Lesson 17\n\"No Trend, No Divergence\" (没有趋势, 没有背驰)",
                 fontsize=14, fontweight="bold")
    plt.tight_layout()
    save(fig, "07_trend_vs_consolidation.png")


# =====================================================================
# 8. Divergence (背驰) & MACD
# =====================================================================
def chart_divergence():
    fig, axes = plt.subplots(2, 1, figsize=(14, 9), gridspec_kw={"height_ratios": [2, 1]})

    ax1, ax2 = axes

    # Price: two down legs where second makes new low
    x = np.arange(30)
    # Simulated price path
    price = np.array([
        20, 19, 18.5, 17, 16, 15, 14, 13, 14.5, 16, 17.5, 18, 17, 16,
        15.5, 16.5, 17, 16, 15, 14.5, 13.5, 12.5, 12, 11.5, 12, 13, 14, 15, 14, 13
    ])

    ax1.plot(x, price, "b-", lw=2)
    ax1.fill_between(x[:8], price[:8], alpha=0.15, color="red", label="Down move A")
    ax1.fill_between(x[16:24], price[16:24], alpha=0.15, color="orange", label="Down move C")

    # Arrows showing new low
    ax1.annotate("Low A = 13", xy=(7, 13), fontsize=10, color="red",
                 arrowprops=dict(arrowstyle="->"))
    ax1.annotate("Low C = 11.5  (NEW LOW!)", xy=(23, 11.5), fontsize=10, color="orange",
                 arrowprops=dict(arrowstyle="->"), xytext=(20, 9.5))

    ax1.set_title("Top Divergence (顶背驰) — Lesson 15", fontsize=13, fontweight="bold")
    ax1.set_ylabel("Price")
    ax1.legend()

    # MACD: second area smaller
    macd_a = np.array([0, -0.5, -1.2, -1.8, -2.2, -2.5, -2.0, -1.0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0])
    macd_c = np.array([0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, -0.3, -0.8, -1.2, -1.5, -1.3, -0.8, -0.3, 0, 0, 0, 0, 0, 0])
    macd = macd_a + macd_c

    colors = ["#4caf50" if h >= 0 else "#f44336" for h in macd]
    ax2.bar(x, macd, color=colors, width=0.7, alpha=0.7)

    # Area labels
    ax2.annotate("MACD Area A\n= LARGE", xy=(4, -2.5), fontsize=11,
                 color="red", fontweight="bold",
                 bbox=dict(facecolor="white", alpha=0.8))
    ax2.annotate("MACD Area C\n= SMALL", xy=(19, -1.5), fontsize=11,
                 color="orange", fontweight="bold",
                 bbox=dict(facecolor="white", alpha=0.8))

    ax2.text(15, 0.8, "Price makes NEW LOW but MACD area is SMALLER\n=> DIVERGENCE (背驰) => Reversal imminent!",
             fontsize=11, color="#d32f2f", fontweight="bold",
             bbox=dict(boxstyle="round", facecolor="#ffebee"))
    ax2.set_ylabel("MACD Histogram")
    ax2.set_xlabel("Time")
    ax2.axhline(0, color="gray", lw=0.5)

    plt.tight_layout()
    save(fig, "08_divergence.png")


# =====================================================================
# 9. Three classes of buy/sell points
# =====================================================================
def chart_buy_sell_points():
    fig, ax = plt.subplots(figsize=(16, 9))

    # Simulate a down-trend → reversal → up-trend with hubs
    pts = [
        (0, 20), (2, 17), (4, 19), (6, 14), (8, 17),
        (10, 11), (12, 15), (14, 12), (16, 14),  # Hub
        (18, 10), (20, 16), (22, 13), (24, 18),
        (26, 15), (28, 20)
    ]

    px = [p[0] for p in pts]
    py = [p[1] for p in pts]
    ax.plot(px, py, "b-", lw=2, alpha=0.6)

    # Mark fractals
    for i, (x, y) in enumerate(pts):
        if i % 2 == 0:
            is_top = (y > pts[i-1][1]) if i > 0 else False
            marker = "rv" if is_top else "g^"
            ax.plot(x, y, marker, markersize=8, zorder=4)

    # Hub rectangle
    hub_rect = mpatches.Rectangle((10, 12), 8, 3, lw=2, ec="#ff9800",
                                   fc="#fff3e0", alpha=0.4)
    ax.add_patch(hub_rect)
    ax.text(14, 12.3, "Hub (中枢)\n[ZD=12, ZG=15]", ha="center", fontsize=10,
            color="#e65100", fontweight="bold")

    # B1 (1st class buy) - divergence at bottom
    ax.plot(18, 10, "g^", markersize=20, zorder=6, markeredgecolor="black", markeredgewidth=1)
    ax.annotate("B1 — 1st Buy Point (第一类买点)\nDivergence: price new low,\nbut MACD area smaller",
                xy=(18, 10), xytext=(20, 6.5), fontsize=10, color="#388e3c", fontweight="bold",
                arrowprops=dict(arrowstyle="->", color="#388e3c", lw=2),
                bbox=dict(boxstyle="round", facecolor="#e8f5e9"))

    # B2 (2nd class buy) - pullback after B1
    ax.plot(22, 13, "g^", markersize=16, zorder=6, markeredgecolor="black", markeredgewidth=1)
    ax.annotate("B2 — 2nd Buy (第二类买点)\nPullback does NOT break\nbelow B1's low (10)",
                xy=(22, 13), xytext=(24.5, 9), fontsize=10, color="#66bb6a", fontweight="bold",
                arrowprops=dict(arrowstyle="->", color="#66bb6a", lw=2),
                bbox=dict(boxstyle="round", facecolor="#e8f5e9"))

    # B3 (3rd class buy) - retest doesn't break ZG
    ax.plot(26, 15, "g^", markersize=13, zorder=6, markeredgecolor="black", markeredgewidth=1)
    ax.annotate("B3 — 3rd Buy (第三类买点)\nAfter leaving hub upward,\npullback stays above ZG (15)",
                xy=(26, 15), xytext=(24, 21), fontsize=10, color="#a5d6a7", fontweight="bold",
                arrowprops=dict(arrowstyle="->", color="#a5d6a7", lw=2),
                bbox=dict(boxstyle="round", facecolor="#e8f5e9"))

    ax.axhline(y=15, color="#ff9800", ls="--", alpha=0.4, label="ZG")
    ax.axhline(y=12, color="#ff9800", ls="--", alpha=0.4, label="ZD")

    ax.text(0.5, -0.08,
            "B1: Strongest reversal signal (divergence). B2: Confirmation (pullback holds above B1).\n"
            "B3: Breakout confirmation (retest stays above hub's ZG). Sell points are exact mirrors. (Lessons 15, 17, 20)",
            transform=ax.transAxes, ha="center", fontsize=10, style="italic",
            bbox=dict(boxstyle="round", facecolor="#e3f2fd"))

    ax.set_title("Three Classes of Buy Points (三类买点) — Lessons 15, 17, 20",
                 fontsize=14, fontweight="bold")
    ax.set_ylabel("Price")
    ax.set_ylim(5, 23)
    save(fig, "09_buy_sell_points.png")


# =====================================================================
# 10. Multi-level analysis & interval nesting
# =====================================================================
def chart_multi_level():
    fig, axes = plt.subplots(3, 1, figsize=(14, 10), sharex=False)

    # Weekly level
    ax = axes[0]
    pts_w = [(0, 20), (4, 35), (8, 25), (12, 40)]
    ax.plot([p[0] for p in pts_w], [p[1] for p in pts_w], "b-", lw=3)
    rect = mpatches.Rectangle((0, 25), 8, 10, lw=2, ec="#ff9800", fc="#fff3e0", alpha=0.4)
    ax.add_patch(rect)
    ax.set_title("Weekly (周线) — big picture", fontweight="bold")
    ax.annotate("Divergence zone\n(zoom in!)",
                xy=(8, 25), xytext=(9, 20), fontsize=10, color="red", fontweight="bold",
                arrowprops=dict(arrowstyle="->", color="red", lw=2))

    # Daily level
    ax = axes[1]
    pts_d = [(0, 28), (3, 35), (5, 30), (7, 33), (9, 26), (11, 30), (13, 25)]
    ax.plot([p[0] for p in pts_d], [p[1] for p in pts_d], "b-", lw=2)
    rect = mpatches.Rectangle((3, 26), 8, 7, lw=2, ec="#ff9800", fc="#fff3e0", alpha=0.4)
    ax.add_patch(rect)
    ax.set_title("Daily (日线) — zoomed into weekly divergence zone", fontweight="bold")
    ax.annotate("Sub-level divergence\n(zoom in further!)",
                xy=(13, 25), xytext=(10, 22), fontsize=10, color="red", fontweight="bold",
                arrowprops=dict(arrowstyle="->", color="red", lw=2))

    # 30-min level
    ax = axes[2]
    pts_m = [(0, 27), (3, 30), (5, 26), (7, 28), (9, 25), (11, 27), (13, 24.5)]
    ax.plot([p[0] for p in pts_m], [p[1] for p in pts_m], "b-", lw=1.5)
    ax.plot(13, 24.5, "g^", markersize=16, zorder=5)
    ax.annotate("EXACT turning point!\n(B1 at smallest level)",
                xy=(13, 24.5), xytext=(9, 22), fontsize=10, color="#388e3c",
                fontweight="bold",
                arrowprops=dict(arrowstyle="->", color="#388e3c", lw=2),
                bbox=dict(boxstyle="round", facecolor="#e8f5e9"))
    ax.set_title("30-minute (30分钟) — pinpoint the turn", fontweight="bold")

    for ax in axes:
        ax.set_ylabel("Price")

    fig.suptitle("Interval Nesting (区间套) & Multi-Level Analysis — Lessons 37, 52, 81\n"
                 "Zoom from higher to lower timeframes to find the EXACT turning point",
                 fontsize=13, fontweight="bold")
    plt.tight_layout()
    save(fig, "10_multi_level.png")


# =====================================================================
# 11. MA Kisses
# =====================================================================
def chart_ma_kisses():
    fig, axes = plt.subplots(1, 3, figsize=(16, 5))

    x = np.linspace(0, 10, 100)

    # Fly kiss
    ax = axes[0]
    ma_short = np.sin(x) * 2 + 10
    ma_long = np.sin(x * 0.8) * 1.5 + 10
    ax.plot(x, ma_short, "b-", lw=2, label="Short MA")
    ax.plot(x, ma_long, "r-", lw=2, label="Long MA")
    ax.set_title("Fly Kiss (飞吻)\nMAs barely approach,\nno real cross", fontweight="bold")
    ax.legend(fontsize=8)

    # Lip kiss
    ax = axes[1]
    ma_short = np.sin(x * 1.1) * 2 + 10
    ma_long = np.sin(x * 0.9) * 2 + 10
    ax.plot(x, ma_short, "b-", lw=2, label="Short MA")
    ax.plot(x, ma_long, "r-", lw=2, label="Long MA")
    cross_idx = np.where(np.diff(np.sign(ma_short - ma_long)))[0]
    for ci in cross_idx[:2]:
        ax.plot(x[ci], ma_short[ci], "ko", markersize=8)
    ax.set_title("Lip Kiss (唇吻)\nMAs touch briefly\n(1-2 bar crossing)", fontweight="bold")
    ax.legend(fontsize=8)

    # Wet kiss
    ax = axes[2]
    ma_short = np.sin(x * 0.5) * 0.3 + 10 + np.random.RandomState(42).randn(100) * 0.1
    ma_long = np.sin(x * 0.5) * 0.3 + 10 + np.random.RandomState(43).randn(100) * 0.1
    ax.plot(x, ma_short, "b-", lw=2, label="Short MA")
    ax.plot(x, ma_long, "r-", lw=2, label="Long MA")
    ax.fill_between(x, ma_short, ma_long, alpha=0.2, color="purple")
    ax.set_title("Wet Kiss (湿吻)\nMAs intertwine for many bars\n=> Major reversal signal!", fontweight="bold", color="#d32f2f")
    ax.legend(fontsize=8)

    for ax in axes:
        ax.set_ylabel("Price")

    fig.suptitle("MA Kiss Classification (均线吻) — Lesson 15", fontsize=14, fontweight="bold")
    plt.tight_layout()
    save(fig, "11_ma_kisses.png")


# =====================================================================
# 12. Complete pipeline overview
# =====================================================================
def chart_pipeline():
    fig, ax = plt.subplots(figsize=(16, 6))
    ax.axis("off")

    steps = [
        ("Raw K-lines\n(原始K线)", "#e3f2fd"),
        ("Inclusion\nMerge\n(包含处理)", "#e8f5e9"),
        ("Fractals\n(分型识别)", "#fff3e0"),
        ("Bi / Strokes\n(笔)", "#fce4ec"),
        ("Segments\n(线段)", "#f3e5f5"),
        ("Hubs\n(中枢)", "#fff8e1"),
        ("Divergence\n(背驰)", "#e0f2f1"),
        ("Buy/Sell\nPoints\n(买卖点)", "#fbe9e7"),
        ("Strategy\n(操作建议)", "#e8eaf6"),
    ]

    box_w = 0.09
    gap = 0.015
    start_x = 0.03

    for i, (label, color) in enumerate(steps):
        x = start_x + i * (box_w + gap)
        rect = mpatches.FancyBboxPatch((x, 0.3), box_w, 0.4,
                                        boxstyle="round,pad=0.01",
                                        facecolor=color, edgecolor="#555",
                                        linewidth=1.5)
        ax.add_patch(rect)
        ax.text(x + box_w / 2, 0.5, label, ha="center", va="center",
                fontsize=9, fontweight="bold",
                transform=ax.transAxes)
        if i < len(steps) - 1:
            ax.annotate("", xy=(x + box_w + gap * 0.3, 0.5),
                        xytext=(x + box_w + gap * 0.05, 0.5),
                        xycoords="axes fraction", textcoords="axes fraction",
                        arrowprops=dict(arrowstyle="->", color="#333", lw=2))

    # Lesson references
    lessons = ["", "L62", "L62,82", "L62", "L62,65,67", "L17,20,24", "L15,25", "L15,17,20", "L33,38,108"]
    for i, ref in enumerate(lessons):
        if ref:
            x = start_x + i * (box_w + gap)
            ax.text(x + box_w / 2, 0.22, ref, ha="center", fontsize=7, color="gray",
                    transform=ax.transAxes)

    ax.set_title("Chan Theory Analysis Pipeline — Complete Processing Flow",
                 fontsize=14, fontweight="bold", pad=20)
    save(fig, "12_pipeline.png")


# =====================================================================
# 13. Hub extension, expansion, migration
# =====================================================================
def chart_hub_advanced():
    fig, axes = plt.subplots(1, 3, figsize=(18, 6))

    # Extension
    ax = axes[0]
    rect = mpatches.Rectangle((0, 10), 4, 3, lw=2, ec="#ff9800", fc="#fff3e0", alpha=0.5)
    ax.add_patch(rect)
    # Extended part
    rect2 = mpatches.Rectangle((4, 10), 4, 3, lw=2, ec="#ff9800", fc="#fff3e0", alpha=0.3, ls="--")
    ax.add_patch(rect2)
    pts = [(0, 10), (1, 13), (2, 10.5), (3, 12.5), (4, 10.5), (5, 13), (6, 11), (7, 12.5), (8, 10)]
    ax.plot([p[0] for p in pts], [p[1] for p in pts], "b-", lw=1.5)
    ax.set_title("Hub Extension (中枢延伸)\nLesson 25: 6+ elements\n=> same hub grows", fontweight="bold")
    ax.text(4, 9, "Original → Extended", ha="center", fontsize=9, color="#e65100")
    ax.set_ylim(8, 15)

    # Expansion (two hubs merge)
    ax = axes[1]
    rect1 = mpatches.Rectangle((0, 10), 3, 3, lw=2, ec="#2196f3", fc="#e3f2fd", alpha=0.5)
    ax.add_patch(rect1)
    rect2 = mpatches.Rectangle((4, 11), 3, 3, lw=2, ec="#2196f3", fc="#e3f2fd", alpha=0.5)
    ax.add_patch(rect2)
    # Merged
    rect3 = mpatches.Rectangle((0, 10), 7, 4, lw=3, ec="#e91e63", fc="#fce4ec", alpha=0.3)
    ax.add_patch(rect3)
    ax.text(3.5, 15.5, "Overlapping hubs merge\n=> Higher-level hub!", ha="center",
            fontsize=10, color="#e91e63", fontweight="bold")
    ax.set_title("Hub Expansion (中枢扩展)\nLesson 36: overlapping hubs\nmerge into higher level", fontweight="bold")
    ax.set_ylim(8, 17)

    # Migration
    ax = axes[2]
    for i, (x, zd, zg) in enumerate([(0, 10, 13), (4, 13, 16), (8, 16, 19)]):
        rect = mpatches.Rectangle((x, zd), 3, zg - zd, lw=2, ec="#ff9800", fc="#fff3e0", alpha=0.5)
        ax.add_patch(rect)
        ax.text(x + 1.5, (zd + zg) / 2, f"Hub {i+1}", ha="center", fontsize=10, fontweight="bold")
    ax.annotate("", xy=(3.5, 15), xytext=(3.5, 12),
                arrowprops=dict(arrowstyle="->", color="#388e3c", lw=3))
    ax.annotate("", xy=(7.5, 18), xytext=(7.5, 15),
                arrowprops=dict(arrowstyle="->", color="#388e3c", lw=3))
    ax.text(5.5, 20.5, "Hubs migrate upward\n=> Strong uptrend!", ha="center",
            fontsize=10, color="#388e3c", fontweight="bold")
    ax.set_title("Hub Migration (中枢移动)\nLesson 70: non-overlapping hubs\nmoving in one direction", fontweight="bold")
    ax.set_ylim(8, 22)

    for ax in axes:
        ax.set_ylabel("Price")

    plt.tight_layout()
    save(fig, "13_hub_advanced.png")


# =====================================================================
# 14. Post-divergence outcomes
# =====================================================================
def chart_post_divergence():
    fig, axes = plt.subplots(1, 3, figsize=(16, 6))

    for idx, (ax, title, color, desc) in enumerate(zip(axes, [
        "Level Expansion\n(级别扩展)", "Consolidation\n(更大级别盘整)", "Reverse Trend\n(反向趋势)"
    ], ["#f44336", "#ff9800", "#388e3c"], [
        "Weakest rebound:\nstays below DD\nof last hub",
        "Medium rebound:\nre-enters last hub\n[ZD, ZG] zone",
        "Strongest reversal:\nbreaks through\nthe entire hub"
    ])):
        # Hub
        rect = mpatches.Rectangle((2, 12), 4, 4, lw=2, ec="#ff9800", fc="#fff3e0", alpha=0.4)
        ax.add_patch(rect)
        ax.text(4, 14, "Last Hub", ha="center", fontsize=10, fontweight="bold", color="#e65100")

        # Down trend into divergence
        ax.plot([0, 2, 4, 6, 7], [18, 16, 15, 13, 11], "b-", lw=2)
        ax.plot(7, 11, "g^", markersize=14, zorder=5)
        ax.text(7, 10.2, "B1", fontsize=10, color="#388e3c", fontweight="bold", ha="center")

        if idx == 0:  # Level expansion - weak bounce
            ax.plot([7, 9], [11, 11.5], color=color, lw=2.5)
            ax.annotate("Bounce barely\nreaches DD", xy=(9, 11.5), fontsize=9, color=color)
        elif idx == 1:  # Consolidation
            ax.plot([7, 9], [11, 14], color=color, lw=2.5)
            ax.annotate("Re-enters hub\nzone", xy=(9, 14), fontsize=9, color=color)
        else:  # Reverse trend
            ax.plot([7, 9], [11, 17], color=color, lw=2.5)
            ax.annotate("Breaks above\nhub entirely!", xy=(9, 17), fontsize=9, color=color)

        ax.set_title(title, fontsize=12, fontweight="bold", color=color)
        ax.text(4, 8.5, desc, ha="center", fontsize=9, style="italic",
                bbox=dict(boxstyle="round", facecolor="lightyellow"))
        ax.set_ylim(7, 20)
        ax.set_ylabel("Price")

    fig.suptitle("Three Outcomes After Divergence (背驰后三种走势) — Lesson 29",
                 fontsize=14, fontweight="bold")
    plt.tight_layout()
    save(fig, "14_post_divergence.png")


# =====================================================================
# Generate all charts
# =====================================================================
if __name__ == "__main__":
    print("Generating tutorial charts...")
    chart_kline_basics()
    chart_inclusion()
    chart_fractals()
    chart_bi()
    chart_segment()
    chart_hub()
    chart_trend_vs_consolidation()
    chart_divergence()
    chart_buy_sell_points()
    chart_multi_level()
    chart_ma_kisses()
    chart_pipeline()
    chart_hub_advanced()
    chart_post_divergence()
    print("Done! All charts saved to docs/images/")
