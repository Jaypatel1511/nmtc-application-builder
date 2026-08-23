# Data Sources

This page documents the primary data sources that underpin the intelligence layer and the 17-library open source stack the platform is built on.

---

## CDFI Fund NMTC Award Announcements (CY2020–CY2024)

**Source:** [cdfifund.gov/programs-training/programs/new-markets-tax-credit](https://www.cdfifund.gov/programs-training/programs/new-markets-tax-credit)

**What is publicly available:**
- Round-level aggregate statistics: total applications received, awards made, total dollars allocated, average award size
- CDE-level award announcements: which entities received allocations and for how much

**What we use from these sources:**
- Round-level acceptance rates to populate `NMTC_AWARD_ROUNDS` and compute `acceptance_rate_baseline`
- Round-level aggregates only. **No winner distribution is inferred or held** — the reference bands this package applies to distress concentration, geographic diversity, sector mix and impact intensity are registered `HOUSE` and unsourced, not percentiles of past Allocatees. (Corrected 1.5.1: this line claimed the aggregates were used *"to infer winner distributions"*, which is the inference the sources below explicitly cannot support.)

**What is NOT available:**
- Application-level data for non-winners (not published by the CDFI Fund)
- Individual project-level details from winner applications
- NOFA scores for any application (winner or non-winner)

This is the critical limitation that prevents computation of true win probability — see [Methodology](methodology.md) and [Limitations](../about/limitations.md) for the full discussion.

---

## Withdrawn: "CDFI Fund Annual Reports (FY2018–FY2023)"

**This page previously listed a source that does not exist.** It is recorded here rather than
deleted, because the page was published to the docs site and a reader may have acted on it.

The withdrawn entry claimed a *CDFI Fund NMTC Program Annual Report* series spanning FY2018–FY2023,
linked to `cdfifund.gov/research`, and said we used its "impact statistics tables: jobs created and
retained per dollar of QEI invested" and a "NMTC Investments by Business Type" table.

Established from primary sources:

- **The series does not exist.** The CDFI Fund's Research & Data listings contain, for NMTC, exactly
  two things: the *Compliance Review Report of New Markets Tax Credit Program* (August 2017), and the
  *NMTC Public Data Release* — Summary Report plus Data File, published FY2023, FY2024 and FY2025 and
  cumulative FY2003 onward. There is no annual report series and no FY2018–FY2023 span. The NMTC
  "annual report" is OMB collection 1559-0027, filed **to** the Fund through CIIS; its supporting
  statement states the confidential and proprietary information it collects will not be published.
- **No jobs-per-dollar figure is published, in any denominator.** The Summary Report gives job counts
  and dollar counts in separate tables and never divides them. Searching the FY2024 Summary Report
  (FY2003–FY2022, 24pp) returns zero occurrences of "per dollar" and zero of "jobs per".
- **No "NMTC Investments by Business Type" table appears in it** — zero occurrences of "Business Type".

`WINNER_IMPACT_BENCHMARKS`, `WINNER_SECTOR_PATTERNS` and `WINNER_GEOGRAPHIC_PATTERNS` in
`nmtcapp/data/historical_awards.py` are therefore **unsourced constants of this tool**, and are marked
as such in that module. They do not reach any generated application — verified by rendering every
format and searching the output by value as well as by label. They do feed the Streamlit alignment
scores, which now say on their face that they are this tool's own assumptions.

**The real publication**, if you want the Fund's own NMTC figures, is the
[NMTC Public Data Release](https://www.cdfifund.gov/documents/data-releases) — Summary Report and
Data File.

## Distress-level definitions (added 1.2.0)

The two distress tiers this tool reports come from the **CDFI Fund NMTC LIC Eligibility workbook**
itself — the `.xlsb` the package downloads and loads — not from a prose description of it.
Columns **O** and **P**, verbatim — the letters the Fund's own NOTES sheet uses:

| Column | NOTES sheet label | Header, verbatim |
|---|---|---|
| O | `Column O. Severe Distress` | `Severe distress=LIC AND (Poverty>30%; MFI<=60%;Unemployment>=1.5)` |
| P | `Column P. Deep Distress` | `Deep distress=LIC AND (Poverty>40%; MFI<=40%;Unemployment>=2.5)` |

!!! warning "Corrected in 1.2.1"
    This page, and the generated methodology appendix, cited these as
    "columns 14 and 15" through 1.2.0. Those are the **0-based positional
    indices** of the same two columns in the data sheet's header row — correct
    as array offsets, and not what the Fund calls them. A reader opening the
    workbook to check the quotation would look at columns N and O and find the
    unemployment ratio and severe distress. It was a citation-precision defect
    inside the text added to fix a citation defect.

The semicolons read as **or**; both tiers additionally require the tract to be a Low-Income Community.
Through 1.2.0-rc the generated methodology note printed severe distress's thresholds under the *deep*
label, omitted the median-family-income limb from both, and credited the result to documents that do
not carry that wording. Fixed.

---

## NMTC Program NOFA

**Source:** CDFI Fund Notice of Funds Availability (NOFA), published annually

**What we use:**
- Scoring criteria weights for the five application categories (Business Strategy, Community Outcomes, Management Capacity, Capitalization, Prior Awards)
- Distress concentration requirements and bonus criteria (Native American areas, high-migration rural counties, Opportunity Zones)
- Program rules: 39% credit rate, 7-year compliance period, minimum QEI thresholds

**Note:** The NOFA is revised each year. Scoring weights and specific criteria can change between rounds. The current library reflects the CY2024 NOFA structure. Always verify against the applicable NOFA for your specific application round.

---

## Integration libraries (open source, third party)

The library wraps four community-developed Python libraries:

| Library | What it does | Used for |
|---------|--------------|---------|
| `nmtc-mapper` | Census tract lookup and NMTC eligibility determination | Enriching `PipelineProject.is_nmtc_eligible` and `distress_level` |
| `nmtc-calc` | NMTC deal economics computation (credits, investor equity, CDE fees) | `deal_economics_summary` in `ApplicationAnalysis` |
| `cdfidata` | CDFI Fund certified entity data | CDE track record and peer data |
| `impact-ledger` | Impact metrics aggregation and benchmarking | Jobs and community outcome standardization |

---

## The open source stack

NMTC Application Builder is built on these open source libraries:

**Core data science:**
- `pandas >= 1.3` — DataFrames for pipeline and analysis results
- `numpy >= 1.21` — Numerical operations in scoring and statistics

**CDFI/NMTC domain:**
- `nmtc-mapper >= 0.4.2` — Census tract eligibility
- `nmtc-calc >= 0.1.0` — NMTC deal economics
- `cdfidata >= 0.1.7` — CDFI Fund data
- `impact-ledger >= 0.2.0` — Impact measurement

**Configuration:**
- `pyyaml >= 6.0` — YAML configuration loading for CDE profiles

**Output (optional):**
- `python-docx >= 1.1.0` — Word document generation (`[word]` extra)
- `openpyxl >= 3.0.9` — Excel workbook generation (`[excel]` extra)
- `reportlab >= 4.0.0` — PDF generation (`[pdf]` extra)

**Visualization (optional):**
- `matplotlib >= 3.7` — All five visualization functions (`[viz]` extra)

**Development:**
- `pytest >= 7.0` — Test suite
- `pytest-cov >= 4.0` — Coverage reporting
- `jupyter >= 1.0` — Example notebooks

---

## Data recency and update policy

The embedded historical data in `nmtcapp/data/historical_awards.py` covers CY2020–CY2024 award rounds. Data is updated when:

1. The CDFI Fund publishes new award announcement data (typically once per year)
2. Annual report data is released with new impact statistics

Users working on CY 2026 and later applications should verify that the winner patterns used for scoring reflect the most recent available data. (This line named "CY2025" until 1.5.5. The CDFI Fund has never run a round by that name: the most recent PUBLISHED round is CY 2024-2025, awarded 23 Dec 2025, and the upcoming one is CY 2026.) Check the `historical_awards.py` module header comment for the current data coverage date.

To see the current round data programmatically:

```python
from nmtcapp.data.historical_awards import get_historical_winners

df = get_historical_winners()
print(df[["round", "acceptance_rate", "avg_award", "median_award"]])
```
