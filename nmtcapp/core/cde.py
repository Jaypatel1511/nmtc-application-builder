"""CDE (Community Development Entity) profile definition and helpers."""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional

import yaml

logger = logging.getLogger(__name__)


# Human-readable description of every field ``from_yaml`` requires, keyed by
# the YAML key. Used to build the error a CDE actually sees: 1.1.5 printed a
# raw Python set difference ("missing required fields: {'contact',
# 'governance', ...}"), which names the keys but not what to put in them, and
# gave no hint that the shipped scaffold used DIFFERENT names for two of them.
_FIELD_GUIDANCE = {
    "name": "your CDE's full legal name",
    "cde_id": "your CDFI Fund CDE certification ID, e.g. CDE-2025-001",
    "certification_date": "the date your CDE was certified, as YYYY-MM-DD",
    "mission": "your CDE's mission statement, one or two sentences",
    "target_markets": "the states or markets you deploy into, as a YAML list",
    "prior_awards": "prior NMTC allocations, as a YAML list (use [] if none)",
    "contact": "a mapping with at least name and email",
    "governance": "a mapping describing your board, e.g. board_members: 7",
}


def _missing_fields_message(path: str, missing: set, data: dict) -> str:
    """Name what the CDE must complete, in the order the scaffold lists it."""
    lines = [
        f"CDE profile {path} is missing {len(missing)} required "
        f"field{'s' if len(missing) != 1 else ''}:",
        "",
    ]
    for key in _FIELD_GUIDANCE:
        if key in missing:
            lines.append(f"  {key}: <{_FIELD_GUIDANCE[key]}>")
    for key in sorted(missing - set(_FIELD_GUIDANCE)):
        lines.append(f"  {key}: <required>")
    lines += [
        "",
        "Add each key at the top level of the file. "
        "`nmtcapp init <dir>` writes a scaffold with every one of them.",
    ]
    return "\n".join(lines)


@dataclass
class CDEProfile:
    """Complete profile of a Community Development Entity applying for NMTC allocation.

    Example::

        cde = CDEProfile(
            name="Midwest Impact CDE, LLC",
            cde_id="CDE-2019-0042",
            certification_date="2019-03-15",
            mission="Deploy NMTC capital in deep-distress communities across the Midwest",
            target_markets=["Illinois", "Ohio", "Michigan", "Wisconsin"],
            prior_awards=[{"year": 2021, "amount": 45_000_000, "deployment_status": "fully_deployed"}],
            contact={"name": "Jane Smith", "email": "jsmith@midwestimpact.org"},
            governance={"board_members": 7, "community_representatives": 3},
        )
    """
    name: str
    cde_id: str
    certification_date: str
    mission: str
    target_markets: List[str]
    prior_awards: List[Dict]
    contact: Dict
    governance: Dict
    website: Optional[str] = None
    extra: Dict = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.name or not self.name.strip():
            raise ValueError("CDEProfile.name must not be empty")
        if not self.cde_id or not self.cde_id.strip():
            raise ValueError("CDEProfile.cde_id must not be empty")
        if not isinstance(self.target_markets, list):
            raise ValueError("CDEProfile.target_markets must be a list")
        if not isinstance(self.prior_awards, list):
            raise ValueError("CDEProfile.prior_awards must be a list")

    @classmethod
    def from_yaml(cls, path: str, allow_sample: bool = False) -> "CDEProfile":
        """Load a CDEProfile from a YAML file.

        The YAML file should have keys matching CDEProfile field names; the
        shipped ``cde_profile_template.yaml`` uses exactly those names.

        Refuses a file carrying the shipped sample CDE's identity unless
        ``allow_sample=True`` — see :mod:`nmtcapp.core.sample_identity`.

        Example::

            cde = CDEProfile.from_yaml("my_cde.yaml")
        """
        try:
            with open(path, "r") as f:
                data = yaml.safe_load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"CDE profile file not found: {path}")
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in CDE profile {path}: {e}")

        if not isinstance(data, dict):
            raise ValueError(
                f"CDE profile {path} did not parse to a mapping of fields. "
                "Expected a YAML file with top-level keys such as 'name' and "
                "'cde_id'."
            )

        required = {"name", "cde_id", "certification_date", "mission",
                    "target_markets", "prior_awards", "contact", "governance"}
        # A key present but left blank is NOT completed. The scaffold ships
        # every required key with an empty value, so an untouched scaffold has
        # no absent keys at all — checking only for absence let it through to
        # __post_init__, which said "CDEProfile.name must not be empty" and
        # named exactly one of the eight things still to do.
        #
        # prior_awards is the one exception: [] is a real answer, meaning a
        # first-time applicant with no prior allocation.
        blank_is_answer = {"prior_awards"}
        missing = {
            key for key in required
            if key not in data
            or (key not in blank_is_answer and data.get(key) in ("", [], {}, None))
        }
        if missing:
            raise ValueError(_missing_fields_message(path, missing, data))

        # Refuse shipped sample identity before anything is scored or rendered.
        if not allow_sample:
            from nmtcapp.core.sample_identity import assert_not_sample_identity
            assert_not_sample_identity(
                name=data.get("name"),
                cde_id=data.get("cde_id"),
                ein=data.get("ein"),
                source=path,
            )

        known_keys = {
            "name", "cde_id", "certification_date", "mission",
            "target_markets", "prior_awards", "contact", "governance",
            "website",
        }
        extra = {k: v for k, v in data.items() if k not in known_keys}
        return cls(
            name=data["name"],
            cde_id=data["cde_id"],
            certification_date=data["certification_date"],
            mission=data["mission"],
            target_markets=data["target_markets"],
            prior_awards=data.get("prior_awards", []),
            contact=data["contact"],
            governance=data["governance"],
            website=data.get("website"),
            extra=extra,
        )

    @classmethod
    def sample(cls) -> "CDEProfile":
        """Return a realistic sample CDEProfile for testing and demos.

        Example::

            cde = CDEProfile.sample()
            print(cde.name)
        """
        return cls(
            name="Riverbend Community Capital CDE, LLC",
            cde_id="CDE-2018-0117",
            certification_date="2018-06-20",
            mission=(
                "Deploy New Markets Tax Credit capital into deep-distress communities "
                "across the Midwest and South, with a focus on healthcare, education, "
                "and small business operating businesses in persistent poverty counties."
            ),
            target_markets=[
                "Illinois", "Ohio", "Michigan", "Indiana",
                "Tennessee", "Georgia", "Louisiana", "Missouri",
            ],
            prior_awards=[
                {"year": 2019, "amount": 40_000_000, "deployment_status": "fully_deployed",
                 "states": ["IL", "OH", "TN"], "sectors": ["healthcare", "small_business"]},
                {"year": 2021, "amount": 55_000_000, "deployment_status": "fully_deployed",
                 "states": ["IL", "GA", "LA"], "sectors": ["education", "affordable_housing"]},
                {"year": 2023, "amount": 60_000_000, "deployment_status": "partially_deployed",
                 "states": ["OH", "MI", "MO", "TN"], "sectors": ["healthcare", "community_facility"]},
            ],
            contact={
                "name": "Sarah Johnson",
                "title": "President & CEO",
                "email": "sjohnson@riverbendcapital.org",
                "phone": "312-555-0192",
            },
            governance={
                "board_members": 9,
                "community_representatives": 4,
                "independent_directors": 3,
                "board_meeting_frequency": "quarterly",
            },
            website="https://riverbendcommunitycapital.org",
            extra={
                # Business Strategy scoring inputs
                "products_below_market_pct": 0.42,
                "products_flexible_indicia_count": 5,
                "pipeline_pct_identified": 0.83,
                "has_own_capital_at_risk": False,
                "prior_award_count": 3,
                "years_in_operation": 7,
                "track_record_pipeline_alignment_pct": 0.76,
                "track_record_deployment_pct": 0.80,
                # Community Outcomes scoring inputs
                "pct_persistent_poverty": 0.31,
                "pct_us_territories": 0.0,
                "has_quantified_outcomes": True,
                "has_third_party_validation": True,
                "lic_board_representation_pct": 0.44,
                "has_community_engagement_track_record": True,
                # Priority Points scoring inputs
                "dbc_focus_years": 4,
                "dbc_dollar_volume_pct": 0.62,
                "unrelated_entities_pct": 0.82,
                # Phase 2 flags
                "has_favorable_fee_structure": True,
                "has_prior_reporting_issues": False,
            },
        )

    def total_prior_allocation(self) -> float:
        """Sum of all prior award amounts in dollars."""
        return sum(a.get("amount", 0) for a in self.prior_awards)

    def to_dict(self) -> Dict:
        """Serialize to a JSON-safe dictionary."""
        return {
            "name": self.name,
            "cde_id": self.cde_id,
            "certification_date": self.certification_date,
            "mission": self.mission,
            "target_markets": self.target_markets,
            "prior_awards": self.prior_awards,
            "contact": self.contact,
            "governance": self.governance,
            "website": self.website,
            "total_prior_allocation": self.total_prior_allocation(),
        }
