"""Canonical alias repair facade for PR161B."""

from .coverage_matcher import match_candidate, reconcile_candidates

__all__ = ["match_candidate", "reconcile_candidates"]
