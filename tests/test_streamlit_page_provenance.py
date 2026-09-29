"""Every page says which release is serving and which round it is based on (1.7.2 F1, F3).

F1 -- THE APP CARRIED NO VERSION STAMP ON ANY PAGE
==================================================

The 1.7.1 app settle read found that the only version-like strings anywhere
in the app were historical references inside the methodology prose. What
established that the deployed app was on 1.7.1 was an accident: the Home
banner's "1,961 tests", which moved only because 1.7.1 happened to add tests.
A release that changed prose without changing the count would have been
indistinguishable from its predecessor -- on the surface a user is most likely
to be looking at, when the 1.6.5 and 1.7.0 P0s were both DIAGNOSED by reading
a version stamp. R6 (1.7.1) closed the same gap on the workbook.

Every page now calls ``utils.render_version_stamp()``, which reads
``nmtcapp.__version__`` at CALL time through R6's own helper
(``_document_properties.generator_stamp``). Asserted here per page, rendered,
against the INSTALLED distribution's version -- and once with the version
monkeypatched, which a stamp typed or cached at import could not follow.

F3 -- THE PIPELINE OPTIMIZER RENDERED NO ROUND-PROVENANCE NOTE
==============================================================

Pages 1, 2 and 4 called ``round_provenance_paragraphs()``; page 3 did not,
and it is a scoring and selection surface. Home did not either, and Home's
sample-CDE box names a round. Both now render paragraph 0 -- READ, not
retyped -- above any ``st.stop()``, and this asserts it on the COLD render of
every page: the page as it first loads, before anything is clicked, which is
the render a CDE who never presses a button actually sees.

A page may be exempted only by an entry in ``PROVENANCE_EXEMPT`` with a
written reason. There are none.

THE PAGE LIST IS THE DIRECTORY'S. Parametrized from
``test_streamlit_surface_enumeration.page_files()`` at collection time, so a
new page is gated here the moment it exists. Rendering is shared with the F2
gate through ``tests/streamlit_render.py``.
"""
from __future__ import annotations

from importlib.metadata import version as _dist_version

import pytest

from tests.streamlit_render import rendered_pages, texts
from tests.test_streamlit_surface_enumeration import page_files

PAGES = page_files()


def _installed_version() -> str:
    return _dist_version("nmtc-application-builder")


def _captions(at) -> list:
    return [text for kind, text in texts(at) if kind == "caption"]


# ---------------------------------------------------------------------------
# F1
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("relpath", PAGES)
def test_every_page_stamps_the_installed_version(relpath):
    """Cold AND after the page's action: the stamp must survive both."""
    import nmtcapp

    expected = f"Running nmtc-application-builder v{_installed_version()}"
    assert nmtcapp.__version__ == _installed_version(), (
        "nmtcapp.__version__ and the installed distribution disagree; the "
        "stamp would be asserted against the wrong number")
    for state in ("cold", "driven"):
        at = rendered_pages()[relpath][state]
        assert not at.exception, f"{relpath} ({state}) raised: {at.exception}"
        assert expected in _captions(at), (
            f"{relpath} ({state}) renders no version stamp {expected!r}.\n"
            f"Captions it rendered: {_captions(at)}\n\n"
            "Call utils.render_version_stamp() near the page title. The "
            "deployed app is the surface a user is most likely to be looking "
            "at, and a stamp is what diagnosed the 1.6.5 and 1.7.0 P0s."
        )


def test_the_stamp_is_read_at_call_time_not_import_time(monkeypatch):
    """A typed or import-time-cached stamp cannot follow a patched version.

    Renders page 3 FRESH (not from the shared cache) with ``__version__``
    patched, the way the rendered-baseline gate proves the workbook stamp is
    version-independent.
    """
    import nmtcapp
    from streamlit.testing.v1 import AppTest
    from tests.streamlit_render import _APP_DIR

    monkeypatch.setattr(nmtcapp, "__version__", "9.9.9-callt")
    at = AppTest.from_file(str(_APP_DIR / "pages/3_Pipeline_Optimizer.py"),
                           default_timeout=300)
    at.run()
    assert not at.exception, f"page 3 raised: {at.exception}"
    assert "Running nmtc-application-builder v9.9.9-callt" in _captions(at), (
        f"the stamp did not follow a patched nmtcapp.__version__: {_captions(at)}")
