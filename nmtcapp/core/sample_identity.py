"""Refusal gate: shipped sample identity must never be submitted as a CDE's own.

WHY THIS EXISTS

Through 1.1.5 the shipped ``pipeline_template.xlsx`` was not blank. Its "CDE
Profile" sheet carried a complete fictional CDE — Riverbend Community Capital
CDE, LLC, CDE-2018-0117, EIN 82-1234567, plus eighteen scoring attributes. The
Streamlit sidebar served that file as "Download blank template (Excel)".

A CDE that filled in the Pipeline sheet and never touched the CDE Profile sheet
uploaded Riverbend's identity. ``streamlit_app/utils.py`` built a correct
neutral profile and then merged the parsed sheet over it, so the neutral
profile lost. Riverbend's ``has_prior_reporting_issues: False`` then reached
``sections/base._compliance_statement`` and rendered, into a federal filing:

    Per this CDE's own profile declaration, no prior NMTC reporting issues
    have been recorded.

— through the exact function 1.2.0 added to stop unconditional clean-compliance
claims. The fabrication was chased out of the generator and walked back in
through the inputs.

1.2.0 blanks the template and stops the identity merge. This module is the
third defence, and the only one that survives someone re-adding the data: any
profile whose identity IS the shipped sample's is refused at load.

MATCHING IS EXACT, NOT FUZZY. A real CDE can legitimately share an EIN prefix,
a state, or a word in its name with the sample; refusing on a prefix or a
substring would block real users. Only a full, case-insensitive,
whitespace-stripped equality on name, CDE ID or EIN counts, and the error names
which field matched so a false positive is diagnosable rather than mysterious.
"""
from __future__ import annotations


class SampleDataError(ValueError):
    """Raised when shipped fictional sample data is used as a real CDE profile."""


# Every identity value that ships inside this package's own sample files.
# cde_profile_sample.yaml and pipeline_sample.xlsx disagree on the EIN, so both
# are listed rather than assuming one canonical value.
_SAMPLE_NAMES = frozenset({"riverbend community capital cde, llc"})
_SAMPLE_CDE_IDS = frozenset({"cde-2018-0117"})
_SAMPLE_EINS = frozenset({"82-1234567", "82-4491073"})

_FIELDS = (
    ("CDE name", _SAMPLE_NAMES),
    ("CDE ID", _SAMPLE_CDE_IDS),
    ("EIN", _SAMPLE_EINS),
)


def _norm(value) -> str:
    return str(value).strip().lower() if value is not None else ""


def matched_sample_field(name=None, cde_id=None, ein=None):
    """Return the name of the identity field that matches the shipped sample.

    Returns ``None`` when nothing matches.

    Example::

        matched_sample_field(name="Riverbend Community Capital CDE, LLC")
        # -> 'CDE name'
        matched_sample_field(name="Riverbend Housing Partners")
        # -> None   (substring overlap is not a match)
    """
    for value, (label, known) in zip((name, cde_id, ein), _FIELDS):
        normalised = _norm(value)
        if normalised and normalised in known:
            return label
    return None


def assert_not_sample_identity(name=None, cde_id=None, ein=None, source: str = "this file") -> None:
    """Refuse a CDE profile carrying the shipped sample's identity.

    Fails loud. A silent pass-through is what produced a rendered compliance
    assertion about a CDE that does not exist.

    Example::

        assert_not_sample_identity(name=cde_name, source="my_upload.xlsx")
    """
    field = matched_sample_field(name=name, cde_id=cde_id, ein=ein)
    if field is None:
        return
    raise SampleDataError(
        f"{source} carries the {field} of the fictional sample CDE that ships "
        f"with nmtc-application-builder (Riverbend Community Capital CDE, LLC "
        f"/ CDE-2018-0117). Refusing to score or generate an application "
        f"against sample identity.\n\n"
        f"Enter your own CDE's details. The blank forms are "
        f"nmtcapp/templates/pipeline_template.xlsx (CDE Profile sheet, row 4) "
        f"and nmtcapp/templates/cde_profile_template.yaml; "
        f"`nmtcapp init <dir>` writes a copy of the YAML for you.\n\n"
        f"If you are deliberately running the shipped sample, load it with "
        f"allow_sample=True (library) or --demo (CLI), which labels every "
        f"screen as fictional."
    )
