"""
Tests for nmtcapp.visualization.maps — all 5 chart functions.

Tests verify:
- Each function returns the output_path string
- Each function creates a PNG file at output_path
- PNG files are non-trivially sized (> 5000 bytes), confirming actual content
- Functions work with the standard sample Application
- Edge cases: empty-ish pipelines, single project, all-same state, etc.
"""
import os
import pytest

from nmtcapp.core.application import Application
from nmtcapp.core.cde import CDEProfile
from nmtcapp.core.pipeline import Pipeline, PipelineProject


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_app():
    """Standard 20-project sample application."""
    cde = CDEProfile.sample()
    pipeline = Pipeline.sample(n=20)
    app = Application(cde=cde, requested_allocation=65_000_000)
    app.add_pipeline(pipeline)
    return app


@pytest.fixture
def small_app():
    """Minimal 5-project application for edge-case testing."""
    cde = CDEProfile.sample()
    pipeline = Pipeline.sample(n=5)
    app = Application(cde=cde, requested_allocation=35_000_000)
    app.add_pipeline(pipeline)
    return app


@pytest.fixture
def concentrated_app():
    """Application with all projects in one state (IL) for concentration tests."""
    cde = CDEProfile.sample()
    projects = [
        PipelineProject(
            project_id=f"PRJ-IL-{i:03d}",
            project_name=f"Chicago Project {i}",
            qalicb_name=f"Chicago QALICB {i} LLC",
            address=f"{1000 + i * 100} S Michigan Ave",
            city="Chicago",
            state="IL",
            sector="healthcare" if i % 2 == 0 else "education",
            project_type="real_estate",
            total_project_cost=10_000_000,
            qei_request=7_000_000,
            qlici_amount=7_000_000,
            expected_jobs_created=40,
            expected_jobs_retained=10,
            is_nmtc_eligible=True,
            distress_level="deep",
            census_tract="17031838200",
            is_native_area=False,
            is_high_migration_rural=False,
            is_opportunity_zone=False,
        )
        for i in range(1, 8)
    ]
    pipeline = Pipeline(projects)
    app = Application(cde=cde, requested_allocation=50_000_000)
    app.add_pipeline(pipeline)
    return app


@pytest.fixture
def mixed_distress_app():
    """Application with all distress levels represented."""
    cde = CDEProfile.sample()
    projects = []
    distress_levels = ["deep", "severe", "lic", None]
    states = ["IL", "TX", "NY", "CA"]
    sectors = ["healthcare", "education", "small_business", "affordable_housing"]
    for i, (dlevel, state, sector) in enumerate(zip(distress_levels, states, sectors)):
        projects.append(PipelineProject(
            project_id=f"PRJ-MD-{i:03d}",
            project_name=f"Mixed Distress Project {i}",
            qalicb_name=f"Mixed QALICB {i} LLC",
            address=f"{100 + i * 50} Main St",
            city=["Chicago", "Houston", "New York", "Los Angeles"][i],
            state=state,
            sector=sector,
            project_type="real_estate",
            total_project_cost=8_000_000,
            qei_request=5_500_000,
            qlici_amount=5_500_000,
            expected_jobs_created=35,
            expected_jobs_retained=10,
            is_nmtc_eligible=True,
            distress_level=dlevel,
            census_tract=f"1703183820{i}",
            is_native_area=False,
            is_high_migration_rural=False,
            is_opportunity_zone=False,
        ))
    pipeline = Pipeline(projects)
    app = Application(cde=cde, requested_allocation=25_000_000)
    app.add_pipeline(pipeline)
    return app


# ---------------------------------------------------------------------------
# Import guard — skip all tests if matplotlib is not installed
# ---------------------------------------------------------------------------

pytest.importorskip("matplotlib", reason="matplotlib not installed — skipping visualization tests")

from nmtcapp.visualization.maps import (
    plot_pipeline_map,
    plot_distress_heatmap,
    plot_sector_distribution,
    plot_readiness_radar,
    plot_winner_alignment,
)


# ---------------------------------------------------------------------------
# Tests: plot_pipeline_map
# ---------------------------------------------------------------------------

class TestPlotPipelineMap:

    def test_returns_output_path(self, sample_app, tmp_path):
        out = tmp_path / "pipeline_map.png"
        result = plot_pipeline_map(sample_app, str(out))
        assert result == str(out)

    def test_file_exists(self, sample_app, tmp_path):
        out = tmp_path / "pipeline_map.png"
        plot_pipeline_map(sample_app, str(out))
        assert out.exists()

    def test_file_size_gt_5kb(self, sample_app, tmp_path):
        out = tmp_path / "pipeline_map.png"
        plot_pipeline_map(sample_app, str(out))
        assert out.stat().st_size > 5000, (
            f"PNG is too small ({out.stat().st_size} bytes) — likely empty or corrupt"
        )

    def test_works_with_small_pipeline(self, small_app, tmp_path):
        out = tmp_path / "pipeline_map_small.png"
        result = plot_pipeline_map(small_app, str(out))
        assert result == str(out)
        assert out.exists()
        assert out.stat().st_size > 5000

    def test_works_with_concentrated_pipeline(self, concentrated_app, tmp_path):
        out = tmp_path / "pipeline_map_conc.png"
        result = plot_pipeline_map(concentrated_app, str(out))
        assert result == str(out)
        assert out.exists()
        assert out.stat().st_size > 5000

    def test_works_with_mixed_distress(self, mixed_distress_app, tmp_path):
        out = tmp_path / "pipeline_map_mixed.png"
        result = plot_pipeline_map(mixed_distress_app, str(out))
        assert result == str(out)
        assert out.exists()
        assert out.stat().st_size > 5000

    def test_output_is_png(self, sample_app, tmp_path):
        """Verify PNG magic bytes in the output file."""
        out = tmp_path / "pipeline_map.png"
        plot_pipeline_map(sample_app, str(out))
        with open(str(out), "rb") as f:
            header = f.read(8)
        # PNG magic bytes: 89 50 4E 47 0D 0A 1A 0A
        assert header[:4] == b"\x89PNG"

    def test_accepts_pathlib_string(self, sample_app, tmp_path):
        out = str(tmp_path / "pipeline_map_str.png")
        result = plot_pipeline_map(sample_app, out)
        assert result == out
        assert os.path.exists(out)


# ---------------------------------------------------------------------------
# Tests: plot_distress_heatmap
# ---------------------------------------------------------------------------

class TestPlotDistressHeatmap:

    def test_returns_output_path(self, sample_app, tmp_path):
        out = tmp_path / "distress_heatmap.png"
        result = plot_distress_heatmap(sample_app, str(out))
        assert result == str(out)

    def test_file_exists(self, sample_app, tmp_path):
        out = tmp_path / "distress_heatmap.png"
        plot_distress_heatmap(sample_app, str(out))
        assert out.exists()

    def test_file_size_gt_5kb(self, sample_app, tmp_path):
        out = tmp_path / "distress_heatmap.png"
        plot_distress_heatmap(sample_app, str(out))
        assert out.stat().st_size > 5000

    def test_works_with_small_pipeline(self, small_app, tmp_path):
        out = tmp_path / "distress_heatmap_small.png"
        result = plot_distress_heatmap(small_app, str(out))
        assert result == str(out)
        assert out.exists()
        assert out.stat().st_size > 5000

    def test_works_with_concentrated_pipeline(self, concentrated_app, tmp_path):
        out = tmp_path / "distress_heatmap_conc.png"
        result = plot_distress_heatmap(concentrated_app, str(out))
        assert result == str(out)
        assert out.exists()
        assert out.stat().st_size > 5000

    def test_works_with_mixed_distress(self, mixed_distress_app, tmp_path):
        out = tmp_path / "distress_heatmap_mixed.png"
        result = plot_distress_heatmap(mixed_distress_app, str(out))
        assert result == str(out)
        assert out.exists()
        assert out.stat().st_size > 5000

    def test_output_is_png(self, sample_app, tmp_path):
        out = tmp_path / "distress_heatmap.png"
        plot_distress_heatmap(sample_app, str(out))
        with open(str(out), "rb") as f:
            header = f.read(4)
        assert header == b"\x89PNG"


# ---------------------------------------------------------------------------
# Tests: plot_sector_distribution
# ---------------------------------------------------------------------------

class TestPlotSectorDistribution:

    def test_returns_output_path(self, sample_app, tmp_path):
        out = tmp_path / "sector_dist.png"
        result = plot_sector_distribution(sample_app, str(out))
        assert result == str(out)

    def test_file_exists(self, sample_app, tmp_path):
        out = tmp_path / "sector_dist.png"
        plot_sector_distribution(sample_app, str(out))
        assert out.exists()

    def test_file_size_gt_5kb(self, sample_app, tmp_path):
        out = tmp_path / "sector_dist.png"
        plot_sector_distribution(sample_app, str(out))
        assert out.stat().st_size > 5000

    def test_works_with_small_pipeline(self, small_app, tmp_path):
        out = tmp_path / "sector_dist_small.png"
        result = plot_sector_distribution(small_app, str(out))
        assert result == str(out)
        assert out.exists()
        assert out.stat().st_size > 5000

    def test_works_with_concentrated_pipeline(self, concentrated_app, tmp_path):
        """Single-state pipeline with only 2 sectors."""
        out = tmp_path / "sector_dist_conc.png"
        result = plot_sector_distribution(concentrated_app, str(out))
        assert result == str(out)
        assert out.exists()
        assert out.stat().st_size > 5000

    def test_works_with_all_same_sector(self, tmp_path):
        """All projects in one sector — edge case."""
        cde = CDEProfile.sample()
        projects = [
            PipelineProject(
                project_id=f"PRJ-HS-{i:03d}",
                project_name=f"Healthcare Project {i}",
                qalicb_name=f"HC QALICB {i} LLC",
                address=f"{500 + i * 10} Main St",
                city="Chicago",
                state=["IL", "TX", "NY", "CA", "OH"][i % 5],
                sector="healthcare",
                project_type="real_estate",
                total_project_cost=8_000_000,
                qei_request=6_000_000,
                qlici_amount=6_000_000,
                expected_jobs_created=30,
                expected_jobs_retained=5,
                is_nmtc_eligible=True,
                distress_level="deep",
            )
            for i in range(6)
        ]
        app = Application(cde=cde, requested_allocation=40_000_000)
        app.add_pipeline(Pipeline(projects))
        out = tmp_path / "sector_dist_single.png"
        result = plot_sector_distribution(app, str(out))
        assert result == str(out)
        assert out.exists()
        assert out.stat().st_size > 5000

    def test_output_is_png(self, sample_app, tmp_path):
        out = tmp_path / "sector_dist.png"
        plot_sector_distribution(sample_app, str(out))
        with open(str(out), "rb") as f:
            header = f.read(4)
        assert header == b"\x89PNG"


# ---------------------------------------------------------------------------
# Tests: plot_readiness_radar
# ---------------------------------------------------------------------------

class TestPlotReadinessRadar:

    def test_returns_output_path(self, sample_app, tmp_path):
        out = tmp_path / "readiness_radar.png"
        result = plot_readiness_radar(sample_app, str(out))
        assert result == str(out)

    def test_file_exists(self, sample_app, tmp_path):
        out = tmp_path / "readiness_radar.png"
        plot_readiness_radar(sample_app, str(out))
        assert out.exists()

    def test_file_size_gt_5kb(self, sample_app, tmp_path):
        out = tmp_path / "readiness_radar.png"
        plot_readiness_radar(sample_app, str(out))
        assert out.stat().st_size > 5000

    def test_works_with_small_pipeline(self, small_app, tmp_path):
        out = tmp_path / "readiness_radar_small.png"
        result = plot_readiness_radar(small_app, str(out))
        assert result == str(out)
        assert out.exists()
        assert out.stat().st_size > 5000

    def test_works_with_concentrated_pipeline(self, concentrated_app, tmp_path):
        out = tmp_path / "readiness_radar_conc.png"
        result = plot_readiness_radar(concentrated_app, str(out))
        assert result == str(out)
        assert out.exists()
        assert out.stat().st_size > 5000

    def test_works_with_mixed_distress(self, mixed_distress_app, tmp_path):
        out = tmp_path / "readiness_radar_mixed.png"
        result = plot_readiness_radar(mixed_distress_app, str(out))
        assert result == str(out)
        assert out.exists()
        assert out.stat().st_size > 5000

    def test_output_is_png(self, sample_app, tmp_path):
        out = tmp_path / "readiness_radar.png"
        plot_readiness_radar(sample_app, str(out))
        with open(str(out), "rb") as f:
            header = f.read(4)
        assert header == b"\x89PNG"

    def test_uses_polar_plot_dimensions(self, sample_app, tmp_path):
        """Verify the radar covers all 5 win-alignment dimensions via score_win_probability."""
        score = sample_app.score_win_probability()
        dims = score.dimensional_scores
        assert len(dims) == 5, f"Expected 5 dimensions, got {len(dims)}: {list(dims.keys())}"
        expected_keys = {
            "distress_concentration",
            "geographic_diversity",
            "impact_intensity",
            "sector_diversity",
            "pipeline_quality",
        }
        assert set(dims.keys()) == expected_keys


# ---------------------------------------------------------------------------
# Tests: plot_winner_alignment
# ---------------------------------------------------------------------------

class TestPlotWinnerAlignment:

    def test_returns_output_path(self, sample_app, tmp_path):
        out = tmp_path / "winner_alignment.png"
        result = plot_winner_alignment(sample_app, str(out))
        assert result == str(out)

    def test_file_exists(self, sample_app, tmp_path):
        out = tmp_path / "winner_alignment.png"
        plot_winner_alignment(sample_app, str(out))
        assert out.exists()

    def test_file_size_gt_5kb(self, sample_app, tmp_path):
        out = tmp_path / "winner_alignment.png"
        plot_winner_alignment(sample_app, str(out))
        assert out.stat().st_size > 5000

    def test_works_with_small_pipeline(self, small_app, tmp_path):
        out = tmp_path / "winner_alignment_small.png"
        result = plot_winner_alignment(small_app, str(out))
        assert result == str(out)
        assert out.exists()
        assert out.stat().st_size > 5000

    def test_works_with_concentrated_pipeline(self, concentrated_app, tmp_path):
        out = tmp_path / "winner_alignment_conc.png"
        result = plot_winner_alignment(concentrated_app, str(out))
        assert result == str(out)
        assert out.exists()
        assert out.stat().st_size > 5000

    def test_works_with_mixed_distress(self, mixed_distress_app, tmp_path):
        out = tmp_path / "winner_alignment_mixed.png"
        result = plot_winner_alignment(mixed_distress_app, str(out))
        assert result == str(out)
        assert out.exists()
        assert out.stat().st_size > 5000

    def test_output_is_png(self, sample_app, tmp_path):
        out = tmp_path / "winner_alignment.png"
        plot_winner_alignment(sample_app, str(out))
        with open(str(out), "rb") as f:
            header = f.read(4)
        assert header == b"\x89PNG"

    def test_compare_to_winners_returns_three_dimensions(self, sample_app):
        """Verify compare_to_winners returns distress, geographic, impact keys."""
        from nmtcapp.intelligence.pattern_analysis import compare_to_winners
        analysis = sample_app.analyze()
        comparison = compare_to_winners(analysis.pipeline_result)
        assert "distress" in comparison
        assert "geographic" in comparison
        assert "impact" in comparison


# ---------------------------------------------------------------------------
# Tests: Module-level import and __all__
# ---------------------------------------------------------------------------

class TestModuleImports:

    def test_visualization_init_exports_all_functions(self):
        import nmtcapp.visualization as viz
        assert hasattr(viz, "plot_pipeline_map")
        assert hasattr(viz, "plot_distress_heatmap")
        assert hasattr(viz, "plot_sector_distribution")
        assert hasattr(viz, "plot_readiness_radar")
        assert hasattr(viz, "plot_winner_alignment")

    def test_visualization_all_list(self):
        from nmtcapp.visualization import __all__
        expected = {
            "plot_pipeline_map",
            "plot_distress_heatmap",
            "plot_sector_distribution",
            "plot_readiness_radar",
            "plot_winner_alignment",
        }
        assert set(__all__) == expected

    def test_top_level_nmtcapp_exports_viz(self):
        import nmtcapp
        assert hasattr(nmtcapp, "plot_pipeline_map")
        assert hasattr(nmtcapp, "plot_distress_heatmap")
        assert hasattr(nmtcapp, "plot_sector_distribution")
        assert hasattr(nmtcapp, "plot_readiness_radar")
        assert hasattr(nmtcapp, "plot_winner_alignment")

    def test_direct_import_from_maps(self):
        from nmtcapp.visualization.maps import (
            plot_pipeline_map,
            plot_distress_heatmap,
            plot_sector_distribution,
            plot_readiness_radar,
            plot_winner_alignment,
        )
        assert callable(plot_pipeline_map)
        assert callable(plot_distress_heatmap)
        assert callable(plot_sector_distribution)
        assert callable(plot_readiness_radar)
        assert callable(plot_winner_alignment)


# ---------------------------------------------------------------------------
# Tests: Multiple outputs in same tmp_path (independence)
# ---------------------------------------------------------------------------

class TestMultipleOutputs:

    def test_all_five_functions_same_dir(self, sample_app, tmp_path):
        """Generate all five charts to the same directory, verify all created."""
        outputs = {
            "pipeline_map": tmp_path / "pipeline_map.png",
            "distress_heatmap": tmp_path / "distress_heatmap.png",
            "sector_dist": tmp_path / "sector_dist.png",
            "radar": tmp_path / "radar.png",
            "winner": tmp_path / "winner.png",
        }
        plot_pipeline_map(sample_app, str(outputs["pipeline_map"]))
        plot_distress_heatmap(sample_app, str(outputs["distress_heatmap"]))
        plot_sector_distribution(sample_app, str(outputs["sector_dist"]))
        plot_readiness_radar(sample_app, str(outputs["radar"]))
        plot_winner_alignment(sample_app, str(outputs["winner"]))

        for name, path in outputs.items():
            assert path.exists(), f"{name} PNG not created at {path}"
            assert path.stat().st_size > 5000, (
                f"{name} PNG too small ({path.stat().st_size} bytes)"
            )

    def test_all_functions_return_correct_paths(self, sample_app, tmp_path):
        """Verify each function returns exactly the path it was given."""
        paths = [
            str(tmp_path / "pm.png"),
            str(tmp_path / "dh.png"),
            str(tmp_path / "sd.png"),
            str(tmp_path / "rr.png"),
            str(tmp_path / "wa.png"),
        ]
        funcs = [
            plot_pipeline_map,
            plot_distress_heatmap,
            plot_sector_distribution,
            plot_readiness_radar,
            plot_winner_alignment,
        ]
        for func, path in zip(funcs, paths):
            result = func(sample_app, path)
            assert result == path, f"{func.__name__} returned {result!r}, expected {path!r}"
