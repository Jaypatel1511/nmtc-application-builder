"""Question 25 as the ALLOCATION APPLICATION states it, in one place.

THE DEFECT THIS REPLACES (1.3.0 S1)

Through 1.2.2 the rendered basis note was written against the *CY 2024-2025
NMTC Program Review Process* — a seven-page **summary** of how the CDFI Fund
scores an application. The Review Process describes Question 25 in one
sentence per commitment:

    "at least 85% of its QLICIs in specified areas of severe distress and/or
     areas characterized by multiple indicia of distress"
    "at least 20% of its QLICIs to 'Deep Distress' areas"

Both sentences are real, and both were quoted correctly. They are also a
summary, and the summary loses two things the **instrument** — the Allocation
Application itself, Question 25 at printed pp. 38-41 — states plainly:

  1. THE 20% IS THE TOP RUNG OF A LADDER, NOT A BAR. Question 25(b)(i) is a
     dropdown of 0 / 5 / 10 / 15 / 20, and selecting 20 opens a second field
     for any figure from 20% to 100%. A CDE that can honestly commit 10%
     selects 10 and has failed nothing. The shipped note told that CDE to
     compute a share and compare it to 20%, which reads as a pass/fail
     threshold they miss.

  2. QUESTION 25(b) IS FOUR AREA TYPES, NOT ONE. Deep Distress, NMTC Native
     Areas, High Migration Rural Counties and U.S. Island Areas. A CDE with
     Native Area, High Migration Rural or Island Area QLICIs was told to leave
     them out of a numerator they belong in.

Both errors push the same way: **the CDE understates itself to a federal
agency.** Every prior round in this cycle removed a claim that OVERSTATED what
the Fund requires; this is the first false negative in the package, and it is
the same class as nmtc-mapper 0.4.2 reporting 168 tracts ineligible when they
statutorily qualified.

THE DURABLE RULE: A SUMMARY DOCUMENT IS NOT THE INSTRUMENT. The Review Process
is a safe source for *how the Fund scores*. It is not a safe source for *what
the Applicant is asked to commit to*, because the thing the Applicant fills in
is the Application. Where the two differ, the Application governs and the
citation must name it.

WHY THIS TEXT LIVES IN ONE MODULE. It renders on four surfaces — the Section B
table (markdown, Word, PDF) and the Excel Summary Dashboard. Through 1.2.2 the
markdown/Word/PDF copy lived in ``sections/section_b_outcomes.py`` and the
workbook carried **no basis note at all**, which is how a raw
``pct_deep_or_severe`` float came to sit under a percent format on the
dashboard with no denominator in its label. Four near-identical copies is the
shape that produced the 1.2.0 defect where a sentence was deleted from one file
and stayed live in a second. One authority, read by every surface.

PROVENANCE. CY 2024-2025 NMTC Program Allocation Application, 142 pp.,
1,525,626 bytes, SHA-256 0280c6bc7b35f6015e2c2b1be4b1c07b3864f2dcbaeadfbbbf8bde
d8de12834f, retrieved 2026-08-17 from
https://www.cdfifund.gov/system/files/2024-11/CY_2024-2025_NMTC_Program_Allocation_Application.pdf
and text-extracted LOCALLY with pypdf — not fetched through a summarising
model, which is the provenance failure this whole cycle exists to correct.
Question 25 spans printed pp. 38-41 (PDF pages 65-68); Question 25(b)'s four
area types run to printed p. 42 (PDF page 69).
"""
from __future__ import annotations

from nmtcapp.data.benchmark_thresholds import (
    DEEP_DISTRESS_MIN_PCT, SEVERE_DISTRESS_MIN_PCT,
)

#: The row label. Its claim — the commitments are denominated in QLICIs while
#: every share this package computes is denominated in QEI — is what the
#: Application confirms most directly: Question 25(a) says "at least 85% of its
#: QLICIs (in terms of aggregate dollar amounts)".
Q25_BASIS_LABEL = (
    "BASIS NOTE — the CDFI Fund's two distress commitments are measured on "
    "QLICIs, not on QEI"
)

#: Short form for a sheet label that has to state its own denominator inline.
Q25_QEI_BASIS_SUFFIX = "(a share of QEI, not of QLICIs — see the basis note below)"

#: Items 1-5 of Question 25(a): ONE is enough. Printed p. 39 (PDF 66).
Q25A_ITEMS_1_TO_5 = (
    "Severe Distress",
    "NMTC Native Areas",
    "U.S. Island Areas",
    "Non-Metropolitan Counties",
    "Targeted Populations",
)

#: Items 6-12 of Question 25(a): at least TWO are required. Printed pp. 39-40
#: (PDF 66-67). This seven-item list is what "multiple indicia of distress"
#: means in the Review Process's one-sentence summary.
Q25A_ITEMS_6_TO_12 = (
    "25% poverty / 70% median family income / 1.25x unemployment",
    "Brownfield Sites",
    "ARC and/or DRA Areas",
    "Colonias Areas",
    "Federal Medically Underserved Areas",
    "FEMA Disaster Areas",
    "Low-Income and Low-Access to Supermarkets",
)

#: The four area types of Question 25(b). Printed pp. 41-42 (PDF 68-69).
Q25B_AREA_TYPES = (
    "Deep Distress",
    "NMTC Native Areas",
    "High Migration Rural Counties",
    "U.S. Island Areas",
)

#: The selectable rungs of Question 25(b)(i), verbatim from the Response
#: column: "0 / 5 / 10 / 15 / 20, if selected enter exact percentage 20-100%
#: in 25(b)(ii)".
Q25B_LADDER = (0, 5, 10, 15, 20)

#: Distinct area types across BOTH commitments. Twelve in 25(a) plus Deep
#: Distress and High Migration Rural Counties from 25(b); NMTC Native Areas and
#: U.S. Island Areas appear in both lists and are counted once.
Q25_DISTINCT_AREA_TYPES = 14

#: The five this package carries a per-project field for. Counted here rather
#: than typed into the sentence so the two cannot drift.
Q25_AREA_TYPES_MODELLED = 5


def q25_basis_note() -> str:
    """The basis note, rendered identically on every surface.

    SAYS WHAT THE TOOL CAN SEE, AND THEN SAYS WHY THAT IS NOT AN ANSWER. The
    1.2.2 note's "computes neither figure" was true and unhelpfully pessimistic:
    the package does return a verified distress level and does carry native-area,
    territory and high-migration-rural flags, and a CDE reading only "computes
    neither" has no way to know which of its qualifying routes are represented
    here at all.

    THE OVER-PROMISE THIS IS WRITTEN AGAINST. A list of visible fields reads,
    to a CDE under deadline, as a claim that those fields answer the
    commitment — five of fourteen looks like a partial answer. It is not a
    partial answer, because the commitment is a share of QLICI DOLLARS and this
    package weights nothing by QLICI dollars: holding a flag for an area type
    contributes zero percent of a QLICI-denominated share. So the list is
    stated together with what it is not, in the same paragraph, and the
    paragraph ends on the CDE's own obligation rather than on the list.
    """
    return (
        "Question 25 of the CY 2024-2025 NMTC Allocation Application (printed "
        "pp. 38-41) sets both commitments, and both are measured on QLICIs — "
        "specifically on QLICIs \"in terms of aggregate dollar amounts\", "
        "tested for each QLICI. "
        #
        # 25(a). The twelve items, and the ONE-of-five / TWO-of-seven rule that
        # the Review Process's "multiple indicia of distress" compresses away.
        f"Question 25(a) asks for at least {SEVERE_DISTRESS_MIN_PCT:.0%} of "
        "QLICIs in areas characterized by at least ONE of items 1-5 ("
        + "; ".join(Q25A_ITEMS_1_TO_5) + ") or by at least TWO of items 6-12 ("
        + "; ".join(Q25A_ITEMS_6_TO_12) + "). \"Multiple indicia of distress\" "
        "is that two-of-seven test, applied per QLICI — not a loose notion of "
        "compounded distress and not a category of its own. "
        #
        # 25(b). The correction that matters most: a ladder, not a bar, over
        # four area types rather than one.
        f"Question 25(b)(i) is NOT a {DEEP_DISTRESS_MIN_PCT:.0%} bar. It is a "
        "selectable commitment level — "
        + ", ".join(str(r) for r in Q25B_LADDER[:-1])
        + f" or {Q25B_LADDER[-1]}, and selecting {Q25B_LADDER[-1]} opens a "
        f"field for any figure from {Q25B_LADDER[-1]}% to 100% — over FOUR "
        "qualifying area types: " + ", ".join(Q25B_AREA_TYPES[:-1])
        + f" and {Q25B_AREA_TYPES[-1]}. A CDE that can honestly commit "
        f"{Q25B_LADDER[2]}% selects {Q25B_LADDER[2]} and has failed nothing; a "
        "CDE whose QLICIs sit in Native Areas, High Migration Rural Counties "
        "or Island Areas must count them, and no Deep Distress figure in this "
        "document does. The Application further states that \"A QLICI that "
        "meets this commitment will also automatically meet the commitment "
        "made in Question 25(a).\" "
        #
        # The denominator, unchanged from 1.2.1's FIX-3 and still the reason
        # the note exists at all.
        "Every distress share in this document is a share of QEI. "
        "nmtc-application-builder computes neither QLICI-denominated figure — "
        "it reads this pipeline's QLICI amounts only to print them in Appendix "
        "A and to check that each is no larger than its QEI — so no figure in "
        "this document answers either commitment, and none may be presented to "
        "the CDFI Fund as doing so. "
        #
        # What IS visible, and why it is still not an answer.
        "WHICH OF THE CDE'S QUALIFYING ROUTES ARE VISIBLE HERE: this package "
        f"carries a per-project field for {Q25_AREA_TYPES_MODELLED} of the "
        f"{Q25_DISTINCT_AREA_TYPES} distinct area types Question 25 lists — a "
        "tool-verified distress level covering Severe Distress and Deep "
        "Distress, and three CDE-declared and tool-unverified flags for NMTC "
        "Native Areas, High Migration Rural Counties and U.S. territory (which "
        "is the CDE's own word; the Application's U.S. Island Areas is a "
        "specific list of five). It carries NOTHING for Non-Metropolitan "
        "Counties, nothing for Targeted Populations, and nothing for any of "
        "items 6-12; it computes no multi-indicia measure at all. Holding "
        "those fields is not a partial answer to Question 25 and must not be "
        "read as one: the commitment is a share of QLICI DOLLARS, this package "
        "weights nothing by QLICI dollars, and a flag that enters no "
        "denominator contributes nothing to a share. "
        #
        # The overlap, and the instruction.
        "Deep Distress is a strict subset of severe distress, so the "
        "severe-distress share already includes the deep-distress share. The "
        "CDE must compute both QLICI-denominated shares from its own QLICI "
        "amounts, against the Application's own area lists, before stating "
        "either commitment. (The CY 2026 NOAA is not yet published.)"
    )
