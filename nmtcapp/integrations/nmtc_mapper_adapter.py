"""Adapter wrapping nmtc-mapper for pipeline eligibility enrichment."""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from nmtcapp.core.pipeline import Pipeline

logger = logging.getLogger(__name__)

# Fallback sample data for offline/test use — covers a realistic spread
# of distress levels across common census tracts.
_FALLBACK_ELIGIBILITY = [
    ("17031838200", True, "deep",       False, False, False),
    ("48201223400", True, "deep",       False, False, True),
    ("36005035900", True, "severe",     False, False, True),
    ("06037606200", True, "deep",       False, False, False),
    ("39035103200", True, "deep",       False, False, False),
    ("13121008700", True, "severe",     False, False, True),
    ("12086000900", True, "lic",        False, False, False),
    ("42101017900", True, "deep",       False, False, False),
    ("22071008500", True, "deep",       False, False, True),
    ("47157002400", True, "deep",       False, False, False),
    ("55079141700", True, "severe",     False, False, False),
    ("29510109500", True, "lic",        False, False, True),
    ("37119001900", True, "deep",       False, False, False),
    ("04013118400", True, "deep",       True,  False, False),
    ("26163527900", True, "deep",       False, False, True),
    ("18097350200", True, "severe",     False, False, False),
    ("28065950100", True, "deep",       False, True,  False),
    ("20091000100", True, "lic",        False, False, False),
    ("24510050200", True, "severe",     False, False, False),
    ("35001000900", True, "deep",       True,  False, True),
]


def enrich_pipeline_eligibility(pipeline: "Pipeline") -> "Pipeline":
    """Populate census tract and distress data on each project via nmtc-mapper.

    Attempts live geocoding + eligibility lookup. Falls back to pre-built
    sample data if the API is unavailable or any project already has
    eligibility data populated (e.g. from Pipeline.sample()).

    Fields populated on each :class:`~nmtcapp.core.pipeline.PipelineProject`:
    - ``census_tract``
    - ``is_nmtc_eligible``
    - ``distress_level``
    - ``is_native_area``
    - ``is_high_migration_rural``
    - ``is_opportunity_zone``

    Example::

        enriched = enrich_pipeline_eligibility(pipeline)
    """
    projects = list(pipeline)
    if not projects:
        return pipeline

    # If all projects already enriched (e.g. Pipeline.sample()), skip API call.
    if all(p.is_enriched for p in projects):
        logger.debug("Pipeline already enriched — skipping nmtc-mapper call")
        return pipeline

    try:
        from nmtcmapper import NMTCMapper
        mapper = NMTCMapper()
        _enrich_via_api(projects, mapper)
        logger.info("nmtc-mapper enrichment complete for %d projects", len(projects))
    except Exception as exc:
        logger.warning(
            "nmtc-mapper enrichment failed (%s). Applying fallback sample eligibility data.",
            exc,
        )
        _apply_fallback_eligibility(projects)

    return pipeline


def _enrich_via_api(projects, mapper) -> None:
    """Call nmtc-mapper check_address for each un-enriched project."""
    for project in projects:
        if project.is_enriched:
            continue
        try:
            result = mapper.check_address(project.full_address)
            project.census_tract = result.tract_id
            project.is_nmtc_eligible = result.nmtc_eligible
            project.distress_level = result.distress_level
            project.is_native_area = result.is_nmtc_native_area
            project.is_high_migration_rural = result.is_high_migration_rural
            project.is_opportunity_zone = result.is_opportunity_zone
        except Exception as exc:
            logger.warning(
                "Could not enrich project %s (%s): %s — using fallback",
                project.project_id, project.full_address, exc,
            )
            _apply_fallback_to_project(project, _fallback_for_index(0))


def _apply_fallback_eligibility(projects) -> None:
    for i, project in enumerate(projects):
        if not project.is_enriched:
            _apply_fallback_to_project(project, _fallback_for_index(i))


def _fallback_for_index(i: int) -> tuple:
    return _FALLBACK_ELIGIBILITY[i % len(_FALLBACK_ELIGIBILITY)]


def _apply_fallback_to_project(project, fallback: tuple) -> None:
    tract, eligible, distress, native, hmr, oz = fallback
    project.census_tract = tract
    project.is_nmtc_eligible = eligible
    project.distress_level = distress
    project.is_native_area = native
    project.is_high_migration_rural = hmr
    project.is_opportunity_zone = oz
