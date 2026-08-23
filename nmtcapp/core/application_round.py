"""The round a CDE is FILING INTO — and what to render when nobody said.

Not to be confused with ``renderers/_round_provenance``, which records the
round this package READS. The two were conflated in one field through 1.5.4
and that is the defect this module exists to keep separated:

  * ``_round_provenance.CITED_ROUND``  — CY 2024-2025. The tool's fact, and
    the tool is entitled to assert it because it retrieved and hash-verified
    the instrument.
  * ``Application.application_round``  — the round the CDE's own submission
    is aimed at. **The user's fact.** The tool has no way to know it and
    therefore no business defaulting it.

THE DEFECT (1.5.5 T1). ``Application.__init__`` defaulted this to the string
``"CY2025"``. The CDFI Fund has never run a round by that name: the encoded
instrument is CY **2024-2025** (closed 29 Jan 2025, awarded 23 Dec 2025 at
$10 billion) and the upcoming one is CY **2026** (announced 12 Aug 2026 at
$5 billion, not yet open). ``data/historical_awards.NMTC_AWARD_ROUNDS`` —
this package's own record of rounds that happened — has no CY2025 key. So a
CDE who never touched the field got a generated application document
asserting a round that does not exist, on the title page, in the running
footer, and inside the executive-summary sentence.

WHY THE FIX IS A DISCLOSURE AND NOT A BETTER DEFAULT. Replacing "CY2025"
with "CY 2026" would swap a false claim for an unverified one — a guess
about the reader's own submission, rendered as fact, with nothing on the page
to say it was guessed. A CDE preparing for CY 2027, or re-running a closed
round, would be handed the wrong round silently. So the absence is rendered
as an absence. See ``tests/test_application_round.py`` for the full ruling,
including why REQUIRING the field is a 2.0.0 change rather than a patch.

The three shapes below exist because the round appears in three grammatical
positions across the renderers, and each degrades differently when there is
nothing to say. One module so a fourth surface cannot invent a fourth
answer.
"""
from __future__ import annotations

from typing import Optional

#: Rendered in a LABELLED field — "Application Round: <this>". Names who owns
#: the fact, because a bare blank in a table cell reads as a formatting bug
#: rather than as a deliberate refusal to guess.
ROUND_UNSPECIFIED_VALUE = "not specified — CDE to state"

#: Rendered where the round stands ALONE with no adjacent label, such as the
#: Excel cover sheet's metadata strip. Carries its own noun for that reason.
ROUND_UNSPECIFIED_STANDALONE = "Application round not specified"


def is_round_specified(value: Optional[str]) -> bool:
    """True when the user actually supplied a round.

    Whitespace is not a round. An uploaded "Application Round" cell holding
    a stray space must degrade to the disclosure, not render one.

    Example::

        is_round_specified("CY 2026")   # True
    """
    return bool(value and value.strip())


def round_label(value: Optional[str]) -> str:
    """Value for a labelled field — "Application Round: <this>".

    Example::

        round_label(None)   # 'not specified — CDE to state'
    """
    return value.strip() if is_round_specified(value) else ROUND_UNSPECIFIED_VALUE


def round_label_standalone(value: Optional[str]) -> str:
    """Value where the round stands alone with no adjacent label.

    Example::

        round_label_standalone(None)   # 'Application round not specified'
    """
    return value.strip() if is_round_specified(value) else ROUND_UNSPECIFIED_STANDALONE


def allocation_round_clause(value: Optional[str], noun: str = "") -> str:
    """Narrative clause — "…allocation<this>." — or nothing at all.

    The clause DISAPPEARS when unspecified rather than degrading to a
    disclosure, because the sentence around it is already true without it:
    "requests $65.0 million in New Markets Tax Credit allocation. Our
    20-project pipeline spans 19 states." The title page carries the
    disclosure once; repeating it mid-sentence in every executive summary
    would be noise, and the one thing that must not happen here — naming a
    round — cannot happen either way.

    ``noun`` preserves each renderer's own phrasing -- the Markdown builder
    says "for application round CY 2026" where Word and PDF say "for
    CY 2026". Harmonising them would be a gratuitous rewording in a patch,
    and the wording is not what was broken.

    Example::

        allocation_round_clause("CY 2026")                        # ' for CY 2026'
        allocation_round_clause("CY 2026", "application round ")  # ' for application round CY 2026'
        allocation_round_clause(None, "application round ")       # ''
    """
    return f" for {noun}{value.strip()}" if is_round_specified(value) else ""


def nmtc_round_phrase(value: Optional[str]) -> str:
    """Running header/footer phrase — "NMTC CY 2026" or just "NMTC".

    Example::

        nmtc_round_phrase(None)   # 'NMTC'
    """
    return f"NMTC {value.strip()}" if is_round_specified(value) else "NMTC"
