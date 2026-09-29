"""No surface may claim the house winner constants are measurements of past winners (1.7.2 F2).

THE DEFECT
==========

``streamlit_app/app.py``'s Methodology Disclosure adjudicated this in 1.2.x,
citing ``nmtcapp/data/historical_awards.py`` as denying the claim:

    "Alignment scores measure similarity to this tool's own assumed winner
     patterns, which are unsourced house constants — not measurements of past
     winners, and not a CDFI Fund publication."

The 1.7.1 app settle read found two surfaces on the same app still asserting
the opposite, unqualified: Home's "Getting started" ("score your application
against historical winner patterns") and the Pipeline Optimizer's subtitle
("maximizes composite alignment with historical NMTC winner patterns") -- on
the one page with no disclosure at all. The repo-wide sweep this release ran
found the same claim in the Win Alignment Scorer's own Methodology Notice
("patterns observed in historical NMTC award winners (CY2020–CY2024)"), in
``OptimizationResult.methodology_note`` (rendered on page 3 and by
``summary()``), in the README ("five years of CDFI Fund award data"), in
seven docs pages, in the example notebook, in the sector-mix chart title and
in a dozen docstrings. The one-surface-fixed shape, again.

THE GATE -- R11's SHAPE, APPLIED TO THIS CLAUSE
===============================================

WHAT IT IS, STATED HONESTLY: A SPELLING REGISTRY, NOT A DETECTOR. It catches
the spellings listed in FORBIDDEN and the nouns in WINNER_NOUN, and nothing
it has not been told about. The first cut passed eleven evasions a hostile
lane wrote in minutes -- "five years of CDFI Fund award data", "patterns of
past awardees", "past winners' profiles", "winners' patterns", "patterns
measured from CY2020-2024 award recipients", "successful NMTC applicants",
"what prior awardees looked like", "what award-winning CDEs looked like",
"Past winners averaged 80%", "vs. CY2020-2024 winners", "compares favourably
with recent winners" -- and its qualifier and negation rules accepted a
matching word ANYWHERE in the sentence or clause. Fix round 1 (P8/X4) widened
the spellings to cover every one of those (each is asserted below), bound a
negation to the 4 tokens before the match and a qualifier to 6 tokens either
side of the noun in the same clause.

Fix round 2 found the gate wrong in BOTH directions. It flagged true
sentences ("Enter the CDE's past NMTC awards in the track record table", "The
CDFI Fund publishes award recipients each round") and passed new claims:
"It is no secret that past winners averaged 80%" slipped through the
negation window, and "the winner median", "Winners consistently exceed",
"Winning CDEs typically", "prior-round allocatees", "calibrated on the award
books" and "top-ranked CDEs from prior rounds" matched no spelling at all.
Bare "award(s)" is gone from the past-winners rule; awardees, allocatees and
award/allocation recipients fire only in a claim context; a negation now
excuses a match only when it DIRECTLY governs it (``_GOVERNED``); and every
probe either lane sent is in EVASIONS or NOT_CLAIMS.

A NEW PHRASING WILL STILL PASS. This round's own probes are the proof: none
of the spellings above existed until a hostile reader wrote a sentence the
previous registry did not know. What this gate buys is that every spelling
ever found stays found, and that the true sentences it once flagged stay
unflagged. It does not claim that every evasion is caught.

Fix round 3 is the same lesson a third time: fifteen more phrasings passed
the round-2 gate -- a statistic word beside an allocatee noun ("Prior
Allocatees averaged 80%", "the top quartile of allocatees", "historical
allocatee data"), a selected population with a statistic verb ("Winning
pipelines average 7 states", "awarded CDEs exceed"), and derivations from
"actual NMTC awards", "award data" and "award books". Each has a spelling
now and is a must-fail case. KNOWN LIMITS, stated rather than hidden: the
allocatee-statistic window is 3 tokens, so "Allocatees across the five
rounds from 2019 to 2023 averaged 80%" passes; "data", "distribution" and
"population" beside an allocatee noun count only after a past/CY qualifier,
because "the Fund does publish Allocatee-level deployment data" is true; and
a negation anywhere in the gap breaks the link.

R11 (1.7.1) moved ``LOWER_BOUND_CLAUSE`` into ``renderers/_disclosure``, read
it on every surface, forbade the contradicting sentence document-wide, pinned
the true half so it could not be softened, required the surfaces to state it
identically, and walked the installed package for retyped copies. This does
the same for ``_disclosure.ASSUMED_WINNER_PATTERNS_CLAUSE``:

1. FORBIDDEN -- the provenance claim, in every spelling the sweep found and the
   obvious neighbours: "historical ... winners/winner patterns", "observed in
   ... winners", "trained on ... winner data", "typical winner", "what winners
   do", "winning applications", "compares to past winners". Scanned over:

     * every Streamlit page RENDERED, cold and after its action (the list is
       the directory's, via ``test_streamlit_surface_enumeration``);
     * the four generated formats and the CLI, through their committed
       baselines (``tests/rendered_baseline``, ``tests/cli_baseline``), which
       their own gates hold byte-equal to live output;
     * the installed ``nmtcapp`` package, ``streamlit_app/``, ``README.md``
       and ``pyproject.toml`` -- whole files, so comments and docstrings too;
     * in a checkout, ``docs/``, ``mkdocs.yml``, ``examples/``,
       ``CONTRIBUTING.md``, ``CITATION.cff`` and ``scripts/``.

   Rendered text gets NO exemption. Source text may quote a withdrawn phrase
   to record it -- this file's own history section does -- and each such
   RECORD is listed in ``RECORDS`` with its reason, must still match (no dead
   entries), and excuses exactly one line.

2. AGREEMENT -- a user-facing sentence that names winner patterns, winner
   benchmarks, winner figures or a winner distribution must say, in the same
   sentence, that they are this tool's own / assumed / house / unsourced, or
   deny the thing outright. Scanned over rendered pages, README, docs, the
   notebook and the package's string literals (docstrings included; comments
   are maintainers' notes and are held only to rule 1).

3. THE TRUE HALF IS PINNED -- the clause's load-bearing phrases, so a "fix"
   that softens the disclosure to agree with a claim fails.

4. ONE STRING -- the clause is present VERBATIM on every rendered page that
   carries it and in the README and docs copies that cannot interpolate it,
   and no ``.py`` outside ``_disclosure`` retypes it.

WHAT IS DELIBERATELY OUT OF SCOPE
=================================

* ``CHANGELOG.md`` -- a dated record whose entries quote withdrawn wording by
  design, including the 1.7.2 entry that records these very phrases.
* ``tests/`` source -- tests quote the forbidden phrases in order to forbid
  them. The rendered baselines under ``tests/`` ARE scanned: they are output.
* Identifiers -- ``WINNER_DISTRESS_PATTERNS``, ``compare_to_winners``,
  ``winner_p75`` keys. Renaming public API is a minor release, and a name is
  not a sentence; the constants' own comments now say what they are.
"""
from __future__ import annotations

import ast
import os
import re
from pathlib import Path

import pytest

from nmtcapp.renderers._disclosure import (
    ASSUMED_WINNER_PATTERNS,
    ASSUMED_WINNER_PATTERNS_CLAUSE,
)
# Imported at MODULE level for its side effect: it puts the repo root and
# streamlit_app/ on sys.path. A test that does `import utils` before this has
# run fails when selected on its own (fix round 1, X2) -- in a full run some
# other module had already imported it, which is how that stayed hidden.
import tests.streamlit_render  # noqa: E402,F401

_REPO_ROOT = Path(__file__).resolve().parent.parent

#: RULE 1. Each pattern is one spelling of "these figures were measured from
#: past winners". ``\W+`` spans newlines and ``#``, so a claim hard-wrapped
#: across two lines of a docs page or a comment is still one match. A word
#: token is ``\w+(?:[–-]\w+)*`` -- hyphens only INSIDE a word -- because
#: ``[\w–-]+\W+`` lets both halves claim a dash and backtracks exponentially
#: on a ``# -----`` ruler (measured: 121 s on one page module).
_W = r"\w+(?:[–-]\w+)*"          # one word token; hyphens only inside a word
_GAP = rf"(?:{_W}\W+)"            # a token and what follows it

#: The nouns of a PAST-WINNER POPULATION. Plural only for allocatees and
#: recipients: "any prior Allocatee that requires action by the CDFI Fund" is
#: the NOAA's term of art for one entity, not a population.
_NON = r"(?<!non-)(?<!non )(?<!non)"
_POP = (rf"(?:{_NON}winners|awardees|allocatees|(?:award|allocation)\W+recipients|"
        r"selected\W+cdes|top[- ]ranked\W+cdes)")
#: The words that make a population noun a STATISTICAL claim about it.
_STAT = (r"(?:patterns?|profiles?|statistics|distributions?|averages?|data|"
         r"medians?|means?|percentiles?|benchmarks?|figures?|norms?|shares?|"
         r"concentrations?|mix)")
#: Verbs whose subject, when it is a winner population, makes the sentence a
#: measurement claim: "Winners consistently exceed ...", "Award winners
#: concentrate ...", "Winning CDEs typically deploy ...". An adverb may sit
#: between (fix round 2).
_ADVERB = (r"(?:consistently|typically|usually|generally|often|tend\w*\W+to|"
           r"rarely|always|mostly|overwhelmingly|historically|on\W+average|all|also)")
_CLAIM_VERB = (r"(?:exceed|average|concentrat|score|cluster|show|outperform|"
               r"deploy|serve|target|favou?r|draw|place|put|hold|reach|carry|"
               r"invest|allocate|commit|finance|fund|request|receive|report|"
               r"achieve|have|had|are|were|look|resembl|mirror|sit|fall|land|"
               r"rang|spread|span|focus|prioriti[sz]|emphasi[sz]|clear|meet|"
               r"beat|top|lead|dominat)\w*")

#: fix round 3. Allocatee-population nouns, singular admitted (the statistic
#: word beside it is what makes the claim), and the words that make them one.
_ALLOC = (r"(?:allocatees?|awardees?|(?:award|allocation)\W+recipients?|"
          r"recipients\W+of\W+(?:nmtc\W+)?(?:allocations?|awards?))")
_STATW = (r"(?:averag\w*|medians?|means?|typical\w*|exceed\w*|quartiles?|"
          r"deciles?|percentiles?|p\d\d|track(?:s|ed|ing)?\b(?!\W+records?)|"
          r"concentrat\w*|\d+(?:\.\d+)?\s?%)")
#: "data", "distribution", "population" are NOT statistic words on their own:
#: "the Fund does publish Allocatee-level deployment data" and "Per-Allocatee
#: distributions ARE published" are true. They count only after a past /
#: CY qualifier: "historical allocatee data", "CY2020-2024 allocatee data".
_PAST_Q = r"(?:historical|past|prior|previous|recent|cy\s?\d{4}(?:[–-]\d{2,4})?)"
#: one token and what follows it, WITHOUT crossing ; : . ! ?
#: A negation inside the gap breaks the link: "not a distribution of past
#: Allocatees and not percentiles of anything published" pairs nothing.
_CGAP = rf"(?:(?!(?:not|no|never|nor)\b){_W}[^\w;:.!?]+)"

FORBIDDEN = {
    "historical-winners": re.compile(rf"historical\W+{_GAP}{{0,3}}?winn\w*", re.I),
    "observed-in-winners": re.compile(rf"observed\W+in\W+{_GAP}{{0,6}}?winn\w*", re.I),
    "measured-from-awardees": re.compile(
        rf"measured\W+(?:from|on|across|among)\W+{_GAP}{{0,4}}?"
        r"(?:winn|award|allocatee|recipient)\w*", re.I),
    "trained-on-winner-data": re.compile(
        rf"trained\W+on\W+{_GAP}{{0,4}}?winn\w*"
        r"|(?<!non-)(?<!non )\bwinn(?:er|ing)\W+data\b", re.I),
    # Narrowed to claim contexts: "prior award data" is the CDE's OWN history
    # (tables/track_record_table) and is not a claim about winners.
    "award-data": re.compile(
        rf"(?:years?\W+of|cdfi\W+fund|historical|past|winner|based\W+on|"
        # fix round 3: the derivation verbs. NOT "use(s)": "The bands use no
        # award data" is a denial whose "no" governs the match.
        rf"drawn\W+from|derived\W+from|comes?\W+from|came\W+from|calibrated\W+on|"
        rf"built\W+on)\W+{_GAP}{{0,2}}?award\W+data\b", re.I),
    "typical-winner": re.compile(
        r"typical\W+(?:winn\w*|awardees?|allocatees?|recipients?)", re.I),
    "what-winners-did": re.compile(
        rf"\bwhat\W+{_GAP}{{0,2}}?(?:winners|awardees|allocatees|recipients|"
        r"award[- ]winning)\b", re.I),
    "winning-applications": re.compile(r"winning\W+applications?\b", re.I),
    # fix round 2: "Winning CDEs typically ...".
    "winning-entities": re.compile(
        rf"{_NON}\bwinning\W+(?:cdes?|applicants?|entities|organi[sz]ations|allocatees|"
        r"community\W+development\W+entities)\b", re.I),
    "award-winning": re.compile(r"\baward[- ]winning\b", re.I),
    # fix round 2: awardees, allocatees and award/allocation recipients are
    # flagged ONLY in a claim context -- a statistic of them, a comparison
    # with them, a population "across"/"among" them, a possessive, or a
    # past/prior/recent qualifier on the plural. "The CDFI Fund publishes
    # award recipients each round" is a true statement and passes; the bare
    # ``award recipients`` alternative that flagged it is gone.
    "population-statistic": re.compile(
        rf"\b{_STAT}\W+(?:of|from|across|among|for)\W+{_GAP}{{0,3}}?{_POP}\b"
        # "across"/"among" for WINNERS only: "realized deployment across
        # Allocatees" and "a program-level goal across all Allocatees" are true
        # statements about what the Fund publishes and requires.
        rf"|\b(?:across|among|of\W+all)\W+{_GAP}{{0,2}}?{_NON}winners\b"
        rf"|\b(?:mirror\w*|resembl\w*|match\w*|track\w*|reflect\w*|like|"
        rf"compar\w*|vs\b\.?|versus|against|relative\W+to|drawn\W+from|"
        rf"derived\W+from|based\W+on|calibrated\W+(?:on|to|against))\W+"
        rf"{_GAP}{{0,3}}?(?:awardees|allocatees|(?:award|allocation)\W+recipients|"
        rf"selected\W+cdes|top[- ]ranked\W+cdes)\b"
        r"|\b(?:awardees|allocatees|recipients)['’]", re.I),
    "successful-applicants": re.compile(
        rf"\bsuccessful\W+{_GAP}{{0,2}}?applicants?\b", re.I),
    "possessive-winners": re.compile(r"\bwinners['’]", re.I),
    # fix round 2: the bare ``award(s)`` alternative is DROPPED -- "Enter the
    # CDE's past NMTC awards in the track record table", "List your most
    # recent award", "Section E lists the CDE's recent awards" are the CDE's
    # own history. Winners always; awardees/allocatees/recipients as a
    # plural population, including "prior-round allocatees".
    "past-winners": re.compile(
        rf"\b(?:past|prior|previous|recent|historical|earlier)\W+{_GAP}{{0,3}}?winn\w*"
        # Bare "prior" is NOT here for allocatees: "[prior Allocatees]" is the
        # NOAA's own audience label on Table 1 deadlines, rendered verbatim.
        # "prior-round allocatees" is.
        rf"|\b(?:past|previous|recent|historical|earlier|prior[- ]rounds?)\W+"
        rf"{_GAP}{{0,3}}?(?:awardees|allocatees|(?:award|allocation)\W+recipients)\b"
        rf"|\bprior\W+{_GAP}{{0,3}}?(?:awardees|(?:award|allocation)\W+recipients)\b",
        re.I),
    "versus-winners": re.compile(
        rf"(?:\bvs\b\.?|versus|against|compar\w*|relative\W+to|favou?rably\W+with)"
        rf"\W+{_GAP}{{0,3}}?winners?\b(?![- ](?:patterns?|benchmarks?|"
        r"distributions?|figures?|statistics|profiles?|bands?|heuristics?|"
        r"thresholds?))", re.I),
    # fix round 2: a statistic OF a winner population, spelled as a noun
    # phrase: "the winner p75", "the winner median", "winner mean".
    "winner-statistic": re.compile(
        r"(?<!non-)\bwinners?[- ](?:p\d\d|median|mean|average|percentile|"
        r"quartile|decile)s?\b", re.I),
    # fix round 2: a winner population as the SUBJECT of a measurement verb.
    "winners-as-subject": re.compile(
        rf"{_NON}\b(?:award\W+)?winners\W+(?:{_ADVERB}\W+)?{_CLAIM_VERB}\b", re.I),
    # fix round 2: the Fund's award books or its Public Data Release named as
    # the CALIBRATION SOURCE of a band or threshold. Naming the release as
    # the Fund's real series (historical_awards.py) is not this.
    # "avg_award ... computed from the Award Book" is a round-level table
    # statistic, not a band, and passes: a derivation verb counts only with a
    # band-like noun before it; "calibrated" is band-like by itself.
    "calibration-source": re.compile(
        rf"(?:calibrat\w*|benchmarked)\W+(?:on|from|against|using|with|to|by)\W+"
        rf"{_GAP}{{0,3}}?(?:award\W+books?|public\W+data\W+release)\b"
        rf"|\b(?:bands?|thresholds?|benchmarks?|cut\W+points?|medians?|"
        rf"percentiles?|patterns?|figures?|numbers|values|scores|statistics)\W+"
        rf"{_GAP}{{0,2}}?(?:derived|drawn|taken|measured|built|based|sourced|"
        rf"computed|set|fitted|estimated|come|comes|came|pulled)\W+(?:on|from|"
        rf"against|using|with|to|by)\W+{_GAP}{{0,3}}?(?:award\W+books?|public\W+"
        rf"data\W+release)\b"
        rf"|\b(?:bands?|thresholds?|benchmarks?|cut\W+points?|medians?|"
        rf"percentiles?)\W+(?:from|per|using|off)\W+{_GAP}{{0,3}}?(?:award\W+"
        r"books?|public\W+data\W+release)\b", re.I),
    # fix round 2: "top-ranked / selected CDEs from prior rounds".
    "prior-round-cdes": re.compile(
        rf"\b(?:top[- ]ranked|selected|successful|funded|awarded|winning|"
        rf"high[- ]scoring)\W+(?:cdes?|applicants?|applications?|entities)\W+"
        rf"(?:from|in|of)\W+{_GAP}{{0,2}}?(?:prior|past|previous|recent|earlier)"
        r"\W+rounds?\b"
        r"|\btop[- ]ranked\W+(?:cdes?|applicants?|applications?)\b", re.I),
    # fix round 3: a STATISTIC WORD within 3 tokens of an allocatee /
    # awardee / recipient noun, in either order, inside one clause (a comma
    # or a parenthesis does not end it; ; : . ! ? do). Singular counts here
    # ("historical allocatee data", "the Allocatee population"), because the
    # statistic word is what makes it a claim. What keeps passing: the NOAA
    # label "[prior Allocatees]" (no statistic word near it, and a semicolon
    # after it), "a program-level goal across all Allocatees" (the 20% is six
    # tokens away), and "track record" (not a statistic).
    "allocatee-statistic": re.compile(
        rf"\b{_ALLOC}\b[^\w;:.!?]+{_CGAP}{{0,3}}?{_STATW}"
        rf"|{_STATW}[^\w;:.!?]+{_CGAP}{{0,3}}?{_ALLOC}\b"
        rf"|\b{_PAST_Q}\W+{_CGAP}{{0,1}}?{_ALLOC}\W+(?:data|distributions?|"
        r"populations?|statistics|figures)\b", re.I),
    # fix round 3: a selected population with a statistic or measurement
    # verb: "Winning pipelines average 7 states", "Funded applications
    # average", "awarded CDEs exceed this floor".
    "selected-population-statistic": re.compile(
        rf"{_NON}\b(?:winning|funded|awarded|selected|successful|top[- ]ranked)\W+"
        # not "projects": "the selected projects must span" is the
        # optimizer's own selection
        rf"(?:cdes?|applicants?|applications?|pipelines?|entities)\W+"
        rf"{_CGAP}{{0,2}}?(?:{_STATW}|{_CLAIM_VERB})", re.I),
    # fix round 3: figures derived from awards qualified as real / past:
    # "Figures drawn from actual NMTC awards". The CDE's own "past NMTC
    # awards" in a track-record instruction carries no derivation verb.
    "derived-from-awards": re.compile(
        rf"\b(?:drawn|derived|taken|measured|calibrated|sourced|built|inferred|"
        rf"computed|estimated)\W+(?:from|on)\W+{_GAP}{{0,2}}?(?:actual|real|past|"
        rf"prior|previous|historical|published|recent)\W+{_GAP}{{0,2}}?awards\b", re.I),
}

#: A match is a DENIAL, not a claim, only when a negation DIRECTLY GOVERNS it
#: (fix round 2): "not"/"no"/"never" immediately before the match or its
#: determiner ("not past winners", "no winner data"), or before a denial
#: head that takes the match as its object ("not measurements of past
#: winners", "not a percentile of past winners", "No corpus of winning
#: applications", "not derived from past winners"). Fix round 1 accepted a
#: negation ANYWHERE in the 4 tokens before the match, so "It is no secret
#: that past winners averaged 80%" and "Scores are never far from successful
#: NMTC applicants" were excused -- "no" governs "secret", "never" governs
#: "far". The head list is the list of nouns and participles whose negation
#: denies the measurement; a new one is a gate edit, reviewed like any other.
_DET = r"(?:a|an|the|any|its|their|this|these|those|such)"
_DENIAL_HEAD = (
    r"(?:measurements?|measures?|percentiles?|samples?|corpus|corpora|records?|"
    r"data|figures?|averages?|medians?|statistics?|surveys?|counts?|"
    r"distributions?|populations?|lists?|set|dataset|study|studies|"
    r"derived|drawn|taken|inferred|measured|computed|sourced|calibrated|"
    r"sampled|based|estimated|fitted)")
#: The negation, optionally with the one verb it negates when that verb's
#: object IS the match -- "does not publish application-level data for
#: winners", "holds no sector distribution for past Allocatees", "has never
#: been compared to a winner-population".
_NEG = (r"\b(?:not|no|never|nor)\b(?:\W+(?:publish|hold|carr|contain|use|load|"
        r"ha[sv]e?|compute|include|ship|embed|read|been|be)\w*)?")
#: Modifiers allowed between the negation and what it governs: hyphenated
#: compounds and a closed list of attributive words. NOT an arbitrary token:
#: "no secret that past winners" must not reach "past winners" through
#: "secret that".
_MOD = (r"(?:(?:\w+(?:-\w+)+|sector|project|pipeline|application|applicant|"
        r"public|published|measured|such|other|real|actual|any|either)\W+)")
_GOVERNED = re.compile(
    rf"{_NEG}\W+(?:{_DET}\W+)?{_MOD}{{0,2}}"
    rf"(?:{_DENIAL_HEAD}\W+(?:of|from|on|across|among|about|by|for|in|to|with)\W+"
    rf"(?:{_DET}\W+)?{_MOD}{{0,2}}){{0,2}}$", re.I)
_CLAUSE_BREAK = re.compile(r"[;:.!?—–()\[\]]")
#: Every rule is deniable except the ones whose words cannot be a denial:
#: "historical ... winners", "observed in ... winners", "trained on".
_DENIABLE = set(FORBIDDEN) - {"historical-winners", "observed-in-winners",
                              "trained-on-winner-data"}

#: RULE 2. The nouns of the claim, and the qualifier that must BIND to them:
#: within ``_QUALIFIER_WINDOW`` tokens before or after the noun, in the same
#: sentence. The first cut accepted a qualifier anywhere in the sentence, so
#: "winner patterns show strong CDEs win; this tool's own view differs" passed.
WINNER_NOUN = re.compile(
    r"(?<!non-)\bwinners?[- ](?:patterns?|benchmarks?|distributions?|figures?|"
    r"statistics|profiles?|bands?|heuristics?|thresholds?)\b", re.I)
QUALIFIER = re.compile(
    r"assumed|\bhouse\b|this tool'?s(?: own)?|this package'?s(?: own)?|"
    r"unsourced|not measurements?|\bno winner|\bnot (?:a|against|derived|"
    r"inferred)\b|never|does not exist", re.I)
_QUALIFIER_WINDOW = 6
_QUALIFIER_CLAUSE_BREAK = re.compile(r"[;:.!?—–]")

#: The provenance clause's load-bearing phrases (RULE 3).
CLAUSE_ANCHORS = (
    "this tool's own assumed winner patterns",
    "unsourced house constants",
    "not measurements of past winners",
    "not a CDFI Fund publication",
)

#: RECORDS -- source lines that QUOTE a withdrawn phrase in order to record
#: that it was withdrawn. ``(path, fragment of that line, why)``. Each must
#: match exactly one line that rule 1 or rule 2 flags; a record that matches
#: nothing is dead and fails. Rendered text can never be a record.
RECORDS = (
    ("nmtcapp/data/historical_awards.py", '"HISTORICAL NMTC WINNERS". They feed',
     "1.2.0's module docstring recording the grep it ran over rendered output"),
    ("nmtcapp/data/historical_awards.py", 'announcements. The "typical winner" patterns below',
     "1.7.2's correction to the data-quality note, naming the phrase it corrects"),
    ("nmtcapp/intelligence/benchmarks.py", '1.5.0: "Compare a pipeline analysis result against historical NMTC winner',
     "the module docstring quoting the summary 1.5.0 withdrew"),
    ("nmtcapp/renderers/_disclosure.py", "historical winners, NOT PROBABILITY OF SELECTION. Use as diagnostic",
     "wrap_disclosure's docstring quoting the truncated disclosure 1.3.1 fixed"),
    ("nmtcapp/renderers/_disclosure.py", "#: Optimizer's subtitle (\"maximizes composite alignment with historical NMTC",
     "the clause's own history, quoting page 3's struck subtitle"),
    ("nmtcapp/renderers/_disclosure.py", '#: application against historical winner patterns") and the Pipeline',
     "the clause's own history, quoting Home's struck sentence"),
    ("nmtcapp/renderers/_disclosure.py", '#: Notice ("patterns observed in historical NMTC award winners"), the',
     "the clause's own history, quoting page 2's struck notice"),
    ("nmtcapp/optimizer/pipeline_optimizer.py", '# "Objective: maximize composite alignment score with historical NMTC winner',
     "the comment recording the methodology note 1.7.2 corrected"),
    ("nmtcapp/visualization/maps.py", '#: ("Application vs. Historical Winner Patterns"), one function over. The',
     "the sector-mix title comment citing B3's precedent"),
    ("nmtcapp/visualization/maps.py", '# THE TITLE SAID "Application vs. Historical Winner Patterns" (B3). It',
     "B3's own record of the suptitle it corrected"),
    ("streamlit_app/app.py", '# "Trained on CY2020-2024 winner data" was withdrawn in 1.2.0. Nothing',
     "the stats-bar comment recording 1.2.0's withdrawal"),
    ("streamlit_app/app.py", '# "observed in historical NMTC award winners" asserted an empirical',
     "the disclosure comment recording the phrase the disclosure replaced"),
    ("streamlit_app/app.py", '# WAS "Score your application\'s alignment with patterns in historical',
     "the feature-card comment recording 1.7.2's correction"),
    ("streamlit_app/pages/3_Pipeline_Optimizer.py", '# WAS "maximizes composite alignment with historical NMTC winner patterns"',
     "the subtitle comment recording 1.7.2's correction"),
    ("streamlit_app/pages/1_Pipeline_Analyzer.py", 'A number a CDE reads as "what winners do" is a',
     "B3's comment explaining why 'Winner' was deleted from two labels"),
    ("streamlit_app/pages/1_Pipeline_Analyzer.py", '# WITHDRAWN IN 1.2.0. This chart used to read "Benchmarks vs. historical',
     "1.2.0's record of the chart title it withdrew"),
    ("streamlit_app/utils.py", 'OBSERVED IN HISTORICAL NMTC AWARD WINNERS (CY2020–CY2024)" (1.7.2 F2). That',
     "render_methodology_warning's docstring recording the notice it replaced"),
    ("docs/workflow/pipeline-analysis.md", 'typical winner patterns" for C and "Application not viable in current form" for',
     "the correction note quoting the grade labels 1.5.x withdrew"),
    ("docs/about/why.md", 'computes "the winner distribution" for those four dimensions',
     "the 1.5.1 correction note quoting the paragraph it corrected"),
    ("docs/quickstart.md", 'This passage said the engine "benchmarks each dimension against historical',
     "the 1.5.1 note quoting the passage it withdrew"),
    # -- added with the widened spellings (fix round 1, P8/X4). Quotes of
    #    withdrawn wording, and uses of the words that are not the claim.
    ("nmtcapp/renderers/_question_22.py", 'a benchmark row scored against a "winner',
     "the docstring recording the benchmark row 1.4.0 deleted"),
    ("streamlit_app/pages/1_Pipeline_Analyzer.py", "The CDFI Fund publishes winner-level award data",
     "a true statement about what the Fund publishes, in the comment explaining why no winner distribution exists"),
    ("docs/workflow/recommendations.md", "Both are claims about what past Allocatees did, this package holds no such",
     "the correction note naming the withdrawn claims as claims"),
    ("docs/workflow/recommendations.md", 'targets "derived from the winner distribution"',
     "the 1.5.1 warning quoting the engine the page used to describe"),
    ("docs/workflow/visualizations.md", 'that the dashed line was a **"Winner Benchmark"** at **75**',
     "the 1.5.1 warning quoting the label it corrected"),
    ("docs/workflow/visualizations.md", '"Winner Benchmark" attributes the line to a population of past Allocatees this package has never held',
     "the same warning, explaining why the label was false"),
    ("docs/workflow/visualizations.md", "calling it a winner benchmark traded a sourced threshold for an unsourced one",
     "the same warning, naming the mislabel it corrected"),
    ("docs/workflow/visualizations.md", '"shows exactly where you stand relative to the winner distribution"',
     "the correction note quoting the paragraph it replaced"),
    ("docs/reference/data-sources.md", '*"to infer winner distributions"*',
     "the 1.5.1 correction quoting the claim it withdrew"),
    ("nmtcapp/data/benchmark_thresholds.py", '"90%" strings in the Review Process are 16.90% of awardees',
     "a Review Process statistic about actual awardees, quoted to rule out a threshold -- a federal figure, not a winner pattern (re-listed in fix round 3)"),
    # -- added with fix round 2's spellings (winner p25/median/mean, winners
    #    as the subject of a measurement verb, past Allocatees). Each is a
    #    quote of withdrawn wording or a denial whose negation does not sit
    #    directly on the phrase; each was read in context before listing.
    ('nmtcapp/data/historical_awards.py', 'of them asserting measurements of winners ("Winners consistently exceed this',
     'the module docstring quoting the struck distress source line, as struck'),
    ('nmtcapp/data/historical_awards.py', '"winners rarely exceed 35%"). 1.7.2 struck them',
     'the module docstring quoting the struck sector field comment, as struck'),
    ('nmtcapp/intelligence/benchmarks.py', '#   3. THE WINNER MEAN IS A COMPLEMENT TOO.',
     'a maintainer comment naming the house constant rural_pct_mean by its old label while showing it is not a measurement'),
    ('nmtcapp/visualization/maps.py', '# RELABELLED (B3). These read "Winner P25 / Winner P50 (Median) /',
     "B3's record of the bar labels it removed"),
    ('nmtcapp/visualization/maps.py', '# Winner P75" until this change. All nine values are HOUSE constants;',
     "the second line of B3's record of the bar labels it removed"),
    ('nmtcapp/visualization/maps.py', '#     "Winners typically have >=50% in high-priority sectors',
     'the comment quoting the chart annotation it deleted'),
    ('streamlit_app/pages/1_Pipeline_Analyzer.py', '#: median states" and "Winner mean HHI" with nothing on the screen saying whose',
     'the caption comment quoting the two geographic labels B3 removed'),
    ('streamlit_app/pages/1_Pipeline_Analyzer.py', '# labelled "Winner p25 / Winner median / Winner p75", with a green/red',
     'the comment recording the delta labels 1.4.0 removed'),
    ('streamlit_app/pages/1_Pipeline_Analyzer.py', '# median states: **7**", "Winner mean HHI: **620**" and "Winner rural',
     "1.4.0 R5's record of the three hand-typed literals it removed"),
    ('streamlit_app/pages/1_Pipeline_Analyzer.py', '# scored. Until this change these lines read "Winner median states: 7"',
     "B3's record of the label wording it deleted"),
    ('streamlit_app/pages/1_Pipeline_Analyzer.py', '# and "Winner mean HHI: 620". Both numbers are HOUSE constants of',
     "the second line of B3's record of the deleted label wording"),
    ('streamlit_app/pages/1_Pipeline_Analyzer.py', '# values under the labels "Winner p25 / Winner median / Winner p75 /',
     'the comment quoting the chart labels it replaced'),
    ('streamlit_app/pages/1_Pipeline_Analyzer.py', '# Winner top 10%" — a claim about a POPULATION OF PAST ALLOCATEES,',
     'the same comment naming the replaced labels as a population claim with no population behind it'),
    ('streamlit_app/pages/1_Pipeline_Analyzer.py', '# NUMBERS. Re-deriving what a winner percentile actually is would be',
     'a maintainer comment saying a real winner percentile would need a source the package lacks'),
    ('docs/about/why.md', 'distress concentration is 72%, which is at the winner p25. Raising it to 82%',
     'the 1.5.1 correction note quoting the example it withdrew'),
    ('docs/about/why.md', '(winner median) is estimated to add 8–15 alignment score points.',
     'the second line of the 1.5.1 quote of the withdrawn example'),
    ('docs/quickstart.md', 'winners" and could recommend "lifting project count to winner median" or',
     'the 1.5.1 note quoting the passage it withdrew (second line)'),
    ('docs/workflow/optimization.md', 'They read `# winner median is 13`, `# above winner p25 of 4 states` and',
     'the 1.5.1 warning quoting the constraint comments it corrected'),
    ('docs/workflow/optimization.md', '`# above the winner p25 floor`. **No such medians or percentiles exist.**',
     "the same warning's third quote, followed by its denial"),
    ('docs/workflow/recommendations.md', 'winner distribution", advice to "reach at least the winner p25 of 4 states,',
     'the warning quoting the advice of an engine that does not exist'),
    ('docs/workflow/recommendations.md', '1. **It was a winner-population claim.** `p25`, `winner median`, "gaps that',
     'the correction note naming the withdrawn claim as a claim'),
    ('docs/workflow/recommendations.md', 'in this tool has ever been compared to a population of past Allocatees.',
     "a denial ('no score in this tool has ever been compared') whose negation governs the subject, not the phrase"),
    ('docs/workflow/recommendations.md', 'category the engine cannot emit, a "winner median of 82%" it does not hold, and',
     'the note describing the fabricated block it replaced'),
    ('docs/workflow/recommendations.md', '> The goal is to reach at least the winner p25 of 4 states, ideally 7+ states.',
     "the blockquote of the withdrawn paragraph, introduced as 'The paragraph that stood here read'"),
    ('docs/workflow/visualizations.md', 'to a population of past Allocatees this package has never held. The line it',
     "a denial whose negation ('has never held') follows the phrase"),
    ('docs/workflow/visualizations.md', 'The bar labels said `Winner P25 / Winner P50 (Median) / Winner P75` on the',
     'the page recording the bar labels an earlier round relabelled'),
    ('docs/workflow/visualizations.md', 'winner percentiles afterwards. **All nine values are `HOUSE` constants**',
     'the same record: the page kept the old name after the relabel, and says the values are house'),
    ('docs/workflow/visualizations.md', '**Reference annotation:** none. The chart carried a note reading *"Winners',
     'the page quoting the chart annotation that was deleted'),
)

#: Surfaces that must carry the clause VERBATIM (RULE 4). EVERY PAGE, counted
#: from the directory, unless classified here with the reason it does not --
#: a hand-typed list of disclosing pages is the enumeration F4 replaced.
CLAUSE_EXEMPT_PAGES = {
    "pages/1_Pipeline_Analyzer.py": (
        "Its two house-winner figures state their own provenance where they "
        "render -- the distress chart's caption (this tool's own screening "
        "band, not a percentile of past winners) and the jobs-per-QEI caption "
        "(WINNER_IMPACT_BENCHMARKS, this tool's own unsourced figures, not "
        "percentiles of any measured population) -- and rule 2 holds every "
        "sentence on the page to that; it renders no alignment score."
    ),
}
CLAUSE_FILES = ("README.md",)
CLAUSE_CHECKOUT_FILES = (
    "docs/about/limitations.md",
    "docs/workflow/optimization.md",
    "docs/reference/api.md",
)


# ---------------------------------------------------------------------------
# The corpus
# ---------------------------------------------------------------------------

def _is_checkout() -> bool:
    """mkdocs.yml is the checkout marker the fund-attribution gate uses: the
    sdist ships neither it nor docs/, so their joint absence is the sdist."""
    return (_REPO_ROOT / "mkdocs.yml").is_file()


def _package_root() -> Path:
    import nmtcapp
    return Path(os.path.abspath(nmtcapp.__file__)).parent


def _source_files() -> dict:
    """``{display path: Path}`` for every source file rule 1 reads."""
    files = {}
    pkg = _package_root()
    for path in sorted(pkg.rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        files["nmtcapp/" + path.relative_to(pkg).as_posix()] = path
    app = _REPO_ROOT / "streamlit_app"
    for path in sorted(app.rglob("*")):
        if path.suffix in (".py", ".md", ".txt") and "__pycache__" not in path.parts:
            files[path.relative_to(_REPO_ROOT).as_posix()] = path
    for name in ("README.md", "pyproject.toml"):
        files[name] = _REPO_ROOT / name
    if _is_checkout():
        docs = _REPO_ROOT / "docs"
        assert docs.is_dir(), (
            "mkdocs.yml is present but docs/ is not: a checkout with its docs "
            "tree deleted, which is the state in which a walk scans nothing"
        )
        for root in (docs, _REPO_ROOT / "examples", _REPO_ROOT / "scripts"):
            for path in sorted(root.rglob("*")):
                if path.suffix in (".md", ".py", ".ipynb", ".yml", ".sh") and path.is_file():
                    files[path.relative_to(_REPO_ROOT).as_posix()] = path
        for name in ("mkdocs.yml", "CONTRIBUTING.md", "CITATION.cff"):
            files[name] = _REPO_ROOT / name
    for shown, path in files.items():
        assert path.is_file(), f"{shown} is missing -- the scan would read nothing there"
    return files


def _baseline_files() -> dict:
    out = {}
    for sub in ("rendered_baseline", "cli_baseline"):
        for path in sorted((_REPO_ROOT / "tests" / sub).glob("*.txt")):
            out[f"tests/{sub}/{path.name}"] = path
    return out


def _rendered_units() -> list:
    """``[(location, text)]`` -- one unit per prose element per page state."""
    from tests.streamlit_render import rendered_pages, texts

    units = []
    for rel, states in rendered_pages().items():
        for state in ("cold", "driven"):
            at = states[state]
            assert not at.exception, f"{rel} ({state}) raised: {at.exception}"
            for i, (kind, text) in enumerate(texts(at)):
                units.append((f"rendered:{rel}:{state}:{kind}#{i}", text))
    return units


# ---------------------------------------------------------------------------
# The two rules
# ---------------------------------------------------------------------------

def _line_at(text: str, offset: int):
    start = text.rfind("\n", 0, offset) + 1
    end = text.find("\n", offset)
    return text.count("\n", 0, offset) + 1, text[start:end if end >= 0 else None]


def _denied(text: str, match) -> bool:
    """True only when a negation directly governs the match (see _GOVERNED).
    Reads the 80 characters before it, within the clause."""
    clause = _CLAUSE_BREAK.split(text[max(0, match.start() - 80):match.start()])[-1]
    return bool(_GOVERNED.search(clause))


def forbidden_hits(text: str) -> list:
    """``[(rule, offset, matched text)]`` for every rule-1 claim in ``text``."""
    hits = []
    for rule, pattern in FORBIDDEN.items():
        for m in pattern.finditer(text):
            if rule in _DENIABLE and _denied(text, m):
                continue
            hits.append((rule, m.start(), m.group(0)))
    return hits


_SENTENCE = re.compile(r"(?<=[.!?])\s+(?=[A-Z*_`>\"'(])")


def unqualified_sentences(text: str) -> list:
    """Sentences naming a winner-pattern noun with no qualifier (rule 2)."""
    flat = re.sub(r"`[^`]*`", " ", text)        # identifiers are not prose
    flat = re.sub(r"\s+", " ", flat)
    out = []
    for sentence in _SENTENCE.split(flat):
        for m in WINNER_NOUN.finditer(sentence):
            # Same CLAUSE as well as within the token window: a qualifier
            # across a semicolon or a dash qualifies a different claim.
            # Parentheses do NOT break this window: "assumed (house) winner
            # patterns" binds its qualifier. A semicolon, colon or dash does.
            left = _QUALIFIER_CLAUSE_BREAK.split(sentence[:m.start()])[-1]
            right = _QUALIFIER_CLAUSE_BREAK.split(sentence[m.end():])[0]
            before = re.findall(r"\S+", left)[-_QUALIFIER_WINDOW:]
            after = re.findall(r"\S+", right)[:_QUALIFIER_WINDOW]
            window = " ".join(before + [m.group(0)] + after)
            if not QUALIFIER.search(window):
                out.append(sentence)
                break
    return out


#: Names whose interpolation into an f-string IS the qualifier. An f-string
#: is reconstructed with these substituted by their values, so
#: ``f"those are {ASSUMED_WINNER_PATTERNS_CLAUSE}."`` is read as the sentence
#: it renders. Any other interpolation becomes a neutral placeholder.
_QUALIFYING_NAMES = {
    "ASSUMED_WINNER_PATTERNS": ASSUMED_WINNER_PATTERNS,
    "ASSUMED_WINNER_PATTERNS_CLAUSE": ASSUMED_WINNER_PATTERNS_CLAUSE,
}


def _string_literals(path: Path) -> list:
    """``[(lineno, text)]`` for every string literal (docstrings included),
    with f-strings reconstructed as one unit rather than read in pieces."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    out, consumed = [], set()
    for node in ast.walk(tree):
        if isinstance(node, ast.JoinedStr):
            parts = []
            for value in node.values:
                consumed.add(id(value))
                if isinstance(value, ast.Constant):
                    parts.append(str(value.value))
                elif (isinstance(value, ast.FormattedValue)
                      and isinstance(value.value, ast.Name)
                      and value.value.id in _QUALIFYING_NAMES):
                    parts.append(_QUALIFYING_NAMES[value.value.id])
                else:
                    parts.append("<value>")
            out.append((node.lineno, "".join(parts)))
    for node in ast.walk(tree):
        if (isinstance(node, ast.Constant) and isinstance(node.value, str)
                and id(node) not in consumed):
            out.append((node.lineno, node.value))
    return out


def _prose_units(files: dict) -> list:
    """``[(display path, lineno, text)]`` units rule 2 reads from source."""
    units = []
    for shown, path in files.items():
        if path.suffix == ".py":
            units.extend((shown, ln, s) for ln, s in _string_literals(path))
        elif path.suffix in (".md", ".ipynb"):
            units.append((shown, 1, path.read_text(encoding="utf-8")))
    return units


@pytest.fixture(scope="module")
def corpus():
    return {
        "source": _source_files(),
        "baselines": _baseline_files(),
        "rendered": _rendered_units(),
    }


def _flagged(corpus) -> list:
    """Every flagged line: ``(where, line, detail, excusable)``."""
    flagged = []
    for shown, path in corpus["source"].items():
        text = path.read_text(encoding="utf-8")
        seen = set()
        for rule, offset, matched in forbidden_hits(text):
            lineno, line = _line_at(text, offset)
            if lineno in seen:
                continue
            seen.add(lineno)
            flagged.append((f"{shown}:{lineno}", line.strip(), f"{rule}: {matched!r}", True))
    for shown, lineno, text in _prose_units(corpus["source"]):
        for sentence in unqualified_sentences(text):
            flagged.append((f"{shown}:{lineno}", sentence.strip(),
                            "unqualified winner noun", True))
    for shown, path in corpus["baselines"].items():
        text = path.read_text(encoding="utf-8")
        for rule, offset, matched in forbidden_hits(text):
            lineno, line = _line_at(text, offset)
            flagged.append((f"{shown}:{lineno}", line.strip(), f"{rule}: {matched!r}", False))
        for sentence in unqualified_sentences(text):
            flagged.append((shown, sentence, "unqualified winner noun", False))
    for where, text in corpus["rendered"]:
        for rule, offset, matched in forbidden_hits(text):
            flagged.append((where, _line_at(text, offset)[1].strip(), f"{rule}: {matched!r}", False))
        for sentence in unqualified_sentences(text):
            flagged.append((where, sentence, "unqualified winner noun", False))
    return flagged


def _record_for(where: str, line: str):
    path = where.rsplit(":", 1)[0]
    for rec_path, fragment, _why in RECORDS:
        if rec_path == path and fragment in line:
            return (rec_path, fragment)
    # rule-2 sentences are whitespace-flattened; compare flattened too
    flat_line = re.sub(r"\s+", " ", line)
    for rec_path, fragment, _why in RECORDS:
        if rec_path == path and re.sub(r"\s+", " ", fragment) in flat_line:
            return (rec_path, fragment)
    return None


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_the_scan_reads_what_it_claims_to(corpus):
    """Anti-vacuity: every tree was reached and the rendered pages said something."""
    src = corpus["source"]
    assert sum(1 for p in src if p.startswith("nmtcapp/")) >= 60, "package walk read too little"
    assert sum(1 for p in src if p.startswith("streamlit_app/")) >= 7, "app walk read too little"
    if _is_checkout():
        assert sum(1 for p in src if p.startswith("docs/")) >= 15, "docs walk read too little"
        assert any(p.startswith("examples/") for p in src), "examples/ was not read"
    assert len(corpus["baselines"]) >= 5, "the rendered/CLI baselines were not found"
    rendered_pages = {w.split(":")[1] for w, _ in corpus["rendered"]}
    from tests.test_streamlit_surface_enumeration import page_files
    assert rendered_pages == set(page_files()), (
        f"rendered {sorted(rendered_pages)}; the directory has {sorted(page_files())}")
    assert sum(len(t) for _, t in corpus["rendered"]) > 50_000, (
        "the rendered pages carry almost no text -- AppTest drove nothing")


def test_no_surface_claims_the_winner_patterns_were_measured(corpus):
    """RULES 1 AND 2, every surface. The only exemption is a listed RECORD in source."""
    offending = []
    for where, line, detail, excusable in _flagged(corpus):
        if excusable and _record_for(where, line):
            continue
        offending.append(f"  {where}\n      {detail}\n      | {line[:220]}")
    assert not offending, (
        "a surface states or implies that this tool's winner patterns are "
        "measurements of past winners. They are "
        f"{ASSUMED_WINNER_PATTERNS_CLAUSE!r} "
        "(renderers/_disclosure.ASSUMED_WINNER_PATTERNS_CLAUSE). Interpolate "
        "the clause, or say what the figure actually is -- and do not describe "
        "the Win Alignment Scorer's score with it: that score applies the CY "
        "2024-2025 Review Process structure and reads no WINNER_* constant.\n\n"
        + "\n".join(offending)
    )


def test_every_record_still_records_exactly_one_line(corpus):
    """No dead records, and no record wide enough to excuse two lines.

    SCOPED TO WHAT WAS SCANNED: in the sdist job docs/ is absent, so a docs
    record has nothing to match there and is not dead -- the same rule
    test_fund_attribution_source's dead-entry check applies.
    """
    # One quote can trip BOTH rules -- a spelling (rule 1, reported by line)
    # and an unbound noun (rule 2, reported by sentence). A record may excuse
    # at most one line per rule, and must excuse at least one.
    counts = {(p, f): {"spelling": set(), "noun": set()}
              for p, f, _ in RECORDS if p in corpus["source"]}
    for where, line, detail, excusable in _flagged(corpus):
        if not excusable:
            continue
        rec = _record_for(where, line)
        if rec:
            kind = "noun" if detail == "unqualified winner noun" else "spelling"
            counts[rec][kind].add(where)
    bad = {k: {r: sorted(w) for r, w in v.items()} for k, v in counts.items()
           if not (v["spelling"] or v["noun"])
           or len(v["spelling"]) > 1 or len(v["noun"]) > 1}
    assert not bad, (
        "RECORDS entries must each excuse exactly one flagged line (dead or "
        f"too wide): {bad}")
    for rel in CLAUSE_EXEMPT_PAGES:
        assert rel in _pages(), f"CLAUSE_EXEMPT_PAGES names {rel}, which is not a page"
    for path, _fragment, why in RECORDS:
        assert len(why) >= 30, f"record in {path} carries no real reason: {why!r}"
        assert not path.startswith("rendered:"), "rendered text can never be a record"


#: The eleven evasions fix round 1 was handed, plus the qualifier-anywhere
#: one. Each must be caught by rule 1 or rule 2 -- asserted, not remembered.
EVASIONS = (
    "scoring your pipeline against five years of CDFI Fund award data",
    "It compares patterns of past awardees.",
    "It uses past winners' profiles.",
    "It measures winners' patterns.",
    "These are patterns measured from CY2020-2024 award recipients.",
    "Benchmarks mirror successful NMTC applicants.",
    "See what prior awardees looked like.",
    "See what award-winning CDEs looked like.",
    "Past winners averaged 80% deep distress.",
    "The 9-metric comparison vs. CY2020-2024 winners.",
    "Your pipeline compares favourably with recent winners.",
    "Winner patterns show multi-state CDEs win; this tool's own view differs.",
    # -- fix round 2: the probes both hostile lanes sent back, as given in the
    #    coordinator's fix-round-2 list. Negations that do not govern:
    "It is no secret that past winners averaged 80%",
    "Scores are never far from successful NMTC applicants",
    # allocatee(s), and allocation recipients, in a claim context:
    "Bands track allocatees' profiles.",
    "Thresholds sit at the medians of CY2022 allocatees.",
    "Typical allocatees deploy in five states.",
    "Benchmarks mirror allocation recipients.",
    "Figures are drawn from recent allocation recipients.",
    "Bands match prior-round allocatees.",
    # a statistic of winners, spelled as a noun phrase:
    "The winner p75 is 18 jobs per $1MM.",
    "Compare your pipeline with the winner median.",
    "The winner mean is 7.2 states.",
    # winners as the subject of a measurement verb:
    "Winners consistently exceed this floor.",
    "Across winners (2020-2023), deep distress averaged 80%.",
    "Winning CDEs typically deploy in five states.",
    "Award winners concentrate in healthcare.",
    # the award books / Public Data Release as the calibration source:
    "The bands are calibrated on the award books.",
    "Thresholds are derived from the Public Data Release.",
    "Bands from the Public Data Release set the competitive line.",
    # top-ranked / selected CDEs from prior rounds:
    "Top-ranked CDEs from prior rounds deploy in seven states.",
    "Selected CDEs from prior rounds averaged 80% deep distress.",
    "Top-ranked CDEs average 7.2 states.",
    # -- fix round 3: the audit's allocatee-statistic and selected-population
    #    probes, as listed in the coordinator's fix-round-3 message. All
    #    fifteen passed the round-2 gate.
    "Prior Allocatees averaged 80% severe distress.",
    "Across allocatees (2020-2023), the median was 0.8.",
    "Among allocatees, 80% is typical.",
    "Scores are based on historical allocatee data.",
    "Historically, awarded CDEs exceed this floor.",
    "Based on award data, not this tool's own guesses.",
    "These figures come from CDFI Fund award books.",
    "Recipients of allocations average 7 states.",
    "The top quartile of allocatees exceeds 90%.",
    "Distress bands track the Allocatee population.",
    "Winning pipelines average 7 states.",
    "Funded applications average 7 states.",
    "Figures drawn from actual NMTC awards.",
    "calibrated on CY2020-2024 allocatee data",
    "Allocatees in past rounds averaged 80% deep distress",
)

#: And what must NOT be caught: denials within the window, the CDE's own
#: award history, the NOAA's term of art.
NOT_CLAIMS = (
    "not measurements of past winners",
    "not a percentile of past winners",
    "No corpus of winning applications is loaded anywhere.",
    "The bands use no award data.",
    "this tool's own assumed (house) winner patterns",
    "the three prior NMTC award rounds of the CDE",
    "Formats prior award data into the track record table.",
    "any prior Allocatee that requires action by the CDFI Fund",
    # -- fix round 2: the CDE's own track record, and true statements about
    #    what the Fund publishes. Each was flagged by the round-1 gate.
    "Enter the CDE's past NMTC awards in the track record table",
    "List your most recent award and its QEI amount",
    "Section E lists the CDE's recent awards",
    "The CDFI Fund publishes award recipients each round",
    # the NOAA's own audience label, rendered verbatim on Table 1 deadlines
    "Report QEIs and certify QLICIs deadline [prior Allocatees]",
    # denials the negation directly governs
    "This package holds no sector distribution for past Allocatees.",
    "The CDFI Fund does not publish application-level data for winners.",
    "a score that has never been compared to a winner population",
    "not percentiles of any measured population of past Allocatees",
    # a round-level table statistic, not a band calibration
    "avg_award is computed from the Award Book's own figures",
    "Application-level data for non-winners remains unpublished.",
    # -- fix round 3: true sentences near the new allocatee-statistic rule
    "The 20% is a program-level goal across all Allocatees and a bar on what an Allocatee",
    "11:59 p.m. ET on September 22, 2026 (Electronically via AMIS) [prior Allocatees]; CY",
    "The Fund does publish Allocatee-level deployment data (NMTC Public Data Release 2003-2023).",
    "Per-Allocatee distributions ARE published.",
    "not a distribution of past Allocatees and not percentiles of anything published",
    "Minimum number of distinct states the selected projects must span.",
    "Enter the prior Allocatee's track record for the last three rounds.",
)


@pytest.mark.parametrize("phrase", EVASIONS)
def test_every_known_evasion_is_caught(phrase):
    assert forbidden_hits(phrase) or unqualified_sentences(phrase), (
        f"the gate passes {phrase!r}; add the spelling rather than the phrase")


@pytest.mark.parametrize("phrase", NOT_CLAIMS)
def test_a_denial_or_an_unrelated_use_is_not_caught(phrase):
    assert not forbidden_hits(phrase) and not unqualified_sentences(phrase), (
        f"the gate flags {phrase!r}, which is not a claim that the winner "
        "patterns were measured -- a false positive is how a gate stops being read")


def test_a_negation_outside_its_window_does_not_excuse_a_claim():
    """The first cut excused any 'not' earlier in the clause."""
    assert forbidden_hits(
        "Scores are not probabilities and they are tuned on what past winners did")


@pytest.mark.parametrize("phrase", (
    "It is no secret that past winners averaged 80%",
    "Scores are never far from successful NMTC applicants",
    "There is no doubt that winners consistently exceed this floor.",
    "Not surprisingly, the winner median is 82%.",
))
def test_a_negation_that_governs_something_else_does_not_excuse_a_claim(phrase):
    """Fix round 2: a negation excuses a match only when it DIRECTLY governs
    it. Round 1's 4-token window excused the first two of these."""
    assert forbidden_hits(phrase), f"the gate excuses {phrase!r}"


def test_the_clause_keeps_its_true_half():
    """RULE 3. Agreement by softening the disclosure is not the fix."""
    for anchor in CLAUSE_ANCHORS:
        assert anchor in ASSUMED_WINNER_PATTERNS_CLAUSE, (
            f"ASSUMED_WINNER_PATTERNS_CLAUSE no longer says {anchor!r}; "
            "data/historical_awards.py and tests/scoring_attribution.txt still "
            "rule every winner constant HOUSE and unsourced"
        )
    assert ASSUMED_WINNER_PATTERNS_CLAUSE.startswith(ASSUMED_WINNER_PATTERNS)


def _pages() -> list:
    from tests.test_streamlit_surface_enumeration import page_files
    return page_files()


@pytest.mark.parametrize("relpath", _pages())
def test_each_page_renders_the_clause_verbatim_or_is_classified(relpath):
    """RULE 4, rendered, on the COLD load. Markdown bold is stripped first:
    Home and page 3 bold the noun phrase, as Home always has."""
    from tests.streamlit_render import page_text
    if relpath in CLAUSE_EXEMPT_PAGES:
        assert len(CLAUSE_EXEMPT_PAGES[relpath]) >= 60, (
            f"{relpath}'s exemption gives no real reason")
        return
    text = page_text(relpath, "cold").replace("**", "")
    assert ASSUMED_WINNER_PATTERNS_CLAUSE in text, (
        f"{relpath} does not render the provenance clause verbatim.\n"
        f"Expected: {ASSUMED_WINNER_PATTERNS_CLAUSE!r}"
    )


def test_the_home_and_optimizer_disclosures_are_one_string():
    """The Methodology Disclosure is rendered on Home and page 3 from one
    constant; the two renders must be byte-identical to it."""
    import utils  # streamlit_app/, on sys.path via tests.streamlit_render
    from tests.streamlit_render import rendered_pages, texts

    # WHETHER THE LEADING "⚠️ " SURVIVES DEPENDS ON THE STREAMLIT VERSION
    # (fix round 1, X1). The resolver picks streamlit 1.64 on 3.10+, where
    # st.info lifts a leading emoji into its icon slot and AppTest reports the
    # body without it; on 3.9 it picks 1.50, which keeps it in the text. Both
    # forms are accepted -- and NOTHING ELSE: the emoji is the only permitted
    # difference, and the body must be byte-identical to the constant.
    expected = utils.METHODOLOGY_DISCLOSURE
    assert expected.startswith("⚠️ ")
    accepted = {expected, expected[len("⚠️ "):]}
    for rel in ("app.py", "pages/3_Pipeline_Optimizer.py"):
        infos = [t for k, t in texts(rendered_pages()[rel]["cold"]) if k == "info"]
        assert accepted & set(infos), (
            f"{rel} does not render utils.METHODOLOGY_DISCLOSURE as an st.info "
            f"(with or without its leading emoji). Infos rendered: {infos}")


#: The scoped lead-in (fix round 1, P6), pinned where it RENDERS (fix round 2,
#: item 3). The one-string test above compares each render with
#: utils.METHODOLOGY_DISCLOSURE, so restoring the old unscoped lead-in in the
#: constant kept it green. This names the words.
DISCLOSURE_LEAD_IN = (
    "The optimizer's alignment score and the benchmark bands measure "
    f"similarity to {ASSUMED_WINNER_PATTERNS}"
)
DISCLOSURE_SCORER_SENTENCE = "The Win Alignment Scorer's score applies"
WITHDRAWN_LEAD_IN = "Alignment scores measure similarity to"


@pytest.mark.parametrize("rel", ("app.py", "pages/3_Pipeline_Optimizer.py"))
def test_the_disclosure_names_what_uses_the_house_patterns(rel):
    """The unscoped lead-in was true of the optimizer's score and false of
    the Win Alignment Scorer's, which page 2 also calls an alignment score."""
    from tests.streamlit_render import rendered_pages, texts
    infos = [t.replace("**", "") for k, t in texts(rendered_pages()[rel]["cold"])
             if k == "info"]
    joined = "\n".join(infos)
    assert DISCLOSURE_LEAD_IN in joined, (
        f"{rel}'s disclosure no longer opens {DISCLOSURE_LEAD_IN!r}. Infos: {infos}")
    assert DISCLOSURE_SCORER_SENTENCE in joined, (
        f"{rel}'s disclosure no longer states the scorer's own basis")
    assert WITHDRAWN_LEAD_IN not in joined, (
        f"{rel} renders the withdrawn lead-in {WITHDRAWN_LEAD_IN!r}")


def test_page_two_says_only_some_recommendations_use_the_house_patterns():
    """RecommendationEngine reads WINNER_PATTERN_THRESHOLDS for the
    eligibility recommendation only (fix round 2, item 4)."""
    from tests.streamlit_render import page_text
    text = page_text("pages/2_Win_Alignment_Scorer.py", "cold").replace("**", "")
    flat = re.sub(r"\s+", " ", text)
    assert "Some recommendations below, and the Pipeline Optimizer, compare" in flat
    assert "The recommendations below and the Pipeline Optimizer compare" not in flat


def test_the_copies_that_cannot_interpolate_state_it_verbatim():
    """RULE 4, files. Markdown cannot interpolate a Python constant, so the
    README and docs copies are held to it character for character -- change
    the constant and these go red rather than drifting."""
    names = list(CLAUSE_FILES) + (list(CLAUSE_CHECKOUT_FILES) if _is_checkout() else [])
    missing = [n for n in names
               if ASSUMED_WINNER_PATTERNS_CLAUSE not in
               re.sub(r"\s+", " ", (_REPO_ROOT / n).read_text(encoding="utf-8"))]
    assert not missing, f"the clause is not stated verbatim in: {missing}"


def test_no_python_module_retypes_the_clause():
    """Walks the INSTALLED package and streamlit_app/ -- the sdist job has no
    ``<repo>/nmtcapp``, and a walk over a missing directory would pass."""
    fragment = "unsourced house constants — not"
    copies, walked = [], 0
    trees = [_package_root(), _REPO_ROOT / "streamlit_app"]
    for tree in trees:
        for path in tree.rglob("*.py"):
            if "__pycache__" in path.parts or path.name == "_disclosure.py":
                continue
            walked += 1
            for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
                if fragment in line:
                    copies.append(f"{path}:{lineno}")
    assert walked >= 60, f"walked only {walked} modules; the sweep read nothing"
    assert not copies, (
        f"the provenance clause is retyped at {copies}; read "
        "_disclosure.ASSUMED_WINNER_PATTERNS_CLAUSE instead")
