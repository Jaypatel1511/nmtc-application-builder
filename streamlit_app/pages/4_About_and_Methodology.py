"""About & Methodology — documentation, data sources, and limitations."""
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pandas as pd
import streamlit as st

from nmtcapp.data.historical_awards import NMTC_AWARD_ROUNDS, APPLICATION_VOLUME_TRENDS
from nmtcapp.data.benchmark_thresholds import (
    HIGHLY_QUALIFIED_AGGREGATE_MIN, HIGHLY_QUALIFIED_SECTION_MIN,
    HOUSE_TOP_TIER_AGGREGATE_MIN, HOUSE_TOP_TIER_SECTION_MIN,
    SEVERE_DISTRESS_MIN_PCT, DEEP_DISTRESS_MIN_PCT,
    DBC_PRIORITY_YEARS_MIN, DBC_VOLUME_PCT_MIN, HOUSE_UNRELATED_ENTITIES_MIN_PCT,
    HOUSE_PRODUCT_FLEXIBILITY_BELOW_MARKET_PCT, HOUSE_PRODUCT_FLEXIBILITY_MIN_INDICIA,
    HOUSE_TRACK_RECORD_DEPLOYMENT_MIN, TRACK_RECORD_PIPELINE_ALIGNMENT_MIN,
    TRACK_RECORD_TO_PROJECTION_MIN,
    TOTAL_APPLICANTS_CY2024_25, TOTAL_REQUEST_CY2024_25_B, TOTAL_AVAILABLE_CY2024_25_B,
)
from utils import apply_theme, metric_classification

apply_theme()
st.title("📖 About & Methodology")
st.markdown(
    "Documentation for NMTC Application Builder — source documents, scoring framework, "
    "gating logic, and known limitations."
)
st.markdown("---")

# ---------------------------------------------------------------------------
# What this tool is / is not
# ---------------------------------------------------------------------------
st.markdown(
    """
## What this tool IS — and IS NOT

**NMTC Application Builder** is an open-source Python library and Streamlit demo
that helps Community Development Entities (CDEs) self-assess their NMTC applications
against the CDFI Fund's **published** CY 2024-2025 Review Process criteria.

### This tool IS:
- A self-assessment framework aligned to the **CDFI Fund's published CY 2024-2025
  scoring structure** (Business Strategy + Community Outcomes + Priority Points)
- A diagnostic tool to identify scoring gaps before submission
- A calculator for the published gating thresholds (85/100 aggregate, 40/50 per section)

### This tool IS NOT:
- A win probability calculator (the CDFI Fund does not publish non-winner data,
  so a true probability of selection cannot be computed)
- A substitute for Phase 2 narrative review (Management Capacity and Capitalization
  Strategy are evaluated through qualitative reviewer judgment)
- An authoritative replication of the CDFI Fund's proprietary scoring rubric
  (sub-score weights within sections are best-effort interpretations)
"""
)

st.info(
    "**Source document:** "
    "[CY 2024-2025 NMTC Allocation Application Review Process]"
    "(https://www.cdfifund.gov/system/files/2025-12/CY_2024_25_NMTC_Program_Review_Process.pdf)"
    " — U.S. Department of the Treasury, CDFI Fund"
)

st.markdown("---")

# ---------------------------------------------------------------------------
# Scoring framework overview
# ---------------------------------------------------------------------------
st.markdown("## Scoring Framework (CY 2024-2025)")

# SAME DEFECT AS THE READINESS GRADE, SECOND SITE (1.5.1 T4) — AND
# delta_color="off" DID NOT FIX IT (1.5.1 audit, F1). The third positional
# argument to st.metric is `delta`, and Streamlit derives the arrow's DIRECTION
# from the delta's sign before delta_color is consulted. "Section 1",
# "Section 2" and "Bonus" carry no sign, so all three still rendered with an
# upward arrow after T4 — grey instead of green, on this tool's own methodology
# page. They are labels; they now get no direction because they are no longer
# deltas.
col1, col2, col3 = st.columns(3)
metric_classification(col1, "Business Strategy", "50 pts", "Section 1")
metric_classification(col2, "Community Outcomes", "50 pts", "Section 2")
metric_classification(col3, "Priority Points", "10 pts", "Bonus")

st.markdown("---")

# Business Strategy
st.markdown(
    f"""
### Section 1 — Business Strategy (50 base points)

| Sub-criterion | Max | Key threshold |
|---|---|---|
| **Product Flexibility** | 10 | ≥ {HOUSE_PRODUCT_FLEXIBILITY_BELOW_MARKET_PCT:.0%} of the portfolio priced below market OR ≥ {HOUSE_PRODUCT_FLEXIBILITY_MIN_INDICIA} indicia — **this tool's own test, see below** |
| **Pipeline Credibility** | 15 | Pipeline projects identified, sized, and timed credibly |
| **Track Record Strength** | 15 | 5-year direct financing record; bonus for own capital at risk |
| **Track Record Alignment** | 10 | ≥ {TRACK_RECORD_PIPELINE_ALIGNMENT_MIN:.0%} pipeline supported by similar prior activity; ≥ {HOUSE_TRACK_RECORD_DEPLOYMENT_MIN:.0%} prior-allocation deployment — **the second is this tool's own, see below** |

> **Sub-score disclosure:** Weights within Business Strategy (e.g., Product Flexibility 10 pts)
> are this tool's interpretation of the Review Process document. The CDFI Fund does not
> publish exact point values for individual sub-criteria.

**Product Flexibility does not measure the CDFI Fund's Question 15 test.** Question 15
(*CY 2024-2025 NMTC Allocation Application*, pp. 20-21) is a single-select ladder — "Choose
one of the following options. Check only one." — in which the Applicant commits that **100%
of its QLICIs** will be provided as equity; equity-equivalent financing; debt at least
**50%** below market; **or** debt satisfying at least **5** indicia of flexible or
non-traditional terms. Lower rungs commit to 33%/4 indicia, 25%/3, or 15%/2, and score
lower. Every rung describes a property of each **individual QLICI**.

This tool computes neither figure. Its sub-score divides a **QEI-weighted share of the
portfolio** priced below market by the Fund's **per-loan discount depth**, and takes the
better of that and an application-level indicia count — so the Fund's "or" sits inside one
loan and this tool's sits across the whole book. Those are different quantities, and the
share-over-depth comparison is not a ratio of anything. **No number in this row answers
Question 15**, and it should not be read as a near-miss against it. The CDE must answer
Question 15 from its own loan terms.

**The {HOUSE_TRACK_RECORD_DEPLOYMENT_MIN:.0%} on Track Record Alignment is this tool's, not the Fund's.** The
{TRACK_RECORD_PIPELINE_ALIGNMENT_MIN:.0%} is Fund-stated and correct (*Review Process* p.7 Part II.A.4: "At least
{TRACK_RECORD_PIPELINE_ALIGNMENT_MIN:.0%} of the Applicant's proposed NMTC investments were supported by a track
record of similar business types and activity types"). The Fund's own {TRACK_RECORD_TO_PROJECTION_MIN:.0%} in that
same paragraph is a different measure — "its most recent 5-year direct financing track
record was {TRACK_RECORD_TO_PROJECTION_MIN:.0%} or more of its **projected NMTC deployment in Exhibit A**" — a
track-record-to-projection ratio. Deployment of a *prior* allocation is reviewed in Phase 2
and carries **no published percentage**.
"""
)

# Community Outcomes
st.markdown(
    f"""
### Section 2 — Community Outcomes (50 base points)

| Sub-criterion | Max | Key threshold |
|---|---|---|
| **Higher Distress Targeting** | 15 | ≥ {SEVERE_DISTRESS_MIN_PCT:.0%} of **QEI** in severely distressed tracts — a proxy for a QLICI-dollar commitment, see below |
| **Deep Distress Commitment** | 10 | ≥ {DEEP_DISTRESS_MIN_PCT:.0%} of **QEI** in Deep Distress areas — a proxy for the **top rung** of a selectable ladder, see below |
| **Special Targeting** | 5 | QEI in U.S. Territories, High Migration Rural, NMTC Native Areas, Persistent Poverty Counties — **this tool's own criterion, not the Fund's, see below** |
| **Community Outcomes Quality** | 10 | Quantified outcomes (jobs, units, sq ft) with third-party methodology |
| **Community Accountability** | 10 | LIC board representation + community engagement track record |

**Basis note — the Fund's two distress commitments are measured on QLICIs, these
sub-scores are measured on QEI.** Question 25 of the CY 2024-2025 **Allocation
Application** (printed pp. 38-41) sets both, denominated in QLICIs *"in terms of
aggregate dollar amounts"* and tested **for each QLICI**.

**Question 25(a)** asks for at least {SEVERE_DISTRESS_MIN_PCT:.0%} of QLICIs in
areas characterized by at least **one** of items 1-5 (Severe Distress; NMTC
Native Areas; U.S. Island Areas; Non-Metropolitan Counties; Targeted
Populations) **or** by at least **two** of items 6-12 (25% poverty / 70% median
family income / 1.25× unemployment; Brownfield Sites; ARC and/or DRA Areas;
Colonias Areas; Federal Medically Underserved Areas; FEMA Disaster Areas;
Low-Income and Low-Access to Supermarkets). *"Multiple indicia of distress"* is
that **two-of-seven** test, per QLICI.

**Question 25(b)(i) is not a {DEEP_DISTRESS_MIN_PCT:.0%} bar.** It is a
selectable commitment level — **0 / 5 / 10 / 15 / 20**, where selecting 20 opens
a field for any figure from 20% to 100% — over **four** area types: Deep
Distress, NMTC Native Areas, High Migration Rural Counties, U.S. Island Areas. A
CDE that can honestly commit 10% selects 10 and has failed nothing, and *"A
QLICI that meets this commitment will also automatically meet the commitment
made in Question 25(a)."*

Every distress share this tool computes is a share of **QEI**; `qlici_amount` is
read only to print it in Appendix A and to check it does not exceed its
project's QEI, and feeds no percentage, no score and no bar. The two sub-scores
above are QEI-based *proxies*, and no figure this tool renders answers either
commitment. This package carries a per-project field for **five of the fourteen**
distinct area types Question 25 lists — a tool-verified distress level covering
Severe and Deep Distress, plus CDE-declared and unverified flags for NMTC Native
Areas, High Migration Rural Counties and U.S. territory — and nothing for
Non-Metropolitan Counties, nothing for Targeted Populations, and nothing for any
of items 6-12. **Holding those fields is not a partial answer to Question 25**:
the commitment is a share of QLICI *dollars* and this tool weights nothing by
QLICI dollars.

*Corrected in 1.3.0.* Through 1.2.2 this note quoted the seven-page **Review
Process** — accurately, and it is a summary. The summary reads as a 20% bar and
compresses Question 25(b)'s four area types into one, which told a CDE to
understate its own qualifying share.

**Special Targeting is this tool's own criterion. The CDFI Fund publishes no such
criterion and no bonus points for it.** The CY 2024-2025 NOAA (89 FR 92283, 21 Nov 2024),
section V.B(b), sets out the complete set of additional points under IRC §45D(f)(2):
*"the CDFI Fund will ascribe additional points to entities that meet one or both of the
statutory priorities"* — a DBC track record (up to five points) and Investments in
Unrelated Entities (five points) — *"Thus, Applicants that meet the requirements of both
priority categories can receive up to a total of ten additional points."* Two priorities,
ten points, and both are scored separately under Priority Points below.

The phrases "Special Targeting" and "bonus points" appear **nowhere** in the CY 2024-2025
Allocation Application (142 pp.), the Review Process (7 pp.), or the NOAA (10 pp.). The
four categories are real NMTC concepts, but the Application uses them to **define a
Disadvantaged Business** (p.132: a Disadvantaged Business is one located in *"a Persistent
Poverty County; a NMTC Native Area; or a U.S. Island Area"*) — they feed the DBC statutory
priority, and are not scored on their own. Treat this row as a house prompt to consider
those areas, not as a bar the CDFI Fund will measure.
"""
)

# Priority Points
st.markdown(
    f"""
### Priority Points (10 bonus points)

Priority Points increase an application's ranking within the Highly Qualified pool
but do not affect gating.

| Criterion | Max | Key threshold |
|---|---|---|
| **DBC Track Record** | 5 | ≥ {DBC_PRIORITY_YEARS_MIN} years AND ≥ {DBC_VOLUME_PCT_MIN:.0%} of financing volume to Disadvantaged Businesses/Communities |
| **Unrelated Entities Commitment** | 5 | ≥ {HOUSE_UNRELATED_ENTITIES_MIN_PCT:.0%} of QEIs to unrelated entities — **this tool's threshold; the Fund's test is Yes/No, see below** |

**The {HOUSE_UNRELATED_ENTITIES_MIN_PCT:.0%} is this tool's own scoring threshold. The CDFI Fund publishes no
percentage here, and its test is not a percentage at all.** Question 23 of the CY 2024-2025
Allocation Application (p.34) is a dropdown: *"Does the Applicant intend to use
substantially all of the proceeds of its QEIs to make QLICIs in one or more businesses in
which persons Unrelated to the Applicant hold the majority equity interest?  ☐ Yes ☐ No"*,
and sub-section E states *"An Applicant that answers 'Yes' to Question 23 will be awarded
five additional points."* A Yes/No intent commitment, binding in the Allocation Agreement.

So this tool grades a continuous share against a binary question. The {HOUSE_UNRELATED_ENTITIES_MIN_PCT:.0%} is not
the Fund's figure, and it is **not** Treas. Reg. §1.45D-1(c)(5)(i)'s 85% either: that
defines "substantially all" for the *deployment* test — QEI cash into QLICIs — which is a
different requirement. Re-basing this row to 85% would swap one unstated number for another
while making the citation look stronger, so it has deliberately not been done. The
**denominator** (proceeds of QEIs) is correct and unchanged; that is what Question 23 and
the NOAA both say.
"""
)

st.markdown("---")

# ---------------------------------------------------------------------------
# Gating logic
# ---------------------------------------------------------------------------
st.markdown("## Highly Qualified Gating Logic")

st.markdown(
    f"""
The CDFI Fund uses a **two-stage gating process** to form the Highly Qualified pool
that advances to Phase 2 review. It publishes **one** gate, shown in the first two rows.
The third row is this tool's own and is marked as such.

| Tier | Aggregate Base Score | Section Minimums | Outcome | Whose threshold |
|---|---|---|---|---|
| **Not Qualified** | < {HIGHLY_QUALIFIED_AGGREGATE_MIN} | Either section < {HIGHLY_QUALIFIED_SECTION_MIN} | Does not advance to Phase 2 | CDFI Fund |
| **Highly Qualified** | {HIGHLY_QUALIFIED_AGGREGATE_MIN}–{HOUSE_TOP_TIER_AGGREGATE_MIN - 1} | Both sections ≥ {HIGHLY_QUALIFIED_SECTION_MIN} | Phase 2 reviewed; award depends on ranking | CDFI Fund |
| **Top Tier** | {HOUSE_TOP_TIER_AGGREGATE_MIN}–100 | Both sections ≥ {HOUSE_TOP_TIER_SECTION_MIN} | Well clear of the published gate | **This tool** |

**Critical rule:** An application that scores below {HIGHLY_QUALIFIED_SECTION_MIN} points in
*either* section does not advance to Phase 2, regardless of aggregate score.

**"Top Tier" is not a CDFI Fund tier.** The Review Process (p.3, Step 2) publishes the
Highly Qualified gate verbatim — *"(i) an aggregate score of at least
{HIGHLY_QUALIFIED_SECTION_MIN} out of a possible total of 50 points in each of the two scored Application
sections; and (ii) an aggregate base score (excluding priority points) of at least
{HIGHLY_QUALIFIED_AGGREGATE_MIN} points"* — and **nothing above it**. The phrase "Top Tier" returns zero hits
across the Allocation Application (142 pp.), the Review Process (7 pp.) and the CY
2024-2025 NOAA (10 pp.); the NOAA's only tier concept is the "highly qualified pool". The
{HOUSE_TOP_TIER_AGGREGATE_MIN}/{HOUSE_TOP_TIER_SECTION_MIN} cut points behind the label are an unsourced house heuristic.

The outcome cell for that row previously read *"High probability of award at or near
maximum requested."* That was an award prediction resting on an invented gate, and this
tool does not compute a probability of selection — see "This tool IS NOT", above. Above the
published gate, ranking and the Phase 2 panel decide the award: the Review Process states
that highly qualified Applicants are ranked *"inclusive of half of the priority points"*
and forwarded to an Allocation Recommendation Panel, which this tool does not model.
"""
)

st.markdown("---")

# ---------------------------------------------------------------------------
# Phase 2 considerations
# ---------------------------------------------------------------------------
st.markdown(
    """
## Phase 2 Considerations (Not Scored by This Tool)

Phase 2 evaluates qualitative factors through CDFI Fund staff review.
This tool reports these as informational flags (`phase2_flags`) but does not score them.

| Factor | What Reviewers Look For |
|---|---|
| **Management Capacity** | Staffing, systems, organizational capability to deploy capital |
| **Capitalization Strategy** | QEI-raising track record; investor relationships; feasibility |
| **Non-Metro Commitment** | This tool reports the CDE's **own declared** Question 22(c) figure, unchanged, and reports the pipeline's measured non-metro **QEI** share separately under its own name. Allocation Application Question 22(c) (printed p. 32) asks "What is the minimum percentage of **QLICIs** that the Applicant is willing to commit to deploy in Non-Metropolitan Counties?" — a blank percentage field for a forward commitment, which the CY 2024-2025 NOAA denominates the same way: "at least 20 percent of their QLICIs (as measured by dollar amount)". **The 20% is a Fund goal across all Allocatees and a bar on what an Allocatee committed to; Question 22 states no minimum an individual Applicant must clear**, and it is not scored in Phase I. The measured share is a share of QEI, determined per project from the OMB county designation for the geocoded tract — projects the tool could not determine are reported as a third bucket, never as metropolitan. |
| **Fee / Compensation Structure** | Fee levels favorable to QALICBs |
| **Prior Reporting Compliance** | Late or inaccurate prior-round reports → potential point deductions |
"""
)

st.markdown("---")

# ---------------------------------------------------------------------------
# Historical round statistics
# ---------------------------------------------------------------------------
st.markdown("## Historical NMTC Round Statistics")
st.markdown(
    "Source: CDFI Fund NMTC Award Announcements (public disclosures). The "
    "CY 2024-2025 row is a **double round covering both years**, announced "
    "23 Dec 2025; its figures are from the CY 2024-2025 NMTC Program Award "
    "Book (142 allocatees of 216 applicants; $10 billion awarded of "
    "$19.2 billion requested), so its counts do not compare like-for-like "
    "with the single rounds above it."
)

rows = []
for round_name, data in NMTC_AWARD_ROUNDS.items():
    rows.append({
        "Round": round_name,
        "Applications": data["applications"],
        "Awards": data["awards"],
        "Total Allocated ($B)": f"${data['total_allocated'] / 1e9:.1f}B",
        "Avg Award ($M)": f"${data['avg_award'] / 1e6:.1f}M",
        "Acceptance Rate": f"{data['acceptance_rate']:.1%}",
        "Announced": data["announcement_year"],
    })

st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
st.markdown(f"> **Trend note:** {APPLICATION_VOLUME_TRENDS['trend_note']}")

st.markdown("---")

# ---------------------------------------------------------------------------
# Limitations
# ---------------------------------------------------------------------------
st.markdown(
    """
## Known Limitations

### 1. Phase 2 not modeled
Phase 2 evaluates Management Capacity and Capitalization Strategy through narrative
review. These are the subjective factors that distinguish applicants within the
Highly Qualified pool. This tool does not score Phase 2.

### 2. Sub-score weights are interpretive
The CDFI Fund publishes section totals (50 pts each) and criterion descriptions,
but does not publish exact point values for individual sub-criteria. This tool's
sub-point allocations (e.g., Product Flexibility 10 pts) are best-effort
interpretations.

### 3. Non-winner data is not available
The CDFI Fund publishes only winner-level data. Application data for non-winning
applicants is not publicly disclosed. The `HistoricalBenchmarks` module uses
winner patterns only.

### 4. Past reporting compliance not modeled
Prior-round reporting issues can result in score deductions. This tool assumes
a clean compliance record unless explicitly flagged in `cde_attributes`.

### 5. Pipeline data quality matters
Scores are only as good as the data provided. Inaccurate distress classifications,
job estimates, or sector assignments will produce misleading results.

### 6. Sample data is illustrative only
The sample pipeline (20 projects, Riverbend Community Capital CDE) is fictional.
Do not use sample output to benchmark a real application.

### 7. The readiness score has no CDFI Fund referent
This page is the tool's disclosure page, and through 1.5.0 it did not mention
the readiness score anywhere — not in this list, not in the scoring framework
above. The readiness grade is the largest number on the Pipeline Analyzer and
the first thing printed on every generated document, and it is **an unsourced
house heuristic**: a weighted composite of six components this tool chose, with
weights this tool assigned, calibrated against nothing. The CDFI Fund publishes
no such score, no such weighting, and no grade. **It does not predict an award
outcome and it is not evidence about an application.**

It is also **not the alignment score** on this page. The alignment score is
assessed against the published CY 2024-2025 Review Process criteria and carries
the Fund's own Highly Qualified gate. The readiness grade is not, and the two
can move in opposite directions: a pipeline can raise its readiness grade while
its alignment score falls below the Fund's gate. **Where they disagree, the
alignment score is the one with a published referent.**

### 8. The Application and the Review Process print different Part I maxima
A CDE reading both CDFI Fund documents will find **two different point maxima
for the same Part I** — the Allocation Application states a *Total Maximum
Points for Part I* of **25**, and the Review Process describes **50 points per
section**, which is the denominator every "/50" on this page is scored against.
Nothing in this package acknowledged the discrepancy, so a CDE who noticed it
had no way to tell which figure this tool was using or why.

**This tool scores against 50**, from the Review Process.

**The reconciliation is now established, from the primary source.** The CY
2024-2025 NMTC Program Review Process states on **PDF p.2**, verbatim:

> "The CDFI Fund's Phase 1 review process, for all eligible Applicants, required
> **two reviewers** to independently evaluate and score the Business Strategy and
> Community Outcomes sections of each Application."

Two reviewers score each of the two sections independently, so the Application's
**per-reviewer** maximum of 25 aggregates to the **50** the Review Process
describes. The same document's **p.3** confirms the denominator in the same
breath as the gate: *"an aggregate score of at least 40 out of a possible total
of **50 points** in each of the two scored Application sections; and (ii) an
aggregate base score (excluding priority points) of at least 85 points."*

**The arithmetic corroborates it independently.** At 25 points per section the
aggregate base maximum would be 50, and a gate requiring "at least 85 points"
would be unreachable. At 2 × 25 = 50 per section the maximum is 100 and the 85
gate is coherent — as is that page's own worked example, where 40 + 38 = 78
falls short of 85.

**What is quoted and what is inferred, kept apart.** The two-reviewer fact and
both point figures are quotations. That the 25 is *per reviewer* is the
inference joining them, and it is the only reading on which both published
numbers and the 85 gate are simultaneously true. The CDFI Fund does not print
the reconciliation itself.

*Retrieved and text-extracted locally with pypdf on 2026-08-21 — Review Process,
7pp, 187,497 bytes, SHA-256 `ad0dc777eab0dc8cf437d970418bcdbea8403eb99b79dd1662f4ce94eab98749`;
Allocation Application re-verified the same day against the SHA-256 already
pinned in `renderers/_round_provenance`, byte count and hash both unchanged.*

**No scoring changes from this disclosure**; the denominators are unchanged.
"""
)

# ---------------------------------------------------------------------------
# Links
# ---------------------------------------------------------------------------
st.markdown("---")
st.markdown("## Links & Resources")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown(
        """
        **Project**
        - [GitHub repository](https://github.com/Jaypatel1511/nmtc-application-builder)
        - [PyPI package](https://pypi.org/project/nmtc-application-builder/)
        - MIT License
        """
    )

with col2:
    st.markdown(
        """
        **CDFI Fund resources**
        - [NMTC Program](https://www.cdfifund.gov/programs-training/programs/new-markets-tax-credit)
        - [CY 2024-2025 Review Process (PDF)](https://www.cdfifund.gov/system/files/2025-12/CY_2024_25_NMTC_Program_Review_Process.pdf)
        - [NMTC Mapping Tool](https://www.cdfifund.gov/programs-training/programs/nmtc/nmtc-mapping-tool)
        """
    )

with col3:
    st.markdown(
        """
        **Getting help**
        - Open an issue on GitHub for bugs or feature requests
        - Pull requests welcome
        - Python 3.9+, MIT License
        """
    )

st.markdown("---")
st.caption(
    "NMTC Application Builder is an independent open-source tool and is not affiliated "
    "with or endorsed by the CDFI Fund or any government agency."
)
