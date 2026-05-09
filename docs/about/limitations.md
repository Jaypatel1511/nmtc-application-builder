# Limitations

This page documents the known limitations of NMTC Application Builder honestly. Understanding these limitations is necessary for using the tool responsibly.

---

## Alignment score is not win probability

This cannot be overstated. The composite score returned by `score_win_probability()` measures alignment with historical winner patterns — not the probability of receiving an NMTC allocation.

The distinction matters practically:
- A score of 80/100 does not mean "80% chance of winning." It means your pipeline is well-aligned with historical winners across most dimensions.
- A score of 40/100 does not mean "40% chance of winning." It means your pipeline has significant gaps relative to typical winner patterns.
- An application that scores 90/100 may still not be funded if a competitor scored 95/100 and the program is oversubscribed. An application that scores 55/100 may be funded if it has other strengths the model does not capture.

The CDFI Fund uses a multi-criterion scoring rubric that includes qualitative assessments of management capacity, community engagement, and organizational track record — dimensions that NMTC Application Builder does not score. A high alignment score is a positive indicator, not a guarantee.

---

## Data recency limitations

The winner pattern statistics embedded in the library (`historical_awards.py`) are derived from CDFI Fund award announcements and annual reports covering CY2020–CY2024. This creates two limitations:

1. **CY2024 data is partially estimated.** At the time of the library's release, CY2024 award announcements were pending. The `CY2024` entry in `NMTC_AWARD_ROUNDS` uses estimated application counts and acceptance rates based on prior round trends. When final CY2024 data is published, the library will be updated.

2. **NOFA criteria change.** The CDFI Fund revises scoring criteria between rounds. A criteria change that shifts relative weights — for example, increasing the weight on geographic diversity or adding new bonus categories — would require recalibration of the dimensional weights in `WinProbabilityModel`. The current library reflects the CY2024 NOFA structure.

Practitioners should always verify that the most recent NOFA aligns with the scoring assumptions the library uses.

---

## What the model cannot do

**Cannot evaluate qualitative dimensions.** The CDFI Fund scores applications on Management Capacity (organizational track record, board composition, CDFi experience) and Business Strategy (narrative coherence, market analysis quality) in ways that require human review. NMTC Application Builder does not assess the quality of your organizational narrative, the strength of your board composition, or the credibility of your market opportunity description.

**Cannot assess investor relationships.** Having committed investors dramatically improves both the credibility of the application and the probability of deploying capital. The library models award size fit (whether the requested allocation is in the typical winner range) but does not model the strength of investor relationships or the certainty of capital deployment.

**Cannot model reviewer subjectivity.** NOFA review involves human readers who may weigh criteria differently from the mechanical model. The alignment score is a systematic approximation — actual scoring by CDFI Fund reviewers involves judgment that cannot be fully captured.

**Cannot predict NOFA changes.** The CDFI Fund sometimes introduces new priority categories (Opportunity Zones, Native American areas, climate resilience) mid-program. The model reflects historical criteria but cannot anticipate future NOFA modifications.

---

## Geographic data limitations

The pipeline map (`plot_pipeline_map`) positions projects at state centroids, not exact addresses. This is a visualization limitation — the intelligence analysis itself uses census tract-level data from `nmtc-mapper`, which is tract-accurate.

If a pipeline has many projects in the same state, the map will show overlapping dots (with small jitter applied) rather than the actual geographic spread of projects within the state. Do not use the pipeline map as a substitute for a precise geographic analysis.

State centroids used are standard geographic center points of the lower 48 states and DC. Alaska and Hawaii are excluded from the contiguous map view.

---

## Non-public application data means benchmarks are approximate

The winner pattern statistics in this library are inferred from CDFI Fund press releases and annual reports — not from a microdata sample of individual applications. The CDFI Fund does not publish application-level data for either winners or non-winners.

Specifically:
- **Distress statistics** are inferred from NOFA thresholds and narrative descriptions in award announcements, not from a dataset of winner applications
- **Geographic statistics** (states, HHI) are estimated from program-level annual report tables
- **Impact statistics** are drawn from the NMTC Impact Table in annual reports, which aggregates across all funded investments for the reporting year

The statistics are reasonable approximations based on the best available public data, but they carry uncertainty that microdata would eliminate. The standard deviations and percentiles in particular are estimated, not computed from a sample.

---

## The optimizer does not guarantee a win

The pipeline optimizer selects the project subset that maximizes alignment score subject to your constraints. This is useful for identifying the best pipeline composition from an available candidate pool — but the selected subset is the optimal answer to the alignment question, not to the funding question.

A pipeline optimized to score 82/100 on alignment does not have a higher probability of winning than a 78/100 pipeline by any quantifiable margin — because we do not know the distribution of competing applications in any given round. The optimizer is a composition tool, not a funding predictor.

---

## Impact projections are unverified

The jobs-per-million-QEI metric, which carries 25% weight in the alignment score, is computed directly from `expected_jobs_created` values entered in each `PipelineProject`. The platform does not verify these projections against comparable deals, market conditions, or industry benchmarks.

CDEs are responsible for ensuring that job projections are reasonable and defensible. Overstated projections will produce an inflated impact score. CDFI Fund reviewers have access to historical data and may scrutinize impact claims — the platform's high impact score will not protect an application with unrealistic projections from reviewer skepticism.

---

## Recommendation: always involve a CDFI expert

NMTC Application Builder is a diagnostic and benchmarking tool — a starting point for analysis, not a substitute for practitioner judgment. Before submitting an application, the pipeline, alignment scores, and recommendations should be reviewed by a qualified CDFI/NMTC practitioner who can:

- Assess qualitative dimensions not captured by the model
- Verify that job projections and impact claims are defensible
- Confirm that the application narrative is coherent and compelling
- Review the deal structure and investor strategy
- Evaluate the application in the context of the specific round's competitive landscape

The library helps you understand your quantitative position. Winning applications are won by practitioners, not algorithms.
