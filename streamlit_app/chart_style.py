"""Centralized chart styling for the Streamlit app.

Both matplotlib and plotly chart wrappers live here so every chart in
every page shares one visual language.
"""

from __future__ import annotations

import matplotlib as mpl
import matplotlib.pyplot as plt
import plotly.graph_objects as go

# ============================================================
# BRAND PALETTE
# ============================================================
NAVY       = "#0E2F56"   # Deep navy — strongest emphasis, primary fills
BLUE       = "#1F4E79"   # Brand primary
MID_BLUE   = "#5B8FBF"   # Mid blue for secondary bars
LIGHT_BLUE = "#B8D4EC"   # Pale blue for tertiary / background fills
ACCENT     = "#F2A900"   # Warm orange — "your pipeline" / highlight
SUCCESS    = "#2E7D5B"   # Muted green — positive deltas, inflows
DANGER     = "#C8443C"   # Muted red — negative deltas, outflows
NEUTRAL    = "#6B7280"   # Cool gray for axes, gridlines, labels
TEXT_DARK  = "#1F2937"   # Almost-black for primary text
TEXT_MUTED = "#6B7280"   # Gray for secondary text
PANEL_BG   = "#FAFAFB"   # Very soft off-white panel background


# ============================================================
# MATPLOTLIB SETUP
# ============================================================
def apply_matplotlib_theme() -> None:
    """Apply the brand visual identity to all matplotlib charts globally."""
    mpl.rcParams.update({
        "font.family":        "DejaVu Sans",
        "font.size":          11,
        "axes.titlesize":     13,
        "axes.titleweight":   "600",
        "axes.labelsize":     11,
        "axes.labelweight":   "500",
        "axes.labelcolor":    TEXT_DARK,
        "xtick.labelsize":    10,
        "ytick.labelsize":    10,
        "xtick.color":        TEXT_MUTED,
        "ytick.color":        TEXT_MUTED,
        "legend.fontsize":    10,
        "axes.spines.top":    False,
        "axes.spines.right":  False,
        "axes.spines.left":   True,
        "axes.spines.bottom": True,
        "axes.edgecolor":     "#D1D5DB",
        "axes.linewidth":     0.8,
        "grid.color":         "#E5E7EB",
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
    """Apply final polish to a matplotlib axes object."""
    if title:
        ax.set_title(title, loc="left", pad=14, color=TEXT_DARK)
    if xlabel:
        ax.set_xlabel(xlabel)
    if ylabel:
        ax.set_ylabel(ylabel)
    for spine in ax.spines.values():
        spine.set_color("#D1D5DB")


def bar_gradient(n: int, lo: str = LIGHT_BLUE, hi: str = NAVY) -> list:
    """Return n matplotlib RGB tuples interpolated from lo to hi (dark = last)."""
    def _rgb(h: str) -> tuple:
        h = h.lstrip("#")
        return tuple(int(h[i:i+2], 16) / 255.0 for i in (0, 2, 4))

    lo_rgb, hi_rgb = _rgb(lo), _rgb(hi)
    colors = []
    for i in range(n):
        t = i / max(n - 1, 1)
        colors.append(tuple(lo_rgb[c] + t * (hi_rgb[c] - lo_rgb[c]) for c in range(3)))
    return colors


# ============================================================
# PLOTLY LAYOUT TEMPLATE
# ============================================================
PLOTLY_LAYOUT = dict(
    font=dict(family="Inter, -apple-system, sans-serif", size=12, color=TEXT_DARK),
    title=dict(
        font=dict(size=15, color=TEXT_DARK),
        x=0.01, xanchor="left",
        pad=dict(t=10, b=20),
    ),
    paper_bgcolor=PANEL_BG,
    plot_bgcolor=PANEL_BG,
    xaxis=dict(
        gridcolor="#E5E7EB", gridwidth=0.6,
        linecolor="#D1D5DB", linewidth=0.8,
        tickfont=dict(color=TEXT_MUTED, size=11),
        title_font=dict(color=TEXT_DARK, size=11),
        zeroline=False,
    ),
    yaxis=dict(
        gridcolor="#E5E7EB", gridwidth=0.6,
        linecolor="#D1D5DB", linewidth=0.8,
        tickfont=dict(color=TEXT_MUTED, size=11),
        title_font=dict(color=TEXT_DARK, size=11),
        zeroline=False,
    ),
    margin=dict(l=60, r=30, t=60, b=60),
    hoverlabel=dict(
        bgcolor="white",
        bordercolor="#D1D5DB",
        font=dict(color=TEXT_DARK, size=12),
    ),
    showlegend=False,
)

PLOTLY_CONFIG = dict(
    displayModeBar=False,
    responsive=True,
)


def style_plotly_fig(fig: go.Figure, title: str | None = None, height: int = 380) -> go.Figure:
    """Apply standard layout to a plotly figure and return it."""
    fig.update_layout(**PLOTLY_LAYOUT)
    if title:
        fig.update_layout(title=title)
    fig.update_layout(height=height)
    return fig
