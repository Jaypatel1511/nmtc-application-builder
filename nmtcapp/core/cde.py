"""CDE (Community Development Entity) profile definition and helpers."""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional

import yaml

logger = logging.getLogger(__name__)


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
    def from_yaml(cls, path: str) -> "CDEProfile":
        """Load a CDEProfile from a YAML file.

        The YAML file should have keys matching CDEProfile field names.

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

        required = {"name", "cde_id", "certification_date", "mission",
                    "target_markets", "prior_awards", "contact", "governance"}
        missing = required - set(data.keys())
        if missing:
            raise ValueError(f"CDE YAML missing required fields: {missing}")

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
