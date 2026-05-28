"""Official-source classifier facade for PR159."""

from .official_source_discovery import AMBIGUOUS_OFFICIAL_DISCOVERY, OFFICIAL_SOURCE_CATALOG


def classifier_audit_records():
    return [*list(OFFICIAL_SOURCE_CATALOG), *list(AMBIGUOUS_OFFICIAL_DISCOVERY)]


__all__ = ["classifier_audit_records"]

