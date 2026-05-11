"""Centralized chart styling — DARK MODE.

Both matplotlib and plotly chart wrappers live here so every chart in
every page shares one visual language.
"""
from __future__ import annotations

import matplotlib as mpl
import matplotlib.pyplot as plt
import plotly.graph_objects as go

# ============================================================
# DARK THEME PALETTE
# ============================================================
# Surfaces
PAGE_BG    = "#0E1117"   # main area
PANEL_BG   = "#1A1F2E"   # chart panel — slightly lifted for hierarchy
SIDEBAR_BG = "#1A1F2E"

# Text
TEXT_LIGHT = "#F3F4F6"   # primary text
TEXT_MUTED = "#9CA3AF"   # secondary / axis labels
TEXT_DIM   = "#6B7280"   # tertiary
TEXT_DARK  = TEXT_LIGHT  # backward-compat alias — old code using TEXT_DARK still works

# Lines and borders
GRID   = "#2A3142"
BORDER = "#374151"

# Brand palette — lifted for dark-theme contrast
NAVY       = "#1E3A66"   # deep brand blue (darkest fill)
BLUE       = "#3B7BB8"   # brand primary
MID_BLUE   = "#7DA8D3"   # mid blue
LIGHT_BLUE = "#B8D4EC"   # pale blue (brightest fill on dark)
ACCENT     = "#F2A900"   # warm orange — "your pipeline" / highlight
SUCCESS    = "#4CAF7B"   # green — positive deltas, inflows
DANGER     = "#E55D55"   # red — negative deltas, outflows
NEUTRAL    = "#9CA3AF"   # gray for reference lines


# ============================================================
# MATPLOTLIB SETUP
# ============================================================
def apply_matplotlib_theme() -> None:
    """Apply the dark-mode brand identity to all matplotlib charts globally."""
    mpl.rcParams.update({
        "font.family":        "DejaVu Sans",
        "font.size":          11,
        "axes.titlesize":     13,
        "axes.titleweight":   "600",
        "axes.labelsize":     11,
        "axes.labelweight":   "500",
        "axes.labelcolor":    TEXT_LIGHT,
        "xtick.labelsize":    10,
        "ytick.labelsize":    10,
        "xtick.color":        TEXT_MUTED,
        "ytick.color":        TEXT_MUTED,
        "text.color":         TEXT_LIGHT,
        "legend.fontsize":    10,
        "legend.labelcolor":  TEXT_LIGHT,
        "axes.spines.top":    False,
        "axes.spines.right":  False,
        "axes.spines.left":   True,
        "axes.spines.bottom": True,
        "axes.edgecolor":     BORDER,
        "axes.linewidth":     0.8,
        "grid.color":         GRID,
        "grid.linewidth":     0.6,
        "grid.alpha":         0.7,
        "axes.grid":          True,
        "axes.grid.axis":     "y",
        "axes.axisbelow":     True,
        "figure.facecolor":   PANEL_BG,
        "axes.facecolor":     PANEL_BG,
        "savefig.facecolor":  PANEL_BG,
        "figure.dpi":         100,
        "savefig.dpi":        200,
        "figure.autolayout":  True,
    })


def style_matplotlib_axes(ax, title=None, xlabel=None, ylabel=None) -> None:
    """Apply final dark-mode polish to a matplotlib axes object."""
    if title:
        ax.set_title(title, loc="left", pad=14, color=TEXT_LIGHT)
    if xlabel:
        ax.set_xlabel(xlabel)
    if ylabel:
        ax.set_ylabel(ylabel)
    for spine in ax.spines.values():
        spine.set_color(BORDER)


def bar_gradient(n: int, lo: str = LIGHT_BLUE, hi: str = NAVY) -> list:
    """Return n matplotlib RGB tuples interpolated from lo (index 0) to hi (index n-1)."""
    def _rgb(h: str) -> tuple:
        h = h.lstrip("#")
        return tuple(int(h[idx:idx + 2], 16) / 255.0 for idx in (0, 2, 4))

    lo_rgb, hi_rgb = _rgb(lo), _rgb(hi)
    colors = []
    for step in range(n):
        t = step / max(n - 1, 1)
        colors.append(tuple(lo_rgb[c] + t * (hi_rgb[c] - lo_rgb[c]) for c in range(3)))
    return colors


# ============================================================
# PLOTLY LAYOUT TEMPLATE
# ============================================================
PLOTLY_LAYOUT = dict(
    font=dict(family="Inter, -apple-system, sans-serif", size=12, color=TEXT_LIGHT),
    # NOTE: no `title` key here — an empty title dict with no .text causes plotly JS
    # to render the literal string "undefined" on screen. Titles are applied only in
    # style_plotly_fig() when the caller supplies a non-None title string.
    paper_bgcolor=PANEL_BG,
    plot_bgcolor=PANEL_BG,
    xaxis=dict(
        gridcolor=GRID, gridwidth=0.6,
        linecolor=BORDER, linewidth=0.8,
        tickfont=dict(color=TEXT_MUTED, size=11),
        title_font=dict(color=TEXT_LIGHT, size=11),
        zeroline=False,
    ),
    yaxis=dict(
        gridcolor=GRID, gridwidth=0.6,
        linecolor=BORDER, linewidth=0.8,
        tickfont=dict(color=TEXT_MUTED, size=11),
        title_font=dict(color=TEXT_LIGHT, size=11),
        zeroline=False,
    ),
    margin=dict(l=60, r=30, t=60, b=60),
    hoverlabel=dict(
        bgcolor=PANEL_BG,
        bordercolor=BORDER,
        font=dict(color=TEXT_LIGHT, size=12),
    ),
    showlegend=False,
)

PLOTLY_CONFIG = dict(
    displayModeBar=False,
    responsive=True,
)


def style_plotly_fig(fig: go.Figure, title: str | None = None, height: int = 380) -> go.Figure:
    """Apply dark-mode standard layout to a plotly figure and return it."""
    fig.update_layout(**PLOTLY_LAYOUT)
    if title:
        fig.update_layout(title=dict(
            text=title,
            font=dict(size=15, color=TEXT_LIGHT),
            x=0.01, xanchor="left",
            pad=dict(t=10, b=20),
        ))
    else:
        # Explicitly clear any pre-existing title so plotly JS doesn't render "undefined"
        fig.update_layout(title=dict(text=""))
    fig.update_layout(height=height)
    return fig
