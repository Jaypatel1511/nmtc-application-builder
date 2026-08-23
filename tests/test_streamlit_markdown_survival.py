"""RENDERED-OUTPUT GATE 2 of 2: does the text a reader SEES still say what the
source says?

WHY THIS CLASS OF GATE EXISTS (1.5.5 T6)

1.5.4 shipped with 1,422 tests collected and 1,421 green, through a hostile
audit and an audit close. Then someone opened the running app and found five
defects in twenty minutes. Every one of them was a defect in what the tool
RENDERS, and every one was invisible to a test that reads the SOURCE.

``tests/test_round_provenance.py`` asserts the note SAYS "$10 billion". It
does. On screen it said "10 billion". Both statements were true at once,
because between the source string and the reader stands a markdown parser
that this package had never modelled.

WHAT WENT WRONG, MECHANICALLY (1.5.5 T3) -- MEASURED, NOT ASSUMED

Streamlit renders ``st.markdown`` / ``st.info`` / ``st.caption`` bodies with
remark/micromark plus ``micromark-extension-math``. That extension registers
an inline-math construct on the ``$`` character with
``singleDollarTextMath`` defaulting to TRUE, so ONE ``$`` opens inline math
and the next matching ``$`` closes it. ``round_provenance_paragraphs()[0]``
contains "$10 billion" and "$5 billion" in the SAME paragraph. The parser
paired them, ate BOTH ``$`` characters, and re-typeset everything between as
math -- turning a federal allocation figure into the unitless "10 billion".

THE PROMPT THAT COMMISSIONED THIS FIX GUESSED "KaTeX". IT IS NOT KaTeX.
Verified in Chrome against the running 1.5.4 app on 2026-08-22: the DOM
contained ZERO ``.katex`` nodes. What the span became was a bare
``<code class="language-math math-inline">`` -- micromark's math node with no
KaTeX pass applied. The visible symptom is therefore MONOSPACE, not
mathematical typesetting, which is what the screenshot's "different typeface"
actually was. The distinction does not change the fix (escape the ``$``) but
it does change what this gate is allowed to claim it models, so it is
recorded here rather than left as folklore.

  ⚠️  SCOPE LIMIT -- READ THIS BEFORE TRUSTING A GREEN FROM THIS FILE  ⚠️

  THIS GATE DOES NOT RUN A BROWSER, A JAVASCRIPT ENGINE, OR STREAMLIT.
  There is none of any of those in CI. What it runs is
  ``inline_math_spans()`` below: a PYTHON RE-IMPLEMENTATION of ONE construct
  from ``micromark-extension-math``, transcribed from the tokenizer shipped
  inside the pinned Streamlit wheel
  (``static/static/js/StreamlitMarkdown.*.js``, function ``mathText``).

  IT THEREFORE OBSERVES:
    * whether a ``$`` on a Streamlit prose surface would open an inline-math
      span that swallows a later ``$`` and the run between them;
    * whether the amounts, units and disclaimer clauses named in
      PROTECTED_PHRASES survive into the text a reader sees.

  IT DOES **NOT** OBSERVE:
    * layout, CSS, fonts, wrapping, truncation, overlap or colour -- nothing
      geometric. Chart geometry is the OTHER gate
      (``tests/test_readiness_chart_geometry.py``);
    * any markdown construct other than inline math -- emphasis, code spans,
      links, tables and HTML are NOT modelled, so a defect caused by one of
      those is invisible here;
    * whether KaTeX renders, since it demonstrably did not;
    * ``$$``-delimited display math, which none of these surfaces uses;
    * anything Streamlit does to text OUTSIDE a markdown body --
      ``st.metric`` values, ``st.dataframe`` cells, chart labels and widget
      captions do not pass through here.

  AND IT IS AN APPROXIMATION IN ONE DIRECTION THAT MATTERS: if the real
  tokenizer would create a span that ``inline_math_spans()`` misses, this
  gate goes green on a broken page. That is why ``test_no_unescaped_dollar_
  on_streamlit_prose_surfaces`` exists ALONGSIDE the rendered-text
  assertions. It checks a STRICTER, PURELY SYNTACTIC invariant -- every
  currency ``$`` is backslash-escaped -- which needs no tokenizer model at
  all. A false green now requires BOTH the model and the syntactic invariant
  to be wrong at once.

  The escape itself is not modelled from documentation either. It was
  executed in a browser against the pinned Streamlit on 2026-08-22:
  ``\\$10 billion ... \\$5 billion`` rendered both dollar signs and produced
  no math node, on ``st.markdown``, ``st.info`` and ``st.caption`` alike.

This file exists because the alternative -- "the source string is correct" --
is a statement this package has now shipped three times while the screen said
something else.
"""
from __future__ import annotations

import ast
import os
import re
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent
_STREAMLIT_APP = _REPO_ROOT / "streamlit_app"

import sys
for _p in (str(_REPO_ROOT), str(_STREAMLIT_APP)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from nmtcapp.renderers._round_provenance import round_provenance_paragraphs
from utils import md


# ---------------------------------------------------------------------------
# The model
# ---------------------------------------------------------------------------
# Transcribed from micromark-extension-math's `mathText` construct as shipped
# in the pinned Streamlit wheel. The JavaScript, de-minified:
#
#   c(code): while code === '$'  -> consume, openLength++
#            else if openLength < 2 && !singleDollarTextMath -> nok
#            else -> go to between()
#   l(code): null -> nok            (unterminated: NO math span)
#            '$'  -> start counting a closing run
#            else -> data
#   d(code): while '$' -> consume, closeLength++
#            closeLength === openLength -> ok   (span closes)
#            otherwise                  -> the run is data; keep scanning
#   previous(code): may not start when the preceding character is '$'
#                   unless that '$' was a characterEscape.
#
# `singleDollarTextMath` is undefined in Streamlit's call, and the extension
# defaults it to true -- which is the whole defect.
#
# A backslash-escaped `\$` never reaches this construct: CommonMark's
# characterEscape consumes it first ($ is ASCII punctuation).
_ESCAPED_DOLLAR = re.compile(r"(?<!\\)((?:\\\\)*)\\\$")


def _unescaped_dollar_positions(text: str) -> list:
    """Indices of every ``$`` that is NOT neutralised by a backslash escape."""
    out = []
    for i, ch in enumerate(text):
        if ch != "$":
            continue
        # Count the contiguous run of backslashes immediately before it. An
        # odd count means this '$' is escaped.
        backslashes = 0
        j = i - 1
        while j >= 0 and text[j] == "\\":
            backslashes += 1
            j -= 1
        if backslashes % 2 == 0:
            out.append(i)
    return out


def inline_math_spans(text: str) -> list:
    """``(start, end)`` half-open spans micromark would tokenize as inline math.

    ``start`` is the opening ``$``; ``end`` is one past the closing ``$``.

    Example::

        inline_math_spans("costs $5 or $9")   # -> [(6, 12)]
        inline_math_spans(r"costs \\$5 or \\$9")  # -> []
    """
    live = _unescaped_dollar_positions(text)
    live_set = set(live)
    spans = []
    idx = 0
    while idx < len(live):
        start = live[idx]
        # `previous`: cannot open immediately after an unescaped '$'.
        if start - 1 in live_set:
            idx += 1
            continue
        # Opening run length.
        run_end = start
        while run_end + 1 in live_set:
            run_end += 1
        open_len = run_end - start + 1
        # Scan forward for a closing run of exactly the same length.
        k = idx + (open_len)
        closed = False
        while k < len(live):
            c_start = live[k]
            c_end = c_start
            while c_end + 1 in live_set:
                c_end += 1
            close_len = c_end - c_start + 1
            if close_len == open_len:
                spans.append((start, c_end + 1))
                idx = k + close_len
                closed = True
                break
            k += close_len
        if not closed:
            # Unterminated -> micromark's `l(null)` takes the nok branch and
            # NO span is produced. The '$' renders literally.
            idx += 1
    return spans


def rendered_text(text: str) -> str:
    """The plain text a reader sees, per the model above.

    Inline-math delimiters are consumed by the parser; the run between them
    survives as text (inside a ``<code>`` element), so what disappears from
    the reader's line is exactly the ``$`` characters. Backslash escapes are
    resolved, since that is what CommonMark does with them.

    Example::

        rendered_text("with $10 billion and $5 billion")
        # -> 'with 10 billion and 5 billion'
    """
    drop = set()
    for start, end in inline_math_spans(text):
        run_end = start
        while run_end < end and text[run_end] == "$":
            run_end += 1
        drop.update(range(start, run_end))
        c_start = end - 1
        while c_start >= start and text[c_start] == "$":
            c_start -= 1
        drop.update(range(c_start + 1, end))
    kept = "".join(ch for i, ch in enumerate(text) if i not in drop)
    # Resolve CommonMark backslash escapes of ASCII punctuation.
    return re.sub(r"\\([!-/:-@\[-`{-~])", r"\1", kept)


# ---------------------------------------------------------------------------
# The surfaces
# ---------------------------------------------------------------------------
_MARKDOWN_CALLS = frozenset({
    "markdown", "info", "caption", "write", "warning", "error", "success",
    "text", "subheader", "header", "title",
})


def _static_parts(node: ast.AST) -> list:
    """Literal text a node contributes, ignoring interpolated values.

    Implicit concatenation arrives pre-joined as one Constant. f-strings are
    walked so their literal segments are checked; a ``{...}`` placeholder
    contributes nothing, which is correct -- an interpolated value cannot be
    checked statically and is covered by the runtime surfaces below.
    """
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return [node.value]
    if isinstance(node, ast.JoinedStr):
        out = []
        for part in node.values:
            if isinstance(part, ast.Constant) and isinstance(part.value, str):
                out.append(part.value)
        # Join with a placeholder so a '$' either side of an interpolation is
        # still seen as sharing one string.
        return ["\u0001".join(out)] if out else []
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        return _static_parts(node.left) + _static_parts(node.right)
    return []


def _streamlit_page_files() -> list:
    files = sorted(_STREAMLIT_APP.glob("*.py")) + sorted((_STREAMLIT_APP / "pages").glob("*.py"))
    assert files, "no Streamlit sources found — this gate would be vacuous"
    return files


def _literal_prose_surfaces() -> list:
    """``(label, text)`` for every literal markdown body in the Streamlit app."""
    surfaces = []
    for path in _streamlit_page_files():
        tree = ast.parse(path.read_text(), filename=str(path))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            fn = node.func
            if not (isinstance(fn, ast.Attribute) and fn.attr in _MARKDOWN_CALLS):
                continue
            for arg in node.args[:1]:
                for text in _static_parts(arg):
                    if text.strip():
                        surfaces.append(
                            (f"{path.relative_to(_REPO_ROOT)}:{node.lineno} st.{fn.attr}", text)
                        )
    assert surfaces, "AST walk found no markdown bodies — this gate would be vacuous"
    return surfaces


def _provenance_render_sites() -> list:
    """``(label, wrapped)`` for each page that renders the round-provenance note.

    ``wrapped`` says whether the page passes the paragraph through
    ``utils.md()``. This is checked rather than assumed: the note lives in
    ``nmtcapp``, so no AST walk of ``streamlit_app/`` would otherwise see its
    text, and a page that renders it raw is exactly the 1.5.4 defect.
    """
    sites = []
    for path in _streamlit_page_files():
        tree = ast.parse(path.read_text(), filename=str(path))
        for node in ast.walk(tree):
            if not (isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Name)
                    and node.func.id == "round_provenance_paragraphs"):
                continue
            # Walk outward: is this call inside an `md(...)` call anywhere in
            # the enclosing statement?
            src = ast.get_source_segment(path.read_text(), node) or ""
            enclosing = _enclosing_statement_source(path, node)
            wrapped = bool(re.search(r"\bmd\s*\(", enclosing))
            sites.append((f"{path.relative_to(_REPO_ROOT)}:{node.lineno}", wrapped, enclosing.strip()))
    return sites


def _enclosing_statement_source(path: Path, node: ast.AST) -> str:
    lines = path.read_text().splitlines()
    start = max(0, node.lineno - 1)
    end = min(len(lines), (getattr(node, "end_lineno", node.lineno) or node.lineno))
    return "\n".join(lines[start:end])


def _runtime_prose_surfaces() -> list:
    """``(label, text)`` for shared notes the pages render but do not contain.

    ``round_provenance_paragraphs()`` is the one that mattered: it lives in
    ``nmtcapp``, is rendered by three pages, and no AST walk of
    ``streamlit_app/`` would ever see its text.

    The text recorded here is what the PAGE emits, not what the module
    returns -- i.e. ``md(para)`` where the page wraps it. The wrapping is
    verified by ``test_round_provenance_is_escaped_at_every_render_site``;
    if a page ever drops the wrapper, that test fails rather than this one
    silently measuring a string no page renders.
    """
    sites = _provenance_render_sites()
    wrapped_everywhere = bool(sites) and all(w for _, w, _ in sites)
    out = []
    for i, para in enumerate(round_provenance_paragraphs()):
        text = md(para) if wrapped_everywhere else para
        out.append((f"_round_provenance.round_provenance_paragraphs()[{i}]"
                    f" as rendered by {len(sites)} page(s)", text))
    return out


def _all_prose_surfaces() -> list:
    return _literal_prose_surfaces() + _runtime_prose_surfaces()


#: Text a reader MUST still see. Each entry is a phrase whose UNIT or
#: DISCLAIMING FORCE is destroyed if the '$' in front of it is eaten. "10
#: billion" is not a smaller version of "$10 billion"; in a federal-allocation
#: disclosure it is not a quantity at all.
PROTECTED_PHRASES = (
    "$10 billion in allocation authority",
    "$5 billion available",
    "$10 billion awarded of",
    "$19.2 billion requested",
)


# ---------------------------------------------------------------------------
# The assertions
# ---------------------------------------------------------------------------
def test_model_reproduces_the_1_5_4_defect():
    """The model must fail the string that FAILED IN CHROME, or it proves nothing.

    This is the anchor. Everything else in this file is only as trustworthy
    as this: the exact text that rendered as "10 billion in allocation
    authority" in the browser on 2026-08-22 must be text the model calls
    broken.
    """
    broken = (
        "awarded 23 Dec 2025 with $10 billion in allocation authority). The "
        "CY 2026 Allocation Application and NOAA are NOT YET PUBLISHED: the "
        "CDFI Fund has announced that CY 2026 will make $5 billion available"
    )
    assert inline_math_spans(broken), "model failed to see the defect it was written for"
    out = rendered_text(broken)
    assert "10 billion in allocation authority" in out
    assert "$10 billion" not in out, "model does not reproduce the observed loss of '$'"
    assert "$5 billion" not in out

    fixed = broken.replace("$", r"\$")
    assert inline_math_spans(fixed) == []
    assert "$10 billion in allocation authority" in rendered_text(fixed)
    assert "$5 billion available" in rendered_text(fixed)


def test_model_leaves_a_lone_dollar_alone():
    """A single unpaired ``$`` is NOT math — micromark takes the nok branch.

    Guards against over-escaping: if this gate demanded escapes where the
    parser does no harm, it would push noise into every surface that prints
    one amount.
    """
    assert inline_math_spans("Requested allocation: $65,000,000") == []
    assert rendered_text("Requested allocation: $65,000,000") == (
        "Requested allocation: $65,000,000"
    )


@pytest.mark.parametrize("phrase", PROTECTED_PHRASES)
def test_protected_phrase_survives_rendering(phrase):
    """Every protected phrase reaches the reader intact on the surface that carries it."""
    carriers = [
        (label, text) for label, text in _all_prose_surfaces() if phrase in text
    ]
    assert carriers, (
        f"no Streamlit surface carries {phrase!r} any more. Either the text was "
        "reworded (update PROTECTED_PHRASES) or the amount was dropped — this "
        "gate refuses to pass vacuously either way."
    )
    for label, text in carriers:
        assert phrase in rendered_text(text), (
            f"{label}: the SOURCE says {phrase!r} but a reader sees\n"
            f"  {rendered_text(text)!r}\n"
            "An inline-math span ate the '$'. Escape it as '\\$'."
        )


def test_no_inline_math_span_on_any_streamlit_prose_surface():
    """No prose surface may contain text micromark would tokenize as inline math.

    None of these pages renders mathematics. Every span here is therefore a
    currency amount being destroyed, not an equation being typeset.
    """
    broken = []
    for label, text in _all_prose_surfaces():
        spans = inline_math_spans(text)
        for start, end in spans:
            broken.append(f"{label}\n    span: {text[start:end][:160]!r}")
    assert not broken, (
        "inline-math spans on prose surfaces — each one eats two '$' and "
        "re-typesets the run between them:\n" + "\n".join(broken)
    )


def test_no_unescaped_dollar_on_streamlit_prose_surfaces():
    """STRICTER, MODEL-FREE BACKSTOP. Every currency ``$`` is backslash-escaped.

    This assertion does not use ``inline_math_spans`` at all, on purpose. It
    is the reason a bug in the model above cannot by itself produce a false
    green: escaping every ``$`` makes a math span impossible regardless of
    how the tokenizer actually behaves.
    """
    offenders = []
    for label, text in _all_prose_surfaces():
        positions = _unescaped_dollar_positions(text)
        if positions:
            offenders.append(f"{label}: {len(positions)} unescaped '$' in {text[:120]!r}")
    assert not offenders, (
        "unescaped '$' on a Streamlit markdown surface. One is currently "
        "harmless; two in one body destroy each other and the run between "
        "them. Escape as '\\$' — verified in Chrome against the pinned "
        "Streamlit:\n" + "\n".join(offenders)
    )


def test_round_provenance_is_escaped_at_every_render_site():
    """Every page rendering the shared note must pass it through ``utils.md()``.

    The note is ONE STRING READ EVERYWHERE and it cannot carry its own
    escape -- a ``\\$`` baked into it would put a literal backslash into a
    generated Word document. So the escape is applied per surface, and this
    is the assertion that a surface has not been added without it.
    """
    sites = _provenance_render_sites()
    assert len(sites) >= 3, (
        f"expected the note on at least 3 Streamlit pages, found {len(sites)} — "
        "if a page dropped it, say so deliberately"
    )
    unwrapped = [f"{label}: {src}" for label, wrapped, src in sites if not wrapped]
    assert not unwrapped, (
        "round-provenance note rendered WITHOUT utils.md() — the '$10 billion' "
        "and '$5 billion' in paragraph 0 will destroy each other:\n"
        + "\n".join(unwrapped)
    )
