# Why NMTC Application Builder

## The problem

Preparing an NMTC allocation application is a discipline that rewards pattern recognition. Experienced practitioners — those who have reviewed dozens of applications, sat on NOFA panels, or advised CDEs through the process — carry intuitions that take years to develop about which parts of a pipeline a reviewer will linger on.

> **Three examples used to stand here and have been removed** (1.5.1). They asserted that healthcare + education combinations "score well on sector diversity", that "a pipeline with only 4 states will be penalized relative to competitors with 8–10", and that a jobs-per-million-QEI figure below 6 "is a meaningful flag for impact reviewers". None of the three is sourced, and all three are claims about how the CDFI Fund scores. The middle one is the sharpest: **the CY 2024-2025 Review Process scores no state count at all**, and the Allocation Application asks for a service area, not a minimum number of states. The same claim, in its executable form, is the geographic recommendation this release withdrew — see `MIN_GEOGRAPHIC_DIVERSITY` in `schema.py`. Leaving the prose version standing would have withdrawn the advice and kept the assertion behind it.

First-time applicants and smaller CDEs typically do not have access to this tacit knowledge. They spend months preparing applications, pay for expensive consulting engagements, and often submit without a clear picture of how competitive their pipeline actually is against the 280–340 other applications the CDFI Fund receives in a typical round.

Even experienced practitioners often work without systematic benchmarking. Pipeline decisions — which projects to include, how to size the request, which markets to expand into — are made based on relationship availability and organizational capacity rather than alignment with the scoring criteria that determine outcomes.

## The solution

NMTC Application Builder is a programmatic intelligence layer on top of publicly available CDFI Fund data. It does three things that were previously either unavailable or required manual effort:

**1. Automates the benchmark lookup.** Instead of manually reading CDFI Fund annual reports and award announcements to extract pattern statistics, the library embeds those statistics as Python constants and applies them to your pipeline automatically. The winner distribution for distress concentration, geographic diversity, sector mix, and impact intensity is computed the moment you call `analyze()`.

**2. Quantifies the gaps.** A consultant might tell you "your distress concentration needs to improve." NMTC Application Builder tells you "your distress concentration is 72%, which is at the winner p25. Raising it to 82% (winner median) is estimated to add 8–15 alignment score points." Specific, measurable, actionable.

**3. Generates the documents.** Producing the formatted Word, Excel, and PDF application package that CDFI Fund reviewers expect has traditionally required significant manual effort — copying data into CDFI Fund templates, formatting tables, generating charts. The library produces a complete application package in a single function call.

## Who benefits

**CDEs applying for their first or second allocation** — the library accelerates the learning curve and reduces the risk of submitting a pipeline with fundamental competitiveness gaps.

**Experienced CDEs optimizing for a competitive round** — even CDEs with strong track records can benefit from systematic analysis. The optimizer can test pipeline composition alternatives that would take hours to evaluate manually.

**CDFI consultants and advisors** — the library provides a structured diagnostic framework that can be used across multiple CDE clients, reducing duplicated analysis effort and providing quantified recommendations to clients.

**Community development researchers** — the library surfaces historical winner pattern statistics and provides a structured API for pipeline-level analysis. Researchers studying NMTC program dynamics or capital deployment patterns may find the data layer useful.

## Origins and motivation

NMTC Application Builder grew from repeated observation that the most consequential application decisions — which projects to include, how to structure geographic coverage, when the pipeline is strong enough to submit — were being made with limited systematic data. The program allocates $5 billion per year to community development projects in distressed census tracts. The quality of the applications that compete for that capital determines which communities get served.

The library is open source because the underlying data (CDFI Fund award announcements and annual reports) is public, and because the methodology should be transparent and auditable. An algorithm that influences which communities receive capital investment should not be a black box.
