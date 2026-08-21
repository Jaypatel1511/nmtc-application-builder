"""
Scoring thresholds for NMTC applications.

Two sections:

SECTION A — CY 2024-2025 scoring thresholds, MIXED PROVENANCE
  Most are read from the CY 2024-2025 NMTC Allocation Application Review Process
  (https://www.cdfifund.gov/system/files/2025-12/CY_2024_25_NMTC_Program_Review_Process.pdf).
  SOME ARE NOT, and this header used to say they all were.

  It read "CDFI Fund Published Thresholds" and "These are the explicit values
  the CDFI Fund uses to evaluate applications". That was the provenance claim
  standing behind five separate false attributions found in the 1.2.2 sweep.

  THE NAME NOW CARRIES THE PROVENANCE. Every constant in this section whose
  value the CDFI Fund does not publish is prefixed ``HOUSE_``. That is not
  cosmetic: streamlit_app/pages/4_About_and_Methodology.py interpolates these
  constants LIVE into the methodology tables a CDE reads, so editing a value
  here silently rewrites rendered text, and D4 stayed invisible for two
  releases behind exactly that mechanism. A rename breaks every consumer at
  import time, which is the only way to guarantee no interpolated surface kept
  the old wording. Renamed in 1.2.2 round 2:

    HOUSE_UNRELATED_ENTITIES_MIN_PCT            the Fund publishes NO percentage
    HOUSE_TRACK_RECORD_DEPLOYMENT_MIN           the Fund's 90% is a different quantity
    HOUSE_TOP_TIER_AGGREGATE_MIN                no tier above Highly Qualified exists
    HOUSE_TOP_TIER_SECTION_MIN                  same
    HOUSE_SPECIAL_TARGETING_TRIGGER_PCT         the criterion itself does not exist
    HOUSE_SPECIAL_TARGETING_MAX                 same
    HOUSE_PRODUCT_FLEXIBILITY_BELOW_MARKET_PCT  Fund's 50% is a per-loan discount depth
    HOUSE_PRODUCT_FLEXIBILITY_MIN_INDICIA       Fund's 5 is a per-loan qualifying form

  NO DEPRECATED ALIASES. Checked before renaming: none of these names is
  exported from ``nmtcapp/__init__`` (they are absent from its ``__all__``),
  and ``benchmark_thresholds`` is named nowhere in docs/, mkdocs.yml or
  README.md. Nothing documented can import them, so an alias would preserve
  only the wrong number under the wrong name.

  NOT RENAMED, AND WHY. Eight further constants here are house figures by this
  package's own admission — the sub-score maximums PRODUCT_FLEXIBILITY_MAX,
  PIPELINE_CREDIBILITY_MAX, TRACK_RECORD_STRENGTH_MAX,
  TRACK_RECORD_ALIGNMENT_MAX, HIGHER_DISTRESS_MAX, DEEP_DISTRESS_MAX,
  COMMUNITY_OUTCOMES_QUALITY_MAX and COMMUNITY_ACCOUNTABILITY_MAX. They differ
  from the eight above in the way that matters to a rename: they weight REAL
  Fund criteria, and every surface that renders them already carries the
  sub-score disclosure ("The CDFI Fund does not publish exact point values for
  individual sub-criteria" — win_probability.py, both methodology tables). No
  false wording is hiding behind them, so renaming them buys nothing this
  round and inflates a diff whose whole purpose is to be reviewable. Prefixing
  them is deferred to 1.2.3 as a deliberate decision, not an oversight.

SECTION B — Legacy winner-pattern thresholds (CY2020–2024)
  Used by HistoricalBenchmarks (benchmarks.py) for the 9-metric tier comparison.
  Kept for backward compatibility. These are inferred from award announcements,
  not published by the CDFI Fund.
"""
from __future__ import annotations

# ===========================================================================
# SECTION A — CY 2024-2025 scoring thresholds, MIXED PROVENANCE
# Primary source: CY_2024_25_NMTC_Program_Review_Process.pdf (7pp, retrieved
# and text-extracted 2026-08-16). Each constant below states whether that
# document actually contains it. Where it does not, the constant says so.
# Rulings are recorded in tests/fund_attribution_allowlist.txt as D1-D6.
# ===========================================================================

# --- Community Outcomes thresholds ---
# CY 2024-2025 NMTC Program Review Process, "Targeting Areas of Higher Distress
# (Question 25)", quoted verbatim from the published document:
#
#   "The Applicant indicated that it will commit to providing at least 85% of
#    its QLICIs in specified areas of severe distress and/or areas
#    characterized by multiple indicia of distress. The Applicant indicated
#    that it will commit to providing at least 20% of its QLICIs to 'Deep
#    Distress' areas."
#
# BOTH SENTENCES ARE REAL AND BOTH ARE INCOMPLETE (1.3.0 S2). They were ruled
# CITED in tests/fund_attribution_allowlist.txt in the 1.2.2 sweep, correctly,
# against the Review Process. The Review Process is a SUMMARY of how the Fund
# scores; the Allocation Application is the INSTRUMENT the Applicant fills in,
# and the sweep never opened it for this question. Re-ruled here against
# Question 25, printed pp. 38-41 of the CY 2024-2025 Allocation Application
# (142 pp., text-extracted locally 2026-08-17). What the summary drops:
#
#   85%  is denominated in QLICIs "IN TERMS OF AGGREGATE DOLLAR AMOUNTS", and
#        "multiple indicia of distress" is a specific two-of-seven test over
#        items 6-12, applied PER QLICI, beside a one-of-five test over items
#        1-5. Seven of those twelve area types have nothing to do with
#        distress tiers at all (Brownfields, Colonias, FEMA, supermarket
#        access...).
#   20%  IS NOT A BAR. Question 25(b)(i) is a selectable ladder — 0 / 5 / 10 /
#        15 / 20 — and selecting 20 opens a field for any figure from 20% to
#        100%. It covers FOUR area types (Deep Distress, NMTC Native Areas,
#        High Migration Rural Counties, U.S. Island Areas), and a QLICI meeting
#        it "will also automatically meet the commitment made in Question
#        25(a)".
#
# So neither constant is a threshold a CDE either clears or misses. Each is the
# figure this package scores its own QEI-denominated proxy against, and the
# comments say that rather than restating the summary. The rendered text that
# carries the real content is renderers/_question_25.q25_basis_note().
SEVERE_DISTRESS_MIN_PCT = 0.85       # Q25(a)'s commitment level: >=85% of aggregate QLICI DOLLARS, one-of-items-1-5 or two-of-items-6-12 per QLICI. Scored here against a QEI proxy.
# ASSIGNED ONCE. This name was assigned twice, on consecutive lines, with the
# same value and two different comments. Found by the 1.2.1 mutation harness:
# changing the first assignment to 0.05 moved nothing, because the second
# reassigned 0.20 immediately afterwards, and the constant pin stayed green
# over what looked like a mutated threshold. A duplicate assignment is a live
# hazard even when the two values agree today — the next editor changes one of
# them and the other silently wins.
DEEP_DISTRESS_MIN_PCT = 0.20         # Q25(b)(i)'s TOP RUNG, not a bar: the ladder is 0/5/10/15/20 over four area types, and 20 opens a 20-100% field. Scored here against a QEI proxy.
# D5 — THE CRITERION DOES NOT EXIST. Round 1 filed this COULD-NOT-ESTABLISH
# because it had retrieved only the Review Process. Round 2 retrieved the other
# two documents and the answer is now DISPROVED, not merely unlocated:
#
#   "special targeting"  0 hits / 0 / 0   Application (142pp), Review Process
#   "bonus point"        0 hits / 0 / 0   (7pp), CY 2024-2025 NOAA (10pp,
#                                          FR vol. 89 no. 225, 92283-92292)
#
# The NOAA settles it affirmatively rather than by absence. Section V.B(b),
# verbatim: "as provided by IRC Sec. 45D(f)(2), the CDFI Fund will ascribe
# additional points to entities that meet ONE OR BOTH of the statutory
# priorities" — DBC track record (up to five) and Unrelated Entities (five) —
# "Thus, Applicants that meet the requirements of both priority categories can
# receive up to a total of ten additional points." Two priorities, ten points,
# both already scored separately by this package. There is no third.
#
# The four categories ARE real and DO appear in the Application — but only
# inside the glossary definition of "Disadvantaged Business or Disadvantaged
# Community", p.132: a Disadvantaged Business is one located in "a Persistent
# Poverty County; a NMTC Native Area; or a U.S. Island Area". They are inputs
# to the DBC priority this package already scores, not a criterion of their own.
#
# THE 10 IS A COINCIDENCE, NOT A SOURCE. The Application does state "up to 10
# additional 'priority points' available under sub-sections B and E" (p.19).
# That is a POINT COUNT for two other criteria. This constant is a SHARE-OF-QEI
# trigger. Reusing a real Fund figure as a different kind of quantity is the
# exact failure D1 is made of; it does not license this number.
#
# THE LIMB STAYS THIS ROUND. win_probability.py:_score_special_targeting still
# reads this constant, and deleting the sub-score would move every Community
# Outcomes total and the rendered baseline with it. Withdrawing the FUND
# ATTRIBUTION is this round; withdrawing the limb is 1.2.3, behind a written
# methodology. Every surface that named the Fund here now says this is the
# tool's own construct.
HOUSE_SPECIAL_TARGETING_TRIGGER_PCT = 0.10   # HOUSE: 10%+ of QEI in a category; no Fund basis

# --- Business Strategy thresholds ---
# p.7 Part II.A.4, and accurate: "At least 70% of the Applicant's proposed NMTC
# investments were supported by a track record of similar business types and
# activity types."
TRACK_RECORD_PIPELINE_ALIGNMENT_MIN = 0.70   # 70%+ NMTC pipeline supported by similar prior activity
# THE FUND'S OTHER 90%, ADDED IN 1.2.2 ROUND 2 SO IT STOPS BEING CONFUSED WITH
# THE HOUSE ONE BELOW. p.7 Part II.A.4, second sentence, verbatim: "The
# Applicant demonstrated that its most recent 5-year direct financing track
# record was 90% or more of its projected NMTC deployment in Exhibit A."
#
# This is a TRACK-RECORD-TO-PROJECTION ratio: past direct financing volume
# against projected NMTC deployment. It is the figure D2 mistook for a
# "deployment rate". Nothing scores against it — this package computes no
# Exhibit A projection — so it exists to be QUOTED CORRECTLY in the one place
# that previously quoted it incorrectly. Deliberately NOT house-prefixed: the
# Fund does publish this one. It shares a value with
# HOUSE_TRACK_RECORD_DEPLOYMENT_MIN and means something else, which is the
# whole of D2 in one line.
TRACK_RECORD_TO_PROJECTION_MIN = 0.90        # Review Process p.7 II.A.4: 5-yr record vs. Exhibit A projection
# D2 — HOUSE. TWO FUND CONCEPTS WERE FUSED INTO ONE INVENTED BAR. Review
# Process p.7 Part II.A.4 states the applicant's "most recent 5-year direct
# financing track record was 90% or more of its projected NMTC deployment in
# Exhibit A" — a TRACK-RECORD-TO-PROJECTION RATIO, comparing what a CDE has
# financed against what it projects in Exhibit A. Deployment of a PRIOR
# allocation is a separate Phase 2 compliance matter (p.4, whether prior-year
# Allocatees issued "the minimum requisite QEIs") and the Fund attaches NO
# percentage to it. "90%+ deployment rate" is neither: grep "deployment rate"
# returns 0 hits across the Application (142pp), the Review Process (7pp) and
# the CY 2024-2025 NOAA (10pp).
#
# What this constant actually divides is attrs["track_record_deployment_pct"],
# a CDE-supplied prior-allocation deployment figure (win_probability.py:478).
# So the 90% is this tool's own bar on a quantity the Fund publishes no bar
# for. The 70% on the same rendered line IS Fund-stated and IS correct
# (TRACK_RECORD_PIPELINE_ALIGNMENT_MIN, above) — a sweep that took the true
# half with the false one would be its own defect.
HOUSE_TRACK_RECORD_DEPLOYMENT_MIN = 0.90     # HOUSE: prior-allocation deployment; no Fund bar exists
# D1 — HOUSE. NOT A PORTFOLIO SHARE, AND THE FUND'S TEST IS A LADDER.
#
# Round 1 read Question 15 through the Review Process alone (p.6 Part II.A.1),
# which describes only what a HIGHLY RANKED application did, and recorded the
# bar as "100% of QLICIs in one of four forms". Round 2 retrieved the
# Application itself and the question is a GRADED SINGLE-SELECT LADDER, p.20-21
# verbatim: "Choose one of the following options. Check only one. The Applicant
# will commit that 100% of its QLICIs will:"
#
#   (a) ... at least 50% below market; or ... at least 5 indicia
#   (b) ... at least 33% below market; or ... at least 4 indicia
#   (c) ... at least 25% below market; or ... at least 3 indicia
#   (d) ... at least 15% below market; or ... at least 2 indicia
#   (e) None of the above.   (f) Not Applicable.
#
# Rung (a) is what the Review Process describes; (b)-(d) are permitted and
# score lower. Writing "Q15 requires 50%/5" into rendered text would therefore
# have installed a NEW misattribution while fixing the old one — it states the
# top rung as though it were the only rung. Every surface corrected this round
# states the ladder.
#
# WHAT THE 50% IS. The DEPTH OF THE RATE DISCOUNT ON AN INDIVIDUAL LOAN, and
# one of four QUALIFYING FORMS a QLICI may take. This constant is divided into
# a QEI-weighted PORTFOLIO SHARE at win_probability.py:435. A share of a
# portfolio over a per-loan discount depth is not a ratio of anything; no label
# makes it sensible, and the rendered surfaces now say so rather than implying
# the sub-score is a near-miss proxy for Q15. Removing the limb moves scored
# figures and the baseline: that is 1.2.3, behind a written methodology.
HOUSE_PRODUCT_FLEXIBILITY_BELOW_MARKET_PCT = 0.50  # HOUSE: portfolio share; Fund's 50% is a per-loan depth
# D1 — HOUSE. Rung (a)'s "at least 5 indicia of flexible or non-traditional
# rates and terms" is a property of an INDIVIDUAL QLICI, alternative to that
# same loan being equity, equity-equivalent, or 50%-below-market. This package
# renders it as an application-level alternative to the portfolio share above:
# the Fund's OR is inside one loan, this tool's OR is across the whole book.
HOUSE_PRODUCT_FLEXIBILITY_MIN_INDICIA = 5          # HOUSE: app-level alternative; Fund's is per-loan

# --- Priority Points thresholds ---
DBC_PRIORITY_YEARS_MIN = 5            # 5+ years DBC focus for full DBC priority points
# p.7 Part II.B.1, and accurate: "at least 70% of its total dollar volume of
# direct financing activities has been provided to DBCs", after "five or more
# years of experience". UPHELD by the 1.2.2 sweep — do not sweep this one.
DBC_VOLUME_PCT_MIN = 0.70             # 70%+ of direct financing volume to DBCs for full credit
# D3 — HOUSE. THE FUND'S TEST IS BINARY; ANY PERCENTAGE IS THE WRONG SHAPE.
#
# Review Process p.7 Part II.B.2 (Question 23): the Applicant commits "to using
# substantially all of the proceeds of its QEIs" — NO PERCENTAGE, here or on
# p.2. Round 2 retrieved the Application and the underlying question is not a
# threshold at all, p.34 verbatim: "23. Investments in Unrelated Entities —
# Does the Applicant intend to use substantially all of the proceeds of its
# QEIs to make QLICIs in one or more businesses in which persons Unrelated to
# the Applicant hold the majority equity interest?  [ ] Yes  [ ] No  (Dropdown
# Menu)". The Application's sub-section E is explicit about what turns on it:
# "An Applicant that answers 'Yes' to Question 23 will be awarded five
# additional points." A yes/no intent commitment worth five priority points.
#
# So this package scores a CONTINUOUS share against a BINARY question. That is
# a category error before it is a wrong number, and it is why the fix is a
# house label rather than a better percentage.
#
# DO NOT RE-BASE TO 85%. Treas. Reg. §1.45D-1(c)(5)(i), verified against eCFR
# title-26: "the term substantially all means at least 85 percent". But read
# what it governs — §1.45D-1(c)(1)(ii), "Substantially all ... of such cash is
# used by the CDE to make qualified low-income community investments". It is
# the DEPLOYMENT test, QEI cash into QLICIs. It is not a bar on the unrelated
# share. Swapping 90% for 85% would trade one unstated number for another
# while STRENGTHENING the appearance of a citation, which is worse than the
# defect it replaced.
#
# THE DENOMINATOR (QEI proceeds) IS CORRECT and must NOT be changed — it is
# the one share this package has right, corroborated by the NOAA: "must meet
# the requirements of IRC Sec. 45D(b)(1)(B) by investing substantially all of
# the proceeds from its QEIs in unrelated businesses."
#
# The only three "90%" strings in the Review Process are 16.90% of awardees
# being Rural CDEs, 90%-of-maximum non-metro, and the p.7 track-record ratio;
# the Application and the NOAA contain none at all.
HOUSE_UNRELATED_ENTITIES_MIN_PCT = 0.90    # HOUSE: Fund's Q23 is Yes/No, not a percentage

# --- Non-Metro / Rural commitments ---
# ALL THREE UPHELD, and the basis is now on the record. 4_About_and_
# Methodology.py:171 shipped a note saying "whether the non-metro commitment is
# QLICI- or QEI-denominated has not been checked against the application's own
# question text". Round 2 retrieved the CY 2024-2025 NOAA (Federal Register
# vol. 89 no. 225, 21 Nov 2024, pp. 92283-92292) and it is stated there
# expressly, on QLICIs:
#
#   "the CDFI Fund will then determine whether the pool of Allocatees will, in
#    the aggregate, invest at least 20 percent of their QLICIs (as measured by
#    dollar amount) in Non-Metropolitan counties"
#
#   "A Rural CDE is one that has a track record of at least three years of
#    direct financing experience, has dedicated at least 50 percent of its
#    direct financing dollars to Non-Metropolitan counties over the past five
#    years, and has committed that at least 50 percent of its NMTC financing
#    dollars with this NMTC Allocation will be deployed in such areas."
#
# NOTE THE DENOMINATOR IS QLICIs, as with Question 25. This package computes
# QEI shares only, so the same proxy caveat applies here as everywhere else.
NON_METRO_MIN_COMMITMENT_PCT = 0.20        # NOAA: >=20% of QLICIs, aggregate across the Allocatee pool
# Review Process p.5: "the CDFI Fund will require Allocatees to invest the
# larger of their 'minimum' commitment, or 90% of their 'maximum' commitment,
# into Non-Metropolitan Counties."
NON_METRO_MAX_COMMITMENT_FACTOR = 0.90     # Review Process p.5: larger of min, or 90% of max
RURAL_CDE_NON_METRO_THRESHOLD = 0.50       # NOAA: 50% of direct financing dollars, and 50% committed

# --- Highly Qualified gating thresholds ---
# p.3 Step 2, verbatim: "(i) an aggregate score of at least 40 out of a
# possible total of 50 points in each of the two scored Application sections;
# and (ii) an aggregate base score (excluding priority points) of at least 85
# points." Both UPHELD.
HIGHLY_QUALIFIED_AGGREGATE_MIN = 85    # 85+ aggregate base score to be "Highly Qualified"
HIGHLY_QUALIFIED_SECTION_MIN = 40      # Each section must score 40+ to be "Highly Qualified"
# D4 — HOUSE, NOT PUBLISHED. The Review Process publishes the gate above and
# NOTHING ABOVE IT. Round 2 checked the other two documents: grep "top tier"
# returns 0 hits across the Application (142pp), the Review Process (7pp) and
# the CY 2024-2025 NOAA (10pp). The NOAA's only tier concept is the "highly
# qualified pool", used four times; the Review Process names it seven.
#
# THE 95 IS A COINCIDENCE, NOT A SOURCE — and this one the round-2 brief did
# not flag. The Review Process does contain a "95%": p.6 Part II.A.1,
# "Applicants purchasing loans from other CDEs committed to require the selling
# CDE to re-invest at least 95% of these proceeds as QLICIs". That is a
# reinvestment share on purchased loans. This constant is an AGGREGATE POINT
# SCORE out of 100. Same digits, different kind of quantity — the same trap as
# the "10 priority points" that does not license SPECIAL_TARGETING, and it
# would have been available to anyone looking to retro-fit a citation here.
#
# recommendations.py:826 and win_probability.py:65 already say "house" in
# rendered text; methodology.md:99, win-alignment.md:87 and
# 4_About_and_Methodology.py:158 did not, and all three tables introduce
# themselves as the CDFI Fund's gating process. Corrected this round.
#
# The TIER ITSELF STAYS. These constants decide a label a CDE is shown
# (win_probability.py:614, :684) and pinned_constants.txt pins that behaviour;
# removing the tier moves scored output. Withdrawing the FUND ATTRIBUTION is
# this round.
HOUSE_TOP_TIER_AGGREGATE_MIN = 95      # HOUSE: no Fund tier above Highly Qualified
HOUSE_TOP_TIER_SECTION_MIN = 45        # HOUSE: same; this tool's own section floor

# --- Section maximums (for reference) ---
BUSINESS_STRATEGY_MAX = 50
COMMUNITY_OUTCOMES_MAX = 50
PRIORITY_POINTS_MAX = 10

# --- Historical program data (CY 2024-2025) ---
TOTAL_APPLICANTS_CY2024_25 = 216
TOTAL_REQUEST_CY2024_25_B = 19.2       # $19.2B requested
TOTAL_AVAILABLE_CY2024_25_B = 10.0     # $10B available
RURAL_CDE_AWARDS_PCT = 0.169           # 16.9% of awards historically to Rural CDEs

# --- Sub-score maximums within each section ---
PRODUCT_FLEXIBILITY_MAX = 10
PIPELINE_CREDIBILITY_MAX = 15
TRACK_RECORD_STRENGTH_MAX = 15
TRACK_RECORD_ALIGNMENT_MAX = 10

HIGHER_DISTRESS_MAX = 15
DEEP_DISTRESS_MAX = 10
# D5 — HOUSE. Unlike its neighbours in this block, this is not a house WEIGHT
# on a real Fund criterion: it allocates 5 of Community Outcomes' 50 points to
# a criterion that appears in none of the three primary documents. See
# HOUSE_SPECIAL_TARGETING_TRIGGER_PCT above for the ruling.
HOUSE_SPECIAL_TARGETING_MAX = 5
COMMUNITY_OUTCOMES_QUALITY_MAX = 10
COMMUNITY_ACCOUNTABILITY_MAX = 10

DBC_TRACK_RECORD_MAX = 5
UNRELATED_ENTITIES_MAX = 5


# ===========================================================================
# SECTION B — Legacy Winner-Pattern Thresholds (CY2020–2024)
# Used by HistoricalBenchmarks (benchmarks.py). Inferred from award data.
# ===========================================================================

WINNER_PATTERN_THRESHOLDS: dict = {
    "min_deep_distress_pct": {
        "strong": 0.75,
        "competitive": 0.50,
        "weak": 0.25,
    },
    "min_geographic_states": {
        "strong": 7,
        "competitive": 4,
        "weak": 2,
    },
    "min_projects": {
        "strong": 13,
        "competitive": 8,
        "weak": 4,
    },
    "max_geographic_hhi": {
        "strong": 500,
        "competitive": 800,
        "weak": 2_000,
    },
    "min_jobs_per_mm_qei": {
        "strong": 18.0,
        "competitive": 10.0,
        "weak": 6.0,
    },
    "max_single_sector_pct": {
        "strong": 0.25,
        "competitive": 0.35,
        "weak": 0.50,
    },
    "min_sectors_represented": {
        "strong": 5,
        "competitive": 3,
        "weak": 1,
    },
    "min_eligible_pct": {
        "strong": 0.98,
        "competitive": 0.90,
        "weak": 0.75,
    },
    # "min_rural_pct" REMOVED (1.4.0 premise ruling). Its tiers were 0.20 /
    # 0.10 / 0.00 — a "strong" band set at the Fund's 20%, which is a
    # program-level goal across all Allocatees and a bar on what an Allocatee
    # COMMITTED to, not a percentage an Applicant's pipeline must reach. Its
    # only consumer, benchmarks.py's rural metric, is deleted; see the note
    # there for the four defects, and renderers/_question_22 for the
    # instrument.
    # "min_native_area_pct" REMOVED (1.4.1 S3). Unlike its neighbours it had
    # NO CONSUMER — no metric in benchmarks.py, nothing in optimizer/ or
    # streamlit_app/ ever read it. It was three unsourced band boundaries that
    # scored nothing, which is the worst version of an unsourced constant: it
    # carried the appearance of a calibrated threshold set while being unable
    # to fail, be reviewed, or be noticed.
}

BENCHMARK_SCORE_POINTS: dict = {
    "strong": 100,
    "competitive": 65,
    "weak": 30,
    "below_weak": 0,
}

BENCHMARK_METRIC_WEIGHTS: dict = {
    "min_deep_distress_pct": 0.25,
    "min_jobs_per_mm_qei": 0.20,
    "min_geographic_states": 0.15,
    "max_geographic_hhi": 0.10,
    "max_single_sector_pct": 0.10,
    "min_sectors_represented": 0.05,
    "min_projects": 0.05,
    "min_eligible_pct": 0.05,
    # "min_rural_pct": 0.05 removed with its metric (1.4.0). These weights now
    # sum to 0.95 rather than 1.00 and that is CORRECT, not an oversight:
    # benchmarks._weighted_score divides by the weights actually present, so
    # the eight surviving metrics renormalise themselves. Topping one of them
    # up by 0.05 to restore a round total would silently reweight a metric
    # nobody decided to reweight.
}
