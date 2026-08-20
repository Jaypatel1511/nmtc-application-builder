"""The extra that turns two output formats into four must be nameable.

THE DEFECT THIS GATE EXISTS FOR (1.3.1 F4)
==========================================

``pyproject.toml`` defines an ``output`` extra carrying python-docx, openpyxl
and reportlab — the three libraries the Word, Excel and PDF renderers import.
None of them is a core dependency, so a plain ``pip install
nmtc-application-builder`` produces a package that renders Markdown and, once
a renderer's import fails, silently drops the rest.

NOTHING A CDE FOLLOWING THE ADVERTISED PATH EVER NAMED THE EXTRA. Not
``nmtcapp init``'s "Next steps", not the notebook that scaffold writes, and not
the one line that mentions the absence at all::

    logger.warning("python-docx not installed — skipping Word output")

which names a library and not the fix, and whose advice — install python-docx —
gets a reader to three of four formats and stops. A CDE pip-installs the
package, generates, and never learns that the PDF and Word renderers exist.

WHAT IS ASSERTED
================

Every surface a first-time CDE meets — the skip message, ``init``'s next steps
and the scaffolded notebook — names the extra AND the exact install command,
and the extra it names is one ``pyproject.toml`` actually defines. That last
part is the half that goes stale: a printed install command for an extra that
was renamed is worse than no command, because it fails at the shell rather than
in the code.
"""
from __future__ import annotations

import json
import os
import re

import pytest

from nmtcapp.core.application import (
    OUTPUT_EXTRA, OUTPUT_EXTRA_INSTALL, _skip_message,
)

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

#: (format, library) for every renderer that can be skipped for a missing dep.
_SKIPPABLE = (("Word", "python-docx"), ("Excel", "openpyxl"), ("PDF", "reportlab"))


def _pyproject_text() -> str:
    with open(os.path.join(_ROOT, "pyproject.toml"), encoding="utf-8") as fh:
        return fh.read()


def _project_name() -> str:
    match = re.search(r'^name\s*=\s*"([^"]+)"', _pyproject_text(), re.M)
    assert match, "pyproject.toml has no project name"
    return match.group(1)


def _extras() -> dict:
    """``{extra: [requirement, ...]}`` from pyproject.toml.

    NO ``importorskip`` HERE, DELIBERATELY. ``tomllib`` is 3.11+ and ``tomli``
    is not in the dev extra, so a TOML-parser skip would make this gate silent
    on exactly the interpreter this package supports a floor of (3.9) — which
    is the shape ``test_ci_fetches_enough_history_to_answer_this_gate`` exists
    to refuse. The block is flat and quoted; a regex reads it on every
    interpreter.
    """
    text = _pyproject_text()
    section = text.split("[project.optional-dependencies]", 1)
    assert len(section) == 2, (
        "pyproject.toml no longer has a [project.optional-dependencies] "
        "section in the form this gate reads. Fix the reader, not the check."
    )
    body = re.split(r"^\[", section[1], maxsplit=1, flags=re.M)[0]
    extras = {}
    for name, block in re.findall(r"^(\w[\w.-]*)\s*=\s*\[(.*?)^\]",
                                  body, re.M | re.S):
        extras[name] = [m.group(1) for m in re.finditer(r'"([^"]+)"', block)]
    assert extras, "no optional-dependency groups parsed out of pyproject.toml"
    return extras


def test_the_extra_this_package_advertises_is_one_it_defines():
    """A printed install command for a renamed extra fails at the shell."""
    extras = _extras()
    assert OUTPUT_EXTRA in extras, (
        f"nmtcapp.core.application.OUTPUT_EXTRA is {OUTPUT_EXTRA!r} and "
        f"pyproject.toml defines {sorted(extras)}. Every surface that tells a "
        "CDE how to get the PDF and Word renderers prints that name."
    )
    project_name = _project_name()
    assert f'{project_name}[{OUTPUT_EXTRA}]' in OUTPUT_EXTRA_INSTALL, (
        f"the printed install command {OUTPUT_EXTRA_INSTALL!r} does not name "
        f"{project_name}[{OUTPUT_EXTRA}]"
    )


def test_the_output_extra_covers_every_skippable_renderer():
    """Installing the extra must actually produce all four formats."""
    extras = _extras()
    declared = {req.split(">")[0].split("=")[0].split("[")[0].strip().lower()
                for req in extras[OUTPUT_EXTRA]}
    missing = [lib for _fmt, lib in _SKIPPABLE if lib.lower() not in declared]
    assert not missing, (
        f"the '{OUTPUT_EXTRA}' extra does not carry {missing}. Every surface "
        "in this package tells a CDE that this one extra gets them all four "
        "formats; if it does not, that instruction is false and they land on "
        "three of four with nothing saying why."
    )


@pytest.mark.parametrize("fmt,library", _SKIPPABLE, ids=[f for f, _l in _SKIPPABLE])
def test_the_skip_message_names_the_extra_and_the_command(fmt, library):
    """The only line that mentions the absence must also mention the fix."""
    message = _skip_message(fmt, library)
    assert library in message, f"the {fmt} skip message no longer names {library}"
    assert OUTPUT_EXTRA_INSTALL in message, (
        f"the {fmt} skip message does not carry the install command. Naming "
        f"the library alone tells a reader to install {library}, which fixes "
        f"{fmt} and leaves the other formats missing — that is how someone "
        "arrives at three of four output formats and stops (1.3.1 F4)."
    )


def test_init_tells_a_cde_how_to_get_all_four_formats(tmp_path, capsys):
    """`nmtcapp init` is the first screen; it is where the path is set."""
    from nmtcapp.cli import cmd_init

    class _Args:
        directory = str(tmp_path / "starter")

    assert cmd_init(_Args()) == 0
    out = capsys.readouterr().out
    assert OUTPUT_EXTRA_INSTALL in out, (
        "`nmtcapp init` never names the output extra. Its 'Next steps' offer "
        "the notebook and `nmtcapp analyze`, and NEITHER produces a document "
        "with a plain install — analyze writes no file at all, and generate() "
        "silently drops Word and PDF (1.3.1 F4).\n\n" + out
    )


def test_the_scaffolded_notebook_names_the_extra_beside_generate(tmp_path):
    """The notebook is the only advertised path that generates anything."""
    from nmtcapp.cli import _make_starter_notebook

    notebook = json.loads(_make_starter_notebook())
    sources = ["".join(cell["source"]) for cell in notebook["cells"]]
    generate_cells = [s for s in sources if "app.generate(" in s]
    assert generate_cells, (
        "the scaffolded notebook no longer mentions app.generate() at all — "
        "the only advertised path to a document is gone"
    )
    for cell in generate_cells:
        assert OUTPUT_EXTRA_INSTALL in cell, (
            "the notebook cell that calls app.generate() does not say that "
            "Word and PDF need the output extra. A CDE runs it, gets Markdown "
            "and Excel, and concludes the tool produces two formats.\n\n" + cell
        )
