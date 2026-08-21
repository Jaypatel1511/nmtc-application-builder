"""Tests for historical_awards data module."""
import pytest
from nmtcapp.data.historical_awards import (
    APPLICATION_VOLUME_TRENDS,
    AWARD_SIZE_TIERS,
    NMTC_AWARD_ROUNDS,
    WINNER_DISTRESS_PATTERNS,
    WINNER_GEOGRAPHIC_PATTERNS,
    WINNER_IMPACT_BENCHMARKS,
    WINNER_SECTOR_PATTERNS,
    get_application_volume_trends,
    get_award_size_percentiles,
    get_historical_winners,
    get_overall_acceptance_rate,
    get_winner_distress_distribution,
    get_winner_geographic_patterns,
    get_winner_sector_distribution,
)


class TestNmtcAwardRounds:
    def test_has_five_rounds(self):
        assert len(NMTC_AWARD_ROUNDS) == 5

    def test_known_rounds_present(self):
        for year in ("CY2020", "CY2021", "CY2022", "CY2023", "CY2024-2025"):
            assert year in NMTC_AWARD_ROUNDS

    def test_each_round_has_required_keys(self):
        required = {"applications", "awards", "total_allocated", "avg_award",
                    "median_award", "acceptance_rate", "announcement_year"}
        for round_name, data in NMTC_AWARD_ROUNDS.items():
            assert required <= set(data.keys()), f"{round_name} missing keys"

    def test_acceptance_rates_plausible(self):
        """A sanity band, widened in 1.5.0 F5 because REALITY LEFT IT.

        The old band was 0.20-0.50. It fit every round in the dict because the
        only round outside it was the one whose figures were invented: CY2024
        carried a fabricated 0.344. The published CY 2024-2025 rate is 0.657 --
        142 allocatees of 216 applicants, a DOUBLE ROUND covering two years --
        so the correction pushed a real number out of a band that had only ever
        been fitted to an estimate. Widening it here is the honest direction;
        clipping the datum to keep the band would have been the other one.
        """
        for round_name, data in NMTC_AWARD_ROUNDS.items():
            rate = data["acceptance_rate"]
            assert 0.20 <= rate <= 0.70, f"{round_name} acceptance rate {rate} out of range"

    def test_total_allocated_at_least_one_round_of_authority(self):
        """Renamed in 1.5.0 F5: one row is no longer five billion.

        CY 2024-2025 is a double round and was awarded $10 billion. The old
        name asserted a fact about the dict that stopped being true the moment
        the invented $5,000,000,000 was replaced with the published figure.
        """
        for data in NMTC_AWARD_ROUNDS.values():
            assert data["total_allocated"] >= 4_900_000_000

    def test_cy2021_most_competitive(self):
        assert NMTC_AWARD_ROUNDS["CY2021"]["acceptance_rate"] < NMTC_AWARD_ROUNDS["CY2020"]["acceptance_rate"]

    def test_awards_less_than_applications(self):
        for round_name, data in NMTC_AWARD_ROUNDS.items():
            assert data["awards"] < data["applications"], f"{round_name}: awards >= applications"


class TestWinnerDistressPatterns:
    def test_mean_deep_severe_above_50pct(self):
        assert WINNER_DISTRESS_PATTERNS["mean_pct_deep_or_severe"] >= 0.50

    def test_percentile_ordering(self):
        d = WINNER_DISTRESS_PATTERNS
        assert d["p25_pct_deep_or_severe"] <= d["p50_pct_deep_or_severe"]
        assert d["p50_pct_deep_or_severe"] <= d["p75_pct_deep_or_severe"]
        assert d["p75_pct_deep_or_severe"] <= d["p90_pct_deep_or_severe"]

    def test_min_floor_below_p25(self):
        d = WINNER_DISTRESS_PATTERNS
        assert d["min_pct_deep_or_severe"] <= d["p25_pct_deep_or_severe"]

    def test_mean_eligible_above_90pct(self):
        assert WINNER_DISTRESS_PATTERNS["mean_pct_eligible"] >= 0.90

    def test_native_area_positive(self):
        assert WINNER_DISTRESS_PATTERNS["mean_pct_native_area"] >= 0.0


class TestWinnerGeographicPatterns:
    def test_mean_states_reasonable(self):
        assert 5 <= WINNER_GEOGRAPHIC_PATTERNS["mean_states"] <= 15

    def test_state_percentile_ordering(self):
        g = WINNER_GEOGRAPHIC_PATTERNS
        assert g["p25_states"] <= g["p50_states"] <= g["p75_states"]

    def test_min_states_at_least_2(self):
        assert WINNER_GEOGRAPHIC_PATTERNS["min_states"] >= 2

    def test_hhi_below_1000(self):
        assert WINNER_GEOGRAPHIC_PATTERNS["mean_hhi"] < 1_000

    def test_the_urban_complement_stays_deleted(self):
        """THIS TEST USED TO ASSERT THE DEFECT (1.5.0 S3).

        It was ``test_urban_rural_pct_sum_to_one``, and it passed:
        ``urban_pct_mean`` 0.82 and ``rural_pct_mean`` 0.18 summed to exactly
        1.000. That is the whole problem. A pair of measured means over a
        population of award winners does not land on 1.000 to three decimals;
        one of them was ARITHMETIC, not measurement -- the 1.4.0 rural ruling
        says so in benchmarks.py in those words.

        So a green test was standing guard over a fabricated complement, and
        the thing it guarded was that the fabrication remained exact. Anyone
        replacing 0.82 with a real measured figure would have gone RED and been
        told to put the invented number back.

        ``urban_pct_mean`` had no consumer in code and is deleted. This asserts
        it stays deleted, which is the opposite assertion on the same line.
        """
        assert "urban_pct_mean" not in WINNER_GEOGRAPHIC_PATTERNS, (
            "urban_pct_mean is back. It was the arithmetic complement of "
            "rural_pct_mean, not a measurement; if a real urban share is ever "
            "needed it must come with a source, not from 1 - rural."
        )


class TestWinnerSectorPatterns:
    def test_every_sector_share_a_consumer_reads_is_present_and_a_share(self):
        """The invariant with a consumer, NOT the total (1.5.0 T1).

        WHAT WAS HERE, AND WHY IT IS GONE. Two tests:
        ``test_sector_shares_sum_to_one`` asserted the eight shares total
        exactly 1.000, and ``test_healthcare_is_largest_sector`` asserted
        healthcare outranks four named others. Both are deleted, for the reason
        ``test_the_urban_complement_stays_deleted`` records one class up.

        The eight shares are 0.22 / 0.18 / 0.17 / 0.14 / 0.12 / 0.08 / 0.05 /
        0.04 -- every one on a 0.01 grid, summing to exactly 1.000, over a
        population of real awards this package holds NO sector breakdown for.
        A sum-to-one assertion over them has exactly two readings and neither
        is a gate:

          * If the partition is a DECLARED CONSTRUCTION -- which it is; the
            registry row says so on its face -- then summing constants that
            were written to sum to one is a TAUTOLOGY. It cannot fail, so it
            tests nothing.
          * If it were ever MEASURED, the same assertion FORBIDS the
            measurement. Eight real sector shares do not land on a 0.01 grid
            totalling 1.000, so anyone substituting real figures goes RED and
            is instructed by a green-tests rule to restore the invented ones.

        THE THIRD READING WAS LOOKED FOR AND DOES NOT EXIST, checked by
        tracing consumers rather than by reasoning about them. If any code
        normalised over the eight, divided by their total, or took a weighted
        mean across them, the sum WOULD be a real invariant. Nothing does:
        ``intelligence/pattern_analysis`` reads the eight keys individually
        into a passthrough dict, and ``optimizer/objectives`` reads only
        ``mean_sectors_represented`` and ``max_single_sector_pct``, neither of
        which is a member of the partition. Every ``sum()`` in either module is
        over pipeline projects. So no consumer depends on the total, and
        deleting the assertion loses no invariant.

        The same argument retires the healthcare ordering: it pins which
        invented number is biggest, has no consumer at all, and goes red the
        moment a real sector mix puts affordable housing first.

        WHAT IS ASSERTED INSTEAD is the property a consumer actually depends
        on -- that each key it indexes exists and holds a fraction. That
        cannot be satisfied by construction alone and cannot forbid a
        measurement, because every real share lies in [0, 1].
        """
        sectors = [
            "healthcare", "affordable_housing", "small_business", "education",
            "community_facility", "mixed_use", "clean_energy", "other"
        ]
        missing = [s for s in sectors if s not in WINNER_SECTOR_PATTERNS]
        assert not missing, (
            f"WINNER_SECTOR_PATTERNS is missing {missing}. "
            "intelligence/pattern_analysis.compare_to_winners indexes all "
            "eight by name and raises KeyError on any that is absent."
        )
        bad = {s: WINNER_SECTOR_PATTERNS[s] for s in sectors
               if not 0.0 <= WINNER_SECTOR_PATTERNS[s] <= 1.0}
        assert not bad, f"sector shares outside [0, 1]: {bad}"

    def test_max_single_sector_pct_below_50pct(self):
        assert WINNER_SECTOR_PATTERNS["max_single_sector_pct"] < 0.50

    def test_mean_sectors_above_three(self):
        assert WINNER_SECTOR_PATTERNS["mean_sectors_represented"] >= 3


class TestWinnerImpactBenchmarks:
    def test_jobs_per_mm_percentile_ordering(self):
        b = WINNER_IMPACT_BENCHMARKS
        assert b["p25_jobs_per_mm_qei"] <= b["p50_jobs_per_mm_qei"] <= b["p75_jobs_per_mm_qei"]
        assert b["p75_jobs_per_mm_qei"] <= b["top_decile_jobs_per_mm_qei"]

    def test_mean_cost_per_job_positive(self):
        assert WINNER_IMPACT_BENCHMARKS["mean_cost_per_job"] > 0

    def test_mean_units_positive(self):
        assert WINNER_IMPACT_BENCHMARKS["mean_units_per_mm_qei"] > 0


class TestQueryFunctions:
    def test_get_historical_winners_returns_dataframe(self):
        import pandas as pd
        df = get_historical_winners()
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 5
        assert "round" in df.columns
        assert "acceptance_rate" in df.columns

    def test_get_winner_distress_distribution_returns_dict(self):
        d = get_winner_distress_distribution()
        assert isinstance(d, dict)
        assert "mean_pct_deep_or_severe" in d

    def test_get_winner_sector_distribution_returns_dict(self):
        s = get_winner_sector_distribution()
        assert isinstance(s, dict)
        assert "healthcare" in s

    def test_get_winner_geographic_patterns_returns_dict(self):
        g = get_winner_geographic_patterns()
        assert isinstance(g, dict)
        assert "mean_states" in g

    def test_get_award_size_percentiles_returns_dict(self):
        tiers = get_award_size_percentiles()
        assert isinstance(tiers, dict)
        assert len(tiers) >= 4

    def test_get_application_volume_trends_returns_dict(self):
        trends = get_application_volume_trends()
        assert isinstance(trends, dict)
        assert "years" in trends
        assert "trend_note" in trends

    def test_get_overall_acceptance_rate_default(self):
        rate = get_overall_acceptance_rate()
        assert 0.25 <= rate <= 0.45

    def test_get_overall_acceptance_rate_custom_rounds(self):
        rate3 = get_overall_acceptance_rate(rounds=3)
        rate5 = get_overall_acceptance_rate(rounds=5)
        # Bands widened in 1.5.0 F5 with the CY 2024-2025 correction. The
        # mean over the last three rounds now includes a 65.7% double round,
        # which lifts it to 0.455 -- outside a ceiling that had been fitted to
        # a fabricated 0.344.
        assert 0.25 <= rate3 <= 0.70
        assert 0.25 <= rate5 <= 0.70

    def test_the_overall_rate_is_a_mean_of_ratios_not_a_pooled_ratio(self):
        """What get_overall_acceptance_rate is a mean OF, asserted (1.5.0 T4).

        The value reaches a CDE: ``win_probability.score_win_probability``
        carries it as ``acceptance_rate_baseline``. Its docstring states the
        construction, and a stated construction with nothing checking it is a
        prose claim -- the shape this project has recorded most often. So the
        three quantities the docstring names are computed here from the same
        dict, and the identity that distinguishes them is asserted.

        THIS IS NOT A CALIBRATION GATE. It does not require 0.4145, or any
        band around it; re-basing the figure is the methodology round's call.
        It requires only that the function keep computing a MEAN OF RATIOS and
        that the pooled alternative stay visibly different, so nobody can
        later describe one as the other -- in either direction.
        """
        recent = list(NMTC_AWARD_ROUNDS.values())[-4:]

        mean_of_ratios = sum(r["acceptance_rate"] for r in recent) / len(recent)
        pooled = (sum(r["awards"] for r in recent)
                  / sum(r["applications"] for r in recent))

        assert get_overall_acceptance_rate(rounds=4) == mean_of_ratios, (
            "get_overall_acceptance_rate no longer returns the unweighted mean "
            "of the per-round rates. Its docstring says it does, and says what "
            "that means for a CDE reading the number. Change both together."
        )
        assert abs(get_overall_acceptance_rate(rounds=4) - pooled) > 0.01, (
            f"the mean-of-ratios ({mean_of_ratios:.4f}) and the pooled rate "
            f"({pooled:.4f}) have converged. While they differ, calling one "
            "'the acceptance rate' without saying which is a live ambiguity "
            "the docstring resolves; if they ever coincide, that paragraph "
            "needs rewriting rather than this assertion relaxing."
        )

        double = [r for r in recent if r.get("double_round")]
        assert double, (
            "no round in the averaged window is flagged double_round. The "
            "docstring's whole caution -- that a two-year round is averaged in "
            "beside single rounds -- is keyed on that flag, and "
            "APPLICATION_VOLUME_TRENDS['trend_note'] tells a reader the same "
            "round 'does not compare like-for-like'. If the window moved past "
            "it, rewrite both."
        )

    def test_award_size_tier_shares_are_shares(self):
        """The total is NOT asserted, and the reason is the same one (1.5.0 T1).

        ``test_award_size_tiers_pct_sum_to_one`` was here. The five shares are
        0.10 / 0.20 / 0.35 / 0.25 / 0.10 -- every one on a 0.05 grid, summing
        to exactly 1.000, over a population of real awards. Real award data
        does not land on a 0.05 grid; a partition somebody wrote down does.

        Its own docstring conceded the tautology and kept the check anyway, on
        the grounds that "an internal-consistency check is still worth having"
        and that deleting it "would remove the one place a reader meets these
        numbers as a set". Neither survives contact with the ruling in
        ``test_the_urban_complement_stays_deleted``: a check that cannot fail
        is not a consistency check, and a reader still meets the set here --
        the assertion below iterates all five.

        THE FUNCTION IS NOT DOING WORK THAT COULD MAKE THE TOTAL AN INVARIANT.
        ``get_award_size_percentiles`` is ``return dict(AWARD_SIZE_TIERS)``, a
        passthrough -- it does not compute, renormalise or derive the shares,
        so the assertion reached constants, not behaviour. Verified by reading
        the function, not assumed from its name. ``AWARD_SIZE_TIERS`` has no
        consumer under ``nmtcapp/`` at all, which 1.5.0 F6 already recorded.
        """
        tiers = get_award_size_percentiles()
        bad = {k: v["pct_of_awards"] for k, v in tiers.items()
               if not 0.0 <= v["pct_of_awards"] <= 1.0}
        assert not bad, f"tier shares outside [0, 1]: {bad}"

    def test_application_volume_lengths_match(self):
        trends = get_application_volume_trends()
        n = len(trends["years"])
        assert len(trends["applications"]) == n
        assert len(trends["awards"]) == n
        assert len(trends["acceptance_rates"]) == n


class TestBenchmarkThresholds:
    def test_thresholds_import(self):
        from nmtcapp.data.benchmark_thresholds import (
            BENCHMARK_METRIC_WEIGHTS,
            BENCHMARK_SCORE_POINTS,
            WINNER_PATTERN_THRESHOLDS,
        )
        assert WINNER_PATTERN_THRESHOLDS
        assert BENCHMARK_SCORE_POINTS
        assert BENCHMARK_METRIC_WEIGHTS

    def test_metric_weights_are_a_normalisable_distribution(self):
        """Positive, and no single metric dominating — NOT summing to 1.0.

        THE ASSERTION THIS REPLACES WAS ``abs(total - 1.0) < 0.01`` AND IT WAS
        MEASURING THE WRONG THING (1.4.0). ``benchmarks._weighted_score``
        divides by the weights of the metrics actually present, so the table
        never needed to sum to anything in particular — the normalisation is
        done at use. What the round total pinned was a coincidence of the table
        having exactly the same rows as the metric list.

        The coincidence made the check actively misleading in both directions.
        Deleting the rural metric with its weight left a mathematically
        identical benchmark and a red test. Adding a metric and forgetting its
        weight — which scores it at 0.0 and silently drags the overall score
        down — leaves the total at 1.0 and a green test.

        So the invariant asserted is the one that matters: every weight is a
        positive share, none of them swamps the rest, and — checked in
        test_application_week3 where the metric list is actually built — the
        weight keys and the metric keys are the same set.
        """
        from nmtcapp.data.benchmark_thresholds import BENCHMARK_METRIC_WEIGHTS

        weights = BENCHMARK_METRIC_WEIGHTS
        assert weights, "the weight table is empty"
        assert all(w > 0 for w in weights.values()), (
            f"non-positive weight(s): "
            f"{[k for k, w in weights.items() if w <= 0]}. A metric weighted "
            "0.0 is computed, rendered and then ignored."
        )
        total = sum(weights.values())
        assert 0.5 <= total <= 1.0, (
            f"weights sum to {total}, outside the sane band. They are "
            "renormalised at use, so the total need not be 1.0 — but a total "
            "this far off means rows were added or removed without thought."
        )
        assert max(weights.values()) / total < 0.5, (
            "one metric carries more than half the benchmark score"
        )

    def test_score_points_ordered(self):
        from nmtcapp.data.benchmark_thresholds import BENCHMARK_SCORE_POINTS
        assert BENCHMARK_SCORE_POINTS["strong"] > BENCHMARK_SCORE_POINTS["competitive"]
        assert BENCHMARK_SCORE_POINTS["competitive"] > BENCHMARK_SCORE_POINTS["weak"]
        assert BENCHMARK_SCORE_POINTS["weak"] > BENCHMARK_SCORE_POINTS["below_weak"]

    def test_each_threshold_has_three_tiers(self):
        from nmtcapp.data.benchmark_thresholds import WINNER_PATTERN_THRESHOLDS
        for metric, tiers in WINNER_PATTERN_THRESHOLDS.items():
            assert "strong" in tiers, f"{metric} missing 'strong' tier"
            assert "competitive" in tiers, f"{metric} missing 'competitive' tier"
            assert "weak" in tiers, f"{metric} missing 'weak' tier"

    def test_deep_distress_strong_threshold_above_competitive(self):
        from nmtcapp.data.benchmark_thresholds import WINNER_PATTERN_THRESHOLDS
        t = WINNER_PATTERN_THRESHOLDS["min_deep_distress_pct"]
        assert t["strong"] >= t["competitive"] >= t["weak"]
