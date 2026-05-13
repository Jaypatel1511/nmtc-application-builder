"""Pipeline and PipelineProject classes for NMTC application management."""
from __future__ import annotations

import csv
import logging
from dataclasses import dataclass, field
from typing import Iterator, List, Optional

import pandas as pd

from nmtcapp.data.schema import VALID_PROJECT_TYPES, VALID_SECTORS

logger = logging.getLogger(__name__)


@dataclass
class PipelineProject:
    """A single QALICB project in the CDE's pipeline.

    Fields starting with ``is_`` / ``census_tract`` / ``distress_level`` are
    populated by :func:`~nmtcapp.integrations.nmtc_mapper_adapter.enrich_pipeline_eligibility`
    and begin as ``None``.

    Example::

        project = PipelineProject(
            project_id="PRJ-001",
            project_name="Southside Health Center",
            qalicb_name="Southside HC QALICB, LLC",
            address="3400 S Michigan Ave",
            city="Chicago",
            state="IL",
            sector="healthcare",
            project_type="real_estate",
            total_project_cost=12_000_000,
            qei_request=8_000_000,
            qlici_amount=8_000_000,
            expected_jobs_created=45,
            expected_jobs_retained=12,
        )
    """
    project_id: str
    project_name: str
    qalicb_name: str
    address: str
    city: str
    state: str
    sector: str
    project_type: str
    total_project_cost: float
    qei_request: float
    qlici_amount: float
    expected_jobs_created: int
    expected_jobs_retained: int = 0
    expected_units_built: Optional[int] = None
    expected_sq_ft: Optional[float] = None
    closing_target_date: Optional[str] = None
    construction_start: Optional[str] = None
    operations_start: Optional[str] = None

    # Populated by analyze() — do not set manually
    census_tract: Optional[str] = None
    is_nmtc_eligible: Optional[bool] = None
    distress_level: Optional[str] = None  # 'deep' | 'severe' | 'lic' | 'ineligible'
    is_native_area: Optional[bool] = None
    is_high_migration_rural: Optional[bool] = None
    is_opportunity_zone: Optional[bool] = None
    # v1.1 per-project flags — drive CDE-level scoring pcts automatically
    is_us_territory: Optional[bool] = None        # project in US Territory → pct_us_territories
    is_persistent_poverty: Optional[bool] = None  # tract is Persistent Poverty County
    is_below_market_rate: Optional[bool] = None   # QLICI offered below market → products_below_market_pct
    is_unrelated_entity: Optional[bool] = None    # QALICB is unrelated to CDE → unrelated_entities_pct

    def __post_init__(self) -> None:
        if self.total_project_cost <= 0:
            raise ValueError(f"Project {self.project_id}: total_project_cost must be > 0")
        if self.qei_request <= 0:
            raise ValueError(f"Project {self.project_id}: qei_request must be > 0")
        if self.qlici_amount <= 0:
            raise ValueError(f"Project {self.project_id}: qlici_amount must be > 0")
        if self.expected_jobs_created < 0:
            raise ValueError(f"Project {self.project_id}: expected_jobs_created must be >= 0")
        if self.sector not in VALID_SECTORS:
            logger.warning("Project %s: unrecognized sector '%s'", self.project_id, self.sector)
        if self.project_type not in VALID_PROJECT_TYPES:
            logger.warning("Project %s: unrecognized project_type '%s'",
                           self.project_id, self.project_type)

    @property
    def full_address(self) -> str:
        return f"{self.address}, {self.city}, {self.state}"

    @property
    def is_enriched(self) -> bool:
        """True if eligibility enrichment has been run on this project."""
        return self.is_nmtc_eligible is not None

    @property
    def is_deep_distress(self) -> bool:
        return self.distress_level in ("deep", "severe")

    def to_dict(self) -> dict:
        return {
            "project_id": self.project_id,
            "project_name": self.project_name,
            "qalicb_name": self.qalicb_name,
            "address": self.address,
            "city": self.city,
            "state": self.state,
            "sector": self.sector,
            "project_type": self.project_type,
            "total_project_cost": self.total_project_cost,
            "qei_request": self.qei_request,
            "qlici_amount": self.qlici_amount,
            "expected_jobs_created": self.expected_jobs_created,
            "expected_jobs_retained": self.expected_jobs_retained,
            "expected_units_built": self.expected_units_built,
            "expected_sq_ft": self.expected_sq_ft,
            "closing_target_date": self.closing_target_date,
            "census_tract": self.census_tract,
            "is_nmtc_eligible": self.is_nmtc_eligible,
            "distress_level": self.distress_level,
            "is_native_area": self.is_native_area,
            "is_high_migration_rural": self.is_high_migration_rural,
            "is_opportunity_zone": self.is_opportunity_zone,
            "is_us_territory": self.is_us_territory,
            "is_persistent_poverty": self.is_persistent_poverty,
            "is_below_market_rate": self.is_below_market_rate,
            "is_unrelated_entity": self.is_unrelated_entity,
        }


class Pipeline:
    """Container for a CDE's pipeline of NMTC candidate projects.

    Example::

        pipeline = Pipeline.sample(n=20)
        print(f"Pipeline has {len(pipeline)} projects")
        for project in pipeline:
            print(project.project_name)
    """

    def __init__(self, projects: Optional[List[PipelineProject]] = None) -> None:
        self._projects: List[PipelineProject] = projects or []

    def add(self, project: PipelineProject) -> None:
        """Add a single project to the pipeline."""
        self._projects.append(project)

    @classmethod
    def from_csv(cls, path: str) -> "Pipeline":
        """Load a pipeline from a CSV file.

        Required columns match ``PipelineProject`` field names. Numeric columns
        are coerced; optional columns default to ``None`` when absent.

        Example::

            pipeline = Pipeline.from_csv("pipeline.csv")
        """
        required_cols = {
            "project_id", "project_name", "qalicb_name",
            "address", "city", "state",
            "sector", "project_type",
            "total_project_cost", "qei_request", "qlici_amount",
            "expected_jobs_created",
        }
        try:
            df = pd.read_csv(path)
        except FileNotFoundError:
            raise FileNotFoundError(f"Pipeline CSV not found: {path}")
        except Exception as e:
            raise ValueError(f"Cannot read pipeline CSV {path}: {e}")

        missing_cols = required_cols - set(df.columns)
        if missing_cols:
            raise ValueError(f"Pipeline CSV missing required columns: {missing_cols}")

        projects = []
        for _, row in df.iterrows():
            try:
                project = PipelineProject(
                    project_id=str(row["project_id"]),
                    project_name=str(row["project_name"]),
                    qalicb_name=str(row["qalicb_name"]),
                    address=str(row["address"]),
                    city=str(row["city"]),
                    state=str(row["state"]),
                    sector=str(row["sector"]),
                    project_type=str(row["project_type"]),
                    total_project_cost=float(row["total_project_cost"]),
                    qei_request=float(row["qei_request"]),
                    qlici_amount=float(row["qlici_amount"]),
                    expected_jobs_created=int(row["expected_jobs_created"]),
                    expected_jobs_retained=int(row.get("expected_jobs_retained", 0) or 0),
                    expected_units_built=_optional_int(row.get("expected_units_built")),
                    expected_sq_ft=_optional_float(row.get("expected_sq_ft")),
                    closing_target_date=_optional_str(row.get("closing_target_date")),
                    construction_start=_optional_str(row.get("construction_start")),
                    operations_start=_optional_str(row.get("operations_start")),
                    # v1.1 per-project flags — accept Y/N/yes/no/true/false
                    is_native_area=_optional_bool(row.get("native_area")),
                    is_high_migration_rural=_optional_bool(row.get("high_migration_rural")),
                    is_opportunity_zone=_optional_bool(row.get("opportunity_zone")),
                    is_us_territory=_optional_bool(row.get("us_territory")),
                    is_persistent_poverty=_optional_bool(row.get("persistent_poverty")),
                    is_below_market_rate=_optional_bool(row.get("below_market_rate")),
                    is_unrelated_entity=_optional_bool(row.get("unrelated_entity")),
                )
                projects.append(project)
            except (ValueError, KeyError) as e:
                raise ValueError(f"Error parsing pipeline CSV row {row.get('project_id', '?')}: {e}")

        logger.info("Loaded %d projects from %s", len(projects), path)
        return cls(projects)

    @classmethod
    def sample(cls, n: int = 20) -> "Pipeline":
        """Return a realistic sample pipeline for testing and demos.

        Projects span multiple states, sectors, and distress levels.
        All eligibility fields are pre-populated (no API calls needed).

        Example::

            pipeline = Pipeline.sample(n=20)
        """
        raw = _SAMPLE_PROJECTS[:n]
        return cls(raw)

    def to_dataframe(self) -> pd.DataFrame:
        """Convert the pipeline to a pandas DataFrame.

        Example::

            df = pipeline.to_dataframe()
            print(df[["project_name", "state", "qei_request"]].head())
        """
        return pd.DataFrame([p.to_dict() for p in self._projects])

    def __len__(self) -> int:
        return len(self._projects)

    def __iter__(self) -> Iterator[PipelineProject]:
        return iter(self._projects)

    def __repr__(self) -> str:
        total_qei = sum(p.qei_request for p in self._projects)
        return (
            f"Pipeline(projects={len(self._projects)}, "
            f"total_qei=${total_qei:,.0f})"
        )


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _optional_bool(val) -> Optional[bool]:
    """Parse Y/N/yes/no/true/false/1/0 strings and native booleans to Optional[bool]."""
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return None
    if isinstance(val, bool):
        return val
    s = str(val).strip().lower()
    if s in ("y", "yes", "true", "1"):
        return True
    if s in ("n", "no", "false", "0"):
        return False
    return None


def _optional_int(val) -> Optional[int]:
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return None
    try:
        return int(val)
    except (ValueError, TypeError):
        return None


def _optional_float(val) -> Optional[float]:
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return None
    try:
        return float(val)
    except (ValueError, TypeError):
        return None


def _optional_str(val) -> Optional[str]:
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return None
    s = str(val).strip()
    return s if s else None


# ---------------------------------------------------------------------------
# Pre-built sample projects (20) — realistic spread across states / sectors
# Eligibility fields are pre-populated for offline testing.
# ---------------------------------------------------------------------------
_SAMPLE_PROJECTS: List[PipelineProject] = [
    PipelineProject(
        project_id="PRJ-001", project_name="Southside Community Health Center",
        qalicb_name="Southside HC QALICB LLC", address="3400 S Michigan Ave",
        city="Chicago", state="IL", sector="healthcare", project_type="real_estate",
        total_project_cost=12_500_000, qei_request=8_500_000, qlici_amount=8_500_000,
        expected_jobs_created=52, expected_jobs_retained=18, expected_sq_ft=24_000,
        closing_target_date="2025-09-30",
        census_tract="17031838200", is_nmtc_eligible=True, distress_level="deep",
        is_native_area=False, is_high_migration_rural=False, is_opportunity_zone=False,
        is_us_territory=False, is_persistent_poverty=True, is_below_market_rate=True,
        is_unrelated_entity=True,
    ),
    PipelineProject(
        project_id="PRJ-002", project_name="East Houston Charter Academy",
        qalicb_name="East Houston Academy QALICB LLC", address="5200 Lawndale St",
        city="Houston", state="TX", sector="education", project_type="real_estate",
        total_project_cost=9_800_000, qei_request=7_000_000, qlici_amount=7_000_000,
        expected_jobs_created=38, expected_jobs_retained=22,
        closing_target_date="2025-12-15",
        census_tract="48201223400", is_nmtc_eligible=True, distress_level="deep",
        is_native_area=False, is_high_migration_rural=False, is_opportunity_zone=True,
    ),
    PipelineProject(
        project_id="PRJ-003", project_name="Bronx Food Hub",
        qalicb_name="Bronx Food Hub QALICB LLC", address="800 Hunts Point Ave",
        city="Bronx", state="NY", sector="small_business", project_type="real_estate",
        total_project_cost=7_200_000, qei_request=5_000_000, qlici_amount=5_000_000,
        expected_jobs_created=65, expected_jobs_retained=8, expected_sq_ft=18_000,
        closing_target_date="2025-08-31",
        census_tract="36005035900", is_nmtc_eligible=True, distress_level="severe",
        is_native_area=False, is_high_migration_rural=False, is_opportunity_zone=True,
    ),
    PipelineProject(
        project_id="PRJ-004", project_name="Watts Manufacturing Center",
        qalicb_name="Watts MFG QALICB LLC", address="9500 S Grape St",
        city="Los Angeles", state="CA", sector="small_business", project_type="operating_business",
        total_project_cost=6_000_000, qei_request=4_500_000, qlici_amount=4_500_000,
        expected_jobs_created=80, expected_jobs_retained=25,
        closing_target_date="2025-11-30",
        census_tract="06037606200", is_nmtc_eligible=True, distress_level="deep",
        is_native_area=False, is_high_migration_rural=False, is_opportunity_zone=False,
    ),
    PipelineProject(
        project_id="PRJ-005", project_name="Cleveland Neighborhood Clinic",
        qalicb_name="Cleveland Clinic QALICB LLC", address="2100 Euclid Ave",
        city="Cleveland", state="OH", sector="healthcare", project_type="real_estate",
        total_project_cost=10_000_000, qei_request=7_500_000, qlici_amount=7_500_000,
        expected_jobs_created=42, expected_jobs_retained=30, expected_sq_ft=20_000,
        closing_target_date="2026-01-31",
        census_tract="39035103200", is_nmtc_eligible=True, distress_level="deep",
        is_native_area=False, is_high_migration_rural=False, is_opportunity_zone=False,
    ),
    PipelineProject(
        project_id="PRJ-006", project_name="Atlanta Affordable Homes Phase II",
        qalicb_name="Atlanta AH QALICB LLC", address="640 McDaniel St SW",
        city="Atlanta", state="GA", sector="affordable_housing", project_type="real_estate",
        total_project_cost=14_000_000, qei_request=9_000_000, qlici_amount=9_000_000,
        expected_jobs_created=15, expected_jobs_retained=5, expected_units_built=72,
        closing_target_date="2025-10-31",
        census_tract="13121008700", is_nmtc_eligible=True, distress_level="severe",
        is_native_area=False, is_high_migration_rural=False, is_opportunity_zone=True,
    ),
    PipelineProject(
        project_id="PRJ-007", project_name="Miami Community Resource Center",
        qalicb_name="Miami CRC QALICB LLC", address="3000 NW 27th Ave",
        city="Miami", state="FL", sector="community_facility", project_type="real_estate",
        total_project_cost=5_500_000, qei_request=4_000_000, qlici_amount=4_000_000,
        expected_jobs_created=28, expected_jobs_retained=10, expected_sq_ft=12_000,
        closing_target_date="2025-09-15",
        census_tract="12086000900", is_nmtc_eligible=True, distress_level="lic",
        is_native_area=False, is_high_migration_rural=False, is_opportunity_zone=False,
    ),
    PipelineProject(
        project_id="PRJ-008", project_name="North Philadelphia Wellness Hub",
        qalicb_name="North Philly Wellness QALICB LLC", address="2500 N Broad St",
        city="Philadelphia", state="PA", sector="healthcare", project_type="mixed_use",
        total_project_cost=11_000_000, qei_request=8_000_000, qlici_amount=8_000_000,
        expected_jobs_created=55, expected_jobs_retained=20, expected_sq_ft=22_000,
        closing_target_date="2026-03-31",
        census_tract="42101017900", is_nmtc_eligible=True, distress_level="deep",
        is_native_area=False, is_high_migration_rural=False, is_opportunity_zone=False,
    ),
    PipelineProject(
        project_id="PRJ-009", project_name="New Orleans Culinary Arts Center",
        qalicb_name="NOLA Culinary QALICB LLC", address="1800 Oretha Castle Haley Blvd",
        city="New Orleans", state="LA", sector="education", project_type="real_estate",
        total_project_cost=8_200_000, qei_request=6_000_000, qlici_amount=6_000_000,
        expected_jobs_created=35, expected_jobs_retained=8, expected_sq_ft=16_000,
        closing_target_date="2025-11-15",
        census_tract="22071008500", is_nmtc_eligible=True, distress_level="deep",
        is_native_area=False, is_high_migration_rural=False, is_opportunity_zone=True,
    ),
    PipelineProject(
        project_id="PRJ-010", project_name="Memphis Small Business Incubator",
        qalicb_name="Memphis SBI QALICB LLC", address="400 Monroe Ave",
        city="Memphis", state="TN", sector="small_business", project_type="operating_business",
        total_project_cost=4_800_000, qei_request=3_500_000, qlici_amount=3_500_000,
        expected_jobs_created=90, expected_jobs_retained=15,
        closing_target_date="2025-08-15",
        census_tract="47157002400", is_nmtc_eligible=True, distress_level="deep",
        is_native_area=False, is_high_migration_rural=False, is_opportunity_zone=False,
    ),
    PipelineProject(
        project_id="PRJ-011", project_name="Milwaukee Affordable Apartments",
        qalicb_name="MKE Affordable QALICB LLC", address="1900 W National Ave",
        city="Milwaukee", state="WI", sector="affordable_housing", project_type="real_estate",
        total_project_cost=13_500_000, qei_request=9_500_000, qlici_amount=9_500_000,
        expected_jobs_created=12, expected_jobs_retained=4, expected_units_built=64,
        closing_target_date="2026-02-28",
        census_tract="55079141700", is_nmtc_eligible=True, distress_level="severe",
        is_native_area=False, is_high_migration_rural=False, is_opportunity_zone=False,
    ),
    PipelineProject(
        project_id="PRJ-012", project_name="St. Louis Community Solar Project",
        qalicb_name="STL Solar QALICB LLC", address="3600 Market St",
        city="St. Louis", state="MO", sector="clean_energy", project_type="operating_business",
        total_project_cost=5_000_000, qei_request=3_800_000, qlici_amount=3_800_000,
        expected_jobs_created=22, expected_jobs_retained=6,
        closing_target_date="2025-10-15",
        census_tract="29510109500", is_nmtc_eligible=True, distress_level="lic",
        is_native_area=False, is_high_migration_rural=False, is_opportunity_zone=True,
    ),
    PipelineProject(
        project_id="PRJ-013", project_name="Charlotte Workforce Training Center",
        qalicb_name="Charlotte WTC QALICB LLC", address="2800 Freedom Dr",
        city="Charlotte", state="NC", sector="education", project_type="real_estate",
        total_project_cost=7_500_000, qei_request=5_500_000, qlici_amount=5_500_000,
        expected_jobs_created=30, expected_jobs_retained=12, expected_sq_ft=14_000,
        closing_target_date="2025-12-31",
        census_tract="37119001900", is_nmtc_eligible=True, distress_level="deep",
        is_native_area=False, is_high_migration_rural=False, is_opportunity_zone=False,
    ),
    PipelineProject(
        project_id="PRJ-014", project_name="Phoenix Native American Health Clinic",
        qalicb_name="Phoenix Native HC QALICB LLC", address="4212 W Indian School Rd",
        city="Phoenix", state="AZ", sector="healthcare", project_type="real_estate",
        total_project_cost=9_000_000, qei_request=6_500_000, qlici_amount=6_500_000,
        expected_jobs_created=48, expected_jobs_retained=25, expected_sq_ft=18_500,
        closing_target_date="2026-01-15",
        census_tract="04013118400", is_nmtc_eligible=True, distress_level="deep",
        is_native_area=True, is_high_migration_rural=False, is_opportunity_zone=False,
        is_us_territory=False, is_persistent_poverty=True, is_below_market_rate=True,
        is_unrelated_entity=True,
    ),
    PipelineProject(
        project_id="PRJ-015", project_name="Detroit Auto Parts Manufacturer",
        qalicb_name="Detroit Auto Parts QALICB LLC", address="7800 E Jefferson Ave",
        city="Detroit", state="MI", sector="small_business", project_type="operating_business",
        total_project_cost=6_500_000, qei_request=5_000_000, qlici_amount=5_000_000,
        expected_jobs_created=110, expected_jobs_retained=45,
        closing_target_date="2025-09-30",
        census_tract="26163527900", is_nmtc_eligible=True, distress_level="deep",
        is_native_area=False, is_high_migration_rural=False, is_opportunity_zone=True,
    ),
    PipelineProject(
        project_id="PRJ-016", project_name="Indianapolis Mixed-Use Community Hub",
        qalicb_name="Indy Community Hub QALICB LLC", address="1200 N Alabama St",
        city="Indianapolis", state="IN", sector="mixed_use", project_type="mixed_use",
        total_project_cost=10_500_000, qei_request=7_500_000, qlici_amount=7_500_000,
        expected_jobs_created=35, expected_jobs_retained=10, expected_sq_ft=20_000,
        expected_units_built=24, closing_target_date="2026-03-15",
        census_tract="18097350200", is_nmtc_eligible=True, distress_level="severe",
        is_native_area=False, is_high_migration_rural=False, is_opportunity_zone=False,
    ),
    PipelineProject(
        project_id="PRJ-017", project_name="Rural Mississippi Health Access Center",
        qalicb_name="Rural MS Health QALICB LLC", address="510 Main St",
        city="Greenville", state="MS", sector="healthcare", project_type="real_estate",
        total_project_cost=4_200_000, qei_request=3_200_000, qlici_amount=3_200_000,
        expected_jobs_created=20, expected_jobs_retained=15, expected_sq_ft=8_000,
        closing_target_date="2025-11-30",
        census_tract="28065950100", is_nmtc_eligible=True, distress_level="deep",
        is_native_area=False, is_high_migration_rural=True, is_opportunity_zone=False,
        is_us_territory=False, is_persistent_poverty=True, is_below_market_rate=True,
        is_unrelated_entity=True,
    ),
    PipelineProject(
        project_id="PRJ-018", project_name="Kansas City Affordable Senior Housing",
        qalicb_name="KC Senior Housing QALICB LLC", address="3500 Troost Ave",
        city="Kansas City", state="KS", sector="affordable_housing", project_type="real_estate",
        total_project_cost=11_800_000, qei_request=8_500_000, qlici_amount=8_500_000,
        expected_jobs_created=10, expected_jobs_retained=3, expected_units_built=56,
        closing_target_date="2026-02-15",
        census_tract="20091000100", is_nmtc_eligible=True, distress_level="lic",
        is_native_area=False, is_high_migration_rural=False, is_opportunity_zone=False,
    ),
    PipelineProject(
        project_id="PRJ-019", project_name="Baltimore Community Food Market",
        qalicb_name="Baltimore Food QALICB LLC", address="2700 Pennsylvania Ave",
        city="Baltimore", state="MD", sector="community_facility", project_type="real_estate",
        total_project_cost=5_800_000, qei_request=4_200_000, qlici_amount=4_200_000,
        expected_jobs_created=45, expected_jobs_retained=8, expected_sq_ft=11_000,
        closing_target_date="2025-10-31",
        census_tract="24510050200", is_nmtc_eligible=True, distress_level="severe",
        is_native_area=False, is_high_migration_rural=False, is_opportunity_zone=False,
    ),
    PipelineProject(
        project_id="PRJ-020", project_name="Albuquerque Mixed-Use Arts District",
        qalicb_name="ABQ Arts QALICB LLC", address="400 Central Ave NE",
        city="Albuquerque", state="NM", sector="mixed_use", project_type="mixed_use",
        total_project_cost=7_800_000, qei_request=5_800_000, qlici_amount=5_800_000,
        expected_jobs_created=32, expected_jobs_retained=9, expected_sq_ft=15_000,
        expected_units_built=18, closing_target_date="2025-12-15",
        census_tract="35001000900", is_nmtc_eligible=True, distress_level="deep",
        is_native_area=True, is_high_migration_rural=False, is_opportunity_zone=True,
    ),
]
