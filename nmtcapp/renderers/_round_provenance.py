"""WHICH ROUND this package reads, and why that is not the round a CDE will file.

THE DEFECT (1.5.0 S1)

Every round-specific citation in this package names the **CY 2024-2025** NMTC
Allocation Application, and names it the way you name a live instrument.
``renderers/_question_25`` and ``renderers/_question_22`` both pin its SHA-256
and quote its page numbers; ``data/benchmark_thresholds`` reads its thresholds;
``intelligence/win_probability`` and the Streamlit methodology tables render
them.

CY 2024-2025 IS CLOSED. It opened 19 Nov 2024, its deadline was 29 Jan 2025,
and it was awarded on 23 Dec 2025. Nothing in this package said so.

WHAT THE PACKAGE IS ACTUALLY DOING, STATED PLAINLY

Through 1.6.4: using the most recent published Application as a proxy for one
that did not exist yet. **That was the correct engineering choice.** There was
no other defensible one, and a tool that declined to encode any instrument
until the CY 2026 one appeared would have been useless during exactly the
window a CDE needed it. The defect was never the choice. It was that the
choice was never disclosed, so a reader had no way to distinguish "this is the
governing instrument" from "this is the nearest available stand-in".

Since 1.6.5: the CY 2026 Application EXISTS (published 17 Sep 2026) and this
package STILL encodes CY 2024-2025, now as a disclosed proxy for a document a
CDE can go and read. Reconciling the encoded figures against it is
``RECHECK_ITEMS`` -- a methodology cycle with its own audit, not a patch --
and until that cycle ships, the note's job is to say so and to point at the
document.

BOTH DIRECTIONS OF ERROR, AND THE SECOND IS EASIER TO CAUSE

  1. OVERSTATING CURRENCY -- citing a closed round as though it governed. That
     is what shipped through 1.4.0.

  2. OVERSTATING UNCERTAINTY -- writing this disclosure so a reader concludes
     the CY 2024-2025 guidance is unreliable and discounts it.

**The CY 2024-2025 Application is not unreliable.** It is a real federal
instrument, retrieved and hash-verified, and it is the best available basis for
preparing a CY 2026 application. A CDE preparing against it is doing the right
thing. A disclosure that drives a CDE to prepare against NOTHING is worse than
the stale citation it replaces -- it converts a small provenance error into an
unprepared applicant.

So the text below tells a CDE **what to re-check against the CY 2026
Application**, and where it is, not that it cannot rely on anything. It is a
re-check list, not a warning label.

WHAT IS NOT CLAIMED HERE, AND WHY

That Question 25's structure is round-invariant. A truncated fetch of the CY
2022 Application showed Question **25** as a **Yes/No dropdown** -- the same
number and the same shape, two rounds earlier -- which is suggestive and is NOT
evidence of stability. The criteria list, the 85%-of-QLICIs threshold value
and the 0/5/10/15/20 ladder at 25(b)(i) were **NOT** confirmed for CY 2022. Writing
"this structure has been stable across rounds" on that evidence would be a new
false claim installed while fixing an old one, which is the exact failure this
package keeps producing. Nothing below says it.

THE CY 2026 FACTS, AND WHERE THEY CAME FROM

THE ROUND HAS OPENED AND THE INSTRUMENT HAS ARRIVED. Those are two facts, two
days apart, and through 1.6.1 this module carried ONE BOOLEAN for both of
them.

  * The CY 2026 **NOAA** is **PUBLISHED** -- Federal Register document
    2026-18883, filed 14 Sep 2026 08:45 ET, publication date 15 Sep 2026. It
    makes $5 billion in aggregate allocation authority available and sets, in
    its Table 1, ten deadlines from 22 Sep 2026 (CDE certification) through
    10 Nov 2026 (the application) to 14 Jan 2027 -- carried whole in
    ``NOAA_TABLE_1`` below.
  * The CY 2026 **Allocation Application** and its Application Materials are
    **PUBLISHED** -- released by the CDFI Fund on 17 Sep 2026
    (cdfifund.gov/news/741) together with the Application FAQs, the
    Application Roadmap Presentation and the AMIS Navigation Guide, all
    linked from the program's "Step 2: Apply" page. Verified on 2026-09-17 by
    retrieving the Application PDF itself: title page "NEW MARKETS TAX CREDIT
    PROGRAM 2026 APPLICATION", running footer "CY 2026 NMTC Allocation
    Application", OMB Approval No. 1559-0016, 137 pages -- pinned in the
    ``UPCOMING_APPLICATION_*`` constants below.

MONOTONE CLAIMS ONLY -- THE 1.6.5 RULE

Every round-provenance defect in this module's history is a PERISHABLE claim:
1.6.2's ``UPCOMING_MATERIALS_PUBLISHED = False``, a negative over two facts;
1.6.3's deadline pinned to a superseded pre-announcement; 1.6.4's
``UPCOMING_APPLICATION_PUBLISHED = False``, the surviving half of the pair,
which went false one day after ``LAST_VERIFIED`` and would have stood for
thirty. "X is published" is monotone: once true it stays true, and a stale
copy of it is still correct. "X is not published" decays, and nothing inside
an installed package can notice the moment it turns.

So this package may assert that something HAS happened. It may not assert
that something HAS NOT. Paragraph 0 states that the CY 2026 Application IS
published and that this tool STILL encodes CY 2024-2025; paragraph 1 points
at where the CY 2026 materials are; paragraph 4's provenance says when the
publication was confirmed. None of the three says "most recent", "no further
materials", or "nothing has superseded this" -- each of those is a decaying
claim wearing a positive sentence. The one negative-shaped branch left in
the module, the ``False`` arm of ``_application_publication_clauses``, is a
dated statement about this tool's own looking and not about the world; it
exists so that the constant governs the sentence in both directions, and
``tests/test_round_provenance`` proves that it does.

THE DATE THAT CAME FROM THE WRONG DOCUMENT -- THE 1.6.4 DEFECT

Through 1.6.3 the CDE certification deadline was ``2026-08-31``, and the note
said, in capitals and in all four formats, that an organization not certified
by then CANNOT APPLY IN CY 2026. **The NOAA says 22 September.** August 31 was
the date in the CDFI Fund's 12 Aug 2026 pre-announcement (``news/738``); the
NOAA superseded it on publication, and for the six days from 16 Sep the package
told eligible applicants they were excluded from a window that was still open.

Two things let that ship. The NOAA was opened three times in the 1.6.2 and
1.6.3 cycles and each time only the field being looked for was read -- that it
exists, that it is $5 billion, that applications close 10 Nov. And the gate
that "checked" the date asserted the literal ``"August 31, 2026"`` against a
note rendering the same literal from the same constant: a check that shares
its source's typo confirms the typo.

So Table 1 is CARRIED, every row, as ``NOAA_TABLE_1``; the two deadlines the
note names by role are lookups into it; ``HARD_EXTERNAL_DEADLINES`` is derived
from it; paragraphs 2-4 of the note are COMPUTED against the Eastern date so
"still ahead" and "has passed" are true on both sides of every row; and
``tests/test_noaa_table_1`` compares the constant to the Federal Register's own
typesetting of the table, carried verbatim in
``tests/noaa_2026_18883_table_1.txt``, rather than to prose derived from the
constant. The section below headed "what the certification paragraph no longer
reasons for the reader" is 1.6.2's and still applies; its closing sentence,
"the AMIS window closed, and the as-of date has arrived", was true of the
wrong date and is now a computation rather than a sentence.

Non-Metropolitan county designations under the CY 2026 NOAA follow OMB
Bulletin 20-01, applied using 2020 census tracts. Recorded here because it is
a CY 2026 fact this module is the right place to hold; it changes no figure in
this package and is not rendered into the note.

WHY ONE BOOLEAN WAS NOT ENOUGH -- THE 1.6.2 DEFECT

``UPCOMING_MATERIALS_PUBLISHED = False`` rendered the sentence "The CY 2026
Allocation Application and NOAA are NOT YET PUBLISHED". That is a
**CONJUNCTION**, and on 15 Sep 2026 one half of it went false while the other
stayed true. A single boolean cannot say so -- it can only be wrong in one
direction or the other, and both wrongs mislead a CDE. So the constant is split
in two, each half carries its own verified date, and the note now distinguishes
the round OPENING from the arrival of the instrument this package ENCODES.

WHAT THE NOTE SAYS ABOUT $5 BILLION, AND WHAT IT NO LONGER SAYS (1.6.2 FIX)

Through the first cut of this release the sentence read "it makes $5 billion
available, **half the prior round**". The arithmetic is right and the
implication is false, and THIS REPOSITORY'S OWN SOURCE SAYS WHY.
``data/historical_awards`` carries ``"double_round": True`` on CY 2024-2025 and
the comment above it reads:

    THE KEY IS "CY2024-2025", NOT "CY2024". The announcement states the awards
    are "a double round, covering 2024 and 2025". Filing a double round under a
    single year beside four single rounds is what made $10 billion look like an
    error against its $5 billion neighbours.

$10 billion over TWO allocation years against $5 billion for ONE is the same
annual rate. A CDE reading "half the prior round" concludes the program was cut
in half and that competition has doubled -- a decision-relevant, false
conclusion, in all four formats, while the same document set says elsewhere
that the prior round "does not compare like-for-like with the single rounds
beside it."

THE CLAUSE IS DELETED AND NOTHING REPLACES IT. An annual-rate comparison would
be a NEW inference, and this package does not make those; the NOAA states an
amount and does not compare it to anything. So the note states the amount.

The clause had also fallen out of a gate's scope in the rewrite that carried it
forward: it previously named "the CDFI Fund", which put it in
``tests/attribution_allowlist.txt``; the 1.6.2 wording dropped the Fund and the
entry went with it while the claim went on rendering. That is recorded here
because the lesson is not about this clause -- a rewrite that drops a scanner's
trigger word silently narrows the scanner.

WHAT THE CERTIFICATION PARAGRAPH NO LONGER REASONS FOR THE READER (1.6.2 FIX)

Two statements went past the NOAA and are gone:

  * "it was the only way to become certified in time". The NOAA states TWO
    eligibility routes. It does not state that AMIS is the only certification
    channel.
  * "which organizations meet the ... as-of date is already fixed". That the
    qualifying set is closed is this package's inference, not the NOAA's
    statement.

What is left is arithmetic on two dates the NOAA does state: the AMIS window
closed, and the as-of date has arrived.

"and no cure" went for the same reason. The NOAA's cure language carries
"except, if necessary and at the request of the CDFI Fund", and it governs
missing materials inside a SUBMITTED application -- a different object from the
certification eligibility this paragraph is about. The package's sentence was
unattributed rather than contradicted, and it errs safe; it is still a claim
this package cannot source, so it is narrowed to "There is no late filing"
rather than attributed. Attributing it would mean quoting a Federal Register
sentence that could not be retrieved from the environment this fix was built
in, which is the worse of the two options offered.

WHAT 1.6.2 THROUGH 1.6.5 DELIBERATELY DO NOT CHANGE

``RECHECK_ITEMS`` still names CY 2024-2025 figures and the note still says so.
The NOAA carries the allocation authority, the application deadline and the
certification rule; it does NOT carry Question 25's ladder, Question 22's
Non-Metropolitan bounds, Question 15's product-flexibility ladder or the
Review Process thresholds. Those live in the Application Materials, which as
of 1.6.5 exist and have NOT been reconciled against this package. Re-working
the round-specific figures inside a provenance patch would leave a release
that cannot be audited as either a correction or a methodology change. That
work is the NEXT release. (Its trigger used to be
``tests/test_round_provenance.test_live_cdfi_fund_check`` asserting the
materials' absence; that assertion was a perishable negative and is gone --
the trigger fired, on 2026-09-17, and this release is its first consequence.)

``APPLICATION_SHA256`` also stays, and stays correct. It was never the defect;
see ``tests/test_round_provenance`` on why a hash cannot fail on staleness.

WHAT WAS SCHEDULED PAST THE EVENT, AND WHAT REPLACED THE REPAIR

``RECHECK_AFTER`` was 2026-11-20 in 1.6.1 -- ten days after the application
deadline. 1.6.2 answered with a gate requiring the horizon to land before
``next_hard_deadline()``. With all of Table 1 carried (1.6.4) that gate and the
expiry itself could not both be green on a deadline day, so the coupling is
gone (1.6.4 fix round, R2): ``RECHECK_AFTER`` is now ``LAST_VERIFIED`` plus
``RECHECK_CADENCE_DAYS``, a cadence for human attention; whether a deadline
has passed is content the note computes. ``next_hard_deadline`` survives for
the one calendar event that does mean "rewrite the note": every filing
deadline behind the Eastern date, on which the suite fails closed.
"""
from __future__ import annotations

import datetime as _datetime
from typing import NamedTuple

#: The round whose Application this package encodes.
CITED_ROUND = "CY 2024-2025"

#: Its status. Named as a constant rather than left implicit, because the
#: implicit version is what shipped: a hash pin that answers "is this the
#: document we read?" and is silent on "is this the round the CDE files?".
CITED_ROUND_STATUS = "closed and awarded"

#: The cited round's own timeline, ISO, from the CDFI Fund's NMTC program
#: page. Through the 1.6.4 tip these three dates were typed into paragraph 0
#: as prose -- the one exception to the rule two lines down that ISO is the
#: arithmetic form and the prose form is derived. Named so the gate that
#: accounts for every year the note mentions (``tests/test_noaa_table_1``,
#: direction 1) can read them instead of exempting the paragraph.
CITED_ROUND_TIMELINE = {
    "opened": "2024-11-19",
    "closed": "2025-01-29",
    "awarded": "2025-12-23",
}

#: The round a CDE reading this today is preparing for.
UPCOMING_ROUND = "CY 2026"

#: ISO dates are the ARITHMETIC form and the US long form is the PROSE form,
#: and the prose form is DERIVED so the two cannot drift. Two hand-maintained
#: spellings of one date is the same retype hazard as two copies of a hash --
#: except a wrong date reads as fine, where a wrong hash at least looks odd.
_MONTH_NAMES = (
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
)


def _us_date(iso: str) -> str:
    """``"2026-11-10"`` -> ``"November 10, 2026"``. ONE spelling, derived.

    Example::

        _us_date("2026-11-10")   # 'November 10, 2026'
    """
    year, month, day = (int(part) for part in iso.split("-"))
    return f"{_MONTH_NAMES[month - 1]} {day}, {year}"


def _short_date(iso: str) -> str:
    """``"2024-11-19"`` -> ``"19 Nov 2024"``: the closed round's history, in
    the compact form paragraph 0 has always used for it. Derived, like
    ``_us_date``, so the timeline constant and the prose cannot drift.

    Example::

        _short_date("2024-11-19")   # '19 Nov 2024'
    """
    year, month, day = (int(part) for part in iso.split("-"))
    return f"{day} {_MONTH_NAMES[month - 1][:3]} {year}"


#: WHETHER THE UPCOMING ROUND'S NOAA HAS PUBLISHED -- and, SEPARATELY, whether
#: the Allocation Application has. Through 1.6.1 this was one boolean named
#: ``UPCOMING_MATERIALS_PUBLISHED`` covering both, and the pair came apart on
#: 2026-09-15: the NOAA published two days before the Application. A
#: conjunction cannot be half-true in code, so it is two constants now.
#:
#: THESE ARE ASSERTIONS WITH DATES ON THEM, NOT MEASUREMENTS. No offline test
#: can distinguish "the Application has published" from "nobody has looked
#: since September". ``tests/test_round_provenance.py`` does not pretend
#: otherwise: it makes the claim EXPIRE, so the failure it can produce is the
#: honest one -- staleness of the LOOKING, not of the fact.
#:
#: BOTH ARE TRUE NOW, AND TRUE IS THE ONLY VALUE EITHER CAN HOLD FROM HERE
#: (1.6.5). "X is published" is MONOTONE: once true it stays true, and a
#: stale copy of it is still correct. "X is not published" DECAYS, and
#: nothing inside an installed package can notice the moment it turns -- which
#: is the whole history of this module's defects (1.6.2, 1.6.3, 1.6.4). So
#: the note derives its Application-status sentences from the constant below
#: (``_application_publication_clauses``), and the branch it takes while the
#: constant is False states a dated fact about THIS TOOL'S OWN LOOKING, never
#: a negative about the world.
UPCOMING_NOAA_PUBLISHED = True

#: The instrument THIS PACKAGE ENCODES, in its CY 2026 edition: PUBLISHED. The CDFI
#: Fund opened the CY 2026 round and released the Allocation Application on
#: 2026-09-17 (``UPCOMING_APPLICATION_ANNOUNCEMENT_URL``); the PDF was
#: retrieved the same day and its title page ("NEW MARKETS TAX CREDIT PROGRAM
#: 2026 APPLICATION", "CY 2026 NMTC Allocation Application") and OMB control
#: number read -- see the ``UPCOMING_APPLICATION_*`` pins below.
#:
#: READ, NOT MERELY DECLARED (1.6.5 R3). Through 1.6.4 this constant was
#: declared here and read by NOTHING in the module -- a declaration shaped
#: like a gate that governed nothing, whose flip to True would have changed
#: no rendered word. Paragraphs 0, 1 and 4 of the note now derive their
#: Application-status clauses from it, so the constant and the sentences
#: cannot disagree, and ``tests/test_round_provenance`` proves the mutation
#: in both directions.
#:
#: FLIPPING IT CHANGED NO THRESHOLD. This package still encodes CY 2024-2025;
#: reconciling its figures against the CY 2026 Application is
#: ``RECHECK_ITEMS``, and that is a methodology cycle with its own audit,
#: not a patch.
UPCOMING_APPLICATION_PUBLISHED = True

#: The CY 2026 Allocation Application, pinned to the day the CDFI Fund
#: announced it and to the PROGRAM PAGE that links it -- not to the upload
#: path. ``system/files/<yyyy>-<mm>/...`` is a versioned upload location and
#: this portfolio has already lost a cycle to one moving (nmtc-mapper 0.6.1,
#: the LIC eligibility workbook); the "Step 2: Apply" page is the addressable
#: resource. The PDF path is carried as SECONDARY provenance of what was
#: retrieved on the verification date, and no gate depends on it resolving.
UPCOMING_APPLICATION_PUBLICATION_DATE = "2026-09-17"
UPCOMING_APPLICATION_ANNOUNCEMENT_URL = "https://www.cdfifund.gov/news/741"
UPCOMING_APPLICATION_PAGE_URL = (
    "https://www.cdfifund.gov/programs-training/programs/"
    "new-markets-tax-credit/apply-step"
)
UPCOMING_APPLICATION_PDF_URL = (
    "https://www.cdfifund.gov/system/files/2026-09/"
    "CY_2026_NMTC_Program_Allocation_Application.pdf"
)
#: What was retrieved on 2026-09-17 from the path above: OMB control number
#: from its page ii, byte count, page count and SHA-256 of the file. These
#: are RETRIEVAL EVIDENCE for the publication claim, not a citation this
#: package reads figures from -- ``APPLICATION_SHA256`` below is still the
#: instrument the figures come from, and it is still CY 2024-2025's.
UPCOMING_APPLICATION_OMB_NUMBER = "1559-0016"
UPCOMING_APPLICATION_SHA256 = (
    "b5c36c715ddfc5f09c44ddf1fdac2b69182c2212104d06fbb2f63f66b84db07d"
)
UPCOMING_APPLICATION_BYTES = 1_576_691
UPCOMING_APPLICATION_PAGES = 137

#: The CY 2026 NOAA, pinned to its Federal Register identity rather than to a
#: page that can be re-edited underneath a citation.
NOAA_FR_DOCUMENT_NUMBER = "2026-18883"
NOAA_FILED_DATE = "2026-09-14"
NOAA_PUBLICATION_DATE = "2026-09-15"
NOAA_URL = "https://www.federalregister.gov/d/2026-18883"

#: Aggregate allocation authority the CY 2026 NOAA makes available. Carried as
#: the rendered string because the note states it as prose, and it is the one
#: CY 2026 figure the NOAA settles; every OTHER round-specific figure in this
#: package is still CY 2024-2025 and ``RECHECK_ITEMS`` still says so.
NOAA_ALLOCATION_AUTHORITY = "$5 billion"

#: WHO A TABLE 1 ROW BINDS. Every row is addressed to an applicant -- the
#: table is headed "Critical Deadlines for Applicants" -- but five of the ten
#: bind only an applicant that is a PRIOR ALLOCATEE: the Subsidiary CDE and
#: Allocation Agreement rows, and the two January 2027 rows, which section
#: III.A.6(a) of the NOAA makes ELIGIBILITY conditions on such an applicant
#: (finalize the Table 2 share of prior-round QEIs and make the QLICIs by 7
#: Jan 2027, report and certify them in AMIS by 14 Jan 2027, or the CY 2026
#: application is ineligible). They are NOT post-award obligations of the
#: CY 2026 round, and the note must not present them as nobody's.
AUDIENCE_APPLICANT = "applicant"
AUDIENCE_PRIOR_ALLOCATEE = "prior allocatee"


class NoaaDeadline(NamedTuple):
    """One row of Table 1, as the Federal Register prints it.

    ``iso`` is the arithmetic form of the date; the prose form is derived by
    ``deadline_text``. ``description`` and ``submission_method`` are the
    instrument's own words, whitespace-normalised and without the trailing
    full stop, so ``tests/test_noaa_table_1`` can compare them to the
    carried excerpt of the Federal Register text.
    """
    iso: str
    time_text: str
    description: str
    submission_method: str
    audience: str


_AMIS = "Electronically via AMIS"

#: TABLE 1 OF THE CY 2026 NOAA, EVERY ROW, IN THE INSTRUMENT'S ORDER (1.6.4).
#:
#: THE DEFECT THIS REPLACES. Through 1.6.3 this module carried TWO of these
#: ten dates, and the CDE certification one was 2026-08-31 -- the date in the
#: CDFI Fund's 12 Aug 2026 PRE-ANNOUNCEMENT (cdfifund.gov/news/738), which the
#: NOAA superseded with 2026-09-22 on the day it published. The note then said,
#: in capitals and in all four formats, that an organization not certified by
#: 31 Aug CANNOT APPLY IN CY 2026, for the six days between 16 Sep and the
#: window's actual close. The NOAA had been opened three times in the 1.6.2
#: and 1.6.3 cycles, and each time only the field being looked for was read.
#:
#: SO THE TABLE IS CARRIED, NOT CITED. Every row, every field, in the
#: instrument's order, and ``tests/noaa_2026_18883_table_1.txt`` holds the
#: Federal Register's own typesetting of it (retrieval URL and SHA-256 in its
#: header) so that ``tests/test_noaa_table_1`` checks this constant against
#: the instrument rather than against prose derived from this constant.
#: Everything below that names a CY 2026 deadline is derived from here.
CDE_CERTIFICATION_ROW = NoaaDeadline(
    "2026-09-22", "11:59 p.m. ET",
    "Community Development Entity (CDE) Certification Application deadline",
    _AMIS, AUDIENCE_APPLICANT,
)
SERVICE_AREA_ROW = NoaaDeadline(
    "2026-09-22", "11:59 p.m. ET",
    "Request to modify CDE certification service area",
    _AMIS, AUDIENCE_APPLICANT,
)
SUBSIDIARY_CDE_CERTIFICATION_ROW = NoaaDeadline(
    "2026-09-22", "11:59 p.m. ET",
    "Subsidiary CDE Certification Application for meeting Qualified Equity "
    "Investment (QEI) issuance thresholds",
    _AMIS, AUDIENCE_PRIOR_ALLOCATEE,
)
APPLICATION_REGISTRATION_ROW = NoaaDeadline(
    "2026-10-06", "5:00 p.m. ET",
    f"{UPCOMING_ROUND} Allocation Application Registration",
    _AMIS, AUDIENCE_APPLICANT,
)
ADD_SUBSIDIARY_CDES_ROW = NoaaDeadline(
    "2026-11-03", "11:59 p.m. ET",
    "Amendment request to add Subsidiary CDEs to Allocation Agreements for "
    "meeting QEI issuance thresholds",
    _AMIS, AUDIENCE_PRIOR_ALLOCATEE,
)
REMOVE_CONTROLLING_ENTITY_ROW = NoaaDeadline(
    "2026-11-03", "11:59 p.m. ET",
    "Amendment request to remove a Controlling Entity from Allocation "
    "Agreement(s)",
    _AMIS, AUDIENCE_PRIOR_ALLOCATEE,
)
LAST_CONTACT_ROW = NoaaDeadline(
    "2026-11-06", "5:00 p.m. ET",
    "Last day to contact CDFI Fund staff",
    _AMIS, AUDIENCE_APPLICANT,
)
APPLICATION_DEADLINE_ROW = NoaaDeadline(
    "2026-11-10", "5:00 p.m. ET",
    f"{UPCOMING_ROUND} Allocation Application deadline (including required "
    "Attachments)",
    _AMIS, AUDIENCE_APPLICANT,
)
QEI_ISSUANCE_ROW = NoaaDeadline(
    "2027-01-07", "11:59 p.m. ET",
    "QEI Issuance and Qualified Low Income Community Investments (QLICIs) "
    "requirements deadline",
    "Not Applicable", AUDIENCE_PRIOR_ALLOCATEE,
)
REPORT_QEIS_ROW = NoaaDeadline(
    "2027-01-14", "11:59 p.m. ET",
    "Report QEIs and certify QLICIs deadline",
    _AMIS, AUDIENCE_PRIOR_ALLOCATEE,
)
NOAA_TABLE_1 = (
    CDE_CERTIFICATION_ROW,
    SERVICE_AREA_ROW,
    SUBSIDIARY_CDE_CERTIFICATION_ROW,
    APPLICATION_REGISTRATION_ROW,
    ADD_SUBSIDIARY_CDES_ROW,
    REMOVE_CONTROLLING_ENTITY_ROW,
    LAST_CONTACT_ROW,
    APPLICATION_DEADLINE_ROW,
    QEI_ISSUANCE_ROW,
    REPORT_QEIS_ROW,
)


def deadline_text(row: NoaaDeadline) -> str:
    """``"11:59 p.m. ET on September 22, 2026"`` -- ONE spelling, derived.

    Example::

        deadline_text(CDE_CERTIFICATION_ROW)  # '11:59 p.m. ET on September 22, 2026'
    """
    return f"{row.time_text} on {_us_date(row.iso)}"


#: THE TWO DEADLINES THE NOTE NAMES BY ROLE. Lookups into the table above, not
#: second copies of a date: through 1.6.3 these were typed here, and one of
#: them was typed from the wrong document.
APPLICATION_DEADLINE = APPLICATION_DEADLINE_ROW.iso
APPLICATION_DEADLINE_TEXT = deadline_text(APPLICATION_DEADLINE_ROW)
AMIS_CDE_CERTIFICATION_DEADLINE = CDE_CERTIFICATION_ROW.iso
AMIS_CDE_CERTIFICATION_DEADLINE_TEXT = deadline_text(CDE_CERTIFICATION_ROW)

#: THE DEADLINES A CDE CAN MISS, which is a narrower set than "dates this note
#: names" and the distinction is load-bearing. ``NOAA_PUBLICATION_DATE`` is an
#: AS-OF date: it fixes whose certification counts, and no reader can act on it
#: on the day. A deadline is something you can still be on the wrong side of by
#: failing to act. Only deadlines belong here, because this tuple is what
#: ``next_hard_deadline`` schedules the re-check against.
#:
#: DERIVED FROM ``NOAA_TABLE_1`` SINCE 1.6.4, by filtering to the FILING
#: WINDOW: every row on or before the application deadline. The two January
#: 2027 rows are deadlines a prior Allocatee can miss, but not by anything it
#: does while applying -- after 10 Nov nothing in this package can help -- so
#: they do not extend the horizon, and ``next_hard_deadline`` still returns
#: ``None`` the day after the application deadline exactly as it did before.
#: The ``(iso, text, what)`` shape is unchanged.
HARD_EXTERNAL_DEADLINES = tuple(
    (row.iso, deadline_text(row), row.description)
    for row in NOAA_TABLE_1
    if row.iso <= APPLICATION_DEADLINE
)


#: The timezone the deadlines above are deadlines IN. The application deadline
#: is written "5:00 p.m. ET" in the note itself; it is not a fact about the
#: machine asking.
DEADLINE_TIMEZONE = "America/New_York"


def _eastern_today():
    """Today's date in ``America/New_York``.

    NO SILENT FALLBACK TO LOCAL TIME. A fallback would restore the exact defect
    this replaces -- a machine-dependent answer to a federal question -- and
    would do it invisibly. A caller in an environment without tzdata can still
    pass ``today=`` explicitly, which is an answer somebody chose rather than
    one that was guessed.
    """
    import datetime as _datetime
    from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

    try:
        zone = ZoneInfo(DEADLINE_TIMEZONE)
    except ZoneInfoNotFoundError as exc:            # pragma: no cover
        raise RuntimeError(
            f"cannot determine the {DEADLINE_TIMEZONE} date: {exc}. The CY "
            "2026 deadlines are Eastern Time deadlines, so answering with "
            "this machine's local date would be wrong by up to a day on the "
            "day it matters most. Install the `tzdata` package, or pass "
            "next_hard_deadline(today=...) explicitly."
        ) from exc
    return _datetime.datetime.now(_datetime.timezone.utc).astimezone(zone).date()


def next_hard_deadline(today=None):
    """The earliest CY 2026 deadline that has NOT yet passed, or ``None``.

    WHAT THIS IS FOR (1.6.4 fix round, R2). It was built so the re-check
    horizon could be required to land before it; that coupling made the suite
    unsatisfiable on every deadline day and is deleted -- ``RECHECK_AFTER`` is
    a cadence now and does not read this. What remains is the ``None`` case,
    and it is DERIVED rather than typed so the gate built on it learns the
    next round's date instead of memorising this one's.

    Returns ``(iso, text, what)`` or ``None`` when every deadline has passed --
    which is itself a finding, not a quiet pass: a note whose every deadline is
    behind it describes a closed round and needs rewriting, so
    ``tests/test_round_provenance.test_the_round_is_not_over`` and
    ``tests/test_noaa_table_1`` both fail closed on ``None``.

    "TODAY" DEFAULTS TO THE EASTERN DATE, NOT THE RUNNER'S (1.6.2 R2)

    Every deadline in ``HARD_EXTERNAL_DEADLINES`` is a federal one, and the
    application deadline is written into the note as **5:00 p.m. ET**. Whether
    it has passed is therefore a question about Eastern Time, and this used to
    answer it with ``date.today()`` -- the local date of whatever machine
    happened to call.

    On 2026-11-10 that is wrong in the direction that matters. A caller east of
    ET (CI in UTC after 19:00 ET, a maintainer in Tokyo all afternoon) reads a
    local date of 2026-11-11, drops the entry, and gets ``None`` -- "this round
    is closed" -- while a CDE still has hours left to file. The same class of
    defect as the one the sibling gate in ``tests/test_round_provenance.py``
    was fixed for, in the one comparison where being a day early is the
    expensive direction.

    ``today`` is still accepted so a caller can ask about any date it likes;
    only the DEFAULT changed.

    Example::

        next_hard_deadline()   # ('2026-11-10', '5:00 p.m. ET on ...', ...)
    """
    import datetime as _datetime

    if today is None:
        today = _eastern_today()
    upcoming = [
        entry for entry in HARD_EXTERNAL_DEADLINES
        if _datetime.date(*(int(p) for p in entry[0].split("-"))) >= today
    ]
    if not upcoming:
        return None
    return min(upcoming, key=lambda entry: entry[0])


#: When the facts above were last verified, ISO-8601. The NOAA is verified
#: against the Federal Register document named above -- on 2026-09-16 from its
#: raw-text endpoint, every Table 1 row, which is how the 31 Aug date was
#: found. The CY 2026 Allocation Application was verified on 2026-09-17 by
#: RETRIEVING THE DOCUMENT ITSELF from ``UPCOMING_APPLICATION_PDF_URL`` and
#: reading its title page and OMB control number, and by reading the
#: announcement at ``UPCOMING_APPLICATION_ANNOUNCEMENT_URL`` and the
#: "Step 2: Apply" page that links the Application, the Application FAQs,
#: the Application Roadmap Presentation and the AMIS Navigation Guide. Those
#: are different kinds of evidence and the note says which is which rather
#: than collapsing them into "verified against cdfifund.gov".
#:
#: THE FACT THIS RELEASE CORRECTS CHANGED ONE DAY AFTER THE PREVIOUS VALUE
#: HERE. 1.6.4 set this to 2026-09-16; the Application published on
#: 2026-09-17; and with ``RECHECK_CADENCE_DAYS = 30`` nothing in the package
#: could have complained before 2026-10-16 -- ten days after the Application
#: Registration deadline the note exists to protect. See the cadence note
#: below and the 1.6.5 CHANGELOG entry for what was and was not done about it.
LAST_VERIFIED = "2026-09-17"

#: How long a verification stays good for, in days. A CADENCE, NOT A
#: DEADLINE (1.6.4 fix round, R2): the question the expiry asks is "has a
#: human re-checked the Fund since ``LAST_VERIFIED``?", which is a question
#: about attention and has nothing to do with when Table 1's rows fall.
#:
#: WHAT THIS REPLACES. Through the 1.6.4 tip ``RECHECK_AFTER`` was typed, and
#: a gate required it to land before ``next_hard_deadline()``. With the whole
#: of Table 1 carried, that rule and ``today <= RECHECK_AFTER`` could not both
#: hold on a deadline day -- the horizon had to be >= today and < today --
#: so the suite was unsatisfiable on 22 Sep, 6 Oct, 3 Nov, 6 Nov and 10 Nov
#: 2026, and every bump between them moved ``LAST_VERIFIED`` across a
#: boundary and regenerated four baselines plus two registries. Whether a
#: deadline has passed is CONTENT: paragraphs 2-4 compute it on every
#: generation and ``tests/test_noaa_table_1`` binds them to the table. The
#: horizon no longer reads the table at all.
#:
#: 30 WAS A JUDGEMENT, AND IT STAYS ONE (1.6.5 R5) -- re-ruled, not relabelled.
#: The 1.6.4 runbook recorded "the 30-day cadence is a judgement, not a
#: derivation", and then the Application published one day after
#: ``LAST_VERIFIED`` and the cadence would have fired ten days after the
#: Registration deadline. The obvious repair -- shrink the number and call it
#: derived -- was considered against the one piece of evidence the repo
#: holds, the intervals between this issuer's own CY 2026 announcements:
#:
#:     2026-08-12  pre-announcement (news/738)        -> 34 days ->
#:     2026-09-15  NOAA, Federal Register 2026-18883  ->  2 days ->
#:     2026-09-17  Allocation Application (news/741)  -> 19 days ->
#:     2026-10-06  Application Registration deadline  -> 35 days ->
#:     2026-11-10  Application deadline
#:
#: Those intervals are 34, 2, 19 and 35 days: no cadence derivable from them
#: is both short enough to have caught the 2-day gap and long enough not to
#: fire as ritual across the 35-day ones. A cadence catches "nobody has
#: looked in a while"; it cannot catch "the world moved yesterday", and no
#: value of this constant would have. What DOES catch that is the event
#: table the note already carries: every Table 1 date is a scheduled moment
#: at which a human is already looking at this module, and the next one is
#: 2026-10-06. So the number is unchanged, its basis is stated plainly as a
#: judgement, and the defence against the next 2-day gap is the rule two
#: constants up -- ship only monotone claims, so that a missed re-check
#: leaves the note UNDERSTATED rather than FALSE. ``tests/test_round_provenance``
#: bounds it at 180.
RECHECK_CADENCE_DAYS = 30

#: The date this claim goes stale and the suite goes red. DERIVED: bump
#: ``LAST_VERIFIED`` to the day you looked and this follows.
RECHECK_AFTER = (
    _datetime.date(*(int(part) for part in LAST_VERIFIED.split("-")))
    + _datetime.timedelta(days=RECHECK_CADENCE_DAYS)
).isoformat()

#: Sources, so a re-check does not start by hunting for the page. The
#: 12 Aug 2026 pre-announcement is kept because 1.6.4's history cites it as
#: the document the wrong certification date came from; the Application's
#: own announcement is ``UPCOMING_APPLICATION_ANNOUNCEMENT_URL`` above.
PROGRAM_PAGE_URL = (
    "https://www.cdfifund.gov/programs-training/programs/new-markets-tax-credit"
)
CY2026_ANNOUNCEMENT_URL = "https://www.cdfifund.gov/news/738"

#: The tab the workbook carries this note on. Named here beside the note so a
#: rename cannot leave the Q25 sheet's cross-reference pointing at nothing.
ROUND_PROVENANCE_SHEET_NAME = "Round Provenance"

#: The CY 2024-2025 Application, pinned. ONE COPY.
#:
#: It was typed into TWO module docstrings -- ``_question_22`` and
#: ``_question_25`` -- as 64 hex characters split across two source lines. Two
#: hand-typed copies of one hash is the retype hazard this package has been
#: bitten by repeatedly (``Q25_QEI_BASIS_CLAUSE`` was three copies agreeing by
#: luck), and it is worse for a hash: nobody proofreads 64 hex characters, so a
#: divergence would look like provenance while pointing at nothing.
APPLICATION_SHA256 = (
    "0280c6bc7b35f6015e2c2b1be4b1c07b3864f2dcbaeadfbbbf8bded8de12834f"
)
APPLICATION_BYTES = 1_525_626
APPLICATION_PAGES = 142
APPLICATION_URL = (
    "https://www.cdfifund.gov/system/files/2024-11/"
    "CY_2024-2025_NMTC_Program_Allocation_Application.pdf"
)

#: What a CDE must re-verify against the CY 2026 Application Materials, which
#: are available at ``UPCOMING_APPLICATION_PAGE_URL``. Written as a re-check
#: list on purpose -- see this module's header on the second direction of
#: error. THE SIX ITEMS ARE UNCHANGED BY 1.6.5 AND STILL OWED: reading the
#: CY 2026 Application to confirm it exists is what 1.6.5 did; reading it to
#: move a threshold is the next methodology cycle.
RECHECK_ITEMS = (
    "the allocation authority and the number of awards available",
    "the CDE certification deadline for eligibility",
    "Question 25's QLICI-denominated commitment levels, its area-type lists "
    "and its ladder",
    "Question 22's QLICI-denominated Non-Metropolitan minimum and maximum",
    "Question 15's product-flexibility ladder",
    "the scoring thresholds in the Review Process",
)


#: Where each computed paragraph sits in ``round_provenance_paragraphs()``.
#: Named so a gate can read "the certification paragraph" without counting.
CERTIFICATION_PARAGRAPH_INDEX = 2
PRIOR_ALLOCATEE_PARAGRAPH_INDEX = 3
DEADLINES_PARAGRAPH_INDEX = 4


def _date(iso: str):
    import datetime as _datetime
    return _datetime.date(*(int(part) for part in iso.split("-")))


def _is_ahead(row: NoaaDeadline, today) -> bool:
    """Day-level, the same rule as ``next_hard_deadline``: the deadline day
    itself is still ahead; the day after, it has passed."""
    return _date(row.iso) >= today


def _row_item(row: NoaaDeadline) -> str:
    """One Table 1 row as a list item: what, when, how, and for whom."""
    item = f"{row.description} — {deadline_text(row)} ({row.submission_method})"
    if row.audience == AUDIENCE_PRIOR_ALLOCATEE:
        item += " [prior Allocatees]"
    return item


def _application_publication_clauses() -> tuple:
    """The three places the note speaks to the CY 2026 Application's status,
    DERIVED from ``UPCOMING_APPLICATION_PUBLISHED`` so they cannot disagree
    with it or with each other (1.6.5 R3a).

    Returns ``(paragraph_0_sentences, paragraph_1_framing, paragraph_4_clause)``.

    WHY A BRANCH AT ALL, GIVEN THE RULE THAT THIS PACKAGE SHIPS ONLY MONOTONE
    CLAIMS. Because a constant that governs nothing is the defect (through
    1.6.4 the constant was declared and read nowhere), and a constant governs
    something only if both of its values render differently. So the False
    branch exists, ``tests/test_round_provenance`` proves it renders when the
    constant is False, and it is written the only way a negative may be
    written here: as a DATED FACT ABOUT THIS TOOL'S OWN LOOKING -- "as of
    <date> this tool had not confirmed ..." -- which stays true after the
    world moves, where "NOT YET PUBLISHED" (1.6.2 through 1.6.4) did not.

    Example::

        p0, p1, p4 = _application_publication_clauses()
    """
    if UPCOMING_APPLICATION_PUBLISHED:
        return (
            f"THE {UPCOMING_ROUND} ALLOCATION APPLICATION AND ITS APPLICATION "
            "MATERIALS ARE PUBLISHED: the CDFI Fund released them on "
            f"{_us_date(UPCOMING_APPLICATION_PUBLICATION_DATE)} "
            f"({UPCOMING_APPLICATION_ANNOUNCEMENT_URL}), and this tool "
            f"confirmed the Application itself on "
            f"{_us_date(LAST_VERIFIED)}. THIS TOOL STILL ENCODES THE "
            f"{CITED_ROUND} INSTRUMENT, which is now a proxy for a document "
            "that exists and can be read.",

            "and that instrument is AVAILABLE NOW: every round-specific "
            "figure in this document must be re-verified against the "
            f"{UPCOMING_ROUND} Application Materials, which the CDFI Fund "
            f"publishes at {UPCOMING_APPLICATION_PAGE_URL}",

            f"the {UPCOMING_ROUND} Application Materials were confirmed "
            f"published on {_us_date(LAST_VERIFIED)}",
        )
    return (
        f"As of {_us_date(LAST_VERIFIED)} this tool had not confirmed "
        f"publication of the {UPCOMING_ROUND} Allocation Application or its "
        f"Application Materials, so the instrument encoded here is still the "
        f"{CITED_ROUND} one.",

        "so every round-specific figure in this document must be re-verified "
        f"against the {UPCOMING_ROUND} Application Materials, which the CDFI "
        f"Fund will publish at {UPCOMING_APPLICATION_PAGE_URL}",

        f"publication of the {UPCOMING_ROUND} Application Materials had not "
        f"been confirmed by this tool as of {_us_date(LAST_VERIFIED)}",
    )


def _certification_paragraph(today) -> str:
    """Paragraph 2: the two eligibility routes, the second's status computed.

    THE 1.6.3 VERSION WAS TYPED, AND TYPED FROM THE WRONG DOCUMENT. It said
    "Neither route is still open ... An organization that did neither CANNOT
    APPLY" against a 31 Aug date the pre-announcement carried and the NOAA
    superseded. Whether the AMIS route is still ahead is now read off Table 1
    against the Eastern date, so the sentence is true on both sides of the
    deadline instead of on neither.
    """
    row = CDE_CERTIFICATION_ROW
    rule = (
        f"THE {UPCOMING_ROUND} CDE CERTIFICATION RULE HAS TWO ROUTES, AND THE "
        "SECOND HAS A DATE IN TABLE 1 OF THE NOAA. To be eligible to apply in "
        f"{UPCOMING_ROUND} an organization must EITHER already be a certified "
        "CDE as of the NOAA's Federal Register publication date, "
        f"{_us_date(NOAA_PUBLICATION_DATE)}, OR submit its CDE Certification "
        f"Application through AMIS by {deadline_text(row)}."
    )
    # ONE SENTENCE IN BOTH BRANCHES, WORD FOR WORD. It is true on both sides
    # of the deadline, and tests/test_attributed_claims rules attributions by
    # exact clause: a sentence that renders only while the route is ahead
    # would leave a dead allowlist entry behind on 23 Sep.
    fund = (
        "The NOAA adds that the CDFI Fund will not provide allocation "
        "authority to an Applicant that is not certified as a CDE."
    )
    if _is_ahead(row, today):
        status = (
            f"As of {_us_date(today.isoformat())} the AMIS route is STILL "
            "AHEAD: an organization that is not yet a certified CDE can still "
            "meet the rule by submitting its CDE Certification Application "
            f"through AMIS by {deadline_text(row)}. {fund} An organization "
            f"that does neither CANNOT APPLY IN {UPCOMING_ROUND}."
        )
    else:
        status = (
            f"As of {_us_date(today.isoformat())} the AMIS route has CLOSED: "
            f"the window shut at {deadline_text(row)}, and the as-of date, "
            f"{_us_date(NOAA_PUBLICATION_DATE)}, has passed. {fund} An "
            f"organization that did neither CANNOT APPLY IN {UPCOMING_ROUND}."
        )
    return (
        f"{rule} {status} There is no late filing; its next opportunity is a "
        "future round."
    )


def _prior_allocatee_paragraph(today) -> str:
    """Paragraph 3: the rows that bind a prior Allocatee, each with ITS date.

    THE 1.6.3 VERSION GAVE TWO ACTIONS ONE DATE. Certifying a Subsidiary CDE
    and adding it to an Allocation Agreement are two Table 1 rows with two
    dates -- 22 Sep and 3 Nov -- and the note put both on 31 Aug and called it
    closed. And it stopped there: the QEI issuance thresholds those actions
    exist to meet are ELIGIBILITY conditions on a prior Allocatee's CY 2026
    application with two more Table 1 dates of their own, both in January
    2027, both after the application deadline. Section III.A.6(a) of the NOAA.
    """
    cert, add = SUBSIDIARY_CDE_CERTIFICATION_ROW, ADD_SUBSIDIARY_CDES_ROW
    issue, report = QEI_ISSUANCE_ROW, REPORT_QEIS_ROW
    when = _us_date(today.isoformat())
    if _is_ahead(cert, today):
        status = f"As of {when} both of those dates are still ahead."
    elif _is_ahead(add, today):
        status = (
            f"As of {when} the Subsidiary CDE certification date has passed "
            "and the amendment date is still ahead."
        )
    else:
        status = f"As of {when} both of those dates have passed."
    return (
        "AND IF YOU ARE A PRIOR ALLOCATEE, TABLE 1 BINDS YOU ON DATES OF ITS "
        "OWN: any prior Allocatee that requires action by the CDFI Fund in "
        "order to meet the Qualified Equity Investment (QEI) issuance "
        f"thresholds published in the {UPCOMING_ROUND} NOAA must submit a CDE "
        "Certification Application for its Subsidiary CDE(s) through AMIS by "
        f"{deadline_text(cert)}, and any Allocation Agreement amendment "
        f"request to add Subsidiary CDEs by {deadline_text(add)}. {status} "
        "The thresholds are eligibility conditions with their own deadlines, "
        "both after the application deadline: the Table 2 share of "
        "prior-round QEIs must be finalized, and the required share of them "
        f"used to make QLICIs, by {deadline_text(issue)}, and those QEIs "
        f"reported and QLICIs certified in AMIS by {deadline_text(report)}. "
        "The QEI issuance "
        "thresholds themselves are in Table 2 of the NOAA, Federal Register "
        f"document {NOAA_FR_DOCUMENT_NUMBER}; this tool neither computes them "
        "nor reproduces them."
    )


def _deadlines_paragraph(today) -> str:
    """Paragraph 4: what is still ahead, COMPUTED, and what has passed.

    "THE ONLY CY 2026 DEADLINE YOU CAN STILL MISS IS THE APPLICATION
    DEADLINE" was a typed sentence through 1.6.3, and it was true on no day:
    on the day it shipped, eight of Table 1's ten rows were still ahead. So
    the set is derived from the table against the Eastern date and rendered
    whole, in the instrument's order; a row that has passed moves to the
    second list rather than disappearing. When nothing is ahead the paragraph
    says so, and ``tests/test_noaa_table_1`` fails closed on that state --
    a note whose every date is behind it describes a closed round.
    """
    when = _us_date(today.isoformat())
    ahead = [row for row in NOAA_TABLE_1 if _is_ahead(row, today)]
    passed = [row for row in NOAA_TABLE_1 if not _is_ahead(row, today)]
    total = len(NOAA_TABLE_1)
    provenance = (
        "Every one of these dates is set by the NOAA, none is a figure this "
        "tool computes, and nothing in this document moves them. Provenance: "
        f"the {UPCOMING_ROUND} NOAA is Federal Register document "
        f"{NOAA_FR_DOCUMENT_NUMBER}, filed {_us_date(NOAA_FILED_DATE)} and "
        f"published {_us_date(NOAA_PUBLICATION_DATE)}; "
        f"{_application_publication_clauses()[2]}."
    )
    if ahead:
        verb = "is" if len(ahead) == 1 else "are"
        lead = (
            f"THE {UPCOMING_ROUND} DEADLINES STILL AHEAD, COMPUTED FROM TABLE "
            "1 OF THE NOAA AGAINST THE EASTERN DATE THIS DOCUMENT WAS "
            f"GENERATED, {when}: {len(ahead)} of the {total} deadlines in "
            f"Table 1 {verb} still ahead — "
            + "; ".join(_row_item(row) for row in ahead) + "."
        )
        if passed:
            gone = (
                "Already passed: "
                + "; ".join(_row_item(row) for row in passed) + "."
            )
        else:
            gone = "Already passed: none."
        return f"{lead} {gone} {provenance}"
    return (
        f"EVERY {UPCOMING_ROUND} DEADLINE IN TABLE 1 OF THE NOAA HAS PASSED "
        f"AS OF THE EASTERN DATE THIS DOCUMENT WAS GENERATED, {when}. Already "
        "passed: " + "; ".join(_row_item(row) for row in passed) + ". "
        f"{provenance}"
    )


def round_provenance_paragraphs(today=None) -> tuple:
    """``round_provenance_note()`` split into paragraphs, same text.

    WHY THIS EXISTS (1.5.0 B1). Markdown, Word and PDF each render the note as
    one flowing string. Excel cannot: a cell has a 409-pt ceiling and the note
    is far longer, so the workbook needs it one paragraph per row. The wrong
    way to get that is a second copy of the text in ``excel_builder`` -- which
    is precisely the shape this module was created to remove, where the round
    caveat existed as three separately-typed sentences that drifted apart.

    So the note is DEFINED here as paragraphs and ``round_provenance_note()``
    is their join. There is still ONE source of truth, and
    ``tests/test_round_provenance.py`` asserts the join is exactly the note, so
    the two views cannot diverge even in principle.

    PARAGRAPHS 2, 3 AND 4 ARE COMPUTED AGAINST ``today`` (1.6.4), which
    defaults to the Eastern date -- the same clock ``next_hard_deadline``
    reads, for the same reason. Which of Table 1's deadlines are still ahead
    is a claim about the day the document is generated, and through 1.6.3 it
    was a typed sentence. ``today`` is accepted so a caller (and the rendered
    baseline) can ask about a fixed date.

    Example::

        paras = round_provenance_paragraphs()
    """
    if today is None:
        today = _eastern_today()
    application_status, recheck_framing, _provenance = (
        _application_publication_clauses()
    )
    # "WHICH IS THE MOST RECENT PUBLISHED APPLICATION" IS GONE (1.6.5). It
    # went false on 2026-09-17 and it is exactly the shape the monotone rule
    # forbids: a superlative over a set the world keeps adding to. What the
    # cited round IS -- a real federal instrument, closed and awarded -- is
    # stated; where it stands in a sequence is not.
    return (
        f"WHICH ROUND THIS IS BASED ON. This tool encodes the "
        f"{CITED_ROUND} NMTC Allocation Application, which is "
        f"{CITED_ROUND_STATUS} (it opened "
        f"{_short_date(CITED_ROUND_TIMELINE['opened'])}, closed "
        f"{_short_date(CITED_ROUND_TIMELINE['closed'])}, and was awarded "
        f"{_short_date(CITED_ROUND_TIMELINE['awarded'])} with "
        f"$10 billion in allocation authority). THE {UPCOMING_ROUND} ROUND "
        f"HAS OPENED: the {UPCOMING_ROUND} NOAA "
        f"IS PUBLISHED — Federal Register document {NOAA_FR_DOCUMENT_NUMBER}, "
        f"publication date {_us_date(NOAA_PUBLICATION_DATE)} — and it makes "
        f"{NOAA_ALLOCATION_AUTHORITY} available, with "
        f"applications due {APPLICATION_DEADLINE_TEXT}. {application_status}",

        f"USE THIS, AND THEN RE-CHECK IT. The {CITED_ROUND} Application is a "
        "real federal instrument and nothing here is unreliable. But it is a "
        f"PROXY for the {UPCOMING_ROUND} instrument, not that instrument, "
        f"{recheck_framing} — specifically: {'; '.join(RECHECK_ITEMS)}.",

        _certification_paragraph(today),
        _prior_allocatee_paragraph(today),
        _deadlines_paragraph(today),
    )


def round_provenance_note(today=None) -> str:
    """The round-provenance disclosure, in the package's own voice.

    ONE STRING, READ EVERYWHERE. The round caveat was previously three
    separately-typed sentences -- ``_methodology.noaa_note()``,
    ``sections/base``'s placeholder and the tail of
    ``_question_25.q25_basis_note()`` -- each saying a different fraction of it
    and each able to drift from the others. That is the shape that produced the
    1.2.0 defect where a sentence was deleted from one file and stayed live in
    a second.

    The text is defined as paragraphs in ``round_provenance_paragraphs()`` and
    joined here; Excel renders the paragraphs and the other three formats
    render this join. Same words, two shapes, no second copy.

    Example::

        note = round_provenance_note()
    """
    return " ".join(round_provenance_paragraphs(today=today))
