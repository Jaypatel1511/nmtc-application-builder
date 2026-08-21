# Generating Outputs

`app.generate()` produces a complete NMTC application document package from the analysis results. It creates the output directory if it does not exist and returns a dict mapping each format name to the generated file path.

```python
paths = app.generate("./drafts/")
print(paths)
# {
#   "markdown": "./drafts/CDE-2018-0117_application.md",
#   "word":     "./drafts/CDE-2018-0117_application.docx",
#   "excel":    "./drafts/CDE-2018-0117_application.xlsx",
#   "pdf":      "./drafts/CDE-2018-0117_application.pdf"
# }
```

File names are derived from the CDE's `cde_id` field (e.g., `CDE-2018-0117_application.docx`).

---

## Generating specific formats

Pass a `formats` list to limit output:

```python
# Word and Excel only
paths = app.generate("./drafts/", formats=["word", "excel"])

# Markdown only (no extra libraries required)
paths = app.generate("./drafts/", formats=["markdown"])
```

Formats: `"markdown"`, `"word"`, `"excel"`, `"pdf"`.

If a required library is not installed, that format is skipped with a warning and omitted from the returned dict. The other formats are still generated.

---

## Word document (.docx)

Requires: `pip install "nmtc-application-builder[word]"`

The Word document follows the CDFI Fund application structure with a cover page, executive summary, and five sections (A through E):

**Cover page:**
- CDE name, ID, and certification date
- Application round and requested allocation
- Contact information
- Generated date

**Executive Summary:**
- Pipeline overview (project count, total QEI, eligibility rate)
- Readiness score and grade
- Top strengths and key areas for improvement

**Section A — Business Strategy:**
- CDE mission and target markets narrative
- Market opportunity description
- Competitive advantage and track record summary

**Section B — Community Outcomes:**
- Distress concentration analysis with comparison to NOFA thresholds
- Geographic footprint and state coverage
- Impact projections (jobs, units, square footage)

**Section C — Management Capacity:**
- Governance structure (board composition)
- Prior award deployment status
- Management team experience summary

**Section D — Capitalization Strategy:**
- NMTC deal economics table (QEI, NMTC credits, investor equity, CDE fees)
- Investor commitment summary

**Section E — Prior Awards:**
- Track record table (all prior NMTC allocations)
- Deployment status by award year

**Supporting tables (embedded in relevant sections):**
- Pipeline project table (all projects with distress level, QEI, and job counts)
- Distress concentration table (breakdown by distress level and state)
- Geographic distribution table (QEI by state)
- Impact summary table

The Word output uses professional styling (deep blue headers, amber accents, alternating row colors) consistent across all output formats.

---

## Excel workbook (.xlsx)

Requires: `pip install "nmtc-application-builder[excel]"`

The Excel workbook contains multiple sheets, each formatted with headers, data validation colors, and number formatting:

**Sheet: Pipeline**
- All pipeline projects with full field set
- Conditional formatting on distress level column (red = deep, yellow = severe, green = LIC)
- QEI totals at the bottom

**Sheet: Distress Analysis**
- Breakdown by distress level (project count, QEI dollars, QEI percentage)
- Comparison column showing winner benchmarks
- Native area and HMR sub-totals

**Sheet: Geographic Distribution**
- QEI by state (sorted descending)
- Project count per state
- HHI calculation

**Sheet: Impact Projections**
- Total jobs created and retained
- Jobs per million QEI vs. winner benchmarks
- Affordable housing units

**Sheet: Deal Economics**
- NMTC credit calculation (39% × QEI over 7 years)
- Investor equity at current market price
- CDE fee estimate
- QEI less CDE fees

!!! note "Renamed in 1.2.1: this row is not a net subsidy"

    This page listed the row as "Net subsidy to QALICB" through 1.2.0, and the
    document itself printed it under that name. It is QEI minus the CDE's fee —
    roughly 97.5% of QEI — and it includes the whole leverage loan, which the
    QALICB or its affiliate repays or refinances after the seven-year
    compliance period. "Net subsidy" is a term of art for the benefit NET OF
    that loan. On the shipped sample the row read $121,582,500 against a
    $124,700,000 QEI.

    No replacement formula is substituted, because no primary source defines
    one: the CY 2024-2025 Allocation Application does not use the phrase at all
    (zero occurrences across 142 pages). The computation is unchanged and the
    label now describes it.

**Sheet: Track Record**
- Prior NMTC award history from CDEProfile
- Deployment status for each award year

**Sheet: Investor Summary**
- Investor identification and commitment information

---

## PDF document (.pdf)

Requires: `pip install "nmtc-application-builder[pdf]"`

The PDF mirrors the Word document structure — cover page, executive summary, sections A through E, and supporting tables — rendered using ReportLab. The PDF uses the same professional color palette (indigo primary, amber accent) and is formatted for standard US Letter (8.5" × 11") at 300 DPI suitable for CDFI Fund electronic submission.

The PDF is primarily useful for final review and archival. For collaboration and editing, the Word document is more practical.

---

## Markdown output (.md)

No extra libraries required. Markdown output is always available.

The Markdown document follows the same structure as the Word and PDF outputs — cover, summary, sections A–E — formatted with standard Markdown headings, tables, and bold text. It is useful for:

- Version control (Markdown diffs well in Git)
- Web publishing (renders natively on GitHub)
- Conversion to other formats via Pandoc

A complete sample in all four formats is generated fresh on every docs build and
published at [Sample Output](../sample-output/). It is not committed to the
repository, so it cannot drift from what the current code produces.

---

## Visualizations are NOT embedded in any generated document

**No chart is embedded in any output format.** Not in Word, not in PDF, not in
Excel, not in Markdown. `app.generate()` produces text and tables only.

This section previously claimed the opposite: that `WordApplicationBuilder`
drew all five charts and placed each one into a named section of the Word
document. That was false for every release in which it appeared. Verified by
execution at 1.4.0 and again at
1.5.0, with `matplotlib` installed so its absence could not be the explanation:
all four formats generate cleanly and the `.docx` contains **zero** chart images
(its only media part is `docProps/thumbnail.jpeg`, a python-docx template
artifact). `grep` confirms the other half: no `add_picture` call and no
`plot_*` call exists anywhere under `nmtcapp/`.

The charts are a **separate, opt-in API**. Call them yourself and place the PNGs
where you want them:

```python
from nmtcapp.visualization import plot_readiness_radar

plot_readiness_radar(app, "./charts/readiness_radar.png")
```

See [Visualizations](visualizations.md) for all five functions. They require
`matplotlib`:

```bash
pip install "nmtc-application-builder[viz]"
```

### Why auto-embedding is not simply switched on

Not an oversight, and not a small feature — a deliberate hold, recorded here so
it is not "fixed" by someone who finds this page and the code disagreeing.

`plot_winner_alignment` charts a pipeline against winner p25/p50/p75 values for
three metrics. Those values are **unsourced**: every one of them is a `HOUSE`
row in `tests/scoring_attribution.txt`, meaning no retrievable document
supports it. `nmtcapp/data/historical_awards.py`'s own header states that the
"Source: CDFI Fund Annual Reports" comments above them cite a publication that
does not exist.

A chart is read as evidence far more readily than a sentence is, and a chart
inside a filed federal application is read as the applicant's own assertion.
Embedding these would move three unsourced comparisons from a PNG a user chose
to make into a document a CDE files with the CDFI Fund.

**Status after the 1.5.0 constant sweep: the constraint still binds.** That
sweep deleted the fabricated `percentile_vs_winners` and six orphaned
constants, and forced a written ruling for all 69 survivors — but 60 of the 69
are still `HOUSE`. (The sixtieth left the unsourced set by being SOURCED: the
CY 2024-2025 award row, whose "award data pending" comment had expired eight
months earlier, is now cited to the Fund's own Award Book.) `plot_winner_alignment`'s three comparisons are among them.
Auto-embedding becomes a legitimate feature once the constants a chart draws
are sourced or gone; it is not one before that.

---

## Example: selective generation

```python
# During development — fast iteration with Markdown only
paths = app.generate("./drafts/", formats=["markdown"])

# For internal review — Word + Excel
paths = app.generate("./review/", formats=["word", "excel"])

# For final submission package — all formats
paths = app.generate("./final/", formats=["markdown", "word", "excel", "pdf"])
```

---

## Output directory behavior

The `output_dir` argument accepts any path, absolute or relative. The directory is created with `os.makedirs(output_dir, exist_ok=True)` — if it already exists, files are overwritten without prompting.

```python
# Absolute path
paths = app.generate("/Users/jane/applications/2025/")

# Relative path (relative to working directory)
paths = app.generate("./drafts/")

# Run-specific subdirectory
import datetime
run_dir = f"./runs/{datetime.date.today()}"
paths = app.generate(run_dir)
```
