#!/usr/bin/env python3
"""Term matching helpers for PR168-RP5A."""

from __future__ import annotations

import re
from typing import Iterable

from tools.pr168_rp5a_config import TERM_TAXONOMY, TermSpec


class CompiledTerm:
    def __init__(self, spec: TermSpec) -> None:
        self.spec = spec
        pattern = spec.term_text_or_regex if spec.is_regex else re.escape(spec.term_text_or_regex)
        self.regex = re.compile(pattern, re.IGNORECASE)

    def matches(self, text: str) -> list[str]:
        values: list[str] = []
        for match in self.regex.finditer(text):
            values.append(match.group(0))
        return values


COMPILED_TERMS = tuple(CompiledTerm(spec) for spec in TERM_TAXONOMY)
TERM_BY_ID = {spec.term_id: spec for spec in TERM_TAXONOMY}


def taxonomy_rows() -> list[dict[str, object]]:
    return [spec.to_row() for spec in TERM_TAXONOMY]


def match_text(text: object) -> list[dict[str, object]]:
    haystack = "" if text is None else str(text)
    matches: list[dict[str, object]] = []
    seen: set[tuple[str, str]] = set()
    for compiled in COMPILED_TERMS:
        for value in compiled.matches(haystack):
            key = (compiled.spec.term_id, value.lower())
            if key in seen:
                continue
            seen.add(key)
            matches.append(
                {
                    "term_id": compiled.spec.term_id,
                    "term_text_or_regex": compiled.spec.term_text_or_regex,
                    "matched_text": value,
                    "term_family": compiled.spec.term_family,
                    "severity": compiled.spec.severity,
                    "canonical_future_interpretation": compiled.spec.canonical_future_interpretation,
                    "old_semantic_risk": compiled.spec.old_semantic_risk,
                    "is_regex": compiled.spec.is_regex,
                }
            )
    return matches


def term_ids_from_matches(matches: Iterable[dict[str, object]]) -> list[str]:
    return sorted({str(match["term_id"]) for match in matches})


def term_families_from_ids(term_ids: Iterable[str]) -> list[str]:
    return sorted({TERM_BY_ID[term_id].term_family for term_id in term_ids if term_id in TERM_BY_ID})


def severities_from_ids(term_ids: Iterable[str]) -> list[str]:
    return [TERM_BY_ID[term_id].severity for term_id in term_ids if term_id in TERM_BY_ID]
