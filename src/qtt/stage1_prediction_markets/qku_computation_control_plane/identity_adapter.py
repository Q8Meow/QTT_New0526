"""Explicit read-only adapter over the canonical RP5C identity library."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from .errors import OwnerAdapterError, ReasonCode


@dataclass(frozen=True, slots=True)
class IdentityViewV1:
    identity_row_id: str
    qku_id: str
    formula_id: str
    qku_family: str
    formula_family: str
    ontology_category: str
    library_version: str
    source_owner: str = "RP5C_IDENTITY_LIBRARY"

    def __post_init__(self) -> None:
        for name in (
            "identity_row_id",
            "qku_id",
            "formula_id",
            "qku_family",
            "formula_family",
            "ontology_category",
            "library_version",
            "source_owner",
        ):
            value = getattr(self, name)
            if not isinstance(value, str):
                raise OwnerAdapterError(
                    ReasonCode.OWNER_DATA_MALFORMED,
                    f"RP5C {name} must be text",
                )
        if not (self.qku_id or self.formula_id):
            raise OwnerAdapterError(
                ReasonCode.OWNER_DATA_MALFORMED,
                "identity view requires qku_id or formula_id",
            )
        if not self.library_version:
            raise OwnerAdapterError(
                ReasonCode.OWNER_DATA_MALFORMED,
                "identity lineage requires a library version",
            )
        if not self.identity_row_id or self.source_owner != "RP5C_IDENTITY_LIBRARY":
            raise OwnerAdapterError(
                ReasonCode.OWNER_DATA_MALFORMED,
                "identity row and canonical owner lineage are required",
            )


def _text_field(row: dict[object, object], field_name: str) -> str:
    value = row.get(field_name)
    if value is None:
        return ""
    if not isinstance(value, str):
        raise OwnerAdapterError(
            ReasonCode.OWNER_DATA_MALFORMED,
            f"RP5C {field_name} must be text",
        )
    return value


def _view(row: object, version: str) -> IdentityViewV1:
    if not isinstance(row, dict):
        raise OwnerAdapterError(
            ReasonCode.OWNER_DATA_MALFORMED, "RP5C row must be an object"
        )
    return IdentityViewV1(
        identity_row_id=_text_field(row, "identity_row_id"),
        qku_id=_text_field(row, "qku_id"),
        formula_id=_text_field(row, "formula_id"),
        qku_family=_text_field(row, "qku_family"),
        formula_family=_text_field(row, "formula_family"),
        ontology_category=_text_field(row, "ontology_category"),
        library_version=version,
    )


class RP5CIdentityAdapterV1:
    """All owner I/O occurs only when one of these methods is explicitly invoked."""

    def __init__(self, repo_root: str | Path) -> None:
        self._repo_root = Path(repo_root).resolve()

    def _load(self, expected_versions: dict[str, str] | None = None) -> dict:
        from tools.pr168_rp5c_library_reader import load_library

        if expected_versions is not None and (
            not isinstance(expected_versions, dict)
            or any(
                not isinstance(key, str)
                or not key
                or not isinstance(value, str)
                or not value
                for key, value in expected_versions.items()
            )
        ):
            raise OwnerAdapterError(
                ReasonCode.OWNER_DATA_MALFORMED,
                "expected RP5C versions must be a string mapping",
            )
        try:
            library = load_library(
                self._repo_root, expected_versions=expected_versions
            )
        except (OSError, KeyError, ValueError, TypeError) as exc:
            raise OwnerAdapterError(
                ReasonCode.OWNER_DATA_MISSING,
                "RP5C library could not be loaded with the requested lineage",
            ) from exc
        if not isinstance(library, dict):
            raise OwnerAdapterError(
                ReasonCode.OWNER_DATA_MALFORMED,
                "RP5C library must be an object",
            )
        versions = library.get("versions")
        if (
            not isinstance(versions, dict)
            or not isinstance(versions.get("library_version"), str)
            or not versions["library_version"]
        ):
            raise OwnerAdapterError(
                ReasonCode.OWNER_DATA_MALFORMED,
                "RP5C library version lineage is missing",
            )
        return library

    def get_qku(
        self, qku_id: str, *, expected_versions: dict[str, str] | None = None
    ) -> IdentityViewV1:
        from tools.pr168_rp5c_library_reader import get_qku

        if not isinstance(qku_id, str) or not qku_id:
            raise OwnerAdapterError(
                ReasonCode.OWNER_DATA_MALFORMED, "qku_id must be nonempty text"
            )
        library = self._load(expected_versions)
        row = get_qku(qku_id, library)
        if row is None:
            raise OwnerAdapterError(
                ReasonCode.OWNER_DATA_MISSING, f"unknown canonical qku: {qku_id}"
            )
        return _view(row, str(library["versions"]["library_version"]))

    def get_formula(
        self, formula_id: str, *, expected_versions: dict[str, str] | None = None
    ) -> IdentityViewV1:
        from tools.pr168_rp5c_library_reader import get_formula

        if not isinstance(formula_id, str) or not formula_id:
            raise OwnerAdapterError(
                ReasonCode.OWNER_DATA_MALFORMED,
                "formula_id must be nonempty text",
            )
        library = self._load(expected_versions)
        row = get_formula(formula_id, library)
        if row is None:
            raise OwnerAdapterError(
                ReasonCode.OWNER_DATA_MISSING,
                f"unknown canonical formula: {formula_id}",
            )
        return _view(row, str(library["versions"]["library_version"]))

    def load_rows(
        self,
        identity_ids: Iterable[str],
        *,
        expected_versions: dict[str, str] | None = None,
    ) -> tuple[IdentityViewV1, ...]:
        from tools.pr168_rp5c_library_reader import load_rows

        if isinstance(identity_ids, str | bytes):
            raise OwnerAdapterError(
                ReasonCode.OWNER_DATA_MALFORMED,
                "RP5C identity ids must be an iterable of exact identifiers",
            )
        requested_values = tuple(identity_ids)
        if any(
            not isinstance(identity_id, str) or not identity_id
            for identity_id in requested_values
        ) or len(set(requested_values)) != len(requested_values):
            raise OwnerAdapterError(
                ReasonCode.OWNER_DATA_MALFORMED,
                "RP5C identity ids must be unique nonempty strings",
            )
        requested = tuple(sorted(requested_values))
        library = self._load(expected_versions)
        rows = load_rows(requested, library)
        if len(rows) != len(requested):
            raise OwnerAdapterError(
                ReasonCode.OWNER_DATA_MISSING,
                "one or more RP5C identity rows are missing",
            )
        version = str(library["versions"]["library_version"])
        views = tuple(_view(row, version) for row in rows)
        if len({view.identity_row_id for view in views}) != len(views):
            raise OwnerAdapterError(
                ReasonCode.OWNER_DATA_CONTRADICTORY,
                "RP5C returned duplicate identity rows",
            )
        return views
