# ``community_need_documentation`` (hmda_adapter) was REMOVED in 1.2.0.
#
# It could not reach real HMDA data by any code path: the success branch
# called hmdaanalyzer.load_sample() — synthetic data — and the disparity
# figures it published were module-level literals (0.28 denial rate, 2.1×
# disparity) reached whenever generate_disparity_report()'s str return hit
# a .get(). It rendered those literals as application prose. Nothing in the
# document-generation path consumed it; Section B fabricated its own copy of
# the same claim, which is also gone. Community need is now the CDE's to
# document, as a bracketed placeholder. See CHANGELOG 1.2.0.
from nmtcapp.integrations.cdfidata_adapter import cde_track_record
from nmtcapp.integrations.impact_adapter import build_impact_portfolio
from nmtcapp.integrations.nmtc_calc_adapter import compute_pipeline_economics
from nmtcapp.integrations.nmtc_mapper_adapter import enrich_pipeline_eligibility

__all__ = [
    "cde_track_record",
    "build_impact_portfolio",
    "compute_pipeline_economics",
    "enrich_pipeline_eligibility",
]
