"""One authority for what the non-metropolitan share is, and what it is not.

WHY THIS MODULE EXISTS (1.4.0 R3)

``intelligence/geographic_analysis`` computes ``non_metro_pct``: the share of
this pipeline's **QEI** sitting in verified OMB Non-Metropolitan Counties. It
renders on three surfaces — the ``nmtcapp analyze`` summary, the Streamlit
Geographic tab, and (until 1.4.0) a benchmark row scored against a "winner
mean". On two of those three it rendered as a bare percentage with no
denominator and no statement of what question it does or does not answer.

THE DENOMINATOR IS NOT SWAPPED, AND THAT IS A FINDING RATHER THAN A DEFERRAL.
Question 22(c)/(d) asks for a percentage of **QLICIs**, so the obvious repair
is to change the basis. It is the wrong repair, because Question 22 does not
ask for a measurement at all. Read from the instrument (provenance below),
printed p. 32 / PDF page 59:

    (c) What is the minimum percentage of QLICIs that the Applicant is
        willing to commit to deploy in Non-Metropolitan Counties?
        ______%                                  Numerical - Percentage

    (d) What is the maximum percentage of QLICIs that the Applicant is
        willing to commit to deploy in Non-Metropolitan Counties?
        ______%                                  Numerical - Percentage

"Willing to commit to deploy" is a forward undertaking about capital the
Applicant does not yet have, entered into a blank field, and the Application
says what happens to it: the figures "shall become a condition of its
Allocation Agreement with the CDFI Fund". It is the same shape as Question
25(a)/(b), which the methodology round established as a dropdown and a menu
rather than a measurement.

So swapping QEI for QLICI would move this figure closer to the *units* of a
commitment while leaving it a characterisation of a current pipeline. More
credible, no more correct — and credible-but-wrong is the harder failure to
catch downstream. The basis stays QEI and every surface says so.

WHERE THE APPLICATION *DOES* WANT THE PIPELINE, IT SAYS SO — and this is what
the share is legitimately good for. Question 22(f)'s own notes instruct:
"Indicate the number and dollar amount of transactions that have already been
identified in Non-Metropolitan Counties, for which underwriting is completed or
underway. Reference sample transactions in the Applicant's non-metropolitan
pipeline included in Table A5." That is a narrative and a transaction list, not
a percentage — which is exactly what ``metro_status_qei`` carries alongside the
share, and why the counts are returned with the dollars.

AND QUESTION 22 IS NOT SCORED IN PHASE I. Printed p. 31, verbatim: "Question 22
will not be evaluated and scored in Phase I of Allocation Application reviews.
Therefore, this question is not used to determine whether an Applicant scored
highly enough to receive consideration for an NMTC Allocation."

THE 20% IS A FUND GOAL AND A COMMITMENT THRESHOLD, NEVER A PIPELINE BAR. Also
printed p. 31: "the CDFI Fund has established the goal that: (i) 20% of all
QLICIs made by Allocatees under this Round are invested in Non-Metropolitan
Counties", and the formula reduction falls on "all Allocatees in the pool that
have not committed to investing a minimum of 20% of their QLICIs in
Non-Metropolitan Counties". Both readings are about what an Applicant COMMITS
to, across the whole Allocatee pool. Question 22 states no minimum an
individual Applicant must clear. This is why 1.4.0 R4 deletes
``non_metro_meets_minimum``.

AN INCONSISTENCY IN THE INSTRUMENT ITSELF, recorded so a later reader does not
"correct" this module toward it. The printed p. 31 NOTE says the Fund may
require deployment "at or above the minimum indicated in Question 22(b), but
not more than the maximum percentage indicated in Question 22(c)". In the
question table on printed p. 32, 22(b) is a **count of years** (0-6) and the
minimum/maximum percentages are 22(c) and 22(d). The table is the field list an
Applicant fills in and governs; the NOTE is off by one letter against it. The
NOTE's own Rural CDE sentence — "commits to a figure of 50% or greater in
response to Question 22(c)" — agrees with the table, not with itself.

PROVENANCE. CY 2024-2025 NMTC Program Allocation Application, 142 pp.,
1,525,626 bytes, SHA-256 0280c6bc7b35f6015e2c2b1be4b1c07b3864f2dcbaeadfbbbf8bde
d8de12834f, re-downloaded and re-hashed for this round from
https://www.cdfifund.gov/system/files/2024-11/CY_2024-2025_NMTC_Program_Allocation_Application.pdf
and text-extracted LOCALLY with pypdf. Identical to the hash
``renderers/_question_25.py`` pins, so both modules read the same instrument.
Question 22's NOTE block is printed p. 31 (PDF page 58); the question table is
printed p. 32 (PDF page 59).
"""
from __future__ import annotations

from nmtcapp.renderers._question_25 import Q25_QEI_BASIS_CLAUSE

#: The denominator clause. IMPORTED, NOT RETYPED — it is the same sentence the
#: four generated documents already carry for the distress shares, hostile-
#: audited across three rounds, and ``_question_25`` records that retyping it
#: is how three copies came to agree by luck. One string, every surface.
Q22_QEI_BASIS_CLAUSE = Q25_QEI_BASIS_CLAUSE

#: What the figure IS, in one clause that fits on a metric label or a CLI line.
#: A share of QEI, and a description of the pipeline as it stands today.
Q22_NON_METRO_BASIS_SHORT = (
    f"{Q22_QEI_BASIS_CLAUSE}; a characterisation of this pipeline, "
    "not an answer to Question 22"
)

#: The metric label for the Streamlit Geographic tab. The screen is where a CDE
#: reads a number before it ever generates a document (1.3.1 F2), so the label
#: carries the basis on the figure's own face rather than in a caption.
Q22_NON_METRO_METRIC_LABEL = "Non-metro share of QEI"

#: The label for the third bucket, wherever it renders. "Not determined" and
#: never "Unknown": the tool's failure to resolve a tract is not a property of
#: the tract, and a CDE reading "Unknown" beside two determinations may take it
#: for a third category of county rather than an absence of an answer.
Q22_UNDETERMINED_LABEL = "Not determined"

#: The two determined labels. The Fund's terms, not this package's — "rural"
#: and "urban" are what produced the twelve-state list, and neither word
#: appears in Question 22.
Q22_NON_METRO_LABEL = "Non-metropolitan"
Q22_METRO_LABEL = "Metropolitan"


def q22_basis_note() -> str:
    """The full basis note, for surfaces with room for a paragraph.

    Says three things in this order: what the figure is a share of, what
    Question 22 actually asks for, and what the third bucket means. The order
    matters — a CDE who stops reading after one sentence has the denominator.

    Example::

        note = q22_basis_note()
    """
    return _q22_basis_note_text()


def q22_undetermined_caveat(undetermined_pct: float) -> str:
    """One sentence naming the undetermined share, or "" if there is none.

    RENDERED BESIDE THE FIGURE, NOT INSTEAD OF IT. A share with a third bucket
    of zero needs no caveat and gets none; a share with a non-empty third
    bucket must say so wherever it renders, because the two determined
    percentages no longer sum to 1.0 and a reader who assumes they do will
    read the metropolitan share as the complement of the non-metropolitan one
    — which is precisely the arithmetic 1.4.0 R2 removed.

    Example::

        q22_undetermined_caveat(0.0)    # -> ""
        q22_undetermined_caveat(0.07)   # -> "7% of QEI ... not determined ..."
    """
    if not undetermined_pct:
        return ""
    return (
        f"{undetermined_pct:.0%} of QEI sits in projects with no "
        "Non-Metropolitan County determination — not geocoded, or the tract "
        "is absent from the CDFI Fund eligibility table. Those dollars are "
        "reported separately and are counted as neither; they are NOT "
        "metropolitan."
    )


def _q22_basis_note_text() -> str:
    """The note, split at its argument boundaries.

    ONE EXPRESSION IN THE SOURCE, for the reason ``_question_25`` records:
    ``tests/test_fund_attribution_source.py`` scans string expressions with
    ``ast`` and its unit of analysis is one contiguous expression, so splitting
    a quotation and its authority into separate literals silently un-attributes
    both.
    """
    return (
        "BASIS — this figure is the share of this pipeline's QEI in census "
        "tracts the CDFI Fund eligibility table marks as Non-Metropolitan "
        f"Counties: {Q22_QEI_BASIS_CLAUSE}. "
        #
        # What Question 22 asks for, and why this is not it.
        "IT IS NOT AN ANSWER TO QUESTION 22. Question 22(c) and 22(d) of the "
        "CY 2024-2025 NMTC Allocation Application (printed p. 32) ask what "
        "\"minimum percentage of QLICIs the Applicant is willing to commit to "
        "deploy in Non-Metropolitan Counties\" and what maximum — a forward "
        "commitment the Applicant enters as a percentage, which \"shall "
        "become a condition of its Allocation Agreement with the CDFI Fund\", "
        "not a measurement of the pipeline the Applicant holds today. "
        "Question 22 also \"will not be evaluated and scored in Phase I of "
        "Allocation Application reviews\" (printed p. 31). "
        #
        # What it IS good for — the Application's own instruction.
        "WHAT IT IS FOR. Question 22(f) asks the Applicant to \"indicate the "
        "number and dollar amount of transactions that have already been "
        "identified in Non-Metropolitan Counties, for which underwriting is "
        "completed or underway\", referencing Table A5. This figure and the "
        "project counts beside it are that raw material, and are a starting "
        "point for deciding what to commit to in 22(c) — not the commitment. "
        #
        # The 20%.
        "THERE IS NO 20% APPLICANT THRESHOLD. The 20% in this round is a "
        "CDFI Fund goal for \"all QLICIs made by Allocatees under this Round\" "
        "and a bar on what an Allocatee has COMMITTED to; Question 22 states "
        "no minimum an individual Applicant must clear, and this tool no "
        "longer reports whether a pipeline share clears one. "
        #
        # The third bucket.
        "THE THIRD BUCKET. Projects whose county status this tool could not "
        "determine — not geocoded, or geocoded to a tract absent from the "
        "CDFI Fund's eligibility table — are reported separately and counted "
        "as neither metropolitan nor non-metropolitan. They are NOT "
        "metropolitan. The three shares sum to 100% of QEI."
    )
