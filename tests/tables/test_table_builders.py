"""Tests for the six table builder modules."""
import pytest
import pandas as pd


# ---------------------------------------------------------------------------
# Pipeline table
# ---------------------------------------------------------------------------

class TestPipelineTable:
    @pytest.fixture
    def df(self, sample_pipeline, sample_cde):
        from nmtcapp.tables.pipeline_table import build_pipeline_table
        return build_pipeline_table(sample_pipeline, sample_cde)

    def test_returns_dataframe(self, df):
        assert isinstance(df, pd.DataFrame)

    def test_not_empty(self, df):
        assert len(df) > 0

    def test_has_totals_row(self, df):
        last = df.iloc[-1]
        assert str(last.iloc[0]).upper() in ("TOTALS", "TOTAL") or any(
            "total" in str(v).lower() for v in last.values
        )

    def test_has_required_columns(self, df):
        cols = set(df.columns)
        assert "QEI Request ($)" in cols or any("qei" in c.lower() for c in cols)
        assert any("distress" in c.lower() for c in cols)
        assert any("eligible" in c.lower() for c in cols)

    def test_qei_column_is_numeric(self, df):
        qei_col = next(c for c in df.columns if "qei request" in c.lower())
        data_rows = df.iloc[:-1]
        assert pd.to_numeric(data_rows[qei_col], errors="coerce").notna().all()

    def test_project_count_matches_pipeline(self, df, sample_pipeline):
        # rows = projects + 1 totals row
        assert len(df) == len(sample_pipeline) + 1

    def test_investor_equity_computed(self, df):
        cols = [c.lower() for c in df.columns]
        assert any("equity" in c for c in cols)

    def test_cde_fee_computed(self, df):
        cols = [c.lower() for c in df.columns]
        assert any("fee" in c for c in cols)


# ---------------------------------------------------------------------------
# Distress table
# ---------------------------------------------------------------------------

class TestDistressTable:
    @pytest.fixture
    def df(self, sample_pipeline):
        from nmtcapp.tables.distress_table import build_distress_table
        return build_distress_table(sample_pipeline)

    def test_returns_dataframe(self, df):
        assert isinstance(df, pd.DataFrame)

    def test_not_empty(self, df):
        assert len(df) > 0

    def test_has_distress_level_column(self, df):
        assert any("distress" in c.lower() for c in df.columns)

    def test_has_census_tract_column(self, df):
        assert any("tract" in c.lower() or "census" in c.lower() for c in df.columns)

    def test_has_poverty_or_unemployment_column(self, df):
        cols = [c.lower() for c in df.columns]
        assert any("poverty" in c or "unemployment" in c for c in cols)

    def test_row_count_matches_pipeline(self, df, sample_pipeline):
        # +1 for summary/totals row
        assert len(df) == len(sample_pipeline) or len(df) == len(sample_pipeline) + 1

    def test_empty_pipeline_returns_empty_df(self):
        from nmtcapp.tables.distress_table import build_distress_table
        from nmtcapp.core.pipeline import Pipeline
        result = build_distress_table(Pipeline())
        assert result.empty or len(result) == 0


# ---------------------------------------------------------------------------
# Geographic table
# ---------------------------------------------------------------------------

class TestGeographicTable:
    @pytest.fixture
    def df(self, sample_pipeline):
        from nmtcapp.tables.geographic_table import build_geographic_table
        return build_geographic_table(sample_pipeline)

    def test_returns_dataframe(self, df):
        assert isinstance(df, pd.DataFrame)

    def test_not_empty(self, df):
        assert len(df) > 0

    def test_has_state_column(self, df):
        assert any("state" in c.lower() for c in df.columns)

    def test_has_qei_column(self, df):
        assert any("qei" in c.lower() for c in df.columns)

    def test_has_project_count_column(self, df):
        cols = [c.lower() for c in df.columns]
        assert any("count" in c or "projects" in c for c in cols)

    def test_one_row_per_state(self, df, sample_pipeline):
        states_in_pipeline = {p.state for p in sample_pipeline}
        # All states in pipeline should appear (plus possibly a TOTALS row)
        state_col = next(c for c in df.columns if "state" in c.lower())
        table_states = {s for s in df[state_col] if s and s.upper() != "TOTALS"}
        assert states_in_pipeline == table_states or states_in_pipeline.issubset(table_states)

    def test_has_totals_row(self, df):
        last_val = str(df.iloc[-1, 0]).upper()
        assert "TOTAL" in last_val


# ---------------------------------------------------------------------------
# Impact table
# ---------------------------------------------------------------------------

class TestImpactTable:
    @pytest.fixture
    def df(self, sample_pipeline):
        from nmtcapp.tables.impact_table import build_impact_table
        return build_impact_table(sample_pipeline)

    def test_returns_dataframe(self, df):
        assert isinstance(df, pd.DataFrame)

    def test_not_empty(self, df):
        assert len(df) > 0

    def test_has_jobs_column(self, df):
        cols = [c.lower() for c in df.columns]
        assert any("job" in c for c in cols)

    def test_has_qei_column(self, df):
        cols = [c.lower() for c in df.columns]
        assert any("qei" in c for c in cols)

    def test_has_cost_per_job(self, df):
        cols = [c.lower() for c in df.columns]
        assert any("cost per job" in c or "per job" in c for c in cols)

    def test_totals_row_exists(self, df):
        last_val = str(df.iloc[-1].iloc[0]).upper()
        assert "TOTAL" in last_val or "TOTALS" in last_val

    def test_row_count(self, df, sample_pipeline):
        assert len(df) == len(sample_pipeline) + 1  # + totals


# ---------------------------------------------------------------------------
# Investor table
# ---------------------------------------------------------------------------

class TestInvestorTable:
    @pytest.fixture
    def df(self, sample_application):
        from nmtcapp.tables.investor_table import build_investor_table
        return build_investor_table(sample_application)

    def test_returns_dataframe(self, df):
        assert isinstance(df, pd.DataFrame)

    def test_not_empty(self, df):
        assert len(df) > 0

    def test_has_commitment_amount(self, df):
        cols = [c.lower() for c in df.columns]
        assert any("commitment" in c or "amount" in c for c in cols)

    def test_totals_row(self, df):
        last = str(df.iloc[-1].iloc[0]).upper()
        assert "TOTAL" in last

    def test_no_dollar_amount_is_asserted(self, df):
        """Inverted in 1.2.0: there is no arithmetic here to check any more.

        This test used to assert the investor rows summed to the totals row —
        internally consistent arithmetic over figures the tool invented. The
        rows were two made-up investors split 70/30 of (pipeline QEI x 0.39 x
        $0.83), rendered next to "Primary CRA-motivated investor; term sheet
        pending" while Section D's own narrative said the tool "cannot attest
        to any relationship, to investor motivation, or to how many investors
        will participate". The numbers were consistent and entirely fictional.

        Every cell is now a placeholder, so the correct assertion is that no
        cell contains a number at all.
        """
        commit_col = next(c for c in df.columns if "Commitment Amount" in c)
        for value in df[commit_col]:
            text = str(value)
            assert not any(ch.isdigit() for ch in text), (
                f"the investor commitment column contains a figure ({text!r}). "
                "This tool holds no investor data and must not derive a "
                "commitment amount from pipeline QEI."
            )
        assert any("CDE TO COMPLETE" in str(v) for v in df[commit_col]), (
            "the commitment column carries no [CDE TO COMPLETE] marker"
        )

    def test_no_pipeline_returns_empty(self):
        from nmtcapp.tables.investor_table import build_investor_table
        from nmtcapp.core.application import Application
        from nmtcapp.core.cde import CDEProfile
        app = Application(cde=CDEProfile.sample(), requested_allocation=10_000_000)
        result = build_investor_table(app)
        assert result.empty


# ---------------------------------------------------------------------------
# Track record table
# ---------------------------------------------------------------------------

class TestTrackRecordTable:
    @pytest.fixture
    def df(self, sample_cde):
        from nmtcapp.tables.track_record_table import build_track_record_table
        return build_track_record_table(sample_cde)

    def test_returns_dataframe(self, df):
        assert isinstance(df, pd.DataFrame)

    def test_has_allocation_amount(self, df):
        cols = [c.lower() for c in df.columns]
        assert any("allocation" in c or "amount" in c for c in cols)

    def test_has_deployment_status(self, df):
        cols = [c.lower() for c in df.columns]
        assert any("status" in c or "deploy" in c for c in cols)

    def test_sample_cde_has_rows(self, df):
        # CDEProfile.sample() includes prior_awards
        assert len(df) > 0

    def test_cde_no_awards_returns_placeholder(self):
        from nmtcapp.tables.track_record_table import build_track_record_table
        from nmtcapp.core.cde import CDEProfile
        cde = CDEProfile(
            name="New CDE", cde_id="new-cde", certification_date="2020-01-01",
            mission="test", contact={}, target_markets=[], prior_awards=[], governance={},
        )
        df = build_track_record_table(cde)
        assert isinstance(df, pd.DataFrame)
