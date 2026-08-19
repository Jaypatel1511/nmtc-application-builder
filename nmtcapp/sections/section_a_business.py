"""Section A: Business Strategy generator."""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from nmtcapp.data.schema import TARGET_DISTRESS_THRESHOLDS
from nmtcapp.renderers._disclosure import (
    is_partial_unverified, join_truncated, qualified_pct, unverified_qualifier,
)
from nmtcapp.sections.base import SectionGenerator, _cde_todo, _placeholder

if TYPE_CHECKING:
    from nmtcapp.core.application import Application, ApplicationAnalysis

logger = logging.getLogger(__name__)


class SectionABusinessStrategy(SectionGenerator):
    """Generates Section A: Business Strategy content.

    Pulls from CDE mission, target markets, pipeline distress mix,
    geographic diversity, and sector strategy.

    Example::

        gen = SectionABusinessStrategy()
        content = gen.generate_content(application, analysis)
    """
    section_id = "A"
    title = "Business Strategy"
    word_limit = 3000

    def generate_content(self, application: "Application", analysis: "ApplicationAnalysis") -> dict:
        cde = application.cde
        pr = analysis.pipeline_result
        distress = pr.distress_breakdown
        geo = pr.geographic_diversity
        sector = pr.sector_mix

        states = geo.get("states", [])
        states_str = join_truncated(states)
        dominant_sector = sector.get("dominant_sector", "healthcare")
        deep_pct = distress.get("pct_deep_or_severe", 0.0)
        total_qei = pr.total_qei_request
        total_projects = pr.total_projects

        # Distress figures may only be asserted as fact when fully verified.
        degraded = getattr(pr, "eligibility_data_status", "ok") != "ok"
        partial_unverified = is_partial_unverified(pr)

        if degraded:
            distress_clause = (
                "targeting deep and severely distressed census tracts "
                "(distress concentration unverified — eligibility data unavailable)"
            )
        elif partial_unverified:
            distress_clause = (
                f"targeting {deep_pct:.0%} of QEI {unverified_qualifier(pr)} "
                "in deep and severely distressed census tracts"
            )
        else:
            distress_clause = (
                f"targeting {deep_pct:.0%} of QEI in deep and severely "
                "distressed census tracts"
            )

        # B7: "...in markets where conventional capital is systematically absent"
        # was an assertion about credit conditions in the CDE's markets. This
        # tool retrieves no lending, credit-access or disinvestment data of any
        # kind — Section B's community-need placeholder says so in as many
        # words — so it cannot make that claim on a CDE's behalf. What survives
        # is the sector concentration, computed from the pipeline the CDE
        # supplied. The market characterisation is the CDE's to write, and the
        # placeholder below is where it goes.
        thesis = (
            f"{cde.name} will deploy ${application.requested_allocation / 1e6:.1f} million in "
            f"NMTC allocation across {total_projects} projects in {len(states)} states — "
            f"{distress_clause}. "
            f"The pipeline's largest sector concentration is "
            f"{dominant_sector.replace('_', ' ')}."
        ) + _placeholder()

        # B4: this asserted that the CDE's mission "guides our market selection
        # toward persistent-poverty counties and high-migration rural
        # communities" for EVERY CDE, unconditionally — including pipelines
        # where no project carries either flag, and pipelines whose tracts were
        # never verified. It was the worse kind of invented claim, because both
        # are per-project columns the CDE actually fills in
        # (pipeline.py:306,309): the tool asserted the targeting while ignoring
        # the declaration sitting in the input.
        #
        # Now it renders only what the CDE declared, attributed to the
        # declaration, and says nothing when nothing was declared. Suppressed
        # entirely on the degraded path, where no share is trustworthy.
        mission = cde.mission.strip()
        # "..." was appended unconditionally, so a 44-character mission rendered
        # as though it had been cut off. Only elide when something was elided.
        mission_display = (mission[:200].rstrip() + "…") if len(mission) > 200 else mission

        # WHO EACH FLAG BELONGS TO, SEPARATELY (1.2.1 L-2).
        #
        # This sentence used to attribute BOTH shares to "the flags supplied in
        # this CDE's own pipeline submission", and for High Migration Rural
        # that is not where the number comes from. is_high_migration_rural is a
        # CDE-supplied CSV column, but integrations/nmtc_mapper_adapter passes
        # it through _prefer_determinate, which returns the MAPPER's value
        # whenever the mapper has one: _prefer_determinate(False, True) -> False.
        # On a real filing the CDE declared 36.2% of QEI as High Migration
        # Rural, the mapper corrected it to 12.6%, and the document printed
        # 12.6% as the CDE's own declaration — understating what the CDE
        # claimed while crediting the claim to them.
        #
        # THE MAPPER IS RIGHT and its correction stands; what was wrong was the
        # attribution. This is the mirror image of the Native Area defect 1.2.1
        # fixed in the other direction (where a fabricated negative overwrote a
        # correct declaration): both are a sentence naming the wrong author of
        # a figure that reaches a scored Special Targeting criterion.
        #
        # Persistent poverty is untouched by any adapter — no enrichment path
        # assigns is_persistent_poverty — so its clause keeps the original
        # attribution, and the two are now separate sentences rather than one
        # sentence covering both.
        pp_pct = distress.get("pct_persistent_poverty", 0.0)
        hmr_pct = distress.get("pct_high_migration_rural", 0.0)
        clauses = []
        if not degraded and pp_pct > 0:
            clauses.append(
                "Per the persistent-poverty flags supplied in this CDE's own "
                f"pipeline submission, the pipeline places {pp_pct:.0%} of QEI "
                "in tracts declared as persistent-poverty counties."
            )
        if not degraded and hmr_pct > 0:
            clauses.append(
                f"{hmr_pct:.0%} of QEI is in tracts recorded as High Migration "
                "Rural. This share is NOT solely the CDE's declaration: the "
                "high_migration_rural column of the pipeline submission is "
                "overwritten wherever nmtc-mapper returned a determination for "
                "the tract, so where the two disagree the figure above is the "
                "tool's, not the CDE's. Check it against your own submission "
                "before relying on it, and state which governs."
            )
        if clauses:
            targeting = " ".join(clauses) + "\n\n"
        else:
            targeting = _cde_todo(
                "State how these markets were selected and what makes them the "
                "right ones for this allocation. This tool holds no "
                "market-selection rationale: your pipeline submission records "
                "where the projects are, not why you chose those places, and no "
                "project in it is flagged persistent-poverty or High Migration "
                "Rural. Do not describe targeting you cannot evidence."
            ) + "\n\n"

        target_markets_body = (
            f"Primary geographic targets: {states_str}.\n\n"
            f"{cde.name}'s stated mission is: \"{mission_display}\"\n\n"
            f"{targeting}"
        ) + _placeholder()

        if degraded:
            deep_pct_display = "Unverified — eligibility data unavailable"
        elif partial_unverified:
            deep_pct_display = qualified_pct(deep_pct, pr)
        else:
            deep_pct_display = f"{deep_pct:.0%}"

        pipeline_overview = {
            "Total Projects in Pipeline": total_projects,
            "Total Pipeline QEI ($)": f"${total_qei:,.0f}",
            "States Represented": len(states),
            "% QEI in Deep/Severe Distress": deep_pct_display,
            "Dominant Sector": dominant_sector.replace("_", " ").title(),
            "Total Jobs to Be Created": pr.aggregate_impact.get("total_jobs_created", "N/A"),
            "Sector Diversity Score": f"{sector.get('sector_diversity_score', 0):.1f}/100",
        }

        # THE BAND IS INTERPOLATED, NOT TYPED. "≥75%" was a literal in all
        # three branches while data/schema.py owns the value; moving the
        # constant would have changed what the readiness score gates on while
        # the document went on printing 75%. Found by the 1.2.1 mutation
        # harness: it was the one pinned constant whose mutation stayed green.
        band = (
            "(This tool's own internal scoring band is "
            f"≥{TARGET_DISTRESS_THRESHOLDS['target_deep_distress']:.0%}; "
            "it is not a CDFI Fund threshold.)"
        )
        if degraded:
            deployment_distress_line = (
                "QEI deployment strategy: deep/severe distress commitment "
                "unverified — eligibility data unavailable; re-verify before "
                f"asserting a commitment level. {band}"
            )
        elif partial_unverified:
            deployment_distress_line = (
                f"QEI deployment strategy: {deep_pct:.0%} of QEI "
                f"{unverified_qualifier(pr)} committed to deep/severe distress "
                f"tracts. {band}"
            )
        else:
            deployment_distress_line = (
                f"QEI deployment strategy: {deep_pct:.0%} of QEI "
                f"committed to deep/severe distress tracts. {band}"
            )

        # B1 and B6. Two invented facts stood here, in the subsection where
        # deployment capacity is scored:
        #
        #   "...plans to close the first tranche of transactions within 12
        #    months of award announcement."   <- 12 was a literal. No CDE ever
        #                                        supplied a closing timeline.
        #   "All N projects have completed preliminary underwriting review."
        #                                     <- unconditional. `grep -ril
        #                                        underwrit nmtcapp/` finds no
        #                                        underwriting field on
        #                                        PipelineProject, in the CSV
        #                                        templates, or in
        #                                        upload_handler.
        #
        # The second is the same claim this release already removed from
        # Section C, for the reason recorded at section_c_management.py:61-70:
        # "A CDE that submitted this told the Fund, in the subsection where
        # management capacity is scored, that it ran a review it does not run."
        # The remediation was applied there and not here.
        #
        # Neither renders conditionally, because there is no field to render
        # from. Both become the CDE's to state.
        deployment_strategy = (
            f"{cde.name} targets a {application.application_round} award.\n\n"
            + _cde_todo(
                "State your deployment timeline and the diligence status of "
                "each project — when you expect to close the first tranche, "
                "how the rest are sequenced, and how far each project has "
                "actually progressed through your underwriting. This tool "
                "holds neither: your pipeline submission records project "
                "economics and locations, not diligence milestones or target "
                "closing dates. Do not assert that a project has cleared "
                "underwriting review unless it has."
            ) + "\n\n"
            f"{deployment_distress_line}\n\n"
        ) + _placeholder()

        return {
            "section_id": self.section_id,
            "title": self.title,
            "subsections": [
                {"heading": "Investment Thesis and Strategy",
                 "body": thesis, "type": "narrative"},
                {"heading": "Target Markets — Geographic and Demographic",
                 "body": target_markets_body, "type": "narrative"},
                {"heading": "Pipeline Overview",
                 "body": pipeline_overview, "type": "table_ref"},
                {"heading": "QEI Deployment Strategy and Timeline",
                 "body": deployment_strategy, "type": "narrative"},
                {"heading": "Competitive Differentiation",
                 "body": _placeholder(), "type": "narrative"},
            ],
        }
