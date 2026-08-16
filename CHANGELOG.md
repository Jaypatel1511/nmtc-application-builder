# Changelog

All notable changes to `nmtc-application-builder` are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [1.2.1] — 2026-08-15

Patch release. The financial tables, the shipped inputs, and a gate that could
not fail. No public API changes.

1.2.0's final audit returned **ship, not clean** — every remaining defect was
also present in 1.1.5 and not worsened by 1.2.0. This release is those defects,
plus six more found by running the published wheel from a clean venv after the
tag landed, plus what recomputing every derived figure in Appendix A and
Section D from the CDE's own inputs turned up.

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
colour". The rendered-string sweep demands **19**, and 157 constants are swept
where 49 were.

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
