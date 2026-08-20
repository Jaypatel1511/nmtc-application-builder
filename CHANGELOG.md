# Changelog

All notable changes to `nmtc-application-builder` are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [Unreleased] — 1.4.0

**MINOR. The non-metropolitan share stops being a guess, stops being a
benchmark, and starts naming what it is.**

`intelligence/geographic_analysis` computed the pipeline's rural share from a
**hard-coded twelve-state set** whose own comment called itself "(simplified)",
and the module four lines below it conceded *"(In production, this would use
proper CBSA codes from census data.)"* The dependency this package already
installs returns a per-tract OMB answer, and the adapter threw it away.

**A minor, not a patch, for two independent reasons**: the `nmtc-mapper` floor
rises from `>=0.4.2` to `>=0.5.0`, and user-visible computed values move on
three surfaces a CDE reads.

### THE PREMISE RULING — does a non-metropolitan share belong here at all?

Three answers, because the question has three parts.

**THE PER-PROJECT DETERMINATION BELONGS, and is understated by the brief that
asked for it.** Table A5 row (d), *"Located in a Non-Metropolitan County?"*, is
**required by the Fund** and this tool does not supply it — recorded as a gap in
1.2.1 and still open. Question 22(f) instructs the Applicant to *"indicate the
number and dollar amount of transactions that have already been identified in
Non-Metropolitan Counties, for which underwriting is completed or underway"*,
referencing Table A5. `PipelineProject.is_non_metro` is the field that makes
both answerable. It is carried, tri-state.

**THE AGGREGATE SHARE BELONGS AS AN UNBENCHMARKED CHARACTERISATION.** It is
raw material for drafting 22(f) and for deciding what to commit to in 22(c). It
is not an answer to either, and every surface that renders it now says so.

**THE BENCHMARK DOES NOT BELONG, and it is deleted.** `benchmarks.py` scored
`rural_pct` against `WINNER_GEOGRAPHIC_PATTERNS["rural_pct_mean"]` at weight
0.05 and folded the result into `overall_benchmark_score`. Four defects,
stacked:

1. **The CDE's side had no basis** — a QEI share over twelve state codes.
2. **The winner's side has none either, and this package already knew.**
   `data/historical_awards.py`'s own header records that the four
   *"Source: CDFI Fund Annual Reports"* comments — including the one over
   `WINNER_GEOGRAPHIC_PATTERNS` — cite a publication that does not exist, and
   that **"Every value under them is unsourced."** `0.18` is one of them.
3. **The winner mean is a complement too.** `rural_pct_mean` 0.18 and
   `urban_pct_mean` 0.82 sum to exactly 1.000 across a population of award
   winners. That is arithmetic, not measurement — the same structural defect as
   the figure being benchmarked.
4. **There is no question to benchmark.** See R3.

**Fixing (1) alone would have shipped a more authoritative version of the same
misleading comparison.** That is the outcome this ruling refuses.

### R3 — the denominator is LABELLED, not swapped, and Q22 was read to settle it

Retrieved from the instrument this round, hash confirmed identical to the
SHA-256 `renderers/_question_25.py:52` pins — 142 pp., 1,525,626 bytes,
`0280c6bc…12834f` — and text-extracted locally with `pypdf`. Printed p. 32
(PDF 59):

> **(c)** What is the minimum percentage of QLICIs that the Applicant is
> willing to commit to deploy in Non-Metropolitan Counties? `______%` ·
> *Numerical - Percentage*
>
> **(d)** What is the maximum percentage of QLICIs that the Applicant is
> willing to commit to deploy in Non-Metropolitan Counties? `______%`

**"Willing to commit to deploy", into a blank field, and the figure entered
*"shall become a condition of its Allocation Agreement with the CDFI Fund"*.**
It is the Question 25 shape one level down: a forward commitment about capital
the Applicant does not hold, not a measurement of the pipeline it does. Printed
p. 31 adds that *"Question 22 will not be evaluated and scored in Phase I."*

So swapping QEI for QLICI would move the figure closer to the **units** of a
commitment while leaving it a characterisation of a pipeline — more credible
and no more correct. **The basis stays QEI and every surface names it**, using
`renderers/_question_22`, which imports the denominator clause from
`_question_25` rather than retyping it.

**AN INCONSISTENCY IN THE INSTRUMENT, recorded so nobody "corrects" us toward
it.** The p. 31 NOTE says the range runs *"at or above the minimum indicated in
Question 22(b), but not more than the maximum percentage indicated in Question
22(c)"*. In the p. 32 table, **22(b) is a count of years (0-6)** and the
percentages are **22(c)** and **22(d)**. The NOTE also contradicts itself: its
Rural CDE sentence puts the 50% commitment at 22(c). The question table governs.
`docs/reference/methodology.md` had inherited the NOTE's letters and is
corrected.

### R4 — `non_metro_meets_minimum` deleted, and a name collision found underneath it

`win_probability.py:633` was `rural_pct >= 0.20`. **There is no 20% applicant
threshold.** The 20% is a Fund goal for *"all QLICIs made by Allocatees under
this Round"* and a bar on what an Allocatee **committed** to; Question 22 states
no minimum an individual Applicant must clear. **Consumers: none** — one write,
zero reads, in this package and its docs.

**AND THE LINE ABOVE IT WAS WORSE.** `non_metro_commitment_pct` **is a CDE
profile field.** `templates/cde_profile_sample.yaml:126` ships
`non_metro_commitment_pct: 0.22` — a CDE's own answer to Question 22(c) — and it
arrives in `_build_phase2_flags` through `CDEProfile.extra` → `cde_attributes`,
exactly like `has_favorable_fee_structure` two lines below, which **is** read
from `attrs`. Line 632 ignored it and wrote a computed pipeline share over the
top, **under the identical key and in different units** (the YAML is a fraction,
the flag was a percentage number). A CDE who declared 22% read back `7.0`.

**This is the fourth instance of this package discarding a column the CDE filled
in**, after `native_area`, `urban_rural` and the declared tract/distress pair.
The declaration now stands; the measured share is reported as
`non_metro_pipeline_qei_pct` with `non_metro_undetermined_qei_pct` beside it.
The word `commitment` no longer appears on anything this tool computed.

### R5 — the 18% traced, and then deleted rather than pinned

*"Winner rural mean: **18%**"* at `1_Pipeline_Analyzer.py:625` **does** trace to
`WINNER_GEOGRAPHIC_PATTERNS["rural_pct_mean"] = 0.18`, so it was pinnable. It is
deleted instead, per the premise ruling — pinning it would have made a
misleading comparison reproducible.

**THREE HAND-TYPED CONSTANTS SAT THERE, NOT ONE.** *"Winner median states: 7"*
and *"Winner mean HHI: 620"* were literals on the two adjacent lines and are
both keys of the same dict. Both are now interpolated. That takes the recorded
count of hand-typed numbers beside live figures from six to eight.

### R2 — the three-way split, and what happens to `_RURAL_STATES` and `_STATE_MSA_MAP`

`_RURAL_STATES` is **deleted**. Its worst property was not that the twelve were
wrong: `rural_pct` was `1 − urban_pct` where "urban" meant *"in a state absent
from the list"*, so **Alaska, Nebraska, Iowa, Oklahoma and thirty-four other
states were counted metropolitan by default — as was every project the tool had
failed to verify.** Nothing was ever determined to be metropolitan. Three of the
twelve (`MS`, `KS`, `NM`) were simultaneously assigned MSAs by `_STATE_MSA_MAP`
four lines below.

`_STATE_MSA_MAP` is **kept**, ruled separately. It feeds `msa_count`, `msas` and
the per-state MSA label — never the county determination — so deleting it as
collateral would remove the MSA figure from three surfaces for reasons that have
nothing to do with the defect. It is **still wrong** and is recorded rather than
repaired: one MSA per state means `msa_count` can never exceed `states_count`,
and a nineteen-state pipeline reports nineteen MSAs regardless of how its
projects are distributed. A real fix needs CBSA codes per tract, which
`nmtc-mapper` does not return. 1.4.x.

The replacement is three-way and is **not reducible to two**:

| `project.is_non_metro` | bucket |
|---|---|
| `True` | non-metropolitan |
| `False` | metropolitan |
| `None`, or never geocoded | **not determined** |

`None` is not `False`. The three shares sum to 1.0 for any pipeline with QEI,
and the undetermined slice is rendered on every surface — including in the donut
at zero, so the category stays a category.

### THE CLI SUMMARY NOW HAS A BASELINE, AND CAPTURING IT FOUND THE WORST CASE

`tests/cli_baseline/analyze.txt` captures `nmtcapp analyze` across five analyzer
states, replaying twenty recorded `nmtc-mapper` answers so no network is needed.
**43 lines move between `56573c0` and this commit, every one of them inside the
Geographic Diversity block, zero unexplained.** The `unavailable` state is why
it was worth building: with the CDFI Fund eligibility dataset unloadable and not
one project verified, `56573c0` printed

    Urban/Rural:     93% / 7%

— a confident two-way split for a pipeline about which the tool knew nothing.
No test in the tree rendered the summary in that state, so nothing could see it.
It now prints `0% / 0% / 100% not determined`, and
`test_the_degraded_states_do_not_report_a_determined_split` asserts it as a rule
rather than as a baseline.

### THE RENDERED BASELINE MOVED, AND THE BRIEF DID NOT EXPECT IT TO

The round was scoped on the finding that `rural_pct` reaches no generated
document. **That finding is correct and was re-verified.** What moved the
baseline is R1, not R2: `renderers/_question_25`'s basis note states, on all
four surfaces, that this package *"carries NOTHING for Non-Metropolitan
Counties"*. Carrying `PipelineProject.is_non_metro` made that sentence **false**
the moment the field landed.

**Leaving it was not an option available.** The note's own paragraph heading is
*"WHICH OF THE CDE'S QUALIFYING ROUTES ARE VISIBLE HERE"*, and the module was
written against exactly this direction of error: *"the 1.2.2 note's 'computes
neither figure' was true and unhelpfully pessimistic"*, and understating the
package pushes the CDE to **understate itself to a federal agency** — the false
negative this file's header ranks as the worst class of error in the package. So
`Q25_AREA_TYPES_MODELLED` goes 5 → 6 and Non-Metropolitan Counties joins the
provenance enumeration as TOOL-VERIFIED AND TRI-STATE.

> **54 insertions, 44 deletions** in `tests/rendered_baseline/`, measured
> `56573c0`..`HEAD`, in `excel.txt`, `markdown.txt`, `pdf.txt` and `word.txt`.

**Every changed line classified, zero unexplained:**

| Class | Lines | +/− | Surface |
|---|---|---|---|
| Section B basis note — markdown and word render the whole note as ONE line each, so both changes land on one line per surface | 4 | +2 / −2 | markdown, word |
| `Q25 Basis Note` sheet — `A6` gains "6 of the 14"; `A8`/`A9` re-chunk at the sentence boundary the new text pushed past 800 chars. No row added | 6 | +3 / −3 | excel |
| The note itself, re-wrapped across the PDF column — "5 of the 14" → "6 of the 14" and the Non-Metropolitan Counties sentence | 28 | +17 / −11 | pdf |
| Page renumbering — the longer note pushes one page break, so `@@PAGE n` and `Page n` shift by one from page 21 onward | 58 | +30 / −28 | pdf |
| The new page's furniture — one CONFIDENTIAL footer band and one blank line | 2 | +2 / −0 | pdf |
| `Item`/`Value` extraction rows — none; no table gained or lost a row | 0 | +0 / −0 | — |

**No figure moved.** Not one number in any of the four documents changed: the
diff is the basis note's prose, the count it interpolates, and the pagination
that prose displaced.

### Also in this round

- **Test doubles are built from the installed dataclass** (`tests/mapper_doubles.py`).
  Two files hand-listed `SimpleNamespace` stand-ins for `EligibilityResult` —
  the same "validates the mock, not the library" shape that let 0.5.0's removal
  of `is_nmtc_native_area` through every gate. Adding one read broke eight tests
  with `AttributeError` on the double; the fix is that the doubles cannot drift
  again.
- **`BENCHMARK_METRIC_WEIGHTS` no longer sums to 1.0, and that is correct.**
  `_weighted_score` divides by the weights actually present. The test that
  pinned the round total was measuring a coincidence: it went red on a
  mathematically identical benchmark, and would have gone green on a metric
  added without a weight — which scores 0.0 and drags the total down silently.
  It now asserts the weight keys and the metric keys are the same set.
- **`Constraints.min_rural_pct` removed. It was declared and never enforced** —
  `is_feasible` never read it, in any release, while two documentation pages
  listed it as a working constraint. Removing it changes no optimizer behaviour
  because it governed none.

### Found and NOT fixed

- **`core/application.py:181` logs `"allocation $%,.0f"`**, which is not a valid
  printf conversion in Python. **Every `Application()` construction raises inside
  `logging.Formatter` under any INFO-level configuration**; `logging` swallows it
  and prints a "Logging error" traceback instead of the record. Found by the CLI
  capture, which pins its handler at WARNING partly for this reason. It is in the
  1.3.2 queue the brief fenced off, and it is worse than "a formatting typo".
- **`nmtcapp/core/upload_handler.py:43` maps an `Urban/Rural` upload column to
  `urban_rural`, which `from_csv` never reads.** It was NOT wired into
  `is_non_metro`, deliberately: "Rural" is the CDE's own word and
  "Non-Metropolitan County" is an OMB county designation. Merging them would
  recreate, one layer down, the conflation this round removed.
- **`WINNER_GEOGRAPHIC_PATTERNS` remains unsourced** and is still read by
  `pattern_analysis.compare_to_winners` as a reference table. Removing the
  benchmark removed the place where an unsourced mean was *scored against* a
  CDE. The constants themselves are the separate `historical_awards` workstream.
- **`CITATION.cff` says `1.3.0`** and nothing gates it. Bumped to `1.4.0` here;
  the gate is not built.

---

## [Unreleased] — 1.3.1

**PATCH. The eight findings the 1.3.0 confirmation pass returned SHIP with,
plus four things a CDE reads on a screen and nowhere else.**

**THE DEFINING CONSTRAINT, AND IT HELD.** `tests/rendered_baseline/{pdf,
markdown,word,excel}.txt` are **byte-identical to `0643296`** — `git diff`
against them is empty. Nothing in this round touches a generated document.
Three changes came close enough to be worth naming: the frame constants moved
out of `pdf_builder` into `_frame_geometry` (G6), the three distress row labels
moved out of `section_b_outcomes` into `distress_table` (F2), and every
truncated-list call site moved onto one helper (F1). All three were made as
byte-for-byte moves and the baseline gate was run after each.

### Part 0 — the fix round: one false sentence about refusal, and four cheap things

A hostile audit returned SHIP conditional on one docs edit. It confirmed both
renderer diagnoses, re-derived `FLOOR=560` to the digit, and cleared
`section_b_outcomes.py`. Then it found a sentence the build round did not.
**The four baselines did not move in this round either** — verified by blob
hash against `0643296`, not by running the gate, and **no file under
`nmtcapp/` is modified at all.**

- **R1. The docs site published a false statement about the package's refusal
  behaviour, and the page's own build was the counterexample.**
  `docs/hooks/generate_sample_output.py` wrote *"The package refuses to score
  or generate against this identity outside demo mode"* onto the Sample Output
  page, and thirty lines below the sentence called `CDEProfile.sample()` →
  `Application.generate()`, publishing four filing-shaped documents for
  Riverbend at **Readiness Grade A, 86.6/100, $65,000,000**. Proven by
  execution both ways: `sample()` → `generate()` returns four formats with no
  exception; `from_yaml()` on the shipped sample raises `SampleDataError`
  naming the **CDE name** field. The mechanism is that `sample()` is a
  classmethod calling `cls(...)`, `__post_init__` does not check, and
  `generate()` does not check — **the sample path is unguarded, not
  misdirected.** The sentence now states the boundary that exists: the refusal
  sits on `CDEProfile.from_yaml()` (and so on `nmtcapp analyze --cde`, verified
  by running it) and on the Streamlit upload, and on nothing else.
  **Sharper than the audit's framing:** there is no CLI `generate` subcommand
  and no Streamlit generate path, so `Application.generate()` is the *only*
  way to produce a document at all — and it is the path with no guard on it.
- **R1 gate. `tests/test_docs_refusal_claims.py`, and what it cannot see.**
  Four tests: the guard's call sites are exactly
  `{nmtcapp/core/cde.py, streamlit_app/utils.py}` by AST walk; the unguarded
  path is executed and must succeed; the guarded path is executed and must
  refuse and name the field; and every sentence on eighteen published surfaces
  matching a refusal vocabulary must be registered with the basis it was
  checked on. **It does not parse English** — the broad version is not
  buildable, so what is built is a registry that turns a new refusal claim into
  a review event. It is blind to synonyms and to files outside its list, and
  says nothing about whether the refusal is correct policy. The registry
  immediately caught a fourth claim the manual sweep had missed (see below).
- **R2. The published quickstart taught the unguarded path.** `docs/index.md`
  opened with `CDEProfile.sample()` → `app.generate("./drafts/")` as the first
  code block a visitor reads. **Ruled: a caveat above the block, not a
  blank-template rewrite** — and ruled by execution rather than taste.
  `nmtcapp init` then `CDEProfile.from_yaml()` on the scaffolded file raises
  `ValueError: ... is missing 7 required fields`, so a blank-template-first
  quickstart's opening block **cannot run at all**. The quickstart's job is to
  work in sixty seconds; the safer shape does not work in any number of
  seconds. Caveat added; the working block kept.
- **R3. A gate justified its ruling by quoting a heading that exists nowhere.**
  `tests/test_truncated_lists.py` cited *"Recommended Actions"*; the real
  heading is *"Recommended Improvements Before Submission:"*. **The ruling
  survives** — checked against the rendered baseline, where the heading states
  no count — so only the citation was invented. **The prompt for this round
  said one site; there were two.** The second sits in the comment block with
  the quote split across a line break, so a whole-tree grep for the exact
  string does not find it — the same shape as the miss that produced the
  finding. Every other quoted heading in the four new test modules was verified
  against the surface it claims to quote; the rest hold.
- **R4. Three hand-typed "48"s in the round about hand-typed counts, and a
  fourth surface the gate could not see.** Derived, not assumed:
  `0643296` collects **1,097** unfiltered and **1,096** under `-m "not wheel"`;
  `30e8146` collects **1,144** and **1,143**. **Both deltas are 47, not 48.**
  Corrected in `CHANGELOG.md`, `.github/workflows/release.yml` and
  `tests/test_release_floor.py`. Separately, `CONTRIBUTING.md` said
  `# all 544 tests` — **stale by 600** — and `_CLAIM_SITES` covered only
  `README.md` and `streamlit_app/app.py`, so **the gate whose docstring claimed
  every surface stating a test count read two of three.** The miss was one
  absent `(?:all\s+)?` alternative in the pattern; it is now in both patterns
  and asserted by a sensitivity check on the exact line that shipped wrong.
- **R5. The 189-run under-check had no regression test, and now goes red.**
  `test_the_chrome_exemption_is_a_bound_and_not_a_skip` asserts the footer
  heights and the exempted runs **by calling `is_chrome_baseline` directly** —
  it never calls `check_pdf_frames`. Reverting the band selection to the exact
  1.3.0 height test left **all 24 gate tests green**, shown. The new
  `test_the_band_selection_asks_the_predicate_and_not_the_height` drives
  `check_pdf_frames` over a constructed one-run PDF where the two rules
  disagree (y=55 pt: below the frame bottom, not at a footer baseline) and
  asserts both directions. **With the revert re-applied it is the only test
  that fails — 1 failed, 24 passed** — then restored.
  **A figure this round could not reproduce:** the "189 of 1,091 runs" belongs
  to the base gate's pypdf-visitor extraction, not to HEAD's content-stream
  parser. On the base-rendered document at HEAD the two rules agree **exactly**
  (44 runs each, 0 mis-banded), which is precisely why the revert is invisible
  to every other test and why the disagreement has to be constructed.

### Part 0b — the docs-claim sweep

Nothing in this project had ever swept the documentation for claims about the
package's behaviour and **executed** them. Doing so found three more false or
misleading statements beyond R1:

- **`docs/index.md` said the quickstart block "writes the pipeline analysis
  summary to the terminal". It writes nothing** — 0 chars to stdout and 0 to
  stderr, measured. `generate()` logs at INFO to a logger the package never
  configures a handler for; the thing that prints a summary is
  `analysis.summary()`, which the block never calls. Corrected.
- **`docs/workflow/recommendations.md` said `quantified_improvement` "always
  contains a numeric estimate". The field is `str`** — annotated
  `quantified_improvement: str`, and the page's own sample output two
  paragraphs above shows prose. Corrected to say so.
- **`README.md`'s "The app keeps working; it never hard-blocks" is true for the
  documented failure and false for the rest** — found by the R1 registry gate,
  not by hand. Executed both ways on an unenriched pipeline: on
  `NMTCMapperError` all six operations succeed, status becomes `unavailable`
  and the banner renders; on **any other exception** from the data layer
  `analyze()` raises `RuntimeError` at `application.py:250-254`.
  `nmtc_mapper_adapter`'s own docstring says *"Unexpected exceptions
  propagate"*, so the behaviour is intended and the sentence simply does not
  scope it. **Registered with that basis and deferred to 1.3.2** rather than
  reworded here.

Claims run and found **true**: `Pipeline.from_csv` raises `FileNotFoundError`
and `ValueError` as `api.md` states; Markdown output really is available with
`docx`, `openpyxl`, `reportlab` and `matplotlib` all forced unimportable;
`_METHODOLOGY` is exposed on result objects; all four formats really are
generated fresh on every docs build. **True but not provable from outside on
this input:** the optimizer's no-regression guarantee — the sample pipeline
returns `alignment_score_after == alignment_score_before` at 0 iterations, so
the guarantee is untested rather than confirmed.

**Deferred, with reasons, not silently dropped:** `application.py:181` logs
`"allocation $%,.0f"`, which is not a valid `%` conversion, so **every
`Application(...)` raises a logging `ValueError` for any consumer who
configures INFO logging** — real, confirmed, and **pre-existing since the
initial commit `db4277e`**, so it is 1.3.2 rather than a runtime change inside
a docs-and-gates round. The published Sample Output page is also not
markdown-rendered at all: the hook writes `html.escape(...)` inside a `<pre>`,
so the `!!! warning` box a reader sees is literal source text. Also
pre-existing, also 1.3.2.

**FLOOR re-derived and unchanged.** Built the sdist, installed the tarball with
`[dev]` into a fresh venv, copied only `tests/`, `streamlit_app/`, `README.md`
and `pyproject.toml` out of it into a directory with **no `nmtcapp/`**, and ran
the job's exact invocation: **1,150 collected under `-m "not wheel"`, 25
skipped, 1,125 executed, half 562, rounded down 560** — identical on **3.9.25
and 3.12.13**. `MAX_SDIST_SKIPS` stays 28 but now sits **three** skips above
its measurement and two below the point the band goes slack, and the comment
says so instead of still claiming five and sixteen. The `3.9.12` recorded in
three places was a typo for `3.9.25`; no `3.9.12` was ever run.

### Part 1 — the gates

- **G1. The fetch-depth guard was the shape it was written to prevent.**
  `assert "fetch-depth: 0" in text` over the whole of `ci.yml`. Executed: the
  line commented out **passes**, and the line deleted from the `test` job and
  added to the `docs` job **passes**. Only outright deletion failed it. It
  parses the workflow now and asserts `fetch-depth: 0` on the `test` job's
  `actions/checkout` specifically; shown red three ways.
- **G1b. The "fourteen instances" tally is gone from five files.** It was
  hand-maintained and restated in `ci.yml`, `test_pinned_constants`,
  `test_qlici_basis`, `validation/consistency_check` and this file — five
  chances for one number to go stale, which is the defect the entry it points
  at is about. The pattern name does the work; the tally did not.
- **G2. The two PDF gates' self-tests were crossed.** The rendered checker had
  a vacuity proof and no sensitivity proof; the modelled checker had a
  sensitivity proof and no vacuity proof; and the module docstring said "tested,
  twice", which was true of the pair and false of either. Each now has both.
  The three `Table` failure modes are executed and the matrix pinned: mode 1
  (no `colWidths`, `str` cells) reaches both gates, mode 2 (no `colWidths`,
  `Paragraph` cells) correctly reaches neither, mode 3 (`colWidths`, tall row,
  no `splitInRow`) raises `LayoutError` at build time and reaches neither —
  written down so "the frame gates are green" is never read as "the table
  renders".
- **G3. The frame gate's false positive was real, and the diagnosis it came
  with was wrong.** Reproduced at 45 and 50 projects (page 5, the
  aggregate-impact bullet list) and absent at 20. It is NOT pypdf merging runs
  across visual lines — the `Tj` is a single positioned operation. Two
  independent faults, both in the measurement:
  1. **A unicode round trip that does not close.** ReportLab's WinAnsiEncoding
     puts `bullet` at code 0x7F where the PDF spec leaves the code unused. So
     ReportLab draws a bullet as byte 0x7F, pypdf decodes 0x7F to U+007F (DEL),
     and `pdfmetrics.stringWidth` cannot encode U+007F in winansi and charges
     0.761 em where the bullet it drew is 0.350. Three bullets on one line
     inflated it by 13.6 pt at 11 pt. **The line measures 420.00 pt exactly —
     the frame's inner width to the hundredth — and was reported at 434.15.**
  2. **The y coordinate was not a coordinate.** pypdf's visitor advances its
     text matrix by leading × font size rather than by leading, so continuation
     lines came back 165 pt low instead of 15. Runs deep in a wrapped block
     arrived at y = −1,109 where they are drawn at y = 77 — and since the band
     is chosen by height, every one of them was measured against the CHROME
     band, 18 pt wider each side than the frame they are laid into. **The gate
     was false-positiving and under-checking at once, and only the first was
     visible.**

  Fixed at the measurement, not the threshold: runs are read from the content
  stream through the PDF's own text-state machine and measured from raw bytes
  against code-indexed font widths. Findings at 20/45/50 projects: **1.3.0 →
  0 / 1 / 1; 1.3.1 → 0 / 0 / 0**, and the sizes are kept as a regression.
- **G4. The frame gate ran one fixture where the Excel gate runs three.** Both
  PDF gates are parametrised over `("nominal", "partial_unverified",
  "degraded")` now, off the same helper `test_excel_geometry` uses. What the
  parametrisation still does not cover is enumerated in the module: pipeline
  size (covered separately, nominal only), CDE-supplied text, page size and
  font, and the cover page's own frame.
- **G5. The absorbed-fragment counts were printed, not asserted — and the
  printed parent count was not even stable.** `wrapped_fragments` took its
  parent from an unordered `set`, so on one unchanged tree the same gate
  printed **8, 9, 10 and 13 across five `PYTHONHASHSEED` values** while
  reporting it as a fact. Hand-typing "14" would have shipped a flaky gate.
  Made deterministic (longest parent first), and the count replaced with the
  property the narrowing actually claims: **a wrap is one sentence seen through
  two geometries, so a fragment appears on a surface its parent does not.**
  Measured: all 91 N-WRAP fragments appear on the PDF and nowhere else; all 11
  parents appear on Word (6), Markdown (3) or Excel (2) and never on the PDF.
  Zero exceptions, which is what makes it assertable — and growth to 191
  passes if all 191 are wraps, while one invented sentence fails at any total.
  Both narrowings carry a proof that the refusal fires.
  `test_the_wrap_narrowing_cannot_absorb_a_new_claim` was read and does what
  its name says: three cases, against the real allowlist.
- **G6. The frame constant was duplicated and untied — and the planning note
  was wrong about it.** `FRAME_BOTTOM_INCHES` **does** exist, in
  `renderers/_frame_geometry`, and `CHROME_BAND_TOP_PTS` is derived from it in
  the renderer package rather than carried by the gate. What was true is the
  rest: `pdf_builder` hardcoded `0.9 * inch` at five sites (`:339`, `:341`,
  `:348`, `:350`, `:360`) and `inch` / `0.75 * inch` at four more, and nothing
  tied any of them to the module the gate measures against. All nine now read
  the constants, and `test_the_renderer_lays_out_against_the_constants_this_gate_measures`
  reads the frames back off a real `BaseDocTemplate` — not a grep — so it holds
  however the value is spelled.
- **G6b. The chrome exemption was a skip; it is a bound.** The footer band is
  18 pt wider each side than the body frame, and the gate handed it to anything
  drawn below `CHROME_BAND_TOP_PTS` — a height test, which gives the slack to a
  body flowable that lands low as readily as to a page number, and which G3's
  second fault was silently exploiting on every wrapped block. It is granted
  only to runs at a height the footer actually draws at now, and two things are
  asserted: every footer height is below the frame bottom, and every run
  granted the band is the footer.
- **G7. The FIX-2 accounting was wrong in more ways than reported.** The
  planning note said the table counts 10 where the tree says 16. It does — and
  **all five rows are wrong, and they sum to 194, which is the correct total.**
  Re-derived: 16 / 14 / 87 / 10 / 67 against 10 / 13 / 96 / 9 / 66. The prose
  was wrong too — "six distress row labels wrap"; four did.
  `test_the_changelogs_rendered_baseline_delta_matches_the_tree` did not catch
  it because **it parses the blockquote and was never given the table**: it
  asserts the total and the file set, and a hand-typed breakdown under a
  machine-checked total can be arbitrarily wrong so long as it adds up.
  `test_the_changelogs_baseline_class_table_adds_up` is the answer and is
  honest about its reach — it re-derives the one row that is a rule rather than
  a reading and pins the other four to the residual jointly. **And "nothing
  moved on the page" was false**: before B1 the Section B header row was drawn
  as part of a 17,197 pt table that ReportLab centres, putting `Item` at
  x = −8,293.7 pt against x = 95.0 after. See the corrected table in the 1.3.0
  entry.
- **G8. 1.3.0 was still marked Unreleased.** Closed with its real publish
  time, `2026-08-19T21:23:03Z`, read from the PEP 691 simple index
  (`nmtc_application_builder-1.3.0-py3-none-any.whl`, `upload-time`
  `2026-08-19T21:23:03.332923Z`) rather than from the CDN-cached JSON API.

### Part 2 — what a CDE reads

- **F1. A truncated list under an untruncated count, on four surfaces.** Swept:
  every `[:N]` in `nmtcapp/` and `streamlit_app/`, ruled site by site. Four
  were this defect — `intelligence/pipeline_analyzer:77` (the `nmtcapp analyze`
  block), `streamlit_app/pages/1_Pipeline_Analyzer:253`,
  `validation/eligibility_check:43` and `integrations/cdfidata_adapter:77` —
  and the correct pattern already existed at exactly one call site,
  `sections/section_a_business:42`, which four later call sites did not find.
  One statement now, `renderers/_disclosure.join_truncated`, with the existing
  " and others" suffix unchanged so no document moves; the exemplar reads it
  too. Gated syntactically over the tree (AST, so a docstring example is not a
  call site) **and** behaviourally on a pipeline with more unverified projects
  than the preview limit. Both go red on the restored defect.
- **F1b. A methodology disclosure cut mid-sentence, with no ellipsis.** Found
  by F1's sweep and sharper than F1. `intelligence/benchmarks:110` printed
  `methodology_disclosure[:140]` of a 352-character sentence, under the heading
  `Methodology:`. What survived read as a credential; what the cut removed was
  *"non-winner distributions are unknown"*, *"Scores reflect alignment with
  historical winners, not probability of selection"* and *"not as a prediction
  of funding outcomes"* — the whole of the disclosure's work.
  `optimizer/pipeline_optimizer:104` cut the same class at 120 characters and
  lost *"Alignment score ≠ win probability"*. **Truncating body text is a
  display decision; truncating a disclosure changes what the document says, in
  the direction that flatters the tool.** Both wrap now.
- **F2. The Streamlit distress metrics without their basis — and the planning
  note named the wrong metric.** The Deep/Severe metric already carries
  `Q25_QEI_BASIS_CLAUSE`; 1.3.0's B1 ride-along put it there. The two beside it
  did not: `LIC (standard)` and `Native area (CDE-declared)` printed a share of
  QEI with no denominator on its face, next to a metric that names its own. The
  claim that no Streamlit file imports `qualified_pct` is **confirmed** — every
  consumer is under `nmtcapp/renderers` or `nmtcapp/sections`. Fixed by
  CARRYING the document's own labels, extracted byte-identically into
  `tables/distress_table` and imported by both; no wording was composed. The
  gate's AST walk immediately found two more bare percentage metrics on the
  same page (`Rural share`, `High-priority sector %`), which **no document
  renders with a basis**, so there is nothing audited to carry — ruled with the
  reason and reported for 1.4.0.
- **F3. Three test counts on rendered surfaces, none of them right.**
  `streamlit_app/app.py:86` said `890+ tests`; `README.md:289` said
  `# 544 tests`; the tree collected 1,097 at `0643296`. This README has been
  wrong at 658, 544 and 890+. Both corrected to the derived count, and
  `test_a_published_test_count_is_the_one_the_tree_collects` re-derives it with
  `pytest tests/ --collect-only -q` in a subprocess — the same command a reader
  would run — rather than pinning a number.
- **F4. The `[output]` extra was invisible, and worse than reported.** Nothing
  a CDE following the advertised path ever named it. **And there is no CLI
  path to a document at all:** `nmtcapp` has three commands — `init`, `analyze`,
  `version` — and `analyze` prints a report and writes no file. `init`'s "Next
  steps" offers the notebook or `analyze`, and the notebook's `app.generate()`
  line is commented out with no mention of the extra. So a CDE could follow
  every instruction the tool gives and never produce a document. The skip
  message names the extra and the exact install command now (and not just the
  one library, which gets a reader to three of four formats and stops), `init`
  prints it, and the notebook says it beside `generate()`.

### Release plumbing

- **`FLOOR` was stale and the gate is what said so.** 1.3.1 adds 47 tests and
  `test_release_floor_is_derived_from_the_current_suite` went red on
  `FLOOR=530` before anything in `release.yml` was touched — **the first stale
  floor in this file's history caught by a check rather than by somebody
  re-reading the comment beside it.** Re-derived from a pristine clone with the
  job's exact invocation — built the sdist, installed the tarball with `[dev]`
  into a fresh venv, copied only `tests/`, `streamlit_app/`, `README.md` and
  `pyproject.toml` out of the tarball into a directory with no `nmtcapp/` in
  it, and ran from there, **not from inside the unpacked tarball**, which is
  the derivation error FIX-2 recorded:

  ```
  collected under -m "not wheel"  1,143
  skipped in the sdist              -23
  EXECUTED                        1,120
  half                              560
  rounded down                      560
  ```

  Identical on 3.9.25 and 3.12.13: both 1,120 passed / 23 skipped / 1
  deselected. **`MAX_SDIST_SKIPS` went 24 → 28** at the same time: the sdist
  skipped 20 at FIX-2 and skips 23 now, so the ceiling had **one skip of
  headroom left**, and a ceiling about to be crossed by its own measurement
  bounds nothing. All 23 are environment skips and each names its reason; the
  three new ones are `test_the_changelogs_baseline_class_table_adds_up` (needs
  a git checkout) and `test_truncated_lists`' two source-reading checks.

### Refuted

- **`FRAME_BOTTOM_INCHES` does not exist.** It does. See G6.
- **The frame gate's false positive is pypdf merging runs across visual
  lines.** It is not. See G3.
- **The Streamlit distress metric renders a percentage with no basis
  qualifier.** The distress metric carries it; the two beside it did not. See
  F2.
- **The FIX-2 table counts 10 where the tree says 16.** True, and incomplete:
  all five rows are wrong. See G7.

---

## [1.3.0] — 2026-08-19, published 2026-08-19T21:23:03Z

**MINOR, not PATCH, and for TWO reasons — the second was missing from this
entry until FIX-2.**

1. **S3 changes what an existing user's document says without their input
   changing:** an upload with no `qlici_amount` column used to print the
   project's QEI request under the heading **Total QLICI ($)**, and now prints
   `not supplied [CDE TO COMPLETE]`.
2. **B3 changes what an existing user's input MEANS.** `prior_awards: []` — the
   value the shipped scaffold tells a first-time CDE to write — used to load
   through `CDEProfile.from_yaml` and then fail `validation/completeness_check`
   with *"CDE profile missing required field: prior_awards"*. It now passes
   both. **A validator's verdict moved**, which is an accepted-input change and
   is the textbook reason a release is a minor rather than a patch. See B3
   below; it shipped in `ff49064` and this entry did not mention it.

Both are the same shape as 1.1.6 → 1.2.0, where `analyze` began exiting 2 where
it used to run. **The minor bump licenses no extra scope** — the deferred list
at the foot of this entry is unchanged.

### S1 — the basis note instructed a CDE to compute the wrong number

Rounds 1 and 2 of the 1.2.2 cycle removed six claims that **overstated** what
the CDFI Fund requires. This is the opposite, and **the first false negative in
this package**: a shipped instruction that causes a CDE to **understate its own
qualifying share to a federal agency**. Same class as `nmtc-mapper` 0.4.2
reporting 168 tracts ineligible when they statutorily qualified.

The shipped note quoted the *CY 2024-2025 NMTC Program Review Process* — a real
Fund sentence, correctly attributed — and told the CDE to compute a
deep-distress share of QLICIs and compare it to 20%. **Question 25 of the
Allocation Application shows that instruction wrong twice over:**

1. **The 20% is the top rung of a ladder, not a bar.** Question 25(b)(i)'s
   Response column is a dropdown reading *"0 / 5 / 10 / 15 / 20, if selected
   enter exact percentage 20-100% in 25(b)(ii)"*. A CDE that could honestly
   commit 10% read our note as a pass/fail threshold it misses.
2. **Question 25(b) is four area types.** Deep Distress, NMTC Native Areas,
   High Migration Rural Counties and U.S. Island Areas. A CDE with Native
   Area, High Migration Rural or Island Area QLICIs left them out of a
   numerator they belong in.

**Both errors push the same direction.**

The corrected note also carries what the summary compresses away: Question
25(a) is denominated in QLICIs *"in terms of aggregate dollar amounts"*, tested
**for each QLICI**; *"multiple indicia of distress"* is specifically **at least
two of items 6-12**, beside a **one of items 1-5** alternative; and *"A QLICI
that meets this commitment will also automatically meet the commitment made in
Question 25(a)."*

**And it says what the tool CAN see.** "Computes neither figure" was true and
unhelpfully pessimistic. The note now states that this package carries a
per-project field for **five of the fourteen** distinct area types Question 25
lists — a tool-verified distress level covering Severe and Deep Distress, plus
CDE-declared, unverified flags for NMTC Native Areas, High Migration Rural
Counties and U.S. territory — and **nothing** for Non-Metropolitan Counties,
Targeted Populations, or any of items 6-12. It says so in the same paragraph as
the sentence that denies it is an answer, because *five of fourteen* reads as a
partial answer and is not one: the commitment is a share of QLICI **dollars**,
this package weights nothing by QLICI dollars, and a flag that enters no
denominator contributes nothing to a share. That sentence is pinned
(`test_qlici_basis.REQUIRED_NOTE_CLAUSES`) so the field list can never render
without it.

The text moved to **`nmtcapp/renderers/_question_25.py`**, one authority read by
every surface. It had been four near-identical copies, of which the workbook's
was missing entirely — which is exactly how S4 happened.

**Refuted while writing it:** the brief for this round said the package "already
returns severe distress and non-metropolitan status". It does not return
non-metropolitan status. `PipelineProject` has no such field; the only
non-metro figure in the package is `geographic_diversity["rural_pct"]`, a QEI
share over a **hard-coded twelve-state list** (`geographic_analysis.py:16`), not
the OMB Bulletin 20-01 county definition Question 25 item 4 names. The note says
five of fourteen, not six, for that reason.

### S2 — two constants whose comments were known-incomplete

`SEVERE_DISTRESS_MIN_PCT` and `DEEP_DISTRESS_MIN_PCT` were classified **CITED**
in `tests/fund_attribution_allowlist.txt`, ruled correct against the Review
Process, and incomplete against the Application. Both comments corrected; both
allowlist entries re-ruled against the instrument. **Neither became a DEFECT** —
DEFECT means *the authority does not state it*, and the Review Process does
state both sentences. `EXPECTED_DEFECTS` stays **0**; no stop-and-report was
triggered.

Which is precisely why the gate's own documentation now says so, in
`tests/test_fund_attribution_source.py` and at the head of the allowlist:

> **`EXPECTED_DEFECTS = 0` means "no false attributions among those ruled". It
> does not mean "none remain". A gate is exactly as good as the DOCUMENT its
> allowlist was ruled against.**

Measured, not asserted: the 1.2.2 sweep ruled every entry against a seven-page
**summary** and went 6 → 0 honestly on that basis, and this round found two
false-negative defects underneath a green gate reading zero.

### S3 — the QLICI figure the CDE never supplied

`core/upload_handler` set `qlici_amount = qei_request` whenever an upload
omitted the column. Silently. That value rendered as **Total QLICI ($)** — the
CDE's own answer to the Fund's Table A5 row (h) — and satisfied the QLICI ≤ QEI
consistency rule by being exactly equal to the QEI it was copied from.

- **Provenance is carried, not re-detected.** `PipelineProject.qlici_amount_supplied`.
  The obvious cheap check (`qlici_amount == qei_request`) is true of both
  shipped samples, of `Pipeline.sample()`, of the pin fixtures and of the
  baseline fixture, and would misfire on a CDE whose figures legitimately
  match. `test_provenance_is_not_inferred_from_equality` is the gate.
- **It does cross a serialization boundary**, as the brief suspected.
  `load_uploaded_pipeline` writes a temp CSV and re-reads it through
  `Pipeline.from_csv`, so the flag rides the CSV as a column rather than being
  set on the way past. `test_the_flag_survives_the_temp_csv_boundary` pins the
  reason.
- **Warned at upload time**, in `upload_handler` (logger) and on the Streamlit
  uploader (read off the carried flag, not re-derived).
- **`consistency_check`: RULED NOT-CHECKABLE AND REPORTED, NOT SKIPPED.**
  *Rejected — skip silently.* `ValidationResult.passed` stays True either way,
  so a reader cannot tell "checked and passed" from "not checked at all"; that
  turns a trivially-passing check into an invisibly-absent one, which is the
  same defect one level down and harder to see. This module already refuses
  that shape — `CrossSurfaceCheckError` is *raised* rather than returned for
  exactly this reason. "A gate that cannot fail is also a green tick" is this
  package's most-repeated finding; this file is where the instances are
  recorded, and a tally of them used to be restated in four other files, where
  it could only ever go stale. Removed in 1.3.1 (G1).
- **The TOTALS row refuses to sum around it.** A not-supplied cell poisons its
  own column total and no other. An absent affordable-unit count is still NaN
  and still sums with skipna — those are different facts and do not share a
  rule.

**Refuted:** the brief said the defaulted figure renders "markdown, Word, PDF
**and** Excel". It renders on **markdown and Excel only**. `Total QLICI ($)` is a
column of `build_pipeline_table`, and only those two renderers publish that
table — Word and PDF print the six-column `build_pipeline_summary_table`, and
Word's landscape continuation names twelve columns of which QLICI is not one.
`grep -c "Total QLICI"` over the committed baseline returns **1, 0, 0, 1**.
Inventing a QLICI column for two surfaces that deliberately do not carry one, in
order to make a test pass, would have changed the shape of a federal
attachment; instead those two carry a **disclosure sentence** beside the caption
that already directs the reader to the workbook for "QLICI structure". So all
four surfaces disclose it — two in a cell, two in a sentence — and
`test_the_surface_split_is_still_what_it_was_measured_to_be` fails closed if a
renderer ever starts or stops publishing the column.

**Also refuted:** "every fixture in the package collapses the two".
`tests/test_qlici_basis._divergent_pipeline`, added by 1.2.1's FIX-3, already
diverges them — but it constructs `PipelineProject` objects directly, so it
never crosses the upload path where the defaulting happens and never renders a
document. Two new fixtures in `tests/test_qlici_not_supplied.py` close that:
an **upload** whose QLICIs differ from its QEIs (at three distinct ratios, so a
fixed ratio cannot hide a proportional-scaling defect), and an upload with the
**column absent**. Converting the remaining collapsed fixtures is 1.3.1.

### S4 — the Excel cell with no denominator

`Summary Dashboard!A12` read **"Deep/Severe Distress Concentration"** over a raw
float under a percent format: no denominator in the label, and **no basis note
anywhere in the workbook**. The one artifact of the four carrying neither half
of the 1.2.1 remedy, and the one a reviewer opens to copy figures out of. A CDE
copying that cell into Question 25 files a QEI figure against a QLICI
commitment.

1.2.1's CHANGELOG recorded *"the workbook contains no basis note anywhere: zero
occurrences of 'BASIS NOTE'"* as a verified fact. It was verified as the absence
of a **spurious claim**. It was also the absence of the **remedy**, and nothing
in the package could tell the two apart.

The label now names its basis and the workbook carries the S1 note, from the
same function Section B reads.

### The rendered baseline moved — for the first time this cycle

> **13 insertions, 4 deletions** in `tests/rendered_baseline/`, measured
> `63443cc`..`ff49064`, in `excel.txt`, `markdown.txt`, `pdf.txt` and
> `word.txt`.

**CORRECTED IN FIX-2, AND IT IS THE SIXTH STALE HAND-TYPED COUNT OF THIS
CYCLE.** This paragraph shipped as *"Seven insertions, five deletions"* against
a tree that yields 13 and 4, and its table listed `A27`, `A28` and `A30` rows
that do not exist in any commit of this branch — the note went onto its **own
worksheet**, not onto rows 27-30 of the dashboard, so the eight `Q25 Basis
Note!` lines the change actually added were entirely absent from a table headed
"every changed line classified, zero unexplained". It was produced by the very
commit whose own narrative is about the fifth stale count. The figures above are
now **derived from the tree** by
`tests/test_pinned_constants.test_the_changelogs_rendered_baseline_delta_matches_the_tree`,
which re-runs `git diff --numstat` between the two commits this claim names and
fails if either the counts or the set of moved surfaces disagrees.

**Every changed line classified, zero unexplained:**

| Surface | Lines | Changed line | Classification |
|---|---|---|---|
| excel | 1 −, 1 + | `A12` label gains `(a share of QEI, not of QLICIs — see the 'Q25 Basis Note' sheet)` | intended — **S4**, and this is the entry that was invisible before |
| excel | 8 + | `@@SHEET Q25 Basis Note` and `Q25 Basis Note!A1`, `A2`, `A4`–`A9` | intended — S4. A new worksheet, not new dashboard rows |
| markdown | 2 −, 2 + | Section B basis note label and body | intended — S1 |
| word | 1 −, 1 + | `T6\|R7` basis note body | intended — S1 |
| pdf | 1 −, 1 + | Section B basis note body | intended — S1 |

`Summary Dashboard!C12` — `|float|fmt=0.0%|0.8531073446327684` — is deliberately
**unchanged**. The value was never wrong; the label around it was, and that is
what moved. **S3 moves no baseline line**, correctly: the baseline fixture
supplies `qlici_amount`, so nothing about it is defaulted. **No dashboard row
was renumbered**, which is what the withdrawn `A30` row claimed.

### B3 — the scaffold told a CDE to write a value the validator rejected

**Shipped in `ff49064`; this entry did not mention it until FIX-2, and it is
the reason this release is a MINOR.**

`templates/cde_profile_template.yaml:26` reads

```yaml
prior_awards: []          # Prior NMTC allocations. Leave as [] if none.
```

`CDEProfile.from_yaml` accepted it. `validation/completeness_check`, which loops
over `REQUIRED_CDE_FIELDS` and rejects `val == []`, reported **"CDE profile
missing required field: prior_awards"**. The exception lived only inside
`from_yaml`, as a local named `blank_is_answer`, so the two modules disagreed
about the shipped scaffold.

**Why that is a blocker rather than a nuisance.** The tool's core audience is a
first-time CDE. It follows the scaffold, writes `[]`, loads without error, and
is then told its profile is incomplete — and the only field named is **prior
NMTC allocations, a scored track-record item**. The obvious way to clear the
error is to put something in the list. That is a validator applying pressure
toward a false statement about the applicant's own history in a federal filing:
the shipped-inputs rule running backwards, pushing a fabricated value in rather
than leaking one out.

The exception is now one module constant,
`core/cde.CDE_FIELDS_WHERE_EMPTY_IS_AN_ANSWER`, read by both.

### The workbook gained a worksheet, not four rows

`Q25 Basis Note` is a **new sheet**, positioned immediately after the Summary
Dashboard, carrying the S1 note in full. The dashboard's distress label points
at it **by sheet name** rather than at a row number nothing on screen names —
the 1.3.0 draft's pointer said "see the basis note below" and pointed fifteen
rows down, past the readiness block and under the footer, and whether "below"
was even visible depended on the reader's window, because the file stores no
window geometry at all. `tests/test_excel_geometry.test_the_basis_note_is_
reachable_by_name` pins the sheet name, its presence, and its position.

### Excel geometry: a rendered dimension no gate could see

1.3.0 S4 gave `Summary Dashboard!A12` a two-line label; the metrics loop set
`row_dimensions[row].height = 18` for every row, uniformly. Measured in Excel
16.112 at the shipped geometry, **A12 needed 30.0 pt and shipped 18.0**, so the
visible text ended mid-negation at *"(a share of QEI, not"* and the half that
never displayed was the pointer to the note. **The round's own remedy was
invisible on the surface it was written for.**

`tests/rendered_baseline/excel.txt` records cell coordinates, Python types,
number formats and values. Row heights, column widths and merge ranges appear
nowhere in it, so **a correct fix leaves that file byte-unchanged** and the
whole class is structurally unreachable from it. Third instance of the same
shape, after the interpolation mask that hid every printed constant until 1.2.1
and the value-only projection that hid B-3's number formats.

- **`renderers/_sheet_geometry.py`** — every constant measured in Excel 16.112
  against an autofit replica, with the raw runs in its docstring, because
  merged ranges (which every dashboard label is) do not autofit at all.
- **`tests/test_excel_geometry.py`** — re-derives every label's required height
  from the SHIPPED workbook: its actual string, its actual merged span, its
  actual font size. It reads nothing from the builder.
- **No sheet is excluded.** The first draft excluded the six DataFrame sheets
  on the reasoning that `_write_df_to_sheet` sets no heights. That reasoning was
  false — it set `height = 16` uniformly — and the same defect was live on six
  more sheets, including `Investor Commitments!G6`, a 351-character
  `[CDE TO COMPLETE]` instruction displaying one line of nine.

### The Review Process sweep — the durable output of this round

> **A summary document is a safe source for how the Fund SCORES and an unsafe
> source for what the Applicant is asked to COMMIT TO, because the thing the
> Applicant fills in is the Application.**

**75 mentions across 71 lines** of `nmtcapp/`, `streamlit_app/`, `docs/` and
`README.md`. **13 cite the Review Process for a substantive claim** — a
percentage, a commitment, or a list of areas. Of those 13:

> **Corrected in 1.3.0 B1.** This paragraph shipped as *"72 mentions across 68
> lines"*, and **no tree in this repository has ever yielded 72/68**. Measured
> with the derivation now gated by
> `tests/test_pinned_constants.test_the_changelogs_review_process_sweep_matches_the_tree`:
> **75/71 on `03261c1`**, the commit that made the claim, and **67/64 on
> `63443cc`**, the pre-round base. The figure was neither the before nor the
> after. Nothing renders off it — it is a release note — but it was the sweep's
> own headline count, and a sweep that miscounts its own corpus is a sweep
> whose coverage claim nobody can check. The derivation is stated below so the
> next reader can re-run it rather than trust it:
>
> ```
> grep -rn --binary-files=without-match --exclude-dir=__pycache__ \
>      -oE "Review Process" nmtcapp streamlit_app docs README.md | wc -l   # mentions
> grep -rn --binary-files=without-match --exclude-dir=__pycache__ \
>      -E  "Review Process" nmtcapp streamlit_app docs README.md | wc -l   # lines
> ```

- **2 conflicted with the Application and are corrected here** — Question 25's
  85% and 20%, at `benchmark_thresholds.py:81/89`, `distress_analysis.py:64/92`
  and the three rendered notes.
- **1 was stale rather than wrong.** `docs/reference/methodology.md` and the
  Streamlit About page both still said the non-metro commitment's basis *"has
  not been checked against the Application's own question text"*. **1.2.2 round
  2 established it** — from the NOAA, recorded in `benchmark_thresholds.py` —
  **and left the "not checked" sentence live on two rendered surfaces.** Now
  settled a third way, from the instrument: Question 22 (printed p. 31) asks for
  *"a minimum percentage of **QLICIs** the Applicant is willing to commit to
  provide to Non-Metropolitan Counties"*. Both surfaces corrected, and both now
  also disclose that this tool's non-metro figure is a QEI share over a
  twelve-state heuristic rather than the OMB county definition.
- **10 hold.** For seven of them the Application says nothing at all, and each
  is a scoring or review behaviour — which is exactly what the Review Process
  *is* authoritative for. Grep counts over the 142-page Application:

  | Term | Hits in the Application |
  |---|---|
  | `90%` | **0** |
  | `95%` | **0** |
  | `Highly Qualified` | **0** |
  | `aggregate score` | **0** |
  | `40 out of` | **0** |
  | `track record of similar` | **0** |
  | `half of the priority` | **0** |
  | `70%` | 3 — **all three inside Question 25(a) item 6**, none a track-record threshold |

  The other three (Question 15's ladder, Question 23's "substantially all" with
  no percentage, Question 22's 20%/50%) were already ruled against the
  Application in earlier rounds and re-verified here.

**Found while sweeping — REPORT ONLY, nothing is wrong today.** Question 40
(printed p. 72) carries a **second, unrelated 85% that IS denominated in QEI**:
*"Will more than 85% of the QEI proceeds be invested/re-invested in QLICIs?"*
Nothing in this package cites it and no claim here is affected. It is recorded
because this package renders an "85% of QEI" distress proxy, and a reviewer who
knows Question 40 has a ready-made way to misread it.

### `_RURAL_STATES` — the 1.3.1 blocker, recorded here because it is not one yet

`intelligence/geographic_analysis._RURAL_STATES` is a **twelve-state set with no
defensible basis**, and the module says so itself: the line above it reads
*"States typically classified as non-metro / rural (simplified)"*, and the map
below it reads *"(In production, this would use proper CBSA codes from census
data.)"* An acknowledged placeholder, shipping as a live computation.

**Three of the twelve are simultaneously assigned MSAs by the same module.**
`MS`, `KS` and `NM` are in `_RURAL_STATES` and in `_STATE_MSA_MAP` — as Jackson,
Kansas City and Albuquerque. Every dollar in those states is counted rural by
one dict and metropolitan by the other, forty lines apart.

**WHY IT IS NOT A BLOCKER, stated correctly.** The 1.3.0 brief deferred this on
the ground that `non_metro_meets_minimum` is written into `flags` at
`win_probability.py:633` and read by no renderer and no Streamlit page. That
much is true — grep confirms exactly one write and no reads — **but it is not
the reason, because it is not what `_RURAL_STATES` feeds.** The set feeds
`rural_pct` (`geographic_analysis.py:69/96`), and `rural_pct` reaches **three
rendered surfaces**:

| Surface | Where |
|---|---|
| Streamlit Geographic tab | `1_Pipeline_Analyzer.py:527` "Rural share" metric, the urban/rural donut at 571, and the "Winner rural mean: 18% \| Your pipeline: …" line at 608 |
| `nmtcapp analyze` summary | `pipeline_analyzer.py:124` "Urban/Rural: X% / Y%" |
| Benchmark set | `benchmarks.py:242-247` "Rural % of QEI", against a winner mean |

The real reason it is deferred is narrower and had to be measured: **it reaches
none of the four generated documents.** Verified against
`tests/rendered_baseline/` — every occurrence of "rural" in all four artifacts
is *High Migration Rural*, which is a per-project CDE-declared/mapper field and
has nothing to do with this set. Nothing `_RURAL_STATES` computes is filed.

So it fails the harm criterion this cycle ranks by, and only that. It is live on
three screens a CDE reads, it is internally contradictory, and it is unsourced.
**1.3.1, and the fix is deletion or CBSA codes — not a thirteenth state.**

### Still deferred — unchanged by the minor bump

- **The denominator swap** from `qei_request` to `qlici_amount` on any share.
  Behind a written, hostile-audited methodology first.
- **Removing the `below_mkt` limb** from Product Flexibility scoring —
  disclosed in round 2, still arithmetically meaningless, still a scoring
  change.
- **The remaining collapsed fixtures** beyond the two S3 required — 1.3.1.
- **`_score_deep_distress`, `_score_product_flexibility`, `gap_pp`** — all
  three traced in the 1.3.0 audit and confirmed to render into no generated
  document. They shape advice, not the filing. Still wrong, still 1.3.1.

---

## FIX-2 — the same class, on the PDF, and the gate that could not see it

A confirmation pass on `ff49064` confirmed S1-S4 and B1-B3 and then refuted the
premise it was told to attack:

> **Geometry was not the last class of "correct in the source, wrong on the
> page." The PDF is the same class, worse, and invisible to every gate in the
> repo including the new one.**

### B1 — the PDF's key/value tables could not wrap

`renderers/pdf_builder._content_to_flowables` built every section key/value
table as `Table(data)` — no `colWidths`, and bare `str` cells rather than
`Paragraph`. ReportLab cannot wrap a string cell, so it sized each column to
the longest single line. Measured on the baseline fixture at `ff49064`:

| Page | Table width | Frame | What a CDE saw |
|---|---|---|---|
| 9 (Section D) | 691 pt | 432 pt | Every row label pushed off the left edge, and the caveat on **QEI Less CDE Fees** cut mid-word at the right — the number without the sentence saying what it is not |
| 5 (Section B) | **17,207 pt** | 432 pt | A header bar and four empty striped rows. **1.3.0's two reasons for existing rendered as an empty table.** |

**753 words rendered outside the printable band**, on those two pages, in a
document whose source text was correct throughout — measured by reading the
shipped file back and comparing each text run's device position against the
frame it was drawn in. **After the fix: zero, in all three analyzer states**
(nominal, partial-unverified, degraded).

The file had six `Table(` calls and five `colWidths` occurrences; this was the
one without, and it is the generic `table_ref` renderer every section key/value
table passes through. **The defect is older than this cycle** — off-page word
count went 753 at `ff49064` and the caveat has been cut on every PDF this tool
has generated since at least 1.2.1. Four passes over four rounds never rendered
a page and looked at it.

Three things were needed, not one:

- **`colWidths`** off `renderers/_frame_geometry.usable_width()`, the single
  statement of the text column that the four other call sites now also read.
- **`Paragraph` cells**, XML-escaped on the way in. A string cell is one line
  however wide it is.
- **`splitInRow=1`.** This is the part the brief did not know it needed. The
  ~4,000-character basis note wraps to roughly 1,000 pt and no portrait frame
  is 1,000 pt tall; ReportLab splits *between* rows by default and raises
  `LayoutError` on a single row taller than the page. **`colWidths` alone turns
  a silent overflow into a hard build failure.** Verified by execution before
  the fix was written.

**And no `repeatRows`**, which `_df_to_rl_table` does set: a repeated
"Item | Value" header above the continuation of one wrapped cell announces a
row that is not there, and interleaves those two words into any quoted list
that spans the break — which is how `tests/test_pinned_constants` first saw it.
Word's key/value tables do not repeat their header either.

**RULED: the note stays in a table.** A 4,000-character value in a two-column
key/value grid is a fair question, and the three other renderers do not agree
with each other about it — Markdown renders the dict as a `**key:** value`
definition list, Word as an autofit table whose rows break across pages, and
the workbook now puts the note on its own sheet. **Word is the surface to
match**: it and the PDF are the two *paginated* renderings of the same dict,
they are the two a CDE prints, and a reader comparing the .docx and the .pdf of
one filing should not find a table in one and a run of prose in the other.
Markdown's divergence is what a format with no page does, not a third option to
copy. `splitInRow` is what gives a ReportLab row the page-breaking behaviour a
Word row already has.

### B2 — a "do not submit" instruction that never displayed

`renderers/excel_builder` hardcoded `ws.row_dimensions[4].height = 28` on both
banner rows — **in the function the geometry fix edited, two rows above the
cell it fixed.** Measured on the shipped builder:

| State | Ships | Needs | Chars |
|---|---|---|---|
| partial-unverified | 28.0 pt | **75.0 pt** | 519 |
| degraded | 28.0 pt | **30.0 pt** | 168 |

The degraded arm clips at its **shortest possible message**, so no wording made
28 correct. What a CDE never saw, past the partial banner's first two lines:

> *"…Distress and targeting shares count only location-verified projects in the
> numerator but all pipeline QEI in the denominator, so each is a LOWER BOUND …
> **Do not submit until all project locations are verified.**"*

The row that exists to stop a CDE filing was the row that could not finish its
own sentence. Both heights now derive from the text, clamped at Excel's 409 pt
ceiling exactly as the Q25 note block below them already was.

**The round's own geometry gate detected both, and never ran them.** Nothing in
the suite had ever built the workbook with a banner. `tests/test_excel_geometry`
is now parametrized over all three analyzer states — nominal,
partial-unverified, degraded — and every check in it runs against each.

### B4 — the gate that would have caught the PDF, and three vacuity holes

`tests/test_excel_geometry.py` reads the workbook only. It cannot see PDF, Word
or Markdown, which is why B1 survived a round that existed to fix exactly this
class. **`tests/test_render_frame_geometry.py`** is the renderer-agnostic
answer, and it says on its face what it does and does not cover:

- **PDF, rendered.** The shipped file is re-opened and every text-showing
  operation's device position read back, measured against ReportLab's own font
  metrics. This is the page as a CDE sees it, including text no flowable
  produced — the running footer is drawn straight onto the canvas and is
  checked too, against its own wider band, because a gate that reports the page
  number as clipped on sixteen of twenty pages is a gate nobody reads.
- **PDF, modelled.** Every `Table` in the story is asked for its own width and
  compared to the frame it will be placed in. Exact, and it names the flowable
  rather than the coordinates of its debris.
- **Word: covered by mechanism, not by measurement**, and written down as
  weaker. Nothing in this repository can lay out a .docx. What is asserted is
  that no key/value table pins a column width, which is what makes Word fit it
  to the text column.
- **Markdown: out of scope, and not silently.** It has no frame; "outside the
  frame" has no referent. Recorded as a decision, with an assertion that the
  content whose PDF rendering was the defect is still present.

**Both new checks are shown red on their restored defects** — the shipped
`Table(data)` rebuilt on the real Section B content — and **neither can pass
vacuously**: an empty PDF fails on `measured > 0` rather than passing on
`not findings`, and that refusal has its own test.

**The three vacuity holes in the Excel gate are closed, each with a test that
proves it:**

1. **Zero sheets passed.** `assert not findings` is true of a workbook the gate
   never opened. It now asserts sheets exist and that at least one text cell
   was measured.
2. **All-unset heights passed silently.** `if not shipped: continue` skipped
   the cell without saying so, so a builder that stopped setting heights would
   have turned the gate off rather than red. Skips are now returned and
   asserted to be zero — the builder sets an explicit height on every row it
   writes, measured.
3. **A merged cell with `height = None` was skipped on a premise the module's
   own docstring contradicts in capitals** — *"MERGED CELLS DO NOT AUTOFIT …
   Excel's AutoFit is a no-op on a merged range, and every label on the
   dashboard is merged"*. Merged cells are now measured against the sheet's
   default row height, with one exemption stated and bounded: **one** line of
   the **default** font, which is what that height is calibrated for. A
   multi-line merged label, or one at a larger font, is reported.

### The two claim gates learned what a line break is

Making the PDF wrap turned four long unwrapped cells into 91 short visual
lines. **All 91 are contiguous fragments of lines already on the invariance
allowlist — verified, zero orphans — and no allowlisted line went dead**,
because Word and Markdown still carry the same sentences unwrapped.

The alternative was 91 new allowlist entries, and it was rejected: it measures
the renderer instead of the claim. The same Q25 basis note is **one** line in
Word, **one** in Markdown and **nine** in the PDF, and requiring nine rulings
for one sentence would put lines like `Areas; Federal Medically Underserved
Areas;` into the file whose own header reads *"READING THIS FILE IS THE
HIGHEST-VALUE REVIEW ON THIS PACKAGE"*. The file was already conceding the
point by hand — four of its entries are justified as *"Wrapped continuation
of …"* and one says outright that a narrowing *"misses it only because the PDF
extractor wraps the line away from its opening bracket"*. **N-WRAP** and
**N6** are that concession, derived instead of typed: a contiguous substring of
a line a human already ruled, strictly shorter than it and at least 20
characters, is the same ruling. Both gates print how many fragments they
absorbed, and both have a test that an invented claim is **not** absorbed.

`tests/test_qlici_basis` was widened the other way, to the **paragraph**, and
this is a correction rather than a loosening: in Markdown and Word the whole
basis note is one line, so *"does this line name QLICIs"* has always meant
*"does this paragraph name QLICIs"* on three of the four surfaces. The PDF
matched them until its cells wrapped. The block stops at a blank line, and
`test_the_paragraph_widening_cannot_excuse_a_bar_from_the_next_paragraph`
proves it.

`tests/test_pinned_constants` now strips the running header/footer from each
PDF page before matching. `_normalise` collapses whitespace so a pin survives a
**line** wrap; it could not survive a **page** wrap, because what interrupts
the sentence there is chrome rather than whitespace. A pin is a claim about the
document, not about the page it landed on.

### FIX-2's own rendered baseline movement

> **144 insertions, 50 deletions** in `tests/rendered_baseline/`, measured
> `ff49064`..`0643296`, in `pdf.txt` only.

**The largest baseline movement of the cycle**, and Markdown, Word and Excel
are byte-unchanged, which is the check B1 had to pass: it is a PDF layout fix
and it touched the PDF only. Every changed line falls into five classes:

| Class | Lines | + / − | Classification |
|---|---|---|---|
| `Item`/`Value` gain a leading space in extraction | 16 | +8 / −8 | consequential in extraction, NOT on the page — see the correction below |
| Section B's **four** distress row labels wrap | 14 | +10 / −4 | **intended — B1.** The longest was one 86-character line in a 194 pt column |
| The Q25 basis note wraps, over pages 5-7 | 87 | +84 / −3 | **intended — B1.** This is the remedy: 600 words that rendered off-page now render on it |
| Section D's three long values wrap | 10 | +7 / −3 | **intended — B1**, including the QEI-Less-CDE-Fees caveat that was cut mid-word |
| Page numbers +2 from page 6, and two blocks reflow across a break | 67 | +35 / −32 | consequential — the note now occupies two more pages |

**194 lines, zero unexplained.**

#### THIS TABLE WAS WRONG IN EVERY ROW, AND IT SUMMED (corrected in 1.3.1 G7)

As shipped, the five rows read 10 / 13 / 96 / 9 / 66. Every one of them is
wrong, and they **sum to 194** — which is the correct total, and is why nothing
caught it. `test_the_changelogs_rendered_baseline_delta_matches_the_tree`
parses the **blockquote** above and asserts the total and the file set against
`git diff --numstat`. It was never given the table. A hand-typed breakdown
under a machine-checked total can be arbitrarily wrong as long as it adds up,
and this one was: five hand-typed figures, each off, cancelling to the right
answer. **The seventh stale hand-typed count of this cycle, in the entry whose
own narrative is about the sixth.** `test_the_changelogs_baseline_class_table_adds_up`
is 1.3.1's answer and it is honest about its reach — it re-derives the
`Item`/`Value` row from the tree, because that row is the only one statable as
a rule, and asserts the remaining four sum to the residual.

**And "nothing moved on the page" was false.** It is true of the CENTRING —
the header cells were centred by `_rl_table_style` before the fix and after it,
which is what the sentence meant. It is not true of the cells. Before B1 the
Section B header row was drawn as part of a 17,197 pt table that ReportLab
centres on a 612 pt page, so `Item` was laid down at **x = −8,293.7 pt**; after
it, at x = 95.0. The page moved by 8,388.7 pt and this row said it did not.
The claim has been narrowed to what was actually established.

### The whole output surface, enumerated — REPORT ONLY, and the durable part

Four rounds have each found their defect inside the previous round's fix, and
this one exists to fix a defect found inside a fix. The premise worth attacking
was that **the four generated documents are the whole output surface**. They are
not: the CLI block, four Streamlit pages and the published docs site render the
same content through different geometry. Every one was generated and read, in
every state the analyzer can produce.

| Surface | State(s) checked | Result |
|---|---|---|
| PDF | nominal, partial-unverified, degraded | **B1. 753 → 0 off-page words** |
| Excel | nominal, partial-unverified, degraded | **B2. banner 28 pt against 75 and 30** |
| Word | nominal, partial-unverified, degraded | clean — nothing pins a column width |
| Markdown | nominal, partial-unverified, degraded | no frame; nothing can fall out of it |
| `nmtcapp analyze` block | all three | no clipping class. A terminal reflows, and the `:<30` paddings are minimum widths — a long label misaligns a column, it never loses a character. **But see F1.** |
| Streamlit, 4 pages | nominal, rendered in Chrome | **zero clipped elements**, measured as `scrollWidth > clientWidth` under a clipping `overflow`, walked through shadow roots. Zero horizontal page overflow. |
| Docs site, built `--strict` | nominal | zero clipped elements; the site's own sample PDF measures **0 off-page words** |

Two mechanism facts worth writing down, because they are what makes the
Streamlit result hold at widths nobody tested: `stMetricLabel` computes
`white-space: normal; overflow: visible`, so a metric LABEL wraps and cannot
clip at any width — which is why the Q25 denominator disclosure survives in
`Deep / Severe distress (a share of QEI, not of QLICIs)`. `stMetricValue`
computes `white-space: nowrap; overflow: hidden; text-overflow: ellipsis`, so a
metric VALUE is truncated at any width. **No value in this app currently
carries a disclosure**, and that is the load-bearing fact — see F2.

**F1 — the two screens name five unverified projects and say six.** REPORT
ONLY, 1.3.1. `intelligence/pipeline_analyzer.py:77` and
`streamlit_app/pages/1_Pipeline_Analyzer.py:253` both render
`", ".join(unverified_project_ids[:5])` under a count that is not truncated.
Executed on an eight-project pipeline with six unverified:

```
CLI :  6 project(s) could not be location-verified and remain
       UNVERIFIED (no tract assigned): PRJ-D03, PRJ-D04, PRJ-D05, PRJ-D06, PRJ-D07
DOC :  6 of 8 projects could not be location-verified (no census tract
       assigned): PRJ-D03, PRJ-D04, PRJ-D05, PRJ-D06, PRJ-D07, PRJ-D08.
```

`PRJ-D08` is absent from both screens and neither says the list was cut. The
list IS the actionable half — it is what tells a CDE which projects to go and
verify — and the two surfaces that drop it are the two a CDE reads before
generating anything. Same class as B2: a disclosure that is complete in the
source and incomplete on the page. Not fixed here because this round's remit is
B1-B4 and its baseline movement is already the largest of the cycle; the fix is
an `and N more` and a gate that the rendered ID list matches
`unverified_project_ids`.

**F2 — the Streamlit distress metric is a bare percentage.** REPORT ONLY,
1.3.1. `renderers/_disclosure`'s own header states the rule: *"For the partial
case every affected metric must carry its qualifier INLINE ... a separate
disclaimer paragraph can be stripped in editing; an inline qualifier cannot."*
The four documents obey it through `qualified_pct`. **No Streamlit file imports
`qualified_pct` or `unverified_qualifier`** — `1_Pipeline_Analyzer.py:376`
renders `fmt_pct(deep_severe_pct)` unconditionally, so in the partial-unverified
state the screen shows a bare share with the disclosure only in a `st.warning`
above the tab bar. The banner is on screen, so this is weaker than B2; it is
still the exact shape the module's own rule forbids, on the surface a CDE reads
first.

**F3 — two stale hand-typed counts on rendered surfaces.** REPORT ONLY, 1.3.1.
`streamlit_app/app.py:86` renders `✅ 890+ tests` and `README.md:289` reads
`# 544 tests, should all pass`. The tree collects **1,096**. Seventh and eighth
instances of this cycle's signature pattern, both on the first screen a
prospective user sees. The fix is not another digit — it is the treatment
`_sweep_census` already gets: derive it, or do not print it.

**Checked and NOT a defect:** the docs site's `v1.1.2` version badge. It is
mkdocs-material's `md-source__fact--version`, read from the repository's latest
GitHub *release*, and v1.1.2 is genuinely the newest tag. 1.2.0-1.3.0 have
never been tagged, so the badge is accurate about the repository and says
nothing false about the package.

### FLOOR and MAX_SDIST_SKIPS — the measurement behind them was wrong

`FLOOR=520` was correct at `ff49064`. **The measurement recorded beside it was
not.** `release.yml` documented *"1,068 collected, 11 skipped, 1,057
executed"*; the real figure at that commit is **18 skipped**. The 11 comes from
running the suite **inside the unpacked tarball**, which that workflow's own
comment forbids in capitals — doing so puts the tarball's source tree on
`sys.path` and un-skips nine checks that ask whether `nmtcapp/` sits beside
`tests/`. A floor derived from a run the job does not perform.

**That is worse than a stale digit, and it is why it is listed here rather than
as a footnote.** A digit that is stale gets remeasured. A derivation that is
merely plausible gets copied forward — which is precisely what happened to
`MAX_SDIST_SKIPS`, whose comment justified 20 as *"1.8x the measurement"*.
Against the real 18 it was 1.11x: a ceiling one skip above the thing it bounds,
tightened onto a number taken the wrong way.

Both are re-derived here, from a fresh sdist built from a pristine clone and run
with `release.yml`'s exact invocation, **identically on 3.9.25 and 3.12.13**:

|  | value |
|---|---|
| collected under `-m "not wheel"` | 1,096 |
| skipped in the sdist | 20 |
| **executed** | **1,076** |
| half | 538 |
| rounded down to ten | **`FLOOR=530`** |

All twenty are environment skips and each names its own reason: no git
checkout (4), no `nmtcapp/` source tree beside `tests/` (9), no `docs/` (4), no
`.github/workflows/` (3). **None is unconditional** — FIX-2 replaced the one
test that was about to introduce the first (a nominal-state parametrization
with no banner to check) with an assertion that no banner renders.

`MAX_SDIST_SKIPS` goes to **24**, and the ratio is gone from its comment
because a ratio was never the right way to pick it. The ceiling only changes
anything when it crosses a rounding boundary: at 1,096 collected the band's
lower bound is 530 for every ceiling from 17 to 36 and drops to 520 at 37. With
the measured 20 as the other end, the live range is [20, 36]. 24 sits four
above the measurement and twelve below the point where the band goes slack —
which is what 40 was doing before 1.3.0, and what made it an abstention rather
than a ceiling.

---

## [1.2.2] — round 2 of 2

**The six false Fund attributions round 1 ruled are fixed, on all 20 surfaces.
`EXPECTED_DEFECTS` goes 6 → 0.** They were inherited, not introduced here: every
one was live on PyPI and on the published docs site for the whole 1.2.1 cycle,
and round 1 ruled them without fixing any.

**Nothing reaches the public docs site until `mkdocs gh-deploy` is run by hand.**
CI's `docs` job proves the site *compiles*; it does not publish.

### The primary sources, all three retrieved and text-extracted locally

Round 1 had only the Review Process, which is why three of its rulings were
recorded as *could not establish*. Round 2 retrieved the other two. None was
fetched through a summarising model.

| Document | Bytes | Pages |
|---|---|---|
| CY 2024-2025 NMTC Allocation Application | 1,525,626 | 142 |
| CY 2024-2025 NMTC Program Review Process | 187,497 | 7 |
| CY 2024-2025 NOAA — 89 FR 92283-92292, 21 Nov 2024 | 72,819 (FR text) | 10 |

**The NOAA exists and round 1's brief was wrong to doubt it.** The Review
Process names it — "published in the Federal Register on November 21, 2024" —
and it was retrieved from the Federal Register's own API as document
`2024-27029`. The *CY 2026* NOAA is a different document and is still
unpublished; verified against the Federal Register through 2026-08-12, so the
rendered basis note that says so remains true.

Grep counts over all three, which is what the withdrawals rest on:

| Term | Application | Review Process | NOAA |
|---|---|---|---|
| "special targeting" | 0 | 0 | 0 |
| "bonus point" | 0 | 0 | 0 |
| "top tier" | 0 | 0 | 0 |
| "deployment rate" | 0 | 0 | 0 |
| "near-100" | 0 | 0 | 0 |
| "90%" | 0 | 3 | 0 |
| "priority point" | 5 | 4 | 2 |

### The two numeric coincidences, ruled explicitly

Both are real, published, correctly-cited Fund figures that a grep would offer
as a citation for a house constant. **Neither licenses one**, because each is a
different *kind* of quantity:

- **"up to 10 additional priority points"** (Application p.19) is a POINT COUNT
  belonging to two other criteria. `SPECIAL_TARGETING_BONUS_PCT` was a
  SHARE-OF-QEI trigger. Ruled: withdrawal, not citation.
- **"at least 95% of these proceeds as QLICIs"** (Review Process p.6) is a
  REINVESTMENT SHARE on purchased loans. `TOP_TIER_AGGREGATE_MIN` was an
  AGGREGATE POINT SCORE out of 100. Ruled: house, not citation. **This one the
  round-2 brief did not flag**; it was found by grepping every `95` rather than
  only the terms under suspicion.

### Fixed — the six

| Tag | Surfaces | Ruling | Basis |
|---|---|---|---|
| D1 | 6 | **Label + three-part disclosure.** Not withdrawal. | Application pp.20-21 |
| D2 | 3 | **Split into its two true halves.** The 70% is untouched. | Review Process p.7 II.A.4, p.4 |
| D3 | 4 | **House label.** Denominator unchanged; NOT re-based to 85%. | Application p.34 Q23 |
| D4 | **6** | **House label**, and two award predictions withdrawn. | Review Process p.3 Step 2 |
| D5 | 2 | **Withdrawal of the attribution.** | NOAA §V.B(b); Application p.132 |
| D6 | 1 | **Fixed by citation.** | IRC §45D(d); Treas. Reg. §1.45D-1(c)(5)(i) |

**D1 — and a round-1 reading corrected.** Round 1 recorded Question 15 as
"100% of QLICIs must take one of FOUR forms". That is the Review Process p.6
description of a *highly ranked* application — the top rung only. The
Application itself (pp.20-21) shows Q15 is a **single-select ladder**: "Choose
one of the following options. Check only one", at 50%/5 indicia, 33%/4, 25%/3,
15%/2. **Writing round 1's paraphrase into rendered text would have installed a
new misattribution while fixing the old one.** Every corrected surface states
the ladder. The disclosure does three things, not one: it says this sub-score is
not Q15's test, states what Q15 actually asks, and says the number is this
tool's own — because a line that only says what a number *isn't* leaves a CDE
assuming it is a near-miss proxy.

**D3 — why the denominator did not move and why 85% was refused.** Question 23
is a **Yes/No dropdown** (Application p.34) awarded five points for answering
Yes; the Fund's test is not a percentage at all, so this package grades a
continuous share against a binary question. Treas. Reg. §1.45D-1(c)(5)(i) does
put "substantially all" at 85 percent, but for the **deployment** test
(§1.45D-1(c)(1)(ii)), QEI cash into QLICIs. Re-basing would have swapped one
unstated number for another *while strengthening the appearance of a citation*.
**No denominator was changed anywhere in this release.**

**D5 — withdrawal, and now disproved rather than unlocated.** The NOAA settles
it affirmatively: under IRC §45D(f)(2) the Fund ascribes points for "one or
both of the statutory priorities", and "Applicants that meet the requirements of
both priority categories can receive up to a total of ten additional points."
Two priorities, ten points, both already scored separately here. A third
five-point award would make fifteen against a published maximum of ten. The four
categories are real but appear in the Application only inside the glossary
definition of a **Disadvantaged Business** (p.132) — inputs to the DBC priority,
not a criterion.

### Changed — the constant rename

Eight SECTION A constants carrying a false or unstated Fund attribution are now
`HOUSE_`-prefixed, so the compiler finds every consumer and no interpolated
surface can silently keep the old wording. This matters because
`streamlit_app/pages/4_About_and_Methodology.py` interpolates them **live** into
the methodology tables a CDE reads — which is how D4 stayed invisible.

`HOUSE_UNRELATED_ENTITIES_MIN_PCT`, `HOUSE_TRACK_RECORD_DEPLOYMENT_MIN`,
`HOUSE_TOP_TIER_AGGREGATE_MIN`, `HOUSE_TOP_TIER_SECTION_MIN`,
`HOUSE_SPECIAL_TARGETING_TRIGGER_PCT`, `HOUSE_SPECIAL_TARGETING_MAX`,
`HOUSE_PRODUCT_FLEXIBILITY_BELOW_MARKET_PCT`,
`HOUSE_PRODUCT_FLEXIBILITY_MIN_INDICIA`.

**No deprecated aliases**, because the reachability check came back negative:
none of the eight is in `nmtcapp/__init__`'s `__all__`, and
`benchmark_thresholds` is named nowhere in `docs/`, `mkdocs.yml` or `README.md`.

**Re-derived, and deliberately NOT renamed:** eight further SECTION A constants
are house figures by this package's own admission — the sub-score maximums
`PRODUCT_FLEXIBILITY_MAX`, `PIPELINE_CREDIBILITY_MAX`,
`TRACK_RECORD_STRENGTH_MAX`, `TRACK_RECORD_ALIGNMENT_MAX`, `HIGHER_DISTRESS_MAX`,
`DEEP_DISTRESS_MAX`, `COMMUNITY_OUTCOMES_QUALITY_MAX`,
`COMMUNITY_ACCOUNTABILITY_MAX`. They weight **real** Fund criteria and every
surface rendering them already carries the sub-score disclosure, so no false
wording hides behind them. Prefixing them is 1.2.3, as a decision rather than an
oversight.

### Added

- **`TRACK_RECORD_TO_PROJECTION_MIN = 0.90`** — the Fund's *other* 90%, added so
  it stops being confused with the house one. It shares a value with
  `HOUSE_TRACK_RECORD_DEPLOYMENT_MIN` and means something else, and the two now
  render in the same sentence five clauses apart. Pinned to the rendered string.
- **Non-metro provenance established.** The About page shipped a note saying
  "whether the non-metro commitment is QLICI- or QEI-denominated has not been
  checked". The NOAA states it expressly, **on QLICIs**: "at least 20 percent of
  their QLICIs (as measured by dollar amount) in Non-Metropolitan counties", and
  the Rural CDE definition at "at least 50 percent". Recorded at the constants.

**D4 — two surfaces round 1 never listed, found in round 2.** Its true count is
**six**, not four. Both were invisible to the gate for the same reason: they
name no authority token, the blind spot that let
`docs/reference/methodology.md:42` survive the release opened to sweep its
siblings, one detector further out.

- `streamlit_app/pages/2_Win_Alignment_Scorer.py` rendered **"Top Tier gate:
  95+ aggregate AND 45+ in each section"** directly beneath **"Highly Qualified
  gate: 85+ ..."**, in the same weight and the same shape. A CDE read a matched
  pair of CDFI Fund gates; only the first one was.
- `nmtcapp/intelligence/win_probability.py` ended its Top Tier explanation
  **"High probability of Phase 2 advancement; award may approach the maximum
  requested"** — an award prediction, resting on an invented gate, in a package
  that disclaims predicting selection on every other surface. It renders in
  `WinProbabilityScore.summary()`, a **pinned** surface, so unlike the other
  five D4 sites this one was reaching CDEs through the scored output rather
  than only through the methodology tables.

### Changed — the gate itself

**X1-EXCEPT gained a second limb, because round 2 broke the first one by
accident.** Rewriting six defect surfaces into disclosures produced strings that
*disclaim* this tool's threshold and *quote* the Fund's real one in the same
breath — and adding the words "publishes no" to two Streamlit blobs silently
exempted blobs that had been **adjudicated the release before**. A token list
could not keep up, so the rule is general: **a string that cites a document
location — a page, a question number, a statute section, a Part/Step, a Federal
Register cite — is asserting what that document says, and is reviewable however
much disclaiming surrounds it.** Measured before adopting: 8 strings move from
exempt to adjudicated, and all 8 are Fund quotations.

**`AUTHORITIES` gained the two tier names, and they earned their place by
finding something.** "Highly Qualified" is the CDFI Fund's **own name for its
own gate**, so a sentence stating a bar "required for Highly Qualified status"
attributes that bar to the Fund as surely as one saying so in words. "Top Tier"
earns it for the opposite reason: it is this package's **invented** tier, and
stating cut points for it is a provenance claim by omission. Measured before
adopting: 9 further strings become adjudicated, all nine genuine statements of
the gating thresholds — and the widening is what surfaced the two unlisted D4
sites above.

### Proofs

- **`EXPECTED_DEFECTS` 6 → 0**, all 20 DEFECT entries reclassified: CITED where
  the corrected text quotes a document and page, HOUSE where the number is this
  tool's own. **Zero is not a weaker pin than six** — the assertion is equality,
  so a seventh defect fails at 0 exactly as an eighth would have failed at 6.
  Proved by planting a `D7` row: `1 == 0` failed as intended.
- **Round 1's planted-defect proof re-run against the rewritten allowlist**, on
  the exact tabular row that once passed green — `| Planted Criterion | 5 | 60%+
  of QLICIs in planted areas |`, which the gate had classified as a *header* —
  plus a planted prose attribution. Both caught. A gate whose allowlist has been
  rewritten is a gate that has not been proven since.
- **Rendered baseline byte-unchanged**, all four formats. None of the six
  sentences renders on a packaged deliverable fixture, so this is the expected
  result and any movement would have been collateral damage.
- Allowlist: 56 → 76 entries; 24 dropped as dead, 44 added.
- Swept-constant census 158 → 160: `TRACK_RECORD_TO_PROJECTION_MIN` and its
  render-text constant. The eight renames are net-zero.

### Known, and NOT covered by this release

- **The below-market limb of Product Flexibility is still in the scoring
  arithmetic.** `win_probability.py:435` divides a QEI-weighted portfolio share
  by a per-loan rate-discount depth. That is dimensionally meaningless and no
  label makes it sensible. It is **disclosed** on every surface and **not
  removed**, because removing it moves scored figures and the rendered baseline.
  1.2.3, behind a written methodology.
- **The Special Targeting sub-score is still scored**, for the same reason. Only
  the Fund attribution is withdrawn.
- **The readiness score is a house heuristic carrying a limb its own author
  calls meaningless.** After this release the docs say so plainly — but a CDE
  deciding whether to file should read the Product Flexibility disclosure as
  what it is: this tool cannot answer Question 15, and a high sub-score there is
  not evidence of a strong Q15 answer.
- **What the gate still cannot see.** It scans string literals in `nmtcapp/`,
  `streamlit_app/` and `docs/**/*.md`. It does **not** see: `README.md`,
  `CHANGELOG.md`, `CITATION.cff`, docstrings surfaced through `help()`, the
  Excel/Word/PDF renderers' non-literal composition, or any claim assembled from
  fragments at runtime. `nmtc_calc_adapter.py:16`'s docstring — round 1 recorded
  it as reaching developers rather than CDEs — **that reasoning holds**: it is
  not published to the docs site (mkdocs runs no mkdocstrings) and is not
  rendered into any deliverable. Reported, not acted on.

---

## [1.2.2 — round 1 of 2]

**Gate only. No rendered wording changed, and the six false Fund attributions
this round ruled are still live on PyPI and on the published docs site.**

1.2.2 was scoped to close two claims that credit the CDFI Fund with thresholds
it does not state. The brief instructed: rule every threshold against the
primary source, and **if more than two turn up, stop and report before
fixing**. Seven turned up. This round therefore ships the gate that enumerates
them, so the fix round is scoped off a machine-readable list rather than off
anyone's hand-count.

### The primary source, retrieved rather than relayed

The CY 2024-2025 NMTC Program Review Process (7pp) was downloaded and
text-extracted locally, not fetched through a summarising model. Both readings
the brief rested on are **confirmed verbatim** — p.6 Part II.A.1 for Question
15, p.7 Part II.B.2 for Question 23. `Treas. Reg. §1.45D-1(c)(5)(i)` was
verified against eCFR: "substantially all" is at least 85 percent, reduced to
75 in the seventh year.

### Added

- **`tests/test_fund_attribution_source.py`** — a source-side attribution gate
  over `docs/**/*.md`, the Streamlit markdown-in-Python tables, and every
  string literal in `nmtcapp/` and `streamlit_app/`. It exists because the
  rendered-corpus gate cannot see a claim that fires on no fixture, and
  **neither sentence 1.2.2 was opened to close renders on any packaged
  fixture** — so neither the invariance gate, the attribution gate, nor the D1
  baseline had ever seen either one.
  - Two detectors. The tabular one matters: `docs/reference/methodology.md:42`
    contains no authority token at all, so a detector keyed on "CDFI Fund"
    misses the exact line this release was opened for.
  - f-strings are reconstructed before matching. `recommendations.py:326`
    splits its authority and its bar across different AST nodes and is
    invisible without this.
  - Fails closed separately on each half. `docs/` is absent from the sdist
    (`MANIFEST.in: prune docs`), so `mkdocs.yml` is the checkout marker:
    deleting `docs/` from a checkout fails **three** tests; an unpacked sdist
    skips two and passes.
- **`tests/fund_attribution_allowlist.txt`** — 56 entries, every one ruled
  against the retrieved primary source with the page or question it was read
  from. Six outstanding defects are tagged `D1`–`D6` and pinned.

### Fixed

- **`nmtcapp/data/benchmark_thresholds.py` declared its own first half "CDFI
  Fund Published Thresholds"** and "the explicit values the CDFI Fund uses to
  evaluate applications". That was false of at least four constants in it and
  was the provenance claim standing behind five of the seven defects.
  Comment-only; no value changed, no rendered output moved.
- **`tests/test_qlici_basis.py`** — the second walk loop asserted only
  `not hits`, which a walk over zero files satisfies. Its sibling has carried
  `scanned > 40` since 1.2.1. Added.

### Known defects, ruled and NOT fixed

| Tag | Claim | Surfaces |
|---|---|---|
| D1 | Product Flexibility "50%+ below-market OR 5+ indicia" — the 50% is the depth of the rate discount on one loan, not a portfolio share; equity and equity-equivalent are omitted; the share is QEI-weighted against a QLICI commitment | 6 |
| D2 | "90%+ deployment rate" — the Fund's 90% is a track-record-to-projection ratio, not a deployment rate | 3 |
| D3 | Unrelated Entities "90%" — the Fund publishes no percentage; the reg says 85% | 4 |
| D4 | "Top Tier" 95/45 rendered as a Fund gate — the Fund publishes one gate and nothing above it | 4 |
| D5 | Special Targeting "5 bonus points" — absent from the Review Process; the citation names a real section that lacks the claim | 2 |
| D6 | "CDFI Fund expects near-100% eligibility" — uncited; weakest of the six | 1 |

D2, D4 and D5 were not known to exist before this sweep. Every one of the six
was found on at least one surface no prior round had listed.

**Not established:** `SPECIAL_TARGETING_BONUS_PCT` and the Special Targeting
categories themselves. Neither the CY 2024-2025 Application nor the NOAA has
been retrieved; both are prerequisites for the fix round.

---

## [1.2.1] — 2026-08-15

Patch release. The financial tables, the shipped inputs, and a gate that could
not fail. No public API changes.

1.2.0's final audit returned **ship, not clean** — every remaining defect was
also present in 1.1.5 and not worsened by 1.2.0. This release is those defects,
plus six more found by running the published wheel from a clean venv after the
tag landed, plus what recomputing every derived figure in Appendix A and
Section D from the CDE's own inputs turned up.

> ### Two things that had survived three passes unestablished, now established
>
> **The attribution allowlist's 25-line diff has been audited.** It had never
> been. Every claim in it checks out against primary sources rather than
> against the previous round's note:
>
> - The two `CITED` rows were rewritten from "column headers 14 and 15" to
>   "columns O and P". BOTH descriptions are accurate — 14 and 15 are the
>   0-based positional indices the loader binds, O and P are the spreadsheet
>   letters — but a reader who opened the workbook at "column 14" would land on
>   N. **Verified by opening `NMTC_LIC_Eligibility_2016_2020.xlsb` directly**:
>   the NOTES sheet reads `Column O. Severe Distress` and `Column P. Deep
>   Distress`, and the criterion strings the rows quote carry the workbook's
>   own criteria exactly — every threshold, operator and separator.
>
>   **"Byte-identical" was the wrong word and is corrected here**, in a bullet
>   whose subject is fidelity. Read off the `.xlsb` the workbook's NOTES sheet
>   holds `Severe distress=LIC AND (Poverty>30%; MFI<=60%;Unemployment>=1.5)`;
>   the document renders `Severe distress = LIC AND (Poverty>30%; MFI<=60%;
>   Unemployment>=1.5)` — **three whitespace insertions**, around the `=` and
>   after the second semicolon, and three more in the Deep Distress line. The
>   substance is exactly right and no criterion, threshold or operator differs.
>   The claim about the substance was true; the claim about the bytes was not.
>   The rendered methodology note still introduces both lines with the word
>   *"verbatim"*, which has the same problem — recorded under **Known and left
>   alone** rather than changed here, because the fix moves a rendered line and
>   a pinned constant and this release's rendered diff is reserved for FIX-3. The amendment is correct and it is an improvement.
> - The corresponding docs page (`docs/reference/data-sources.md`) carries the
>   same correction, as a table keyed by letter. `gh-pages` still needs a
>   manual `mkdocs gh-deploy`.
> - The two new `HOUSE` rows and the new `PLACEHO` row were each checked
>   against the rendered document: the credit-price/fee-rate disclaimer renders
>   and does disclaim, the statutory 39% beside it carries its IRC §45D(a)(2)
>   citation inline, and the Section E clause renders inside a
>   `[CDE TO COMPLETE]` block.
>
> **A standing portfolio claim was backwards, and is corrected here.**
> `nmtc-mapper` **does** pin the CDFI Fund workbook's shape:
> `ELIGIBILITY_XLSB_COLUMN_COUNT = 16`, nine exact header strings at indices
> 0, 1, 2, 3, 5, 7, 13, 14 and 15, and `_validate_xlsb_header` raising
> `EligibilitySchemaError` with no bypass. **Verified by executing the guard**:
> it fires on a wrong header string and on a wrong column count.
>
> ### Found and left alone (FIX-2), with the evidence
>
> - **The shipped `pipeline_sample_strong.csv` fails its own eligibility
>   check.** Parked by the re-audit as a claim; now established by running the
>   real enrichment against the live CDFI Fund table (85,395 tracts):
>   `check_eligibility(...).passed is False`, on **PRJ-S012** (tract
>   26163515700, Detroit), **PRJ-S013** (18097353300, Indianapolis) and
>   **PRJ-S015** (29510118600, St. Louis) — three of twenty projects in tracts
>   that do not qualify as Low-Income Communities. Note it PASSES on the
>   unenriched path, with warnings, because eligibility is unknown there rather
>   than negative. Not fixed here: changing a shipped sample's tracts is an
>   input change, and choosing replacements is Jay's call.
> - **`styles.SECTION_META` is dead data and has already drifted.** Read by
>   nothing repo-wide. Its `max_words` values duplicate each section class's
>   `word_limit`, and the unit is wrong — the application enforces CHARACTERS.
>   Its `"E"` title now disagrees with `SectionEPriorAwards.title`. Filed
>   `KNOWN` in the pin registry rather than deleted: removing a public name is
>   not a patch-release change.
> - Other duplicated-list instances found by the G-5 sweep and NOT fixed, all
>   outside this pass's scope: the win-probability sub-score keys and nine
>   maxima retyped as magic integers in `streamlit_app/pages/
>   2_Win_Alignment_Scorer.py` (fail-silent through `.get(k, 0)`);
>   `upload_handler._CDE_FIELD_MAP` against the shipped `.xlsx`, whose parser
>   `continue`s past a drifted label so a scoring attribute silently never
>   arrives; `_BOOL_FIELDS` and the int/float key subsets hand-derived from
>   that map; `streamlit_app/utils._IDENTITY_KEYS` as a denylist, which
>   defaults a new key to "scoring attribute"; `excel_builder`'s retyped
>   currency-column list and distress labels; `markdown_builder`'s table of
>   contents against the headings it emits (already divergent, and its anchors
>   do not match the generated slugs); and `utils.TIER_COLORS`, whose keys
>   match no tier the model has produced since the tier vocabulary changed.
>
> **This package pins nothing about that file.** Its only reference to the
> workbook's structure is a comment. So the flagship is protected transitively
> — a re-published file with a changed layout fails inside the dependency
> before any verdict reaches an application — but the criterion TEXT this
> package quotes into the filing (`renderers/_methodology`) is a hand-typed
> copy of the workbook's NOTES sheet, pinned as a `QUOTE:` row against the
> rendered document and against nothing upstream. **The dependency guards the
> file; the flagship quotes it.** Recorded that way rather than the other way
> round, which is how the portfolio has described it for three rounds.

### The constant gate (new)

**Every published constant is now pinned to the string it prints.**
`tests/test_invariant_output.py` collapses every digit run to `N` before it
intersects, which is what makes invariance detectable at all — without it every
dollar figure varies per scenario and nothing is invariant. THE MASK IS CORRECT
AND WAS NOT WEAKENED. But it necessarily erases every constant the document
prints, so that gate was structurally blind to all of them. Measured on the
1.2.0 tree by mutating the rendered 85%/20% commitment to 55%/5%:

```
[baseline 85%/20%]  invariant=207  UNALLOWED=0  DEAD=0
[mutated  55%/ 5%]  invariant=207  UNALLOWED=0  DEAD=0
```

`tests/pinned_constants.txt` + `tests/test_pinned_constants.py` close it. Each
row asserts a literal string against a rendered artifact, carries a source (or
says HOUSE, and the rendered text must then say so too), and fails closed: an
empty registry, a stale pin, a missing source and an unadjudicated constant all
error. A coverage test sweeps `nmtcapp/data/` and requires every constant any
other module reads to be pinned or waived with a reason.

Verified by mutating each pinned constant one at a time: **17 mutations, 17
caught.** The invariant gate stayed green on 16 of the 17.

**Five constants were duplicated as display literals** and are now interpolated,
because a pin over a literal pins the typing rather than the value:

- `win_probability` printed "the 40-point minimum" and "the 85-point minimum"
  while gating on `HIGHLY_QUALIFIED_SECTION_MIN` / `_AGGREGATE_MIN`. Moving
  either constant would have changed which applications were gated out while
  the printed explanation named the old bar.
- `excel_builder.weight_map` hardcoded the readiness weights under keys
  (`eligibility`, `validation`) that do not match `ReadinessScore`'s component
  keys (`eligibility_quality`, `validation_pass_rate`), so `.get(comp, 0)`
  returned **0** for both. **The workbook printed Eligibility Quality 0.0% and
  Validation Pass Rate 0.0%, a Weight column summing to 65%, and two components
  declared weightless** — against a methodology appendix in the same package
  stating 25% and 10%. Found by recomputation, not by any audit.
- `section_a_business` typed the >=75% band; `data/schema.py` owns it.
- The methodology appendix was three hand-typed copies (Word, PDF, markdown)
  whose figures were all literals and which disagreed with each other about the
  names of the readiness components. It is now composed once in
  `renderers/_methodology` from `nmtcapp/data/`.
- `tables/pipeline_table` kept module-local copies of the credit price, credit
  rate and CDE fee rate, so Appendix A and Section D computed the same figures
  from two independent copies of the same three numbers.

`DEEP_DISTRESS_MIN_PCT` was **assigned twice on consecutive lines**; the mutation
harness found it when changing the first assignment moved nothing.

### Fixed — financial tables

- **Appendix A printed five invented columns as data.** The CY 2024-2025 NMTC
  Allocation Application was retrieved and read: the Fund's per-project pipeline
  attachment is **Table A5: Proposed Transactions** (Exhibit A, pp. 82-84), and a
  full-text search of all 142 pages returns **zero** occurrences of "QLICI B",
  "Senior Debt", "Subordinate Debt", "Annual Operating Budget" and "Investor
  Equity". The Fund collects one QLICI total (row h) and defines no tranches.
  So the five are **deleted**, not bracketed as `[CDE TO COMPLETE]`: bracketing
  preserves a form shape, and this one is not the Fund's. The CDE's own
  `qlici_amount` is printed whole as "Total QLICI ($)". The module docstring's
  claim to "mirror CDFI Fund CY2025 Excel template format" went with them.
- **A $15.15MM contradiction inside one document, which `check_consistency`
  passed.** Section D took nmtc-calc's leverage loan (the residual of QEI less
  investor equity); Appendix A sized it at a flat 80% of QEI from a module-local
  constant. On the shipped 20-project sample: Appendix A $98,000,000, Section D
  $82,846,750. Both now use the identity that is true of the structure the
  document describes — leverage + equity = QEI.
- **The two branches of `nmtc_calc_adapter` disagreed with each other**, so a
  user without nmtc-calc installed got a different Section D. `_compute_fallback`
  sized leverage at 80% of QEI where the library returns QEI less equity, and
  returned `avg_leverage_ratio` as a *fraction of QEI* (0.80) where the library
  returns leverage/**equity** (~2.09x) — one key, two incompatible quantities,
  a factor of 2.6 apart. Both branches now model the same structure.
- **`check_consistency` gained a cross-surface arithmetic check.** Any figure the
  document prints in more than one place must be one figure. The shared-figure
  list is derived by calling the renderers, not hand-written. Proven to fail:
  reintroducing the flat-80% leverage produces
  `Total leverage loans disagrees between surfaces of the same document:
  Appendix A (per-project total) $98,000,000; Section D (deal economics)
  $82,846,750 (difference $15,153,250)`.
- **"Net Subsidy to QALICBs" overstated by ~3.3x** — it was QEI minus CDE fees,
  97.5% of QEI, while the term of art means the QALICB's benefit net of the
  leverage loan it repays. **No replacement formula was substituted**: the
  CY 2024-2025 Application never uses the phrase (zero occurrences in 142
  pages), and the closest federal figure is an observation rather than a
  definition — GAO-10-334 reports that eight case-study CDEs "generally agreed
  that it is reasonable to expect that the CDE will leave about 50 percent to
  65 percent of the amount of tax credits investors can claim in QALICBs after
  the 7-year tax credit period". The row is renamed **"QEI Less CDE Fees ($)"**
  and says on its face that it is not the retained benefit. The published
  `total_net_subsidy` dict key is unchanged: this is a patch.
- **The Fund's Deep-only 20% bar rendered above a combined deep+severe figure.**
  Deep-only was computed on every run and reported nowhere. Section B now
  reports deep-only, severe-only and combined as separate rows, and the
  commitment row states that the 85% and 20% bars have different bases.
- **Cell formatting now reads the column, not the magnitude.** Every renderer
  decided currency by `value > 1000`, which is too eager (a non-currency float
  takes a dollar sign) and too timid (a share stored as a fraction is under the
  threshold, so Word and PDF printed "0.33" for 32.8% and Excel rendered it
  "0"). `renderers/_cell_format` formats by what the header declares. Appendix
  C's share is a float again, with a real `pct_cols` entry — it sorts and sums
  in the workbook, which 1.2.0 traded away as a stated cost.
- **Five of the six Excel sheets had stale format configs** — twenty column
  names that do not exist in the tables they format, not just the geographic
  sheet. An unmatched name silently formats nothing. `_write_df_to_sheet` now
  raises on a name it cannot find.
- The Excel Summary Dashboard showed a readiness Weight column with **no
  disclosure of any kind** — the only one of the four artifacts to print the
  weighting without saying whose it was.

### Fixed — citations and provenance

- **The distress-definitions citation was 0-based.** It read "columns 14 and 15";
  the Fund's own NOTES sheet labels them **"Column O. Severe Distress"** and
  **"Column P. Deep Distress"**. Verified by opening
  `NMTC_LIC_Eligibility_2016_2020.xlsb`. A reader checking columns 14 and 15
  would land on N and O. Corrected in the rendered methodology appendix, in
  `tests/attribution_allowlist.txt`, and on the published docs page
  `docs/reference/data-sources.md`. **The docs fix does not reach `gh-pages`
  without a manual `mkdocs gh-deploy`.**
- The statutory **39% credit rate** was the one deal-economics figure with no
  attribution anywhere in the document; the methodology note now states it and
  cites IRC §45D(a)(2).
- **`Native Area` is the CDE's own declaration** and every surface now says so.
  Traced from the rendered `Native Area: 10%` back to the `native_area` CSV
  column: it is not read from nmtc-mapper (which dropped `is_nmtc_native_area`
  at 0.5.0), not defaulted and not inferred. The CDFI Fund publishes no
  tract-keyed NMTC Native Areas resource — the four classes are Census AIANNH
  geographies whose GEOIDs cannot nest into `SSCCCTTTTTT`, and the determination
  is a spatial intersection against the CIMS map. Special Targeting scores it,
  so a wrong figure here is a scored figure.

### Fixed — the CLI summary block

Read the same way as the documents, which is where `Native Area` had been
sitting in plain sight for the whole cycle:

- The `(✗ target)` tick cited `TARGET_DISTRESS_THRESHOLDS`' 0.75 — a value
  `data/schema.py` labels a HOUSE HEURISTIC in capitals. Every rendered document
  got that disclosure in 1.2.0; this block did not.
- `Non-LIC` rolls unverified projects in with ineligible ones, so it is an
  **upper** bound while the distress shares beside it are lower bounds. It now
  says so.
- `Eligible` is a share of project count while everything under Distress
  Concentration is a share of QEI. Two denominators under one heading, neither
  stated; both labels now state their own.

### Fixed — shipped inputs and packaging

- **`3500 Troost Ave, Kansas City, KS` was wrong data, not a geocoder gap.**
  Troost Avenue is a Kansas City, **Missouri** street. The Census geocoder
  resolves the address to MO 64109, tract 29095017800, and refuses it when the
  state is given as KS — which is why a wrong-state row surfaced as "could not
  be verified". Corrected to MO in `pipeline_sample_strong.csv` and
  `Pipeline.sample()`, with the tract, because a Kansas GEOID on a Missouri row
  fails `consistency_check`'s own state-FIPS test.
- **`2800 Freedom Dr, Charlotte, NC` was a geocoder limitation.** Freedom Drive
  is real and 2700, 2801, 2810 and 2900 all resolve; only that exact even number
  is absent from the Census TIGER address ranges. Nudged to 2810.
- **`nmtcapp analyze` exit code, ruled on explicitly.** It stays 0 on a failed
  check — `analyze` is a report, not a gate, and refusing to print a report
  about a pipeline with problems is the opposite of useful — but the failure is
  now named on stderr with the rule stated, `--strict` exits non-zero, and the
  `--help` text says what the exit code means. The library and notebook paths
  behave the same way and return `ValidationResult.passed` for the caller.
- **The docs sample-output hook failed open.** Without the output extras it
  produced two of four formats and logged success under a `--strict` build,
  while `docs/workflow/output-formats.md` told the reader all four are generated
  on every build. It now raises. Demonstrated: the same partial toolchain that
  used to build green now exits 1 with
  `sample output is missing 2 of 4 formats: pdf, word`.
- **`[docs]` extra added.** `pip install -e ".[docs]"` emitted
  `WARNING: ... does not provide the extra 'docs'` and silently installed only
  the core; nothing anywhere pinned the docs toolchain.
- **CI builds the docs on every pull request** (`--strict`). It does not deploy:
  publishing to `gh-pages` is still a manual `mkdocs gh-deploy`, and that is
  stated in both contributing guides.
- **Refusal messages resolve their paths at runtime.** They named
  `nmtcapp/templates/...` as though the reader were in a git checkout. They now
  lead with `nmtcapp init <dir>` and give the resolved packaged path. The
  sample-identity guard itself is untouched and was re-verified: all three
  refusal cases fire, name which field matched, and near-misses still pass.

### Fixed — the gate around the fixes, which was narrower than this file said

A hostile audit of the paragraphs above found the fixes themselves correct and
the gate built around them incomplete. Three blockers, all closed here.

**The release pipeline could not ship this artifact.** `MANIFEST.in` is
`prune docs`, `release.yml` runs the suite from inside the tarball, and two
tests read files the tarball does not carry. Reproduced by building the sdist
from a pristine clone and running `release.yml`'s exact invocation:

```
2 failed, 931 passed, 4 skipped, 1 deselected     PYTEST EXIT CODE: 1
FAILED test_docs_hook_raises_when_a_configured_format_is_missing
FAILED test_every_consumed_constant_is_pinned_or_waived
```

CI was green throughout, because CI runs from a checkout. A tag on that
artifact would have failed the release job with nothing on PyPI — the Aug 6
failure mode by a different road. Both now skip explicitly, each with its own
written reason, mirroring `test_no_committed_generated_artifacts.py`. Not a
`try/except`: a skip is counted, and `FLOOR` subtracts skips from the executed
total, so a skip that starts firing shows up as a smaller number rather than as
green. After the fix: **943 passed, 11 skipped, exit code 0.**

The second failure was hiding a worse one. `_consumed()` walked
`nmtcapp/` with `os.walk`, which yields nothing — silently, without error — for
a directory that does not exist. In the sdist that made every constant look
unconsumed, so the sweep would have reported success having adjudicated none of
them. It failed only because `_module_constants()` opened `schema.py` first and
raised, an accident of ordering standing in for a guard. The roots now raise.

**The constant gate did not cover the class it was built for.** Three mutations,
none of them this release's, all survived with 937 green:

| Mutation | Before | After |
|---|---|---|
| `distress_table._ELIGIBILITY_SOURCE`: ACS 2016–2020 → 2011–2015 | 937 passed | **fails** |
| `styles.DISTRESS_DISPLAY`: swap the `deep` and `severe` labels | 937 passed | **fails** |
| `recommendations.py`: hardcoded federal 85% → 55% | 937 passed | **fails** |

The middle one is the reason the gate's scope changed. It leaves Section B's
narrative share correct — that reads the `distress_level` KEY — and relabels
every project in Appendices A, B and D, which read the LABEL. Reproduced on a
five-project fixture: **the narrative says 19.4% in Deep Distress and the
attachment's Deep rows sum to 47.2%**, in one filing, against a 20% federal bar.
Every gate stayed green: invariance masks digits and these strings have none,
attribution normalises digits, the cross-surface check compares five dollar
figures, and the pin registry had never considered a label dict.

It got through because **a key-to-printed-word mapping had never been a
candidate for pinning** — not because anybody skipped it. So the sweep no longer
asks which directory a constant lives in. It asks the artifact: *does any string
this constant holds appear in the rendered document?* A constant whose strings
appear must be pinned or waived by hand. A constant whose strings do not is
adjudicated by the fixture, on every run, and needs no written waiver — which
matters, because a hand-written "this does not render" is exactly the claim that
goes stale silently.

Widening `DATA_MODULES` to every module that renders was measured first and
rejected: 97 constants would each have needed a row, most saying "this is a
colour". The rendered-string sweep demands **19**, and 208 constants are swept
where 49 were.

> **Remeasured in 1.3.0, and again in FIX-2, and again in 1.4.0.** This
> sentence read **160** when 1.2.2 shipped, **183** at `ff49064` and **203**
> at `56573c0`, each true of its own tree. 1.4.0's five are
> `renderers/_question_22`'s constants, three of which are waived on the
> ground that they reach the CLI summary and the Streamlit Geographic tab
> rather than any of the six document renderers.
> `test_the_changelogs_sweep_figures_match_the_tree` asserts the figure against
> the tree *under test*, not against the tree the paragraph was written on, so
> a release that adds a constant to a swept module makes the sentence false and
> fails the gate — which is what happened here, twice, on purpose. 1.3.0 added
> nine (`renderers/_question_25`, eight, and `_cell_format.NOT_SUPPLIED_INPUT`)
> and FIX-2 adds ten more: eight in the new `renderers/_frame_geometry` and two
> in `renderers/_sheet_geometry` (`DEFAULT_ROW_HEIGHT`, `DEFAULT_FONT_SIZE`).
> **1.3.1 adds ten more and the gate went red on the old figure, which is the
> whole point of it:** four in `renderers/_frame_geometry` (`FOOTER_RULE_INCHES`,
> `FOOTER_TEXT_BASELINE_INCHES`, `CHROME_TEXT_BASELINES_PTS`,
> `CHROME_BASELINE_TOLERANCE_PTS` — G6), three in `tables/distress_table`
> (`LIC_ROW_LABEL`, `NATIVE_AREA_ROW_LABEL`, `HMR_ROW_LABEL` — F2), two in
> `core/application` (`OUTPUT_EXTRA`, `OUTPUT_EXTRA_INSTALL` — F4) and one in
> `renderers/_disclosure` (`LIST_PREVIEW_LIMIT` — F1).
> The figure is a property of the tree and is remeasured with it; the
> paragraph's subject, that the sweep is derived rather than hand-listed, is
> unchanged.

> **Corrected in FIX-2 (G-1).** This paragraph shipped saying **133**, and three
> sites in `tests/test_pinned_constants.py` said the same. All four figures were
> measured on `324e9cd` — the artifact the hostile audit rejected — and carried
> forward without being remeasured; the branch head held 149. The same round's
> other published scope figures were wrong the same way: *outside `data/`* read
> 77 and was 93, *with `streamlit_app/`* read 108 and was 124, *`FMT_*`* read 8
> and was 7, and the distress-label pin count read twelve and was nine. A
> hand-typed count inside a gate is a claim like any other, and none of these
> could fail. Every scope figure is now derived by `_sweep_census()` on the tree
> under test, the module's prose may state none of them (a structural guard
> fails on the claim shape, not on the digit), and
> `test_the_changelogs_sweep_figures_match_the_tree` fails this very sentence if
> it drifts from the tree again.

Two structural holes closed with it: the consumer scan now includes
`streamlit_app/`, and a subscripted pin adjudicates **one** key — through
1.2.1-rc it stripped the subscript, so pinning `NMTC_PROGRAM_CONSTRAINTS
[credit_rate]` silently adjudicated every other key including any added later.

A seventh surface (`RecommendationSet.summary()`, reachable through the public
`app.recommendations()`) and an eighth (`excel_cell_formats`) are now gated. The
second is not text: openpyxl returns `6000000` whether the cell prints
`$6,000,000` or `600000000.0%`, so every `FMT_*` number format was
invisible to every text-based gate. They are now pinned to the column they
format.

Five pin rows named modules the package does not have (`_statute.`,
`_workbook.`) — prose labels for quotations, which no sweep could ever match,
sitting outside the derivation while looking like they were inside it. They now
carry a `QUOTE:` prefix and a test fails on any name with no constant behind it.

**`check_consistency` passed vacuously, in shipped code.** Forcing
`_shared_figures` to return `{}` produced `issues == []` and `passed == True`.
The non-empty guard existed only in the test file. In a CDE's hands there is no
test file. It is now in the validator — and not as a numeric floor: a floor of
4 against 5 pairs lets one drop silently, and re-deriving it from today's count
is how a floor stops being evidence. The check is set equality against the
declared groups, and the declared set is itself derived — every currency column
`pipeline_table` publishes and every dollar row Section D renders must be
compared or excused with a reason.

A missing column now raises instead of hitting a `continue`; that fail-silent
filter is the same shape that cost Word a column below. And the docstring
claiming the pairs were "DERIVED FROM THE RENDERERS, NOT HAND-LISTED" was true
of the values and false of the map — corrected, with the coverage genuinely
derived. `pipeline_table.CURRENCY_COLUMNS` was declared in 1.2.1 saying it
existed "so a column rename cannot silently drop a figure out of the check", and
was then imported by nobody while this module retyped the same names; it is now
read.

The check also compared five dollar figures between two surfaces while its
docstring promised "any figure printed in more than one place". **Total QEI is
printed in Appendices A, C and D as well as Section D; Jobs Created in A and D.
None was compared.** Both are now, and the claim is narrowed to what the code
does with the remaining gap stated.

### Fixed — live text a CDE reads

- **Word's Appendix A silently dropped the Native Area column.** `word_builder`
  asked for `"NMTC Native Area (Y/N)"`; the table renders `"NMTC Native Area
  (CDE-declared, Y/N)"` — the heading 1.2.1 widened so every surface would say
  whose declaration the flag is. `[c for c in landscape_cols if c in
  full_df.columns]` dropped it without a word: **11 columns rendered where the
  comment claimed 12, and this file's "every surface now says so" was false for
  Word's Appendix A, which had stopped saying anything.** The filter is gone;
  an unmatched column raises.
- **The High Migration Rural sentence credited the CDE with a tool-corrected
  figure.** Section A read "Per the flags supplied in this CDE's own pipeline
  submission…" over a share the mapper had overwritten: the CDE declared 36.2%,
  `_prefer_determinate(False, True)` returned `False`, and the document filed
  12.6% as the CDE's own. **The mapper is right; the sentence was wrong about
  its own author** — the mirror image of the Native Area defect fixed in this
  same release. The two flags now carry separate attributions and the HMR
  clause says which authority governs. A sweep of the join that produces this
  defect — a field that is both a CDE-supplied column and adapter-assignable —
  returns exactly two, `is_high_migration_rural` and `is_opportunity_zone`, and
  is now a test rather than a one-off search.
- **A fabricated definition of a federal designation was deleted from live
  recommendation text, and this file did not mention it.** `recommendations.py`
  told a CDE which targeting category to pursue and named one as

  > Persistent Poverty Counties (100+ years at ≥20% poverty)

  **There is no federal designation measured over 100 years.** A Persistent
  Poverty County is measured over THREE DECADES — consecutive decennial
  censuses plus the current ACS — so the parenthetical was wrong by more than
  threefold, in a sentence advising a CDE where to source projects. A CDE
  reading it would look for a century of data that does not exist, or would
  repeat the definition in its own application.

  It was **deleted rather than corrected to 30**: this tool does not determine
  the designation, holds no county list, and cannot cite one, so substituting a
  number nobody here checked against a primary source would have relocated the
  defect rather than removed it. The sentence now points at the authority that
  publishes the list, which is what the CDE has to consult anyway.

  **Recorded here in FIX-2 (G-6).** The deletion shipped in 1.2.1 with a
  fifteen-line note in the source explaining exactly this, and no line at all
  in the release notes — so a CDE holding a 1.2.0 draft containing the
  fabricated definition was never told to remove it. If you have a draft
  generated before this release, delete that parenthetical from it.

- **`RecommendationSet.summary()` printed "below the 85% CDFI Fund threshold"
  from a hardcoded literal.** Every federal figure in `recommendations.py` is
  now interpolated — the 85% and 20% distress bars, the 40/85/45 gating points,
  the 70%/90% track-record bars, the DBC and unrelated-entity bars, and every
  section and sub-score denominator. The 90%/98% "competitive threshold" was
  neither federal nor sourced; it is this package's own winner-pattern band, and
  the sentence now says so.
- **The docs site still described withdrawn output.** `output-formats.md`
  listed "Net subsidy to QALICB" as a row the document contains; it is `QEI Less
  CDE Fees ($)`. `pipeline-analysis.md` carried the same phrase. The attribution
  and fabrication gates render artifacts into a temp directory and never look at
  `docs/`, exactly as they never looked at `examples/sample_output/`. Both pages
  fixed, and a scan of every `.md` page for claims this repository has already
  established to be wrong is now part of the suite. **`gh-pages` does not update
  until `mkdocs gh-deploy` is run by hand.**
- **Section E promised detail it did not have.** "…including states served,
  sectors financed, and outcomes achieved" printed directly above rows reading
  `States: N/A. Sectors: N/A.` Neither field is collected by the CDE profile
  scaffold, and outcomes are a placeholder two subsections below. The sentence
  now names only what the awards carry, and `N/A` — which reads as a value the
  CDE supplied — is replaced by an explicit not-collected marker.
- **`expected_units_built=None` rendered as "0 affordable units",** a supplied
  zero where nothing was supplied, on a field feeding a Community Outcomes
  measure. Same class as the `"Quarterly"` governance default removed in 1.2.0.
  Absent values now render as an em dash, matching the tri-state flags already
  used elsewhere; a real `0` still reads as `0`.
- **An invalid sector rendered as though it were a recognised one.** `retail`
  passed validation with a stderr warning nobody reads and printed as "Retail"
  in Appendix D beside seven Fund categories. **The list is a suggestion on the
  way in and a contract on the way out**: the project still loads — raising
  would reject pipelines that work today, and a patch release is not the place
  — and the rendered cell now marks the sector as unrecognised.

### Fixed — the registry and the bookkeeping

- **Three waivers were wrong by the registry's own definition.**
  `TOP_TIER_AGGREGATE_MIN` and `TOP_TIER_SECTION_MIN` were waived as rendering
  "only when a fixture reaches Top Tier", which waived the fixture rather than
  the constants. A second fixture now reaches the branch — and asserts it did —
  so both are pinned to the tier label they decide. `TARGET_SECTORS`' waiver
  admitted the constant reaches `cli_summary`; its reason is rewritten to what
  is actually true of it. The `DISTRESS_LEVELS` waiver identified its rendered
  twin and stopped there, which is a forwarding address rather than a waiver —
  and the twin was unpinned on every surface at the time. It now says what is
  pinned instead.
- **Thirteen allowlist entries were filed `SOURCED` over an internal defect ID,
  and five more over an assertion that no source exists.** Not one is a false
  statement. But `SOURCED` is the shelf a reviewer skims past assuming somebody
  can go and read the cited thing, and "1.2.1 B-3" is not readable outside this
  repository. Two categories added: `HOUSE` (this package set it, and the
  rendered line admits that) and `UNSOURCED` (no primary source exists, and here
  is the research establishing that) — the latter a *stronger* claim than a
  citation, because it asserts a negative somebody had to go and check.
- **Two pins passed incidentally.** `IRC §45D` appears inside the compliance-
  period and credit-rate sentences that are separately pinned, so the row could
  not fail on anything those two did not already catch; `/100 < 85)` is six
  characters of punctuation. Both are re-anchored to the sentence a CDE reads.
- **`FLOOR` derived itself from stale counts.** `release.yml` said `FLOOR=440`
  from "collected 896 / executed 892" — the 1.2.0 numbers. 1.2.1 collects 954
  and executes 943 in the sdist, so by the file's own rule the floor is **470**.
  The gate still functioned; its derivation had stopped being evidence, in a
  file whose whole premise is that its numbers are.
- **`50 / 50 / 10` existed twice, independently.** `win_probability` hardcoded
  `"max_available"` beside the constants it gates on, which is why the waivers
  for `BUSINESS_STRATEGY_MAX` and its two siblings were *factually true* — a
  duplication recorded in the release that removed five others. All three are
  read now, and the waivers became pins.

### Fixed — three defects THIS RELEASE INTRODUCED, and the gate that finds them

Not inherited. Each was created by the previous fix in this same release, each
one level deeper into the same sentence of Section B, and every gate stayed
green through all three. None of them shipped. This file omitted all of it.

```
B-5's fix  ->  B-1: an exclusive bucket rendered under an inclusive label
B-1's fix  ->  B-3: a year rendered as 2,019
B-1's fix  ->  FIX-3: an honest QEI label rewritten into a QLICI bar assertion
```

- **B-1 — one filing stated both 0.0% and 85% severe distress.** B-5's fix
  split the 85%/20% bars onto their own rows and gave the new row the
  **exclusive** severe bucket under the **inclusive** words "QEI in Severely
  Distressed Tracts", against an Appendix B whose per-project flag counts deep
  as severe. On a pipeline whose distressed tracts are all deep, Section B read
  0.0% while Appendix B flagged every one of them "Yes" — one filing, two
  answers. The subset premise was verified against the Fund's own workbook
  rather than inferred: `NMTC_LIC_Eligibility_2016_2020.xlsb`, columns O and P,
  all 85,395 tracts — 8,061 deep, 13,121 severe-not-deep, **zero**
  deep-but-not-severe. The bucket is renamed `pct_severe_excluding_deep`, so
  the name says what it holds.
- **B-3 — prior-award years rendered as `2,019`** on markdown, Word and PDF.
  B-1's cell-format unification correctly gave the currency columns their
  dollar signs and gave a year a thousands separator on the way past.
  `_cell_format` now declares an IDENTIFIER column class in its own contract.
  Excel had rendered `2,019` since at least v1.2.0, from the magnitude
  auto-detect rather than from 1.2.1.
- **FIX-3 — the QEI shares were relabelled as answers to the Fund's QLICI
  bars.** See the section below.

**The gate: a ~3,250-line rendered-output regression baseline.** Every other
gate in this package asks whether a rendered line is ENTITLED to be there — the
invariance gate asks whether it was derived from the input, the constant gate
whether a published value prints as pinned, the attribution gate whether a
claim carries a citation. **None asked what CHANGED**, and all three defects
above were found by a human reading the output. A byte-diff of all four formats
between v1.2.0 and the branch head, from one fixed fixture, showed two of them
in ninety seconds. Nobody had ever diffed this package's output against its own
last release.

`tests/test_rendered_output_baseline.py` is that diff, kept: one fixed
fully-populated fixture, all four formats projected to text (including Excel's
number formats, because the year defect *is* a number-format defect and the
cell value 2019 is correct either way), normalised for timestamps, temp paths
and the run date only, and diffed line by line against
`tests/rendered_baseline/`. A changed line fails. Regenerating is a separate
deliberate command (`python -m tests.regen_rendered_baseline`) whose output
belongs in the same commit — a gate that writes its own expected output on
failure can never fail. It fails closed on a missing format, an empty
extraction, an absent or suspiciously short baseline, and a fixture that stops
populating a field.

The first 743-line diff was classified in full: 556 intended fixes across 13
distinct changes, 166 consequential reflow, and the two defects above.

### Fixed — the Fund's distress commitments are measured on QLICIs (FIX-3)

**The document told a federal agency the CDE clears a bar this package does not
measure.** The CY 2024-2025 NMTC Program Review Process, "Targeting Areas of
Higher Distress (Question 25)", commits an applicant to *"at least 85% of its
**QLICIs** in specified areas of severe distress and/or areas characterized by
multiple indicia of distress"* and *"at least 20% of its **QLICIs** to 'Deep
Distress' areas"*. Both are shares of **QLICIs**.

Every share this package computes is a share of **QEI**:
`analyze_distress_concentration` buckets and divides `qei_request` and reads
`qlici_amount` never. `qlici_amount` is a required CSV field that reaches
exactly one rendered figure — the "Total QLICI ($)" column of Appendix A — plus
the `QLICI <= QEI` consistency rule. **It feeds no percentage, no score and no
bar.**

**The arithmetic is inherited; the claim was not.** 1.1.5 and 1.2.0 both render
*"QEI in Deep/Severely Distressed Tracts"* — an honest label on an honest
number. B-1's fix rewrote it into a bar assertion without touching the
denominator, on three rows plus two new ones naming the CDE:

```
was:  QEI in Deep Distress Tracts (the 20% bar's own basis)           52.2%
      <CDE> — measured against the 20% Deep Distress bar              52.2%
```

On an 8-project pipeline where only the QLICIs vary, that files 25.0% against a
bar the CDE misses at 9.5%, in a sentence naming the CDE, on all four surfaces.
**Nothing published is wrong and this never shipped.**

- The two `bar's own basis` labels now name their own denominator, and the two
  `measured against the …` rows — exact duplicates of the rows above them whose
  only added content was the assertion — are **deleted**. No share row carries
  a bar percentage at all.
- The commitment row becomes a **BASIS NOTE** stating both mismatches on its
  face: the denominator (QLICIs, not QEI, so no figure above answers either
  commitment) and the numerator (the 85% covers severe distress **or multiple
  indicia**, and this package computes no multi-indicia measure at all, so even
  the QLICI-denominated share would be incomplete against it). It replaces
  *"Read each against its own row above"*, which instructed the reader to make
  exactly the comparison the bases do not support.
- **The same assertion was live in a second file.** `recommendations.py` told a
  CDE *"Only 40% of QEI is in severe distress or multi-indicia distress tracts
  — below the 85% CDFI Fund threshold for full credit"* and subtracted a QLICI
  bar from a QEI share to state a gap in percentage points. It fires on no
  fixture in the package, so no rendered gate had ever seen it. Both findings
  now name the denominator and frame the gap as the distance to **this tool's
  own QEI-based proxy**, which is what it measures.
- `docs/reference/methodology.md` presented both sub-score thresholds as
  "85%+ / 20%+ of QEI" with no mention of QLICIs, and documented a `pct_deep`
  fallback removed in 1.2.1. Both corrected; a basis note added.
- The Streamlit benchmark caption printed the 85%-of-QLICIs bar under a chart
  axis reading "% of QEI"; it now says the two are not comparable.
- `_disclosure.unverified_banner`'s docstring justified the full-pipeline
  denominator as *"it matches the basis the Fund scores on"*. The **shape**
  matches — aggregate over everything, not over the geocoded subset — the
  **basis** does not, and this was the sentence the rendered labels were
  written from. `DISTRESS_SHARE_SEMANTICS`, which the pins consult, said the
  same thing and now says "proxy".

**Two new gates.** `tests/test_qlici_basis.py` pins the corrected text and adds
the general rule: **a rendered line may state one of the Fund's bar percentages
only if the same line names that bar's denominator.** Run against the baseline
at `128436f` it returns twelve hits — the four Section B rows, in each of the
three text formats. It also scans `RecommendationSet.summary()` and the
`nmtcapp analyze` block, which the rendered baseline's fixture cannot reach
because that fixture scores full credit on both distress sub-scores.

**THE EXCEL WORKBOOK IS NOT COVERED BY THIS FIX, AND THAT IS KNOWN.** The
BASIS NOTE lands on markdown, Word and PDF. `excel.txt` is byte-unchanged, and
the reason recorded for that — "Excel does not render this subsection" — is
true of the **subsection** and false of the **figure**. `Summary Dashboard!A12`
reads `Deep/Severe Distress Concentration` and `C12` carries the share as a raw
float under a `0.0%` number format. **The label names no denominator, and the
workbook contains no basis note anywhere**: zero occurrences of "BASIS NOTE",
"a share of QEI" or "not of QLICIs" across all sheets, and its only "QLICI" is
Appendix A's `Total QLICI ($)` column heading. **A CDE copying that cell into
Question 25 would file a QEI figure against a QLICI bar** — which is the exact
harm FIX-3 exists to prevent, on the surface most likely to be copied from.
Two things follow. The cell is invisible to the rendered gate by construction:
the baseline stores it as `|float|fmt=0.0%|0.8531073446327684`, so a scan keyed
on the string "85%" cannot see it, and the label carries none of the framing
words the rule requires. And the figure is not wrong — it is an accurate share
of QEI — so nothing here is a false statement; it is an **unlabelled** one.
**Not fixed in this release** (adding a note to the workbook moves the Excel
baseline, which this patch does not regenerate) and **first in the 1.2.2
queue**, ahead of the denominator swap: it is the shortest path from this
package to a wrong number on a federal application.

**And a fixture whose two denominators actually differ.** Every fixture in the
package sets `qlici_amount == qei_request` — both shipped samples,
`Pipeline.sample()`, the pin fixtures, and the baseline gate's own fixture.
That is why four passes missed this. **A fixture that collapses two distinct
inputs cannot exercise the distinction, and no gate built on it ever will.**
`test_the_two_denominators_actually_diverge` is the first one where they do, and
it fails closed if they ever collapse again.

### Changed — the release floor is derived by a test, not typed

`release.yml`'s sdist job asserts that the tarball's suite executed tests rather
than shipping every module and deselecting the lot. Its threshold was a
hand-typed `FLOOR=470`, **stale for the third time in one cycle** — `440`
carried forward from 1.2.0, then `133` typed in three places, then 470 derived
from `954 / −11 / 943` when a fresh run of the same job gives
`1,022 / −15 / 1,007`. Every one of them was wrong in the safe direction, which
is why nothing ever announced it: **a floor that is too low is not
conservative, it is a gate that has stopped asking anything.**

`FLOOR=500`, and `tests/test_release_floor.py` now parses the assignment, runs a
fresh collection of the same suite under the same marker expression, and fails
when the number drifts out of the band the workflow's own stated rule produces.
Grow the suite without re-deriving and CI says so.

Deriving it inside the step was considered and rejected, and the rejection is
recorded in the workflow: the floor exists to catch a marker change or an `-m`
expression that deselects the suite, and a threshold computed from the same
deselected run moves down with it and can never fail. The reference count has to
come from somewhere the deselection cannot reach.

### Found by mutation

Six mutations, run against the finished gate. Five are killed by a pin; the
sixth was killed by a fix it exposed.

`_PIPELINE_COLUMNS` — the list `word_builder` and `consistency_check` both name
columns against, and which a reader of the module treats as the schema —
**governed nothing but the empty table.** The populated table's columns came
from a row dict, so swapping two entries of the declaration passed 954 tests.
They agreed by coincidence, with nothing checking that they did. The declaration
is now authoritative, a disagreeing dict raises, and the full header run is
pinned in order.

### Known and left alone

Reported rather than fixed, with reasons, in the 1.2.1 branch notes: the 25
invented GEOIDs (two of which were corrected as a consequence of the address
fix), `data/historical_awards.py`, round parameterization and the `"CY2025"`
default, `TOP_TIER_*` as an invented tier (now disclosed as this tool's own
label wherever it prints, but not removed), the readiness weights' attribution,
the sector→NAICS mapping, `geographic_analysis`'s hardcoded `_RURAL_STATES` and
one-MSA-per-state map, the `urban_rural` CSV column that `from_csv` never reads,
`DISTRESS_LEVELS` (a dead constant), and three addresses in
`pipeline_sample_weak.csv` that do not resolve (two verified as bad data, one as
a TIGER range gap).

Two further items, both recorded for the next release rather than patched:

- **Table A5 row (d), "Located in a Non-Metropolitan County?", is required by
  the Fund and this tool does not supply it** — despite column B of the
  eligibility workbook it already downloads and loads carrying the OMB
  designation. That is a real gap in the per-project attachment and a feature,
  not a patch fix.
- **Thirteen sub-scorers in `win_probability` cap at hardcoded literals**
  (`min(15.0, …)`) rather than at the section maxima beside them. It is why the
  eight sub-score maximum constants are waived rather than pinned: a pin on the
  denominator alone would freeze half of a pair whose other half is typed.
  Removing them changes scoring behaviour, which a patch is not the place for.
- **The `Opportunity Zone` columns carry no basis statement.** Like High
  Migration Rural, the flag is CDE-supplied and adapter-overwritable, but unlike
  it the headings credit nobody, so there is no false attribution to fix — only
  an absent one to add. Renaming the column would move a pinned heading, so it
  is recorded rather than done here.

Recorded by FIX-3, all of them **1.2.2** and none of them patch-safe:

- **FIRST IN THE QUEUE — the Excel workbook's distress figure carries no
  denominator and no basis note.** `Summary Dashboard!A12` /
  `C12`: `Deep/Severe Distress Concentration`, the share as a raw float under a
  `0.0%` format, with nothing in the workbook naming what it is a share of and
  no basis note on any sheet. **A CDE copying that cell into Question 25 would
  file a QEI figure against a QLICI bar.** The number is correct as a share of
  QEI; what is missing is the label. It is ranked first because it is the
  shortest path from this package to a wrong number on a federal application,
  and because Excel is the surface a CDE is most likely to copy from. It also
  cannot be caught by the gate FIX-3 added: the baseline stores the cell as
  `|float|fmt=0.0%|…`, so a scan keyed on the rendered "85%" cannot see it.
  Deferred only because writing the note moves the Excel rendered baseline,
  which this patch deliberately does not regenerate — **not** because it is
  judged low-risk.
- **`intelligence/recommendations.py:41` asserts an invariant its own module
  breaks, and a gate leans on it.** The module header states *"EVERY FEDERAL
  FIGURE IN THIS MODULE IS INTERPOLATED, NOT TYPED (1.2.1 L-3)"*. Line 232
  types both figures in *"The CDFI Fund awards full credit for CDEs offering
  50%+ below-market products OR documenting 5+ indicia of flexible terms"* as
  literals; `PRODUCT_FLEXIBILITY_BELOW_MARKET_PCT` and
  `PRODUCT_FLEXIBILITY_MIN_INDICIA` exist in `benchmark_thresholds` and are not
  imported there. **This is not cosmetic**: `test_qlici_basis.py`'s source scan
  detects bars in two ways, and one of them — `_BAR_TOKENS_IN_SOURCE` — looks
  for the constant NAMES precisely because the header says every federal figure
  is written that way. A typed federal figure is visible to that scan only if
  its literal value is one of the two distress bars; 50%, 5, 70% and 90% are
  not, so they are outside the gate entirely. Recorded here rather than fixed
  because interpolating the two constants changes a rendered recommendation
  string, which moves pins this patch does not regenerate. Fixing the header
  claim and the typed figures should travel together, and the sentence itself
  needs review on its merits — the CY 2024-2025 Review Process states the
  Question 15 threshold as *"100% of its QLICIs"*, with "at least 50%
  below-market" describing a rate discount rather than a share of products.
- **The denominator itself.** Switching the distress shares from QEI to QLICIs
  moves every scored figure, including the Community Outcomes sub-scores —
  `_score_higher_distress` and `_score_deep_distress` divide a QEI share by a
  QLICI bar, and that is now stated in a comment beside each. It is a
  methodology change that needs to be written down and hostile-audited before
  it is made, not a patch.
- **There is no multi-indicia measure at all.** The Fund's 85% covers severe
  distress **or** areas characterized by multiple indicia of distress — the
  Question 25 list of twelve. This package computes nothing for the second
  half, so even a QLICI-denominated severe-distress share would be incomplete
  against that bar. A missing methodology, not a bug.
- **`core/upload_handler.py:246-247` sets `qlici_amount = qei_request` when the
  column is absent.** *This is the mechanism that hid FIX-3 for four passes*:
  it silently substitutes one CDE input for another, so the two denominators
  agree on every pipeline uploaded without the column and the distinction can
  never be observed. **A warning would be patch-safe** — it changes no accepted
  input, no parsed value and no rendered figure, only what the CDE is told
  while it happens. **The substitution itself is not**: removing it makes
  previously-accepted uploads fail validation, which is an accepted-input
  change. Recommended for 1.2.2: keep the default, warn on it, and say in the
  warning that the substituted value is not the CDE's own QLICI total.
- **Every fixture in the package collapses the two fields.** Both shipped
  samples, `Pipeline.sample()`, the pin fixtures and the rendered baseline's
  own fixture all set `qlici_amount == qei_request`. The general rule, worth
  stating because it generalises well past this defect: *a fixture that
  collapses two distinct inputs cannot exercise the distinction, and no gate
  built on it ever will.* Fixing the fixtures moves the rendered baseline, so
  it belongs with the denominator work rather than here;
  `tests/test_qlici_basis.py` carries a divergent fixture of its own in the
  meantime.
- **Six more shares are computed on QEI, and how many of them the Fund defines
  on QLICIs COULD NOT BE ESTABLISHED here.** `pct_native_area`,
  `pct_high_migration_rural`, `pct_persistent_poverty`, `pct_us_territories`,
  `pct_below_market_rate` and `pct_unrelated_entity` all divide `total_qei`
  (`distress_analysis.py:179-184`). What the package itself records: only
  `pct_unrelated_entity` has a bar whose basis is written down here at all —
  `UNRELATED_ENTITIES_MIN_PCT`, annotated "90%+ **QEIs** to unrelated entities"
  — and the other five have no bar in `benchmark_thresholds` beyond the shared
  `SPECIAL_TARGETING_BONUS_PCT` 10% trigger, whose basis is likewise unrecorded.
  **No primary source was available in this pass**: no copy of the CY 2024-2025
  Allocation Application or Review Process is checked into the repository or
  cached on this machine, and the count must not be asserted from recollection
  in a file whose subject is fidelity. **None of the six currently renders
  beside a bar, so none is a live false claim today.** But if more than the two
  distress commitments turn out to be QLICI-denominated, **1.2.2 is a wider job
  than a single denominator swap** — establish the count against the
  Application's own question text, per share, before scoping it.
- **The rendered methodology note introduces the workbook criteria with the
  word "verbatim"** over text carrying three whitespace insertions per line.
  See the corrected bullet at the top of this release. The substance is exact;
  the word is not. Changing it moves a rendered line and a pinned constant, and
  this release's rendered diff is reserved for FIX-3.

---

## [1.2.0] — 2026-08-14

Integrity release: the section generators no longer write fabricated statistics,
fabricated CDFI Fund attributions, or false compliance assertions into documents a
CDE submits to a federal agency. Packaging is fixed so `nmtcapp init` works for
users who installed from PyPI.

**Minor, not patch.** Three changes here break a caller, and a version string is
where a pinned user sees that — not a CHANGELOG they may never open. See Breaking.

### Breaking

1. **`community_need_documentation` is removed from the public API.** It was
   exported in `nmtcapp.integrations.__all__`. There is no deprecation shim: a stub
   that raises is still an importable name for a function whose only behaviour was
   fabrication. Community need is now the CDE's to document — Section B emits a
   `[CDE TO COMPLETE: ...]` placeholder. Callers must delete the import.
2. **`nmtcapp analyze <csv>` now exits 2 where it previously ran.** It requires
   `--cde <path>` and `--requested-allocation <dollars>`. A scripted caller relying
   on the old bare form breaks and must pass both flags, or `--demo` to keep running
   against the shipped fictional profile (labelled DEMO MODE on every screen).
   The old behaviour silently scored the user's real pipeline against a fictional
   CDE and an invented $55,000,000.
3. **Native-area rendering changes from `N` to `—` for undeclared projects.** With
   the mapper read deleted (see below), a geocoded project whose pipeline sheet has
   no `native_area` value now keeps `is_native_area = None`, so
   `tables/pipeline_table.py` renders `—` and `tables/distress_table.py` renders
   `—` where both previously rendered `N`/`No`. That is the honest value: nothing
   ever determined it. **Aggregate counts are unaffected** — `distress_analysis.py`
   and `tables/geographic_table.py` both test `if p.is_native_area:`, and `None`
   and `False` are equally falsy. The one count that *does* change is a correction:
   a CDE who declared `native_area = Y` previously had that overwritten with `False`
   and is now counted. Verified by execution, not reasoning.

Templates also relocate into the package (`nmtcapp/templates/`); anything reading
them from the repo root must update its path.

### Disclosure

1.1.5 removed fabrication from the eligibility **adapter**. It did not touch the
**section generators**, which are the part that produces the submitted text. Drafts
generated with 1.1.5 or earlier could contain, with no indication that any of it was
invented:

- An HMDA lending-disparity paragraph in Section B asserting denial rates "exceed 30%"
  with "racial disparities of 2.3×", cited to "HMDA 5-year data, 2018–2022". No HMDA
  call was made on that path; both figures were string literals and the citation was
  for data never fetched. The accompanying tract count was `len()` of a five-key
  bucket dict, so it read "5 census tracts" for every pipeline of every size.
- Two distress thresholds printed under the CDFI Fund's name — "CDFI Fund Competitive
  Minimum 50.0%" and "CDFI Fund Target 75.0%". Neither appears in any CDFI Fund
  publication. The published CY 2024-2025 bar for full Community Outcomes credit is
  **85%** (Application FAQ #79), a value this package already held correctly in
  `benchmark_thresholds.SEVERE_DISTRESS_MIN_PCT` while printing the wrong one.
- Unconditional clean-compliance claims in Sections C and E ("zero compliance
  violations or performance defaults to date"; "All compliance obligations have been
  met"). These were emitted **even for a CDE whose own profile declared prior
  reporting issues** — the field was collected from the user and consulted by no
  section generator.
- Section D labelling the pipeline QEI total as the amount requested, so one document
  carried the CDE's real request on its cover page and a different figure in Section D.

**If you generated drafts with 1.1.5 or earlier, re-generate them on 1.2.0 and review
Section B, C, D and E before submitting.**

**Two things will look different on a re-generated draft even though nothing about
your pipeline changed:**

- **Your Opportunity Zone column may change from "No" to "—".** nmtc-mapper 0.5.0
  made `is_opportunity_zone` `True`-or-`None`: the OZ designation list is
  2010-tract-based while the eligibility table and geocoder are 2020-basis, so a
  non-match and a genuine non-designation are the same observation and cannot be
  told apart. The old "No" was a confident negative the data never supported. This
  happens with **no action on your part** — the dependency floor `>=0.4.2` resolves
  to 0.5.0 on a fresh install. A project you declared as an OZ in your own upload
  keeps its "Yes"; only tool-determined values move. Eligible-tract counts and
  distress verdicts are unchanged between 0.4.3 and 0.5.0 — verified across all
  85,395 rows of the eligibility table.
- **Section A no longer carries a "Historical Distress Rank" row, and the executive
  summary no longer places you in a "tier" of past applicants.** See below.

### Corrected attribution — a cited publication that does not exist

Through 1.1.5 and until late in 1.2.0, every generated application's methodology
note carried:

> IMPACT BENCHMARKS: CDFI Fund Annual Reports, FY2018–FY2023. Average jobs per
> $1MM QEI: 12.0 FTE. Top quartile: ≥20.0 FTE per $1MM.

**There is no such publication, and no such figure.** A primary-source pass
established four independent grounds, any one of them fatal:

1. **The cited series does not exist.** The NMTC "annual report" is OMB
   collection 1559-0027 — the Awardee/Allocatee Annual Report (Institution
   Level Report + Transaction Level Report) that allocatees *file to* the CDFI
   Fund through CIIS. Its OMB supporting statement states that the confidential
   and proprietary information it collects will not be published. The Fund's
   actual NMTC publication series is the *NMTC Public Data Release … Summary
   Report*, which is cumulative FY2003–FY2023 — not a set of annual reports,
   and not an FY2018–FY2023 span.
2. **No jobs-per-dollar figure is published, in any denominator.** The Fund
   reports job counts and dollar counts separately and never divides them.
3. **No distribution is published**, so labelling 20.0 a "top quartile"
   asserted a population percentile nothing supports — the same
   threshold-is-not-a-percentile error that removed three comparative labels
   elsewhere in this release.
4. **The span is impossible even in principle.** Actual job figures stop at
   FY2020 activity; FY2021–FY2023 in the current data release are projections.

The three rendered methodology notes (Markdown, Word, PDF) now state that
5 / 12 / 20 FTE per $1MM QEI are **this tool's own screening bands**, that the
CDFI Fund publishes no jobs-per-QEI benchmark, and that they are not a federal
figure and must not be cited as one — the same treatment given the ≥75%
deep-distress band, so the two read as one policy. Two further assertions of a
"CDFI Fund average" (in the readiness score's strengths and recommendations)
are relabelled the same way, and "top quartile" is gone as a label for the 20.0
band.

**The numbers were not re-cited.** Two derivations land near 12.0 and both are
traps: the plausible ones count transient construction FTEs, which is not what
a reader of "12 FTE per $1MM" assumes, and the one published per-dollar figure
in the record converts to roughly half of 12.0 with 12.0 sitting on its
best-case endpoint. All are derived, not published. Substituting one would
relocate the error rather than fix it. `jobs_per_million_qei_low/avg/high`
survive unchanged as house bands — `validation/readiness_score._impact_score`
is their only reader, and that score already declares itself an unsourced house
heuristic on the face of every methodology note.

`data/schema.py`'s module header also claimed "Historical NMTC allocation award
analysis FY2018–FY2023" as a source. Same phantom span; removed.

**How this was found, because the mechanism matters more than the instance.**
The attribution gate added earlier in this release did not catch it — it
*recorded* it. Six allowlist entries were marked `PROVENANCE UNVERIFIED` and
queued rather than approved, which is what turned an invisible fabricated
citation into a question one research pass could settle. That is the gate
working as designed. Those six entries are now gone rather than downgraded: the
claims were withdrawn, so the clauses no longer render. Three surviving entries
carry a new `DOCUMENT RETRIEVABLE, CONTENT NOT LOCATED` marker — the weaker
sibling of the same defect, queued the same way.

### Fixed — seven unsubstantiated claims removed from generated applications

A hostile re-audit of this branch returned DO NOT SHIP. Seven claims reached a
document a CDE signs and submits, none of them supported by anything the CDE
supplied. All seven are fixed; four had been invisible to every gate.

1. **`sections/section_a_business.py` — "All N projects have completed preliminary
   underwriting review."** Unconditional, in the subsection where deployment
   capacity is scored. `grep -ril underwrit nmtcapp/` finds no underwriting field
   on `PipelineProject`, in the CSV templates, or in `upload_handler`. This is the
   claim this same release removed from Section C, recording at
   `section_c_management.py:61-70` that it told the Fund "it ran a review it does
   not run" — the remediation was applied there and not here. Now a
   `[CDE TO COMPLETE]` covering timeline and diligence status.
2. **`renderers/_disclosure.py` — the unverified-projects banner claimed
   eligibility-dependent figures "reflect verified projects only."** They do not.
   An unverified project has `distress_level = None` so it never enters the
   numerator, but `distress_analysis.py:41` sums **every** project into the
   denominator. Measured: a pipeline whose only verified project was 100% of
   verified QEI and severely distressed reported **48.3%**.
   **The sentence changed, not the arithmetic**, and deliberately: the
   full-pipeline denominator matches the basis the Fund scores on (CY 2024-2025
   Allocation Application, Question 25(a) — "at least 85% of its QLICIs (in terms
   of aggregate dollar amounts)"), and a verified-only denominator would
   **overstate**, in the direction that flatters the applicant — one verified
   deep-distress project out of twenty would file "100%". These figures are now
   described as the lower bounds they are. `markdown_builder.py` and
   `readiness_score.py` carried the same false sentence and are fixed too.
   Note the document carries two denominators on purpose: the eligibility *rate*
   uses a verified-only denominator and says so on its face.
3. **`renderers/word_builder.py`, `renderers/pdf_builder.py` — the methodology note
   printed SEVERE distress's thresholds under the DEEP label.** It read "Deep
   distress = poverty rate >30% or unemployment >1.5× national average. Severe
   distress = LIC plus additional qualifying factors", credited to "CDFI Fund NMTC
   Program guidance and the NMTC Allocation Application Review Process".
   Verified against the Fund's **own NMTC LIC Eligibility workbook** — the `.xlsb`
   this package downloads and loads — columns 14 and 15 read verbatim:

   > col 14 `Severe distress=LIC AND (Poverty>30%; MFI<=60%;Unemployment>=1.5)`
   > col 15 `Deep distress=LIC AND (Poverty>40%; MFI<=40%;Unemployment>=2.5)`

   So a CDE reading the old note was told a 32%-poverty tract is "deep distress";
   the Fund's deep bar is 40%. Both definitions had also dropped the
   median-family-income limb and the "AND LIC" term. **Both tiers are the Fund's
   own and both are kept** — they are separate columns in the Fund's data file and
   separate fields in `nmtc-mapper`, so collapsing them would desynchronise the
   package from its own dependency. The classification *data* was never wrong; only
   the printed legend was, which is its own lesson.
4. **`sections/section_a_business.py` — "guides our market selection toward
   persistent-poverty counties and high-migration rural communities."** Asserted for
   every CDE, including pipelines where no project carries either flag and pipelines
   whose tracts were never verified — while `persistent_poverty` and
   `high_migration_rural` are both per-project columns the CDE fills in. The tool
   asserted the targeting and ignored the declaration. Now renders only what was
   declared, attributed to the declaration, and a placeholder when nothing was. The
   same line also appended "…" to missions it had not truncated.
5. **`sections/section_c_management.py` — `board_meeting_frequency` defaulted to
   `"Quarterly"`.** Not a fallback string: an answer to a governance question the
   CDE was asked and did not answer, printed in a governance table in the section
   where management capacity is scored, indistinguishable from a supplied value.
   Every sibling row defaults to `"N/A"`; this one now matches.
6. **`sections/section_a_business.py` — "within 12 months of award announcement."**
   A literal. No CDE supplies a closing timeline.
7. **`sections/section_a_business.py` — "in markets where conventional capital is
   systematically absent."** An assertion about credit conditions in the CDE's
   markets, which this tool retrieves no data for — while Section B's placeholder
   tells the CDE in as many words that it "does not compute, retrieve or verify
   community-need statistics of any kind".

### Fixed — the tool invented the NAICS code it filed

**`renderers/styles.py:SECTOR_NAICS` is deleted.** The pipeline table printed a
column headed "Sector (NAICS)" whose value was `SECTOR_NAICS.get(p.sector, p.sector)`.

- **No NAICS input exists.** `PipelineProject` has no `naics` field and
  `pipeline_template.csv` has no `naics` column. No CDE ever supplied one.
- **A sector label does not determine a NAICS code.** `small_business` is a *size*
  classification; it mapped to `"722/336 – Food Services / Manufacturing"`, asserting
  every such project is a restaurant or a transportation-equipment manufacturer (336
  is Transportation Equipment Manufacturing, not manufacturing at large).
- **The parentheticals are invented.** 531 is "Real Estate", not "Real Estate (Mixed
  Use)" or "(Residential)" — and two sectors mapped to the same code, separated only
  by the invented parenthetical. 221 is "Utilities"; 624 is "Social Assistance".
- **It degraded silently.** An unrecognised sector fell through to the raw string, so
  `retail` printed under a column headed "Sector (NAICS)".

A NAICS code identifies the QALICB's industry to the Fund and follows the allocation
into CIIS/AMIS compliance reporting. The column now renders the CDE's own sector
label under **"Sector (as supplied)"**. If a NAICS code is required, it is the CDE's
to supply; this tool does not have it.

### Changed — the invariance gate compares meaning, not bytes

`tests/test_invariant_output.py` intersected **raw** rendered lines, so interpolating
any CDE value into a sentence made it invisible. It now masks interpolated values
first — CDE and project names, cities, addresses, sectors, dates, and all digits —
then intersects. **The mask vocabulary is generated from `SCENARIOS` rather than
hand-written**, so it cannot drift from the fixtures.

Two narrowings, both measured rather than assumed:

- **Matching is word-bounded.** Substring matching spliced tokens into real words:
  "QALICB" contains Alabama's `AL`, "CONFIDENTIAL" contains `ID` and `AL`, and
  `<SECTOR>` contains `OR`, so the mask re-masked its own output.
- **Bare two-letter state codes are not masked**; full state names are. `ID` is a
  whole word in the column header "Project ID". Masking them moves the count by one
  line, and that line is a state-summary table row carrying no proposition.

`_is_prose` also drops from five words to **four**: `**Board Meeting Frequency:**
Quarterly` is 38 characters and four words, which is how blocker 5 stayed invisible.
Three words was measured (223 lines) and rejected as dilution.

`tests/invariant_allowlist.txt` grows **116 → 207** entries as a direct result, with a
new `DERIVED` category for a fixed sentence frame whose every figure comes from the
CDE's own inputs. **That growth is the point** — the new entries are not new output,
they are output that was always there and never had to be justified. Two fail-closed
tests assert the mask still masks and still discriminates; each of the five
previously-missed blockers was re-planted and confirmed to turn the gate red.

### Coverage — how much of the output the gates actually adjudicate

**Stated as a number, because the honest denominator is the point.**

The invariance gate compares rendered lines across four disjoint scenarios. It used
to compare them byte-for-byte, which meant interpolating any CDE value into a
sentence hid the sentence from it. It now masks interpolated values first. Measured
on the four fixtures the gate actually runs:

| | lines |
|---|---|
| Structurally-invariant prose lines (things the tool says about every CDE) | **207** |
| Adjudicated on `tests/invariant_allowlist.txt`, each with a justification | **207** |
| Visible to the gate *before* this release's mask and threshold fixes | 126 |
| Structurally-invariant lines that were therefore **invisible** | **81** |

Four of the seven blockers below lived in those 81.

**What is still ungated, stated plainly.** Both gates key on invariance or on
attribution triggers. Neither can see a claim that *varies with the input and is
still wrong* — a threshold labelled as a percentile, a computed value described as a
comparison, a denominator that is not what the sentence says it is. Rendering eleven
diverse scenarios in all four formats yields **448 distinct prose templates**, of
which **287 (64%) are input-varying** and therefore outside both gates by
construction. That surface has not been line-by-line adjudicated.

Two of this release's blockers came out of it (the distress denominator, and the
invented NAICS code), and it is where the next one will be. Read generated output;
do not assume a green suite means the document is true.

*(A figure of "1,917 input-varying lines" circulated in earlier reviews. It does not
reproduce — it summed per-scenario counts without taking the union, inflating the
number roughly fourfold. The distinct-template counts above are the ones to use.)*

### Changed — fabrication removed

Any claim the tool cannot substantiate from the CDE's own inputs is now an explicit
`[CDE TO COMPLETE: ...]` placeholder naming the evidence required, rather than a
softened assertion. An unfinished application must look unfinished.

- **`sections/section_b_outcomes.py`** — the HMDA community-need paragraph is replaced
  by a placeholder containing no percentage, no ratio and no citation. The two
  fabricated CDFI Fund threshold rows are replaced by a single row sourced from
  `benchmark_thresholds.SEVERE_DISTRESS_MIN_PCT` and explicitly labelled CY 2024-2025
  (the CY 2026 NOAA is unpublished, so nothing is presented as a CY 2026 requirement).
- **`sections/section_c_management.py`, `section_e_prior_awards.py`** — compliance
  history now derives from the CDE-supplied `has_prior_reporting_issues` via the shared
  `sections/base._compliance_statement`. Where the CDE declared issues, the text
  contains no clean-history claim at all; where unsupplied, a placeholder. The field is
  narrower than a clean compliance record, so even a declared `False` yields only the
  narrow statement plus a placeholder for the full history. The fabricated "within 18
  months of award" deployment figure (a `# Rough heuristic` in `cdfidata_adapter`) is
  dropped. "Requires {board_members} vote" — which rendered a board headcount as an
  investment-committee approval threshold, e.g. "Requires 9 vote" — is now a placeholder.
- **`sections/section_d_capitalization.py`** — "Allocation Requested" renders
  `application.requested_allocation`; the pipeline total appears as a separate
  "Total Pipeline QEI" row. Investor-relationship and investor-count assertions become
  placeholders. `$0.83`, `2.5%`, `0.39` and `0.80` are sourced from
  `schema.NMTC_PROGRAM_CONSTRAINTS` and labelled market assumptions, not CDFI Fund
  parameters.
- **`sections/section_a_business.py`, `renderers/word_builder.py`,
  `renderers/pdf_builder.py`** — three further surfaces labelled the pipeline QEI total
  "Total QEI Requested"; all now read "Total Pipeline QEI". These were found by the new
  gate, not by reading.
- **`data/schema.py`** — `TARGET_DISTRESS_THRESHOLDS` loses its "derived from CDFI Fund
  published award data" header and is relabelled as house heuristics. The keys are
  retained because five call sites across `readiness_score.py`, `eligibility_check.py`
  and `distress_analysis.py` consume them as internal scoring bands. `max_non_lic`
  (0.10) is **deleted** — it had zero consumers and the statutory rule is the
  substantially-all test, not a 10% non-LIC ceiling.

### Fixed — `analyze` was broken at the declared dependency floor

- **`integrations/nmtc_mapper_adapter.py` no longer reads
  `EligibilityResult.is_nmtc_native_area`.** nmtc-mapper 0.5.0 removed that field,
  and `nmtc-mapper>=0.4.2` resolves directly to 0.5.0, so every geocodable project
  raised `AttributeError` and `nmtcapp analyze` failed outright on any real pipeline
  CSV. Measured across clean installs: the field is **present at 0.4.2 and 0.4.3,
  gone at 0.5.0**.

  Deleting the read is not a compatibility patch — it fixes a live defect at *every*
  version. `PipelineProject.is_native_area` is the **CDE's own declaration**, read
  from the `native_area` CSV column (column 17 of the shipped template) and the
  "Native Area (Y/N)" upload column. At 0.4.2/0.4.3 the mapper's field existed but
  was **always `False`**, so enrichment overwrote a CDE's correctly-supplied `True`
  with a fabricated negative. This is the third instance of the package discarding a
  user's own column (`urban_rural` in `intelligence/geographic_analysis.py` is
  another). The floor stays `>=0.4.2`; **no upper cap is added**.
- **Enrichment no longer erases a CDE declaration with an indeterminate value.**
  `is_high_migration_rural` and `is_opportunity_zone` are *also* CDE-supplied CSV
  columns. 0.5.0 made `is_opportunity_zone` `True`-or-`None` on **every** path (the
  designation list is 2010-tract-based while the eligibility table and geocoder are
  2020-basis, so a non-match and a genuine non-designation are indistinguishable),
  and turned the distress/non-metro booleans tri-state on its indeterminate
  branches. A straight assignment would have overwritten a CDE's correct `True` with
  `None`. The adapter now prefers the determinate value.
- **Not affected, checked:** this package never reads `poverty_rate`, `ami_ratio`,
  `unemployment_rate` or `tract_found` off a result, so 0.5.0's `None`-vs-`NaN`
  two-kinds-of-missing change on those fields is unreachable here.
  `NMTCMapper.data_source == "cdfi_fund"` and
  `check_address(address) -> EligibilityResult` are unchanged at 0.5.0, so the
  provenance check and the call site survive.

### Changed — unverified data no longer renders as a confident negative

- **`tables/impact_table.py`** — `None` rendered as "No" for Native Area, HMR and OZ,
  and as "Pending" for Distress Level. This was the third of three tables; the fix
  applied to the other two in 1.1.5 was described as general but was not. Now matches
  `distress_table._flag` and `pipeline_table._yn_flag`.
- **`tables/distress_table.py`** — the per-row "Data Source" and "ACS Vintage" columns
  stamped the CDFI Fund citation on **every** row, including rows whose eligibility was
  never determined. Unenriched rows now say so.
- **`renderers/word_builder.py`, `renderers/pdf_builder.py`** — the methodology
  appendix asserted "CDFI Fund NMTC Eligibility Table … 2016–2020 ACS 5-Year Estimates"
  unconditionally, including on runs where the download failed. Both now branch on
  eligibility status, as `markdown_builder` already did.
- **`validation/eligibility_check.py`** — the eligible-QEI percentage counted `None` as
  ineligible, reporting "Only 0% of QEI is in eligible tracts" on a pipeline where
  nothing had been verified. It now uses `is True`/`is None`, reports against a
  verified-QEI denominator with the unverified share named, and emits an explicit
  "could not be verified" warning when nothing was checked.
- **`intelligence/win_probability.py`** — `_map_tier_legacy` mapped the withheld
  sentinel "Not Rated — eligibility data unavailable" through a `"marginal"` default,
  manufacturing the rating the scorer deliberately refused to assign. The default is
  now `"not_rated"`.
- **`intelligence/recommendations.py`** — `_overall_assessment` had no partial guard
  (unlike `_build_peer_comparison`) and printed a "Not Qualified (n/100)" verdict with
  hardcoded `/50` and `/100` denominators on degraded runs where 25 of 100 base points
  were unavailable.

### Changed — CLI

- **`nmtcapp analyze`** now requires `--cde <path>` and `--requested-allocation
  <dollars>` and **refuses** (exit 2) without them. It previously substituted
  `CDEProfile.sample()` and an invented $55,000,000, silently scoring the user's real
  pipeline against a fictional CDE and producing ratios against a number nobody
  entered. 1.1.5 fixed this for the Streamlit upload path and left the CLI behind.
  `--demo` runs on the shipped fictional profile and labels every screen as a demo.

### Fixed — packaging

- **`nmtcapp init` now works from a wheel.** Templates moved from the repo root to
  `nmtcapp/templates/` and are declared as `[tool.setuptools.package-data]`.
  `pyproject.toml` previously declared no package data, and `MANIFEST.in` governs only
  the sdist, so **no wheel ever published by this project contained the templates** and
  `nmtcapp init` failed with "Cannot locate the templates directory" for every user who
  installed from PyPI — the on-ramp `README.md` advertises. `_get_templates_dir` is now
  a single `importlib.resources` lookup. Verified end to end: built wheel, installed
  into a clean venv, ran `nmtcapp init`.
- **`README.md`** — the pipeline-template link was relative and 404'd in the PyPI long
  description; it is now absolute to GitHub.

### Removed

- **`integrations/hmda_adapter.py` and `community_need_documentation`** — removed
  entirely, with the `hmda-analyzer` dependency. The adapter could not reach real HMDA
  data by any code path: the *success* branch called `hmdaanalyzer.load_sample()`
  (synthetic data), and `generate_disparity_report()` returns a `str` in every published
  version — verified against the installed 0.3.0, whose signature is annotated `-> str`
  — so the `.get()` raised `AttributeError` into a bare `except` that supplied the
  literals `0.28` and `2.1`. `_build_narrative` rendered those literals as application
  prose. Nothing in the document-generation path consumed it. Option (a), rewiring it to
  `load_from_api`, was rejected: it would rebuild the tool-generated community-need
  narrative that this release deliberately hands back to the CDE. **This removes a
  public API symbol in a patch release** — a deliberate exception, because the symbol's
  only output was fabricated.
- **`cra-scraper`** — dependency and its two documentation references removed. Zero
  imports repo-wide, in any release; declared and never used.

### Dependencies

- `nmtc-mapper>=0.3.4` → **`>=0.4.2`**. 0.3.4 was the *import* floor (first version
  exporting `NMTCMapperError`, `EligibilityDownloadError`, `data_source`). 0.4.2 is the
  *correctness* floor: 0.3.1–0.4.1 report 168 census tracts as not NMTC-eligible when
  they statutorily are, and 0.4.2's loader moves 35,167 → 35,335 eligible of the same
  85,395 tracts — a delta of exactly 168, re-verified against the installed 0.4.2.
- `requires-python = ">=3.9"` is unchanged.

All floor changes are tightenings that **do not move the resolved set on a fresh
install today**; no working environment changes as a result of this release.

### Testing

- **New gate `tests/test_no_fabricated_output.py`** — generates a complete application
  in all four formats (markdown, docx, xlsx, pdf) under two pipelines (fully enriched,
  and every eligibility field `None`), extracts the text **back out of the PDF and DOCX**
  and asserts none of the removed fabrications appear. Asserting against the rendered
  artifact rather than the source is deliberate: a gate that greps `.py` files cannot see
  a fabrication reintroduced through a different string. The denylist is parametrized, so
  `empty_parameter_set_mark = fail_at_collect` turns an emptied list into a collection
  **error** rather than a silent pass — verified by emptying it. Each removed fabrication
  was reintroduced one at a time and the gate confirmed red in all four formats on both
  pipelines before being reverted.
- **New contract gate `tests/integrations/test_mapper_contract.py`** — introspects the
  **installed** nmtc-mapper and asserts every attribute the adapter reads off an
  `EligibilityResult` or an `NMTCMapper` actually exists. The attribute list is
  derived from the adapter source by AST walk, never hand-copied, and an empty
  derivation is a collection **error**.

  This gate exists because the whole suite stayed green while `analyze` was broken:
  the test doubles in `test_no_fabrication.py` and `test_partial_unverified_exports.py`
  constructed `is_nmtc_native_area=False` themselves, so **the tests validated the
  mock, not the library**, and `test_no_fabricated_output.py` renders from
  pre-enriched pipelines and never touches a real `EligibilityResult`. Those three
  doubles no longer construct the dropped field. Proven in the failing direction:
  reading a removed field, reading a bogus mapper attribute, an emptied derivation,
  and re-assigning `project.is_native_area` each turn it red.
- `tests/integrations/test_no_fabrication.py` extended to assert the HMDA adapter stays
  removed and that neither `hmda-analyzer` nor `cra-scraper` is re-declared.
- Suite: **709 → 897 collected, 896 run under `-m "not wheel"`, all passing.**
  `release.yml`'s `FLOOR` is **440**, re-derived from the count the CI step actually
  measures: the sdist job runs 896 and skips 4 (the committed-artifacts gate, which
  needs a git checkout), so 892 execute; half is 446, rounded down to 440.
  *An earlier draft of this entry said "709 → 861" and "FLOOR 350 → 430". Both were
  wrong — the suite was 894 and the floor was already 440. A release note that
  misstates the artifact it ships with is the same defect class one level up, which
  is why it is corrected here rather than quietly overwritten.*

---

## [1.1.5] — 2026-07-11

Data-integrity release: the eligibility adapter no longer fabricates application content.

### Disclosure

The adapter previously substituted a hardcoded 20-tract table when live eligibility
data failed to load, and assigned a fabricated deep-distress tract (17031838200) to
projects whose geocoding failed. Both paths produced fabricated application content —
eligibility, distress levels, and census tracts that did not come from the CDFI Fund
dataset could appear in analyses, scores, and generated application documents without
any indication that they were not real. If you generated drafts with 1.1.4 or earlier
while offline or while the CDFI Fund download was failing, re-run them on 1.1.5.

### Changed
- **`nmtcapp/integrations/nmtc_mapper_adapter.py`** — full rewrite of the failure
  semantics. The hardcoded fallback table is deleted. The adapter now catches only
  typed `nmtcmapper.NMTCMapperError` failures and enters an explicit degraded mode:
  `pipeline.eligibility_data_status = "unavailable"` with the underlying error
  retained for display, and all eligibility fields left `None` (unverified).
  Unexpected exceptions propagate. The `redirect_stdout` suppression around mapper
  construction is removed (0.3.4's progress output is informative; its failures raise).
- **Provenance check** — even on the happy path, a mapper whose `data_source` is not
  `"cdfi_fund"` (e.g. `NMTCMapper.from_sample()`) is refused: sample data can never
  flow into a real application.
- **Geocode failures are per-project honest** — a project whose location cannot be
  verified gets `geocode_success=False`, no census tract, eligibility fields `None`,
  and an explicit "location could not be verified" marker. It is treated as
  UNVERIFIED, never as ineligible and never given a substitute tract.
- **Degraded scoring is explicit and partial** — when eligibility data is unavailable:
  readiness scores exclude `eligibility_quality` and `distress_concentration` and are
  labeled "score computed without eligibility verification (4 of 6 components)";
  composite alignment scores exclude the distress component (4 of 5 components); the
  CDFI Fund framework score excludes Higher Distress Targeting and Deep Distress
  Commitment (25 of 100 base points) and assigns no tier.
- **Degradation disclosure — exactly these surfaces** (both full-unavailable AND
  partial-unverified, where individual projects failed location verification):
  all four export formats (Word, PDF, Excel, Markdown) render a banner naming the
  unverified project IDs, with inline per-metric qualifiers ("67% (2 of 6
  unverified)" in the same cell/line as the figure); the pipeline analyzer summary;
  the `ReadinessScore` object (`partial=True` with a distinct unverified note —
  including when ALL projects are unverified while the dataset loaded fine); and the
  Streamlit pages (analyzer banner, scorer/optimizer partial tags, partial-labeled
  radar). Section A/B narratives render degraded phrasing instead of asserting
  unverified "N% of QEI" figures as fact, and the Markdown methodology note never
  cites a data source that did not load. A never-enriched pipeline defaults to
  `eligibility_data_status="unenriched"` (fail-closed), not "ok".
- **Optimizer before/after on one component basis** — the with/without-eligibility
  basis is computed once from the full input set and shared by every scoring call
  (before, greedy ranking, local search, after). Previously a mixed pipeline scored
  "before" without the distress component but an all-verified "after" subset with
  it, so the reported improvement was measured across two different scales.
- **`dimensional_scores` on fixed structural maxima** — section scores normalize
  against 50/50/10 regardless of a degraded `max_available`, so a degraded Community
  Outcomes 20/25 reads 40.0 (points earned of the structural section), not 80.0.
- **Uploads previously scored against sample CDE attributes while claiming
  zero-defaults** — uploaded pipelines scored against `CDEProfile.sample()`
  attributes (3 prior awards, 76% track-record alignment, third-party validation, …)
  while the analyzer page told upload users that missing CDE fields were "defaulted
  to 0/False". Uploads now get a neutral profile (no prior awards, empty scoring
  attributes), making that disclosure literally true; the sample profile is demo-only.
- **Tables never fabricate or downgrade** — the distress table's poverty-rate column
  is "See ACS" unconditionally (no more ">30%"/">20%" figures inferred from the
  distress label under a CDFI Fund data-source citation); unverified tri-state flags
  (native area, HMR, opportunity zone, severely-distressed) render "—"/"Unverified",
  never "No"/"N".
- Dependency floor raised: `nmtc-mapper>=0.3.4` (fails loud on data-load failure
  instead of serving sample data).

### Known Issues
- Upstream nmtc-mapper 0.3.5 known issue: the geocoder swallows transport errors and
  surfaces geocode failure as an "ineligible"-shaped result with
  `geocode_success=False`. Mitigated on the flagship side: the adapter checks
  `geocode_success` and treats those projects as unverified, not ineligible.
- Deferred to a later release: the distress breakdown's non-LIC bucket absorbs unverified
  projects (unverified counts in denominators; distinct unverified bucket pending);
  sample-data provenance and shared sample instances (`Pipeline.sample()` /
  `CDEProfile.sample()` return pre-verified fixtures marked "ok" and share module
  state; n=25 sampling); Streamlit AppTest coverage for the page-level banners and
  partial tags.

---

## [1.1.4] — 2026-06-22

Release-infrastructure release. No functional or behavioral changes to the application.

### Added
- CI workflow (`.github/workflows/ci.yml`): runs the test suite on push/PR across Python 3.9–3.12.
- Release workflow (`.github/workflows/release.yml`): tag-triggered, builds wheel + sdist,
  tests the built wheel in a clean venv across 3.9–3.12, and publishes to PyPI via OIDC
  Trusted Publisher (PEP 740 attestations). All actions SHA-pinned; a tomllib guard fails
  the release if the git tag and pyproject version disagree.

### Changed
- `scripts/release.sh` no longer uploads to PyPI; publishing is CI-only. It now runs a
  local pre-flight (tests + build) only.

### Notes
- 1.1.4 is the first release published via CI from a tagged commit. Earlier releases 1.1.0
  and 1.1.3 were published pre-CI from a local working tree and have no corresponding git
  tag; that historical gap is accepted and not reconstructed. Tagging discipline starts here.

---

## [1.1.3] — 2026-05-14

Bug-fix release: xlsx upload, CSV encoding fallback, and column name alignment for the
Pipeline Analyzer. The v1.1 template download-and-upload round trip now works end-to-end.

### Fixed

**Critical — xlsx upload broken (Bug 1)**
- **`streamlit_app/pages/1_Pipeline_Analyzer.py` / `nmtcapp/core/upload_handler.py`** —
  Uploading the v1.1 `.xlsx` template failed with `"Pipeline CSV missing required columns"`
  because `pd.read_excel(..., sheet_name="Pipeline")` defaulted to `header=0`, reading
  the title row ("Pipeline — NMTC Application Builder v1.1 | One row per project") as
  the sole column header and leaving all 28 real columns unnamed.
  Fixed by reading the Pipeline sheet via openpyxl directly (same pattern as CDE Profile
  sheet), detecting the v1.1 3-row preamble (title / section banners / column headers)
  by checking cell A1, and using row 3 as the header row.

**Critical — column name drift between template and parser (Bug 3)**
- The upload handler contained a dead alias mapping that expected column names
  (`qei_millions`, `total_project_cost_millions`, `jobs_created`) that exist in neither
  the xlsx template ("QEI ($M)", "Total Cost ($M)", "Jobs Created") nor the CSV files
  (`qei_request`, `total_project_cost`, `expected_jobs_created`). This meant that even
  after fixing Bug 1, a template upload would still fail column-name validation.
  Fixed by adding `_XLSX_PIPELINE_COL_MAP` — a complete display-name → snake_case mapping
  for all 28 Pipeline sheet columns — and multiplying the `QEI ($M)` / `Total Cost ($M)`
  columns by 1,000,000 to convert from the template's human-readable millions to the
  parser's raw-dollar convention.

**High — CSV encoding failure on Windows-1252 files (Bug 2)**
- `pd.read_csv()` defaulted to UTF-8, causing `"'utf-8' codec can't decode byte 0xd2"`
  when users uploaded a CSV exported from Excel on Windows (default cp1252/Windows-1252
  encoding). Fixed with a `utf-8 → utf-8-sig → cp1252 → latin-1` fallback chain; a
  `logging.WARNING` is emitted when a non-UTF-8 encoding is used.

### Changed

- **`nmtcapp/core/upload_handler.py`** (new module) — `load_uploaded_pipeline()` and all
  its helpers (`_read_pipeline_sheet_from_wb`, `_read_csv_with_encoding_fallback`,
  `_parse_cde_profile_from_wb`, `_XLSX_PIPELINE_COL_MAP`) extracted from the Streamlit
  page into this importable module so they can be unit-tested without a Streamlit runtime.

- **Sidebar help text** — updated to reflect that the `.xlsx` template can be uploaded
  directly (no "save as CSV" step), and that CSV files must use the snake_case column
  names from `pipeline_template.csv` with raw dollar values (not millions). UTF-8 and
  Windows-1252 encodings are both noted as accepted.

- **Download button tooltip** — updated from "Edit, save as CSV, then upload" to
  "Fill in your projects, save, and upload the .xlsx directly."

### Added

**Tests**
- `tests/test_template_roundtrip.py` — 3 tests verifying the primary user journey:
  (1) loading the v1.1 template, adding 3 data rows, saving as xlsx bytes, passing to
  `load_uploaded_pipeline`, and asserting a `Pipeline` with 3 projects;
  (2) correct QEI / cost / jobs values after $M → raw-dollar conversion;
  (3) CDE Profile sheet parses to a non-empty dict without error.
- `tests/test_csv_encoding.py` — 5 tests verifying that cp1252-encoded CSVs (smart
  quotes, accented characters, byte 0xd2, trademark symbols) parse correctly, and that
  UTF-8 and UTF-8-with-BOM files still work.

---

## [1.1.2] — 2026-05-13

Documentation and visualization correctness release: all user-visible references to the old 5-dimension model replaced with the current CDFI Fund CY 2024-2025 framework.

### Fixed

**Critical — broken visualizations (C1, H7)**
- **`plot_readiness_radar`** (`nmtcapp/visualization/maps.py`) — `_DIM_MAP` updated from five old objective keys (`distress_concentration`, `geographic_diversity`, `impact_intensity`, `sector_diversity`, `pipeline_quality`) to the three current CDFI Fund section keys (`business_strategy`, `community_outcomes`, `priority_points`). All axis values were previously 0.0; now render correctly. Benchmark reference lines updated to HQ section minimums (BS/CO: 80/100, PP: 70/100). Title updated to "CDFI Fund Section Score Radar". Tier colors updated to `Top Tier / Highly Qualified / Not Qualified`.
- **Streamlit Pipeline Optimizer before/after chart** (`streamlit_app/pages/3_Pipeline_Optimizer.py`) — Replaced broken grouped bar chart (which looked up old objective keys in the new CDFI Fund `dimensional_scores` dict, producing all-zero bars) with: (a) a 3-metric display of CDFI Fund section scores before optimization when `win_score` is in session state, and (b) the optimizer dimension delta chart that was already working correctly as the fallback.

**Critical — stale documentation (C2, C3)**
- **`docs/workflow/win-alignment.md`** — Full rewrite. Previous 174-line document described the old 5-dimension model (Distress 35%, Impact 25%, Geographic 20%, Sector 15%, Pipeline 5%) with stale code examples. New document is a workflow companion to `docs/reference/methodology.md`, covering: basic usage, reading `WinProbabilityScore` output fields, tier classification logic with code examples, CDE attribute supply (YAML vs. inline dict), graceful degradation table, sub-score drill-down pattern, and Phase 2 flags.
- **`docs/index.md`** — Three targeted edits: "five analyses… distress concentration, geographic diversity…" → CDFI Fund CY 2024-2025 three-section framework; Win Alignment Scoring card updated to "Not Qualified / Highly Qualified / Top Tier"; methodology disclosure updated to reference published criteria rather than "historical winner patterns".

**High — stale content and broken notebook (H1–H8)**
- **`CITATION.cff`** — `version` updated `1.0.0` → `1.1.2`; `date-released` updated `2025-05-09` → `2026-05-13`; abstract rewritten to describe CY 2024-2025 scoring framework.
- **`docs/installation.md`** — Version comment `# "1.0.0"` → `# prints the installed version` (version-agnostic; no update needed on each release).
- **`README.md` quickstart comment** — `66/100 [competitive]` → `90/100 [Highly Qualified]` (actual output from `CDEProfile.sample()`). Also updated `score.competitive_tier` to `score.tier` in the print statement.
- **`README.md` "The Solution" paragraph** — Replaced "every dimension the CDFI Fund scores: distress concentration, geographic diversity…" with CDFI Fund CY 2024-2025 three-section framing.
- **`README.md` "What It Does" bullet** — Replaced "5-dimensional score (0–100) against CY2020–2024 winner patterns" with current CDFI Fund section framework.
- **`README.md` notebook table** — Updated notebook 03 description from `5.5 → 65.9 → 79.1/100 — weak→competitive` (old model scores) to `16 → 90 → 96/100 — Not Qualified → Highly Qualified → Top Tier` (actual executed output).
- **`examples/03_intelligence_and_optimization.ipynb`** — Fixed code bug in 7 cells: `result_weak.pipeline_result` and `result_improved.pipeline_result` (attribute does not exist on `PipelineAnalysisResult`) → `result_weak` and `result_improved` directly. Executed all 27 cells; 16/17 code cells have saved outputs (import cell has none, as expected). Arc confirmed: Not Qualified (16/100) → Highly Qualified (90/100) → Top Tier (96/100).
- **`templates/cde_profile_sample.yaml`** — Calibration comments corrected: Community Outcomes `45/50` → `47/50`, Priority Points `7/10` → `9/10`, Aggregate `~88/100` → `~90/100`.

### Added

**Tests**
- `tests/test_radar_chart_keys.py` — 4 tests asserting: (1) `dimensional_scores` has exactly the 3 CDFI Fund section keys, (2) old 5-dimension keys are absent, (3) radar chart axis values are non-zero for the sample pipeline, (4) `plot_readiness_radar` source does not reference old dimension keys. This is the structural test that would have caught the C1/H7 regression.
- `tests/test_sample_score.py` — 2 smoke tests asserting `CDEProfile.sample()` composite score is within ±2 of 90 and tier is Highly Qualified or Top Tier. Catches future scoring drift without a README update.
- `tests/test_sample_yaml_score.py` — 5 smoke tests asserting `cde_profile_sample.yaml` section scores (BS: 43/50, CO: 47/50, PP: 9/10, aggregate: 90/100) are within ±2 of documented values. Catches drift between YAML calibration comments and the scoring model.

---

## [1.1.1] — 2026-05-13

Patch release: fix `__version__` mismatch and add packaging guard tests.

### Fixed

- **`__version__` mismatch** — `nmtcapp.__version__` now reads from package metadata via `importlib.metadata` instead of a hardcoded string, eliminating the `1.0.0` / `1.1.0` drift introduced in the 1.1.0 release.
- **Version sync test** — `tests/test_version.py::test_version_sync` asserts `nmtcapp.__version__ == importlib.metadata.version("nmtc-application-builder")`; fails immediately if the two diverge again.
- **Wheel completeness test** — `tests/test_wheel_completeness.py::test_wheel_completeness` builds the wheel from source, installs it in an isolated venv, and imports every public submodule; run with `pytest -m wheel`.

---

## [1.1.0] — 2026-05-12

Methodology realignment: scoring framework replaced with CDFI Fund's published CY 2024-2025 Review Process criteria.

### Changed

**Scoring framework — `nmtcapp/intelligence/win_probability.py`**
- Replaced 5-dimension winner-pattern alignment model (Distress 25%, Geographic 20%, Sector 15%, Impact 25%, Pipeline 15%) with the CDFI Fund's published two-section framework
- `WinProbabilityScore` now reports: Business Strategy (0–50 pts), Community Outcomes (0–50 pts), Priority Points (0–10 pts), aggregate base score (0–100), aggregate with priority (0–110), tier classification, and gating notes
- Tier classification: **Not Qualified** (< 85 aggregate or either section < 40) → **Highly Qualified** (85–94, both sections ≥ 40) → **Top Tier** (≥ 95, both sections ≥ 45)
- `WinProbabilityModel.score()` accepts an optional `cde_attributes` dict for CDE-level inputs (product flexibility, track record, board composition) that are not derivable from pipeline data alone
- Old `composite_score`, `dimensional_scores`, `competitive_tier` fields retained for backward compatibility

**Recommendations — `nmtcapp/intelligence/recommendations.py`**
- `Recommendation` dataclass gains a `citation` field — each recommendation now cites the specific CDFI Fund Review Process section it addresses
- Valid categories updated: `business_strategy`, `community_outcomes`, `priority_points`, `pipeline`
- Engine dispatches to section-specific recommendation generators when a `WinProbabilityScore` is available; falls back to pipeline-level analysis otherwise

**CDE profile — `nmtcapp/core/cde.py`**
- `CDEProfile` gains an `extra: Dict` field; `from_yaml()` captures unknown YAML keys into `extra` so new scoring attributes can be added without changing the schema
- `CDEProfile.sample()` updated for Riverbend Community Capital to include CDFI Fund scoring attributes (products, track record, governance) targeting the Highly Qualified tier (~87–88/100)
- `Application.score_win_probability()` passes `cde.extra` as `cde_attributes` automatically

**Thresholds — `nmtcapp/data/benchmark_thresholds.py`**
- Added CDFI Fund CY 2024-2025 published thresholds: `HIGHLY_QUALIFIED_AGGREGATE_MIN=85`, `HIGHLY_QUALIFIED_SECTION_MIN=40`, `TOP_TIER_AGGREGATE_MIN=95`, `TOP_TIER_SECTION_MIN=45`, `SEVERE_DISTRESS_MIN_PCT=0.85`, `DEEP_DISTRESS_MIN_PCT=0.20`, `DBC_PRIORITY_YEARS_MIN=5`, `DBC_VOLUME_PCT_MIN=0.70`, `UNRELATED_ENTITIES_MIN_PCT=0.90`
- Legacy winner-pattern thresholds retained for `HistoricalBenchmarks` backward compatibility

**Streamlit demo — `streamlit_app/pages/2_Win_Alignment_Scorer.py`**
- Replaced 5-dimension radar chart with stacked horizontal bar showing all 9 CDFI Fund sub-criteria (4 Business Strategy + 5 Community Outcomes)
- Added aggregate gauge with tier zone color coding (Not Qualified / Highly Qualified / Top Tier)
- Added section minimum status badges and tier badge
- Recommendations panel now displays CDFI Fund citation per recommendation

**Methodology documentation**
- `docs/reference/methodology.md` — fully rewritten: sub-score formulas, gating thresholds, Phase 2 considerations, and "what is not modeled" disclosure
- `streamlit_app/pages/4_About_and_Methodology.py` — updated to reflect the new framework
- `templates/cde_profile_sample.yaml` — updated for Riverbend Community Capital with new scoring fields

**Demo notebook — `examples/03_intelligence_and_optimization.ipynb`**
- Rewritten to walk through Not Qualified → Highly Qualified → Top Tier arc
- Each stage shows CDFI Fund section scores, gating notes, and the specific attribute changes required to advance tiers

### Added

- `distress_breakdown` dict now includes both `pct_deep_or_severe` (combined) and `pct_deep` (deep-only) keys, supporting separate Deep Distress Commitment scoring

**`Pipeline.from_csv()` crash-safety hardening**
- Blank required numeric fields (`total_project_cost`, `qei_request`, `qlici_amount`, `expected_jobs_created`) now raise a friendly `ValueError("'field_name' is required but was left blank")` instead of a raw `cannot convert float NaN to integer` traceback
- Blank required string fields (`project_id`, `state`, etc.) now raise a friendly error instead of silently producing `"nan"` string values
- `expected_jobs_retained` left blank now defaults to 0 instead of crashing
- Comment rows (lines where `project_id` starts with `#`) are silently skipped — uploading `pipeline_template.csv` (which contains inline documentation comments) no longer triggers a confusing parse error
- Empty files / header-only files now raise: `"No project rows found. The file contains only column headers or comments. Please add your project data rows before uploading."`
- Added `_required_str()`, `_required_float()`, `_required_int()`, `_int_with_default()` private helpers

**Tests — `tests/test_csv_robustness.py`** (19 new tests)
- `TestBlankRequiredNumericFields` (6): blank jobs_created, total_cost, qei, qlici, jobs_retained defaults, missing jobs_retained column
- `TestBlankRequiredStringFields` (4): blank project_id, blank state, error includes row ID, bad row in multi-row file
- `TestCommentRowsAndEmptyTemplates` (5): single comment skipped, multiple comments skipped, comment-only → no-data error, empty header-only → no-data error, actual `pipeline_template.csv` file triggers no-data error (not a raw crash)
- `TestValidCsvStillParses` (4): good row, strong sample, weak sample, v1.0 CSV without flag columns
- Sub-score formulas documented in `docs/reference/methodology.md` with explicit disclosure that within-section point weights are this tool's interpretation (the CDFI Fund does not publish exact sub-criterion point values)

**Template v1.1 — `templates/pipeline_template.xlsx`**
- Rebuilt as a 4-sheet Excel workbook: **CDE Profile**, **Pipeline**, **Instructions**, **Valid Values**
- **CDE Profile sheet** (Sheet 1): 30 columns covering CDE identity + all CDE-level scoring inputs (Business Strategy, Community Outcomes, Priority Points, Phase 2 flags). One data row per CDE; Y/N, state, org-type, and application-round dropdowns.
- **Pipeline sheet** (Sheet 2): 28 columns — all prior fields retained plus 7 new fields:
  - `qalicb_name` — QALICB legal entity name (was synthesised automatically, now explicit)
  - `closing_target_date` — target closing date (was in CSV template but missing from xlsx)
  - `native_area` (Y/N) → `pct_native_area` → Community Outcomes Special Targeting sub-score
  - `high_migration_rural` (Y/N) → `pct_high_migration_rural` → Special Targeting
  - `us_territory` (Y/N) → `pct_us_territories` → Special Targeting
  - `persistent_poverty` (Y/N) → `pct_persistent_poverty` → Special Targeting
  - `below_market_rate` (Y/N) → `products_below_market_pct` → BS Product Flexibility sub-score
  - `unrelated_entity` (Y/N) → `unrelated_entities_pct` → Priority Points Unrelated Entities
  - `opportunity_zone` (Y/N) — informational
- **Instructions sheet** (Sheet 3): field-by-field documentation, scoring framework summary, graceful-degradation table, methodology disclosure
- **Valid Values sheet** (Sheet 4): dropdown source lists for all validated fields
- Brand styling: navy `#1B438C` section banners, section color coding per category, frozen header rows, sample data rows

**`PipelineProject` v1.1 — `nmtcapp/core/pipeline.py`**
- 4 new optional boolean fields: `is_us_territory`, `is_persistent_poverty`, `is_below_market_rate`, `is_unrelated_entity`
- `from_csv()` reads the new flag columns (`us_territory`, `persistent_poverty`, `below_market_rate`, `unrelated_entity`, `opportunity_zone`, `native_area`, `high_migration_rural`) with Y/N/yes/no/true/false/1/0 parsing via `_optional_bool()`
- `to_dict()` includes all new flags

**`analyze_distress_concentration()` v1.1 — `nmtcapp/intelligence/distress_analysis.py`**
- Returns 4 new QEI-weighted percentage keys computed from per-project flags: `pct_us_territories`, `pct_persistent_poverty`, `pct_below_market_rate`, `pct_unrelated_entity`

**`WinProbabilityModel` v1.1 — `nmtcapp/intelligence/win_probability.py`**
- `_score_product_flexibility()`: falls back to pipeline-derived `pct_below_market_rate` when `products_below_market_pct` is absent from `cde_attributes`
- `_score_special_targeting()`: reads `pct_persistent_poverty` and `pct_us_territories` from pipeline distress breakdown as fallback when not in `cde_attributes`
- `_score_unrelated_entities()`: falls back to pipeline-derived `pct_unrelated_entity` when `unrelated_entities_pct` is absent from `cde_attributes`

**Streamlit Pipeline Analyzer v1.1 — `streamlit_app/pages/1_Pipeline_Analyzer.py`**
- Accepts v1.1 xlsx template: reads CDE Profile sheet with openpyxl (version-agnostic) and passes all 19 scoring attrs to the Win Alignment Scorer via `CDEProfile.extra`
- Computes pipeline-derived CDE-level pcts from per-project flags during file parsing and merges into `cde_attributes`
- Graceful degradation: when CDE Profile fields are absent, displays "not provided — sub-score defaulted to X" info panel before running analysis
- `get_or_create_app()` gains optional `cde_extra` parameter for injecting user-supplied CDE attributes

**Tests — `tests/test_template_fields.py`**
- `test_template_has_all_methodology_fields`: 11 assertions verifying the xlsx has all 4 sheets with the correct columns, sample data, and scoring flags
- `test_scoring_engine_inputs_match_template`: 5 assertions verifying the canonical scoring-engine attr key set matches the template, WinProbabilityModel reads all keys, distress analysis surfaces all pipeline-derived keys, and pipeline fallbacks work correctly for `below_market_rate` and `unrelated_entity`
- 16 new tests for template field alignment; total suite: 637 passing (up from 602)

---

## [1.0.0] — 2025-05-09

Initial public release. Four weeks of development, 544 tests passing.

### Added

**Week 1 — Core Foundation**
- `Pipeline` and `PipelineProject` classes with CSV ingestion and 20-project sample data
- `CDEProfile` class with YAML loading and sample data
- `Application` orchestration class — single entry point for all functionality
- Eligibility validation, completeness check, and consistency check
- Readiness scoring (0–100, grades A–D) across 5 weighted dimensions
- NMTC eligibility enrichment via `nmtc-mapper` with offline fallback
- Deal economics computation via `nmtc-calc` with manual fallback
- `PipelineAnalyzer` — distress, geographic, sector, and impact sub-analyses

**Week 2 — Output Renderers**
- `WordApplicationBuilder` — full NMTC application draft in `.docx`
- `ExcelApplicationBuilder` — multi-sheet workbook with dashboard, pipeline, and impact tables
- `PDFApplicationBuilder` — formatted PDF via ReportLab
- `MarkdownApplicationBuilder` — clean Markdown output for version control workflows
- Shared `styles.py` color palette and typography constants used across all renderers
- `Application.generate()` — produces all four formats in one call

**Week 3 — Intelligence Layer**
- `WinProbabilityModel` — 5-dimensional alignment scoring against CY2020–2024 winner patterns
- `HistoricalBenchmarks` — 9-metric tier comparison with methodology disclosure
- `RecommendationEngine` — quantified, prioritized improvement actions per dimension
- `PipelineOptimizer` — greedy construction + swap-based local search, no LP/MIP solver
- `OptimizationConstraints` — QEI budget, state diversity, sector, and eligibility constraints
- `analyze_winning_patterns()` and `compare_to_winners()` for pattern analysis
- Three executed example notebooks demonstrating full workflow

**Week 4 — Polish + Distribution**
- `nmtcapp.visualization` module — 5 publication-quality chart functions (300 DPI PNG)
  - `plot_pipeline_map` — project distribution on continental US map
  - `plot_distress_heatmap` — QEI by state with distress-level color coding
  - `plot_sector_distribution` — sector mix vs. winner patterns
  - `plot_readiness_radar` — 5-dimensional radar vs. competitive benchmark
  - `plot_winner_alignment` — pipeline metrics vs. winner p25/p50/p75
- `nmtcapp.cli` — `nmtcapp init`, `nmtcapp analyze`, `nmtcapp version` commands
- `templates/` — `pipeline_template.csv`, `pipeline_sample_strong.csv`,
  `pipeline_sample_weak.csv`, `cde_profile_template.yaml`, `cde_profile_sample.yaml`
- MkDocs documentation site with 13 pages deployed to GitHub Pages
- Streamlit interactive demo app (4 pages: Analyzer, Scorer, Optimizer, Methodology)
- Polished README with badges, architecture diagram, and honest limitations
- `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `CITATION.cff`
- GitHub issue and PR templates
- Version bumped to 1.0.0; PyPI classifiers updated to Production/Stable

### Fixed

- `objectives.py` — distress scoring used wrong level strings (`"deep_distressed"` →
  `"deep"`, `"severely_distressed"` → `"severe"`), causing distress score to always be 0
- `sector_analysis.py` — `max_single_sector_pct` was missing from output dict, causing
  `win_probability._score_sector` to always apply a maximum concentration penalty (score = 0)
- `nmtc_mapper_adapter.py` — suppressed nmtcmapper's raw `print()` 404 messages using
  `contextlib.redirect_stdout`
- `pipeline_optimizer.py` — added no-regression guarantee: reverts to full pipeline if
  optimized subset scores lower than input
- `test_optimizer.py` — `test_eligible_only_filters` was mutating shared `_SAMPLE_PROJECTS`
  objects, causing cross-test `is_nmtc_eligible` contamination

---

## [0.2.0] — 2025-04-30

Weeks 1–3 development release (internal).

- Intelligence layer: `WinProbabilityModel`, `RecommendationEngine`, `PipelineOptimizer`
- Output renderers: Word, Excel, PDF, Markdown
- Core pipeline analysis and validation

## [0.1.0] — 2025-04-15

Initial development release (internal).

- Core `Application`, `Pipeline`, `CDEProfile` classes
- Basic validation and readiness scoring

---

[1.1.3]: https://github.com/Jaypatel1511/nmtc-application-builder/releases/tag/v1.1.3
[1.0.0]: https://github.com/Jaypatel1511/nmtc-application-builder/releases/tag/v1.0.0
[0.2.0]: https://github.com/Jaypatel1511/nmtc-application-builder/releases/tag/v0.2.0
[0.1.0]: https://github.com/Jaypatel1511/nmtc-application-builder/releases/tag/v0.1.0
