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
- Aggregate patterns to infer winner distributions for distress concentration, geographic diversity, sector mix, and impact intensity

**What is NOT available:**
- Application-level data for non-winners (not published by the CDFI Fund)
- Individual project-level details from winner applications
- NOFA scores for any application (winner or non-winner)

This is the critical limitation that prevents computation of true win probability — see [Methodology](methodology.md) and [Limitations](../about/limitations.md) for the full discussion.

---

## CDFI Fund Annual Reports (FY2018–FY2023)

**Source:** [cdfifund.gov/research](https://www.cdfifund.gov/research) — NMTC Program Annual Reports

**What we use:**
- Impact statistics tables: jobs created and retained per dollar of QEI invested (used to populate `WINNER_IMPACT_BENCHMARKS`)
- NMTC Investments by Business Type tables: sector allocation percentages across funded projects (used to populate `WINNER_SECTOR_PATTERNS`)
- Geographic deployment tables: state-level deployment breakdowns (used to infer `WINNER_GEOGRAPHIC_PATTERNS`)

**Coverage:** FY2018–FY2023 annual reports. FY2024 data will be incorporated when published.

**Note on aggregation:** Annual reports present program-level aggregates, not individual application data. Winner patterns in `historical_awards.py` are inferred from these aggregates, not computed from a microdata sample. The inference methodology is described in [Methodology](methodology.md).

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

Users working on CY2025 and later applications should verify that the winner patterns used for scoring reflect the most recent available data. Check the `historical_awards.py` module header comment for the current data coverage date.

To see the current round data programmatically:

```python
from nmtcapp.data.historical_awards import get_historical_winners

df = get_historical_winners()
print(df[["round", "acceptance_rate", "avg_award", "median_award"]])
```
