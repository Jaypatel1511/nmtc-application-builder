from nmtcapp.sections.section_a_business import SectionABusinessStrategy
from nmtcapp.sections.section_b_outcomes import SectionBCommunityOutcomes
from nmtcapp.sections.section_c_management import SectionCManagementCapacity
from nmtcapp.sections.section_d_capitalization import SectionDCapitalizationStrategy
from nmtcapp.sections.section_e_prior_awards import SectionEPriorAwards

ALL_SECTIONS = [
    SectionABusinessStrategy(),
    SectionBCommunityOutcomes(),
    SectionCManagementCapacity(),
    SectionDCapitalizationStrategy(),
    SectionEPriorAwards(),
]

__all__ = [
    "SectionABusinessStrategy",
    "SectionBCommunityOutcomes",
    "SectionCManagementCapacity",
    "SectionDCapitalizationStrategy",
    "SectionEPriorAwards",
    "ALL_SECTIONS",
]
