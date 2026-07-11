"""Adapter wrapping nmtc-mapper for pipeline eligibility enrichment.

Failure semantics (v1.1.5): eligibility data is either verified live CDFI Fund
data or explicitly UNAVAILABLE/UNVERIFIED. Nothing is ever substituted or
fabricated. When nmtc-mapper cannot load its dataset, the pipeline is marked
``eligibility_data_status = "unavailable"`` and every eligibility field stays
``None``; downstream scoring excludes the eligibility component and labels the
score as partial. A project whose location cannot be geocoded gets
``geocode_success = False`` and stays unverified — it is never assigned a
substitute tract and never treated as ineligible.
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from nmtcapp.core.pipeline import Pipeline

logger = logging.getLogger(__name__)


def enrich_pipeline_eligibility(pipeline: "Pipeline") -> "Pipeline":
    """Populate census tract and distress data on each project via nmtc-mapper.

    Uses live geocoding + the CDFI Fund eligibility dataset. If the dataset
    cannot be loaded (:class:`nmtcmapper.NMTCMapperError`), the pipeline is
    marked degraded — ``pipeline.eligibility_data_status == "unavailable"``
    with the underlying error in ``pipeline.eligibility_data_error`` — and
    eligibility fields remain ``None``. Unexpected exceptions propagate.

    Fields populated on each :class:`~nmtcapp.core.pipeline.PipelineProject`:
    - ``census_tract``
    - ``is_nmtc_eligible``
    - ``distress_level``
    - ``is_native_area``
    - ``is_high_migration_rural``
    - ``is_opportunity_zone``
    - ``geocode_success``

    Example::

        enriched = enrich_pipeline_eligibility(pipeline)
        if enriched.eligibility_data_status != "ok":
            print(f"Unavailable: {enriched.eligibility_data_error}")
    """
    projects = list(pipeline)
    if not projects:
        return pipeline

    # If all projects already enriched (e.g. Pipeline.sample()), skip API call.
    if all(p.is_enriched for p in projects):
        logger.debug("Pipeline already enriched — skipping nmtc-mapper call")
        return pipeline

    from nmtcmapper import NMTCMapper, NMTCMapperError

    try:
        mapper = NMTCMapper()
    except NMTCMapperError as exc:
        return _mark_unavailable(pipeline, str(exc))

    # Provenance check (defense-in-depth): only live CDFI Fund data may flow
    # into an application, even if a sample-stamped mapper is injected.
    data_source = getattr(mapper, "data_source", None)
    if data_source != "cdfi_fund":
        return _mark_unavailable(
            pipeline,
            f"eligibility data source is {data_source!r}, not the live CDFI "
            "Fund dataset — refusing to use it for application content",
        )

    _enrich_via_api(projects, mapper, NMTCMapperError)
    pipeline.eligibility_data_status = "ok"
    pipeline.eligibility_data_error = None
    logger.info("nmtc-mapper enrichment complete for %d projects", len(projects))
    return pipeline


def _mark_unavailable(pipeline: "Pipeline", reason: str) -> "Pipeline":
    """Enter degraded mode: eligibility fields stay None, status is explicit."""
    pipeline.eligibility_data_status = "unavailable"
    pipeline.eligibility_data_error = reason
    logger.warning(
        "nmtc-mapper eligibility data unavailable (%s). Eligibility fields "
        "remain unverified; scoring will exclude the eligibility component.",
        reason,
    )
    return pipeline


def _enrich_via_api(projects, mapper, mapper_error: type) -> None:
    """Call nmtc-mapper check_address for each un-enriched project.

    A project whose location cannot be verified (geocode failure or a typed
    mapper error) is marked ``geocode_success = False`` with all eligibility
    fields left ``None`` — unverified, not ineligible, and never a substitute
    tract. Unexpected exceptions propagate.
    """
    for project in projects:
        if project.is_enriched:
            continue
        try:
            result = mapper.check_address(project.full_address)
        except mapper_error as exc:
            logger.warning(
                "Location could not be verified for project %s (%s): %s — "
                "leaving eligibility unverified",
                project.project_id, project.full_address, exc,
            )
            project.geocode_success = False
            continue
        if not result.geocode_success:
            # nmtc-mapper returns an "ineligible"-shaped result on geocode
            # failure; treat it as UNVERIFIED — do not copy those values.
            logger.warning(
                "Location could not be verified for project %s (%s) — "
                "leaving eligibility unverified",
                project.project_id, project.full_address,
            )
            project.geocode_success = False
            continue
        project.geocode_success = True
        project.census_tract = result.tract_id
        project.is_nmtc_eligible = result.nmtc_eligible
        project.distress_level = result.distress_level
        project.is_native_area = result.is_nmtc_native_area
        project.is_high_migration_rural = result.is_high_migration_rural
        project.is_opportunity_zone = result.is_opportunity_zone
