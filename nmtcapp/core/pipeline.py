"""Pipeline and PipelineProject classes for NMTC application management."""
from __future__ import annotations

import csv
import logging
from dataclasses import dataclass, field
from typing import Iterator, List, Optional

import pandas as pd

from nmtcapp.data.schema import (
    REQUIRED_PROJECT_FIELDS, VALID_PROJECT_TYPES, VALID_SECTORS,
)

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

    # ── CDE-DECLARED, read from the upload ────────────────────────────────
    # The shipped v1.1 xlsx template collects both of these — "Census Tract
    # (11-digit)" (col 24) and "Distress Level" (col 15, with a validated
    # dropdown) — and upload_handler maps both. Through 1.1.5 from_csv read
    # NEITHER, so everything a CDE typed into those two columns was written to
    # a temp CSV and silently dropped on the floor.
    #
    # They are deliberately SEPARATE fields from the tool-verified
    # census_tract / distress_level below, not the same field pre-seeded.
    # Merging them would mean a CDE's self-certification and a CDFI Fund
    # lookup shared one slot, so enrichment would have to overwrite one with
    # the other and the rendered value could not say which it was. Keeping two
    # fields makes the provenance structural rather than a convention.
    declared_census_tract: Optional[str] = None
    declared_distress_level: Optional[str] = None

    # ── WHETHER THE CDE ACTUALLY SUPPLIED qlici_amount (1.3.0 S3) ──────────
    #
    # core/upload_handler set ``qlici_amount = qei_request`` whenever the
    # column was absent from an upload, silently, and that value then rendered
    # as "Total QLICI ($)" — the CDE's own answer to the Fund's Table A5 row
    # (h) — in Appendix A on markdown, Word, PDF and Excel. Four passes over
    # this package missed it because every fixture in the tree sets the two
    # equal anyway, so the defaulted value was indistinguishable from a real
    # one in every test that existed.
    #
    # STRUCTURAL, NOT INFERRED. The obvious cheap check — ``qlici_amount ==
    # qei_request`` — is true of both shipped samples, of Pipeline.sample(),
    # of the pin fixtures and of the rendered baseline fixture, and would
    # therefore fire on a CDE whose figures legitimately match. Whether the
    # value was supplied is a fact known at read time; it is carried, in the
    # same spirit as declared_census_tract above, rather than reconstructed.
    #
    # IT CROSSES A SERIALIZATION BOUNDARY, which is why from_csv reads a column
    # for it. load_uploaded_pipeline writes its DataFrame to a temporary CSV
    # and re-reads it through from_csv, so an attribute set on the way in would
    # not survive; the flag rides the CSV as ``qlici_amount_supplied``.
    qlici_amount_supplied: bool = True

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
    # v1.1.5 — set by enrichment; False means the project location could not
    # be verified, so eligibility fields stay None (unverified, NOT ineligible)
    geocode_success: Optional[bool] = None

    def __post_init__(self) -> None:
        if self.total_project_cost <= 0:
            raise ValueError(f"Project {self.project_id}: total_project_cost must be > 0")
        if self.qei_request <= 0:
            raise ValueError(f"Project {self.project_id}: qei_request must be > 0")
        if self.qlici_amount <= 0:
            raise ValueError(f"Project {self.project_id}: qlici_amount must be > 0")
        if self.expected_jobs_created < 0:
            raise ValueError(f"Project {self.project_id}: expected_jobs_created must be >= 0")
        # THE SECTOR LIST IS A SUGGESTION ON THE WAY IN AND A CONTRACT ON THE
        # WAY OUT (1.2.1 L-5).
        #
        # It used to be neither. An unrecognised sector logged a warning to
        # stderr, which nobody running `nmtcapp generate` reads, and then
        # rendered as "Retail" in Appendix D beside seven sectors the Fund's
        # own categories cover — indistinguishable, on the page, from a
        # recognised one.
        #
        # Raising here was considered and rejected for a PATCH release: it
        # would reject pipelines that load today, and a CDE whose business is
        # genuinely outside the eight has a legitimate home in "other". So
        # loading still succeeds. What changes is that the DOCUMENT says so:
        # tables/pipeline_table and tables/impact_table render an unrecognised
        # sector with an explicit marker, so a reviewer sees the tool did not
        # recognise it rather than seeing it silently normalised.
        if self.sector not in VALID_SECTORS:
            logger.warning(
                "Project %s: sector '%s' is not one of the %d sectors this tool "
                "recognises (%s). The project loads and every figure derived "
                "from it is unaffected, but the rendered tables will mark the "
                "sector as unrecognised rather than print it as though it were "
                "a known category.",
                self.project_id, self.sector, len(VALID_SECTORS),
                ", ".join(VALID_SECTORS),
            )
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

    def tract_display(self) -> str:
        """Census tract with its provenance, never bare.

        A tool-verified GEOID and a GEOID the CDE typed into the template are
        different kinds of fact and must not render identically — the row that
        carries them also carries a "CDFI Fund NMTC Eligibility Table"
        citation, and a CDE-declared tract was never checked against that
        table or against the project address.

        Example::

            p.tract_display()   # '17031838200 (CDE-declared, not verified)'
        """
        if self.census_tract:
            return str(self.census_tract)
        if self.declared_census_tract:
            return f"{self.declared_census_tract} (CDE-declared, not verified)"
        return "—"

    def distress_display(self) -> str:
        """Distress level with its provenance, never bare.

        The CDE's declared level is shown when the tool has no verified one,
        so the upload is not silently discarded — but it is labelled, because
        self-certification is not a CDFI Fund determination.
        """
        if self.distress_level:
            return str(self.distress_level)
        if self.declared_distress_level:
            return f"{self.declared_distress_level} (CDE-declared, not verified)"
        return "—"

    @property
    def eligibility_status(self) -> str:
        """Human-readable eligibility verification status for output surfaces."""
        if self.is_nmtc_eligible is not None:
            return "verified"
        if self.geocode_success is False:
            return "unverified — location could not be verified"
        return "unverified — eligibility data not available"

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
            "qlici_amount_supplied": self.qlici_amount_supplied,
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
            "geocode_success": self.geocode_success,
            "eligibility_status": self.eligibility_status,
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
        # Fail-closed default: a pipeline that never went through enrichment
        # must read as degraded, not verified-complete. The adapter sets "ok"
        # when live CDFI Fund data was used and "unavailable" when it could
        # not be loaded (fields stay None); every consumer treats != "ok"
        # as degraded.
        self.eligibility_data_status: str = "unenriched"
        self.eligibility_data_error: Optional[str] = None

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
        # READ THE LIST, DO NOT RETYPE IT (FIX-2 G-5 sweep, third instance).
        #
        # These twelve names were stated in three independent places —
        # data/schema.REQUIRED_PROJECT_FIELDS (which validation/
        # completeness_check imports), this set, and PipelineProject's own
        # non-default dataclass fields. They agreed, by hand and by luck, and
        # the mutation profile is identical to the required-CDE-fields
        # triplication fixed in this same pass: dropping a name from the
        # SCHEMA list stops completeness_check flagging it while from_csv
        # still demands it and every test passes, and adding one to the schema
        # lets a CSV load that later fails at render time.
        #
        # Now derived. The dataclass is checked against the same list by
        # tests/test_121_financial_tables — three statements, one authority.
        required_cols = set(REQUIRED_PROJECT_FIELDS)
        # Skip LEADING '#' lines before the header row. The shipped sample CSVs
        # carry their fictional-data notice at the top, where a human reads it
        # first; pandas would otherwise take that notice as the header and
        # fail with a tokenizing error. Comment rows BELOW the header are
        # dropped separately a few lines down — pipeline_template.csv puts its
        # field documentation there. `comment="#"` is deliberately not used:
        # it would truncate any notes cell containing a '#'.
        try:
            with open(path, "r", encoding="utf-8-sig", errors="replace") as fh:
                skip = 0
                for line in fh:
                    if line.lstrip().startswith("#"):
                        skip += 1
                    else:
                        break
        except FileNotFoundError:
            raise FileNotFoundError(f"Pipeline CSV not found: {path}")

        try:
            df = pd.read_csv(path, skiprows=skip)
        except FileNotFoundError:
            raise FileNotFoundError(f"Pipeline CSV not found: {path}")
        except Exception as e:
            raise ValueError(f"Cannot read pipeline CSV {path}: {e}")

        missing_cols = required_cols - set(df.columns)
        if missing_cols:
            raise ValueError(f"Pipeline CSV missing required columns: {missing_cols}")

        # Drop comment rows (template CSV includes # comment lines as documentation)
        if "project_id" in df.columns:
            df = df[~df["project_id"].astype(str).str.startswith("#")].reset_index(drop=True)

        if len(df) == 0:
            raise ValueError(
                "No project rows found. The file contains only column headers or comments. "
                "Please add your project data rows before uploading."
            )

        projects = []
        for _, row in df.iterrows():
            pid = _optional_str(row.get("project_id")) or "?"
            try:
                project = PipelineProject(
                    project_id=_required_str(row["project_id"], "project_id"),
                    project_name=_required_str(row["project_name"], "project_name"),
                    qalicb_name=_required_str(row["qalicb_name"], "qalicb_name"),
                    address=_required_str(row["address"], "address"),
                    city=_required_str(row["city"], "city"),
                    state=_required_str(row["state"], "state"),
                    sector=_required_str(row["sector"], "sector"),
                    project_type=_required_str(row["project_type"], "project_type"),
                    total_project_cost=_required_float(row["total_project_cost"], "total_project_cost"),
                    qei_request=_required_float(row["qei_request"], "qei_request"),
                    qlici_amount=_required_float(row["qlici_amount"], "qlici_amount"),
                    # 1.3.0 S3. Absent column -> True, because a CSV that
                    # reaches here at all carries qlici_amount (it is in
                    # REQUIRED_PROJECT_FIELDS, checked above), so the value is
                    # the CDE's. The column exists for the ONE writer that
                    # knows otherwise: core/upload_handler, which synthesises
                    # qlici_amount when an upload omits it and must say so
                    # across the temp-CSV boundary between it and this loader.
                    qlici_amount_supplied=(
                        _optional_bool(row.get("qlici_amount_supplied"))
                        is not False
                    ),
                    expected_jobs_created=_required_int(row["expected_jobs_created"], "expected_jobs_created"),
                    expected_jobs_retained=_int_with_default(row.get("expected_jobs_retained"), 0),
                    expected_units_built=_optional_int(row.get("expected_units_built")),
                    expected_sq_ft=_optional_float(row.get("expected_sq_ft")),
                    closing_target_date=_optional_str(row.get("closing_target_date")),
                    construction_start=_optional_str(row.get("construction_start")),
                    operations_start=_optional_str(row.get("operations_start")),
                    # v1.1 per-project flags — accept Y/N/yes/no/true/false
                    # CDE-declared columns — present in the shipped template
                    # and dropped entirely until 1.2.0.
                    declared_census_tract=_optional_str(row.get("census_tract")),
                    declared_distress_level=_optional_str(row.get("distress_level")),
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
                raise ValueError(f"Error parsing pipeline CSV row {pid}: {e}")

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
        pipeline = cls(raw)
        # The sample fixture ships pre-verified eligibility data for offline
        # demos and tests — the one construction path that may claim "ok"
        # without going through the adapter.
        pipeline.eligibility_data_status = "ok"
        return pipeline

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

def _required_str(val, field_name: str) -> str:
    """Parse a required string field; raises ValueError with a user-friendly message if blank."""
    if val is None or (isinstance(val, float) and pd.isna(val)):
        raise ValueError(f"'{field_name}' is required but was left blank")
    s = str(val).strip()
    if not s or s.lower() == "nan":
        raise ValueError(f"'{field_name}' is required but was left blank")
    return s


def _required_float(val, field_name: str) -> float:
    """Parse a required float field; raises ValueError with a user-friendly message if blank."""
    if val is None or (isinstance(val, float) and pd.isna(val)):
        raise ValueError(f"'{field_name}' is required but was left blank")
    try:
        result = float(val)
    except (ValueError, TypeError):
        raise ValueError(f"'{field_name}' must be a number, got: {val!r}")
    if pd.isna(result):
        raise ValueError(f"'{field_name}' is required but was left blank")
    return result


def _required_int(val, field_name: str) -> int:
    """Parse a required integer field; raises ValueError with a user-friendly message if blank."""
    if val is None or (isinstance(val, float) and pd.isna(val)):
        raise ValueError(f"'{field_name}' is required but was left blank")
    try:
        f = float(val)
    except (ValueError, TypeError):
        raise ValueError(f"'{field_name}' must be a whole number, got: {val!r}")
    if pd.isna(f):
        raise ValueError(f"'{field_name}' is required but was left blank")
    return int(f)


def _int_with_default(val, default: int = 0) -> int:
    """Parse an optional integer, returning default when blank or missing."""
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return default
    try:
        f = float(val)
        return default if pd.isna(f) else int(f)
    except (ValueError, TypeError):
        return default


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
        qalicb_name="Charlotte WTC QALICB LLC", address="2810 Freedom Dr",
        city="Charlotte", state="NC", sector="education", project_type="real_estate",
        total_project_cost=7_500_000, qei_request=5_500_000, qlici_amount=5_500_000,
        expected_jobs_created=30, expected_jobs_retained=12, expected_sq_ft=14_000,
        closing_target_date="2025-12-31",
        # C-3: "2800 Freedom Dr" is absent from the Census TIGER address ranges
        # for Freedom Drive (2700, 2801, 2810 and 2900 all resolve), so every
        # demo run printed "Location could not be verified". Nudged to 2810,
        # which resolves, and the tract and distress level are the workbook's
        # own values for it rather than the invented 37119001900.
        census_tract="37119004200", is_nmtc_eligible=True, distress_level="severe",
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
        # C-3: this row said KANSAS. Troost Avenue is a Kansas City, MISSOURI
        # street; Kansas City KS is a separate municipality across the state
        # line. The Census geocoder resolves the address to 3500 TROOST AVE,
        # KANSAS CITY, MO 64109, tract 29095017800 (Jackson County, MO), and
        # refuses it when the state is given as KS — which is why it rendered
        # as "could not be verified" rather than as the wrong-state row it was.
        # Tract corrected with the state, because leaving the Kansas GEOID
        # 20091000100 on a Missouri row would fail consistency_check's own
        # state-FIPS test.
        city="Kansas City", state="MO", sector="affordable_housing", project_type="real_estate",
        total_project_cost=11_800_000, qei_request=8_500_000, qlici_amount=8_500_000,
        expected_jobs_created=10, expected_jobs_retained=3, expected_units_built=56,
        closing_target_date="2026-02-15",
        census_tract="29095017800", is_nmtc_eligible=True, distress_level="lic",
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
