"""
Visualization module for NMTC application charts and maps.

All functions require matplotlib. Install with:
    pip install nmtc-application-builder[viz]
or:
    pip install matplotlib>=3.7
"""
from __future__ import annotations

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    import matplotlib.lines as mlines
    _MATPLOTLIB_AVAILABLE = True
except ImportError:
    _MATPLOTLIB_AVAILABLE = False

import numpy as np

from typing import TYPE_CHECKING

from nmtcapp.data.schema import SECTORS_BY_PRIORITY

if TYPE_CHECKING:
    from nmtcapp.core.application import Application

# ---------------------------------------------------------------------------
# Brand colors (from renderers/styles.py palette)
# ---------------------------------------------------------------------------
_PRIMARY = "#1B438C"      # deep blue
_SECONDARY = "#2E6DA4"    # medium blue
_ACCENT = "#F0A500"       # gold
_ROW_EVEN = "#EBF0FA"     # light blue
_GREEN = "#2D7D46"
_RED = "#C0392B"
_YELLOW = "#C27C0E"
_GRAY = "#6B6B6B"
_BG = "#F5F7FA"

# ---------------------------------------------------------------------------
# State centroids (lat, lon) for all 50 states + DC
# ---------------------------------------------------------------------------
_STATE_CENTROIDS: dict = {
    "AL": (32.8, -86.8), "AK": (61.4, -152.9), "AZ": (34.3, -111.1),
    "AR": (34.9, -92.4), "CA": (36.8, -119.4), "CO": (39.0, -105.5),
    "CT": (41.6, -72.7), "DE": (38.9, -75.5), "FL": (27.8, -81.6),
    "GA": (32.7, -83.4), "HI": (20.9, -157.0), "ID": (44.3, -114.5),
    "IL": (40.0, -89.2), "IN": (39.9, -86.3), "IA": (42.1, -93.5),
    "KS": (38.5, -98.4), "KY": (37.7, -84.9), "LA": (31.2, -91.8),
    "ME": (44.7, -69.4), "MD": (39.0, -76.8), "MA": (42.2, -71.5),
    "MI": (44.4, -85.4), "MN": (46.4, -93.2), "MS": (32.8, -89.7),
    "MO": (38.5, -92.5), "MT": (47.0, -110.5), "NE": (41.5, -99.9),
    "NV": (38.5, -117.2), "NH": (43.7, -71.6), "NJ": (40.1, -74.4),
    "NM": (34.5, -106.2), "NY": (42.9, -75.5), "NC": (35.6, -79.4),
    "ND": (47.5, -100.5), "OH": (40.4, -82.8), "OK": (35.6, -96.9),
    "OR": (44.6, -122.1), "PA": (40.9, -77.8), "RI": (41.7, -71.5),
    "SC": (33.8, -81.2), "SD": (44.4, -100.2), "TN": (35.9, -86.4),
    "TX": (31.1, -97.6), "UT": (39.3, -111.1), "VT": (44.0, -72.7),
    "VA": (37.8, -78.2), "WA": (47.4, -120.5), "WV": (38.6, -80.6),
    "WI": (44.3, -89.8), "WY": (43.0, -107.5), "DC": (38.9, -77.0),
}

# Distress level colors
_DISTRESS_COLORS = {
    "deep": _RED,
    "severe": _YELLOW,
    "lic": _GREEN,
    "ineligible": _GRAY,
    "unknown": _GRAY,
    None: _GRAY,
}


def _require_matplotlib() -> None:
    if not _MATPLOTLIB_AVAILABLE:
        raise ImportError(
            "matplotlib is required for visualization. Install with:\n"
            "    pip install nmtc-application-builder[viz]\n"
            "or:\n"
            "    pip install matplotlib>=3.7"
        )


def _apply_professional_style(ax: "plt.Axes") -> None:
    """Apply consistent professional styling to an axes."""
    ax.set_facecolor(_BG)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color("#CCCCCC")
    ax.spines["bottom"].set_color("#CCCCCC")
    ax.tick_params(colors="#444444", labelsize=9)
    ax.grid(axis="x", color="#E0E0E0", linewidth=0.6, linestyle="--")


# ---------------------------------------------------------------------------
# Task B.1: plot_pipeline_map
# ---------------------------------------------------------------------------

def plot_pipeline_map(application: "Application", output_path: str) -> str:
    """Plot pipeline projects as scatter dots on a simplified US map.

    Args:
        application: An Application instance (pipeline must be set).
        output_path: Path to save the PNG file.

    Returns:
        output_path (string).

    Raises:
        ImportError: If matplotlib is not installed.
    """
    _require_matplotlib()

    analysis = application.analyze()
    pipeline = list(application.pipeline)

    n_projects = len(pipeline)
    total_qei_mm = sum(p.qei_request for p in pipeline) / 1_000_000

    # Build scatter data
    np.random.seed(42)
    lats, lons, sizes, colors = [], [], [], []
    excluded_states = {"AK", "HI"}

    for project in pipeline:
        state = project.state.upper() if project.state else "XX"
        if state in excluded_states:
            continue
        centroid = _STATE_CENTROIDS.get(state)
        if centroid is None:
            continue
        lat, lon = centroid
        # Add jitter so overlapping dots are visible
        lat += np.random.uniform(-0.5, 0.5)
        lon += np.random.uniform(-0.5, 0.5)
        lats.append(lat)
        lons.append(lon)
        # Dot area proportional to QEI (in $M)
        area = max(30, (project.qei_request / 1_000_000) * 12)
        sizes.append(area)
        dlevel = project.distress_level if project.distress_level else "unknown"
        colors.append(_DISTRESS_COLORS.get(dlevel, _GRAY))

    fig, ax = plt.subplots(figsize=(12, 7))
    fig.patch.set_facecolor("white")
    ax.set_facecolor(_BG)

    # Light gray background rectangle for map area
    map_rect = mpatches.FancyBboxPatch(
        (-128, 23), 63, 27,
        boxstyle="square,pad=0",
        linewidth=1.2, edgecolor="#AAAAAA", facecolor=_BG, zorder=0,
    )
    ax.add_patch(map_rect)

    if lats:
        scatter = ax.scatter(
            lons, lats,
            s=sizes, c=colors,
            alpha=0.75, linewidths=0.6, edgecolors="white", zorder=3,
        )

    # Legend for distress levels
    legend_items = [
        mpatches.Patch(color=_RED, label="Deep Distress"),
        mpatches.Patch(color=_YELLOW, label="Severe Distress"),
        mpatches.Patch(color=_GREEN, label="LIC"),
        mpatches.Patch(color=_GRAY, label="Unknown/Other"),
    ]
    ax.legend(
        handles=legend_items,
        loc="lower left",
        fontsize=9,
        framealpha=0.9,
        edgecolor="#CCCCCC",
        title="Distress Level",
        title_fontsize=9,
    )

    # Size reference note
    ax.text(
        -127, 24.0,
        "Dot size ∝ QEI request",
        fontsize=7.5, color="#666666", style="italic",
    )

    ax.set_xlim(-128, -65)
    ax.set_ylim(23, 50)
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_edgecolor("#AAAAAA")

    ax.set_title(
        f"Pipeline Project Distribution — {n_projects} Projects, "
        f"${total_qei_mm:,.1f}MM Total QEI",
        fontsize=13, fontweight="bold", color="#222222", pad=14,
    )

    plt.tight_layout()
    fig.savefig(output_path, dpi=300, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return output_path


# ---------------------------------------------------------------------------
# Task B.2: plot_distress_heatmap
# ---------------------------------------------------------------------------

def plot_distress_heatmap(application: "Application", output_path: str) -> str:
    """Horizontal bar chart showing QEI by state colored by dominant distress level.

    Args:
        application: An Application instance (pipeline must be set).
        output_path: Path to save the PNG file.

    Returns:
        output_path (string).

    Raises:
        ImportError: If matplotlib is not installed.
    """
    _require_matplotlib()

    analysis = application.analyze()
    geo = analysis.geographic_analysis
    state_breakdown = geo.get("state_breakdown", {})

    # Build distress-by-state from pipeline
    pipeline = list(application.pipeline)
    state_distress: dict = {}
    for project in pipeline:
        state = project.state.upper() if project.state else "XX"
        dlevel = project.distress_level if project.distress_level else "unknown"
        if state not in state_distress:
            state_distress[state] = []
        state_distress[state].append(dlevel)

    def _dominant_distress(levels: list) -> str:
        priority = ["deep", "severe", "lic", "ineligible", "unknown"]
        for lvl in priority:
            if lvl in levels:
                return lvl
        return "unknown"

    def _distress_color(levels: list) -> str:
        dom = _dominant_distress(levels)
        return _DISTRESS_COLORS.get(dom, _GRAY)

    # Sort by QEI descending, top 15
    sorted_states = sorted(
        state_breakdown.items(),
        key=lambda x: x[1]["qei_dollars"],
        reverse=True,
    )[:15]

    if not sorted_states:
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.text(0.5, 0.5, "No state data available", ha="center", va="center",
                transform=ax.transAxes, fontsize=12)
        ax.set_title("QEI Deployment by State", fontsize=13, fontweight="bold")
        plt.tight_layout()
        fig.savefig(output_path, dpi=300, bbox_inches="tight", facecolor="white")
        plt.close(fig)
        return output_path

    states = [s for s, _ in sorted_states]
    qei_vals = [v["qei_dollars"] for _, v in sorted_states]
    bar_colors = [
        _distress_color(state_distress.get(s, ["unknown"])) for s in states
    ]

    fig, ax = plt.subplots(figsize=(11, max(5, len(states) * 0.55 + 1.5)))
    fig.patch.set_facecolor("white")

    bars = ax.barh(
        range(len(states)), qei_vals,
        color=bar_colors, edgecolor="white", linewidth=0.5, height=0.68,
        alpha=0.88,
    )

    # QEI dollar labels
    max_qei = max(qei_vals) if qei_vals else 1
    for i, (bar, val) in enumerate(zip(bars, qei_vals)):
        ax.text(
            val + max_qei * 0.01, i,
            f"${val / 1_000_000:.1f}M",
            va="center", ha="left", fontsize=8.5, color="#333333",
        )

    ax.set_yticks(range(len(states)))
    ax.set_yticklabels(states, fontsize=10)
    ax.set_xlabel("QEI Request ($)", fontsize=10)
    ax.invert_yaxis()

    # X-axis formatting
    ax.xaxis.set_major_formatter(
        matplotlib.ticker.FuncFormatter(lambda x, _: f"${x / 1_000_000:.0f}M")
    )

    _apply_professional_style(ax)
    ax.set_xlim(0, max_qei * 1.15)

    # Legend for distress
    legend_items = [
        mpatches.Patch(color=_RED, label="Deep Distress"),
        mpatches.Patch(color=_YELLOW, label="Severe Distress"),
        mpatches.Patch(color=_GREEN, label="LIC"),
        mpatches.Patch(color=_GRAY, label="Other/Unknown"),
    ]
    ax.legend(
        handles=legend_items,
        loc="lower right",
        fontsize=8,
        framealpha=0.9,
        edgecolor="#CCCCCC",
        title="Dominant Distress",
        title_fontsize=8,
    )

    ax.set_title(
        "QEI Deployment by State",
        fontsize=13, fontweight="bold", color="#222222", pad=12,
    )

    plt.tight_layout()
    fig.savefig(output_path, dpi=300, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return output_path


# ---------------------------------------------------------------------------
# Task B.3: plot_sector_distribution
# ---------------------------------------------------------------------------

def plot_sector_distribution(application: "Application", output_path: str) -> str:
    """Horizontal bar chart of QEI by sector, color-coded by priority.

    Args:
        application: An Application instance (pipeline must be set).
        output_path: Path to save the PNG file.

    Returns:
        output_path (string).

    Raises:
        ImportError: If matplotlib is not installed.
    """
    _require_matplotlib()

    analysis = application.analyze()
    sector_analysis = analysis.sector_analysis
    sector_breakdown = sector_analysis.get("sector_breakdown", {})
    total_qei = sector_analysis.get("total_qei", 1.0) or 1.0

    # READ THE TIERS (FIX-2 G-5 sweep). _MED_PRIORITY was hand-typed as
    # {small_business, mixed_use} and had already drifted from schema, which
    # classes community_facility and clean_energy medium too. Those two bars
    # took the LOW-priority grey under a legend announcing "Medium Priority
    # (Small Business/Mixed Use)", while the Streamlit page rendering the same
    # pipeline printed "Priority: Medium" for them in the table alongside.
    _HIGH_PRIORITY = SECTORS_BY_PRIORITY["high"]
    _MED_PRIORITY = SECTORS_BY_PRIORITY["medium"]

    # Sort sectors by QEI descending
    sorted_sectors = sorted(
        sector_breakdown.items(),
        key=lambda x: x[1]["qei_dollars"],
        reverse=True,
    )

    if not sorted_sectors:
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.text(0.5, 0.5, "No sector data available", ha="center", va="center",
                transform=ax.transAxes, fontsize=12)
        ax.set_title("Pipeline Sector Mix vs. Winner Patterns", fontsize=13, fontweight="bold")
        plt.tight_layout()
        fig.savefig(output_path, dpi=300, bbox_inches="tight", facecolor="white")
        plt.close(fig)
        return output_path

    sectors = [s for s, _ in sorted_sectors]
    qei_vals = [v["qei_dollars"] for _, v in sorted_sectors]
    pcts = [v["pct"] * 100 for _, v in sorted_sectors]

    def _sector_color(s: str):
        if s in _HIGH_PRIORITY:
            return _PRIMARY
        if s in _MED_PRIORITY:
            return _SECONDARY
        return _ROW_EVEN

    def _sector_edgecolor(s: str):
        if s in _HIGH_PRIORITY or s in _MED_PRIORITY:
            return "white"
        return _SECONDARY

    def _sector_textcolor(s: str):
        if s in _HIGH_PRIORITY or s in _MED_PRIORITY:
            return "white"
        return "#333333"

    bar_colors = [_sector_color(s) for s in sectors]
    bar_edges = [_sector_edgecolor(s) for s in sectors]

    fig, ax = plt.subplots(figsize=(11, max(5, len(sectors) * 0.60 + 1.5)))
    fig.patch.set_facecolor("white")

    bars = ax.barh(
        range(len(sectors)), qei_vals,
        color=bar_colors, edgecolor=bar_edges, linewidth=0.8, height=0.68,
    )

    max_qei = max(qei_vals) if qei_vals else 1

    # Percentage labels at end of each bar
    for i, (bar, pct) in enumerate(zip(bars, pcts)):
        ax.text(
            qei_vals[i] + max_qei * 0.01, i,
            f"{pct:.1f}%",
            va="center", ha="left", fontsize=8.5, color="#333333",
        )

    # Sector labels (formatted)
    sector_labels = [s.replace("_", " ").title() for s in sectors]
    ax.set_yticks(range(len(sectors)))
    ax.set_yticklabels(sector_labels, fontsize=10)
    ax.invert_yaxis()
    ax.set_xlabel("QEI Request ($)", fontsize=10)

    ax.xaxis.set_major_formatter(
        matplotlib.ticker.FuncFormatter(lambda x, _: f"${x / 1_000_000:.0f}M")
    )

    _apply_professional_style(ax)
    ax.set_xlim(0, max_qei * 1.15)

    # Reference annotation — CDFI Fund winner sector mix note
    ax.annotate(
        "Winners typically have ≥50% in high-priority sectors\n(healthcare, affordable housing, education)",
        xy=(0.97, 0.02), xycoords="axes fraction",
        ha="right", va="bottom", fontsize=7.5, color="#666666",
        style="italic",
        bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="#CCCCCC", alpha=0.85),
    )

    # THE LEGEND IS BUILT FROM THE SAME TIERS THE BARS ARE (FIX-2 G-5 sweep).
    # It was a hand-written parenthetical naming two of the four medium
    # sectors, so it stayed wrong in exactly the way _MED_PRIORITY was — and
    # would have gone on naming the old pair after the sets were corrected.
    def _tier_label(tier: str) -> str:
        names = ", ".join(
            s.replace("_", " ").title() for s in sorted(SECTORS_BY_PRIORITY[tier])
        )
        return f"{tier.title()} Priority ({names})"

    legend_items = [
        mpatches.Patch(color=_PRIMARY, label=_tier_label("high")),
        mpatches.Patch(color=_SECONDARY, label=_tier_label("medium")),
        mpatches.Patch(facecolor=_ROW_EVEN, edgecolor=_SECONDARY, label="Other Sectors"),
    ]
    ax.legend(
        handles=legend_items,
        loc="lower right" if len(sectors) <= 4 else "upper right",
        fontsize=8,
        framealpha=0.9,
        edgecolor="#CCCCCC",
    )

    ax.set_title(
        "Pipeline Sector Mix vs. Winner Patterns",
        fontsize=13, fontweight="bold", color="#222222", pad=12,
    )

    plt.tight_layout()
    fig.savefig(output_path, dpi=300, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return output_path


# ---------------------------------------------------------------------------
# Task B.4: plot_readiness_radar
# ---------------------------------------------------------------------------

def _radar_labels(win_score) -> tuple:
    """Title and series label for the readiness radar.

    Partial scores (eligibility data unavailable) are labeled as such — a
    partial radar must never present itself as a full assessment.
    """
    composite = win_score.composite_score
    tier = win_score.tier
    partial = getattr(win_score, "partial", False)
    partial_tag = " (PARTIAL — eligibility data unavailable)" if partial else ""
    title = f"CDFI Fund Section Score Radar — {composite:.0f}/100 [{tier}]{partial_tag}"
    series_label = f"Your Pipeline ({composite:.0f}/100" + (
        ", PARTIAL)" if partial else ")"
    )
    return title, series_label


def plot_readiness_radar(application: "Application", output_path: str) -> str:
    """Radar/spider chart showing the 3 CDFI Fund section scores.

    Displays Business Strategy (0–50), Community Outcomes (0–50), and
    Priority Points (0–10) normalized to 0–100, with Highly Qualified
    threshold reference lines. Partial scores are labeled PARTIAL in the
    title and legend.

    Args:
        application: An Application instance (pipeline must be set).
        output_path: Path to save the PNG file.

    Returns:
        output_path (string).

    Raises:
        ImportError: If matplotlib is not installed.
    """
    _require_matplotlib()

    win_score = application.score_win_probability()
    dim_scores = win_score.dimensional_scores
    composite = win_score.composite_score
    tier = win_score.tier  # "Top Tier" | "Highly Qualified" | "Not Qualified"
    title_text, series_label = _radar_labels(win_score)

    # Map internal section names → display labels.
    # dimensional_scores normalizes every section to 0–100 against its FIXED
    # structural maximum (business_strategy / community_outcomes: /50,
    # priority_points: /10) — even in partial mode, where fewer points were
    # assessable (a degraded CO 20/25 plots as 40, not 80).
    _DIM_MAP = [
        ("business_strategy",  "Business\nStrategy"),
        ("community_outcomes", "Community\nOutcomes"),
        ("priority_points",    "Priority\nPoints"),
    ]

    categories = [label for _, label in _DIM_MAP]
    pipeline_values = [dim_scores.get(key, 0.0) for key, _ in _DIM_MAP]
    # HQ section minimums scaled to 0–100: BS 40/50=80, CO 40/50=80, PP no gating (7/10=70)
    hq_benchmark = [80.0, 80.0, 70.0]

    N = len(categories)
    angles = [n / float(N) * 2 * np.pi for n in range(N)]
    angles += angles[:1]  # close the loop

    pipeline_vals_closed = pipeline_values + pipeline_values[:1]
    benchmark_vals_closed = hq_benchmark + hq_benchmark[:1]

    fig = plt.figure(figsize=(8, 8))
    fig.patch.set_facecolor("white")
    ax = fig.add_subplot(111, polar=True)

    ax.set_facecolor(_BG)

    # Draw HQ threshold reference
    ax.plot(
        angles, benchmark_vals_closed,
        color=_ACCENT, linewidth=1.8, linestyle="--", label="HQ Min Threshold",
    )
    ax.fill(angles, benchmark_vals_closed, alpha=0.0)

    # Draw section scores
    ax.plot(
        angles, pipeline_vals_closed,
        color=_PRIMARY, linewidth=2.2, linestyle="-", label=series_label,
    )
    ax.fill(angles, pipeline_vals_closed, color=_PRIMARY, alpha=0.15)

    # Add score labels at each vertex
    for angle, val, label in zip(angles[:-1], pipeline_values, categories):
        ax.annotate(
            f"{val:.0f}",
            xy=(angle, val),
            xytext=(angle, min(105, val + 7)),
            ha="center", va="center",
            fontsize=8.5, color=_PRIMARY, fontweight="bold",
        )

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(categories, fontsize=11, color="#333333")

    ax.set_rlim(0, 100)
    ax.set_rticks([25, 50, 75, 100])
    ax.set_yticklabels(["25", "50", "75", "100"], fontsize=7.5, color="#888888")
    ax.grid(color="#CCCCCC", linewidth=0.6)

    tier_colors = {
        "Top Tier":         _GREEN,
        "Highly Qualified": _SECONDARY,
        "Not Qualified":    _RED,
    }
    tier_color = tier_colors.get(tier, _GRAY)

    ax.legend(
        loc="upper right",
        bbox_to_anchor=(1.32, 1.12),
        fontsize=9,
        framealpha=0.9,
        edgecolor="#CCCCCC",
    )

    ax.set_title(
        title_text,
        fontsize=13, fontweight="bold", color=tier_color, pad=20, y=1.08,
    )

    plt.tight_layout()
    fig.savefig(output_path, dpi=300, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return output_path


# ---------------------------------------------------------------------------
# Task B.5: plot_winner_alignment
# ---------------------------------------------------------------------------

def plot_winner_alignment(application: "Application", output_path: str) -> str:
    """Bar/range chart showing pipeline metrics vs. historical winner distributions.

    Shows 3 metrics: distress %, states count, jobs per $MM.
    Each metric shows the pipeline value vs. winner p25/p50/p75 range.

    Args:
        application: An Application instance (pipeline must be set).
        output_path: Path to save the PNG file.

    Returns:
        output_path (string).

    Raises:
        ImportError: If matplotlib is not installed.
    """
    _require_matplotlib()

    from nmtcapp.intelligence.pattern_analysis import compare_to_winners

    analysis = application.analyze()
    comparison = compare_to_winners(analysis.pipeline_result)

    # Three metrics to display
    metrics = [
        {
            "label": "Distress %\n(Deep + Severe)",
            "pipeline": comparison["distress"]["observed_pct_deep_or_severe"] * 100,
            "p25": comparison["distress"]["winner_p25"] * 100,
            "p50": comparison["distress"]["winner_p50"] * 100,
            "p75": comparison["distress"]["winner_p75"] * 100,
            "unit": "%",
            "competitive_threshold": comparison["distress"]["winner_p50"] * 100,
        },
        {
            "label": "States\nServed",
            "pipeline": float(comparison["geographic"]["observed_states"]),
            "p25": float(comparison["geographic"]["winner_p25_states"]),
            "p50": float(comparison["geographic"]["winner_p50_states"]),
            "p75": float(comparison["geographic"]["winner_p75_states"]),
            "unit": "states",
            "competitive_threshold": float(comparison["geographic"]["winner_p50_states"]),
        },
        {
            "label": "Jobs per\n$MM QEI",
            "pipeline": comparison["impact"]["observed_jobs_per_mm_qei"],
            "p25": comparison["impact"]["winner_p25"],
            "p50": comparison["impact"]["winner_p50"],
            "p75": comparison["impact"]["winner_p75"],
            "unit": "jobs/$M",
            "competitive_threshold": comparison["impact"]["winner_p50"],
        },
    ]

    fig, axes = plt.subplots(1, 3, figsize=(14, 6))
    fig.patch.set_facecolor("white")

    for ax, metric in zip(axes, metrics):
        ax.set_facecolor(_BG)
        label = metric["label"]
        pipeline_val = metric["pipeline"]
        p25 = metric["p25"]
        p50 = metric["p50"]
        p75 = metric["p75"]
        comp_thresh = metric["competitive_threshold"]

        # Draw winner range band (p25 to p75) as a horizontal range
        # Using a horizontal bar chart style: 3 bars (p25, p50, p75) + pipeline dot

        # Bar positions
        y_positions = [0, 1, 2, 3]
        labels_bar = ["Winner P25", "Winner P50\n(Median)", "Winner P75", "Your Pipeline"]
        values = [p25, p50, p75, pipeline_val]

        # Colors: winner bars in light blue, pipeline in dark blue
        bar_colors_local = [_ROW_EVEN, _SECONDARY, _ROW_EVEN, _PRIMARY]
        bar_edges_local = [_SECONDARY, _SECONDARY, _SECONDARY, _PRIMARY]
        bar_alpha = [0.85, 0.85, 0.85, 1.0]

        bars = ax.barh(
            y_positions, values,
            color=bar_colors_local,
            edgecolor=bar_edges_local,
            linewidth=0.8,
            height=0.55,
            alpha=0.88,
        )

        # Value labels
        max_val = max(values) if values else 1
        for pos, val, col in zip(y_positions, values, bar_colors_local):
            unit = metric["unit"]
            if unit == "%":
                label_text = f"{val:.1f}%"
            elif unit == "states":
                label_text = f"{val:.0f}"
            else:
                label_text = f"{val:.1f}"
            ax.text(
                val + max_val * 0.02, pos,
                label_text,
                va="center", ha="left", fontsize=8.5,
                color="#333333", fontweight="bold" if pos == 3 else "normal",
            )

        # Competitive threshold line (p50)
        ax.axvline(
            x=comp_thresh, color=_ACCENT, linewidth=1.5,
            linestyle="--", label="Competitive Threshold (P50)", zorder=5,
        )
        ax.text(
            comp_thresh, 3.6,
            "Competitive\nThreshold",
            ha="center", va="bottom", fontsize=6.5, color=_YELLOW,
            style="italic",
        )

        ax.set_yticks(y_positions)
        ax.set_yticklabels(labels_bar, fontsize=8.5)
        ax.set_xlabel(metric["unit"], fontsize=9)
        ax.set_xlim(0, max_val * 1.25)

        # Remove top/right spines
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["left"].set_color("#CCCCCC")
        ax.spines["bottom"].set_color("#CCCCCC")
        ax.tick_params(colors="#444444", labelsize=8)
        ax.grid(axis="x", color="#E0E0E0", linewidth=0.6, linestyle="--")

        # Metric title
        ax.set_title(metric["label"], fontsize=10, fontweight="bold",
                     color="#222222", pad=8)

    fig.suptitle(
        "Application vs. Historical Winner Patterns",
        fontsize=14, fontweight="bold", color="#222222", y=1.02,
    )

    plt.tight_layout()
    fig.savefig(output_path, dpi=300, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return output_path
