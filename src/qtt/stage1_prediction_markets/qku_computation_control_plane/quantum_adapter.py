"""Read-only PR162E-Q semantic views; no backend or simulator execution."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
import json
from pathlib import Path

from .errors import OwnerAdapterError, ReasonCode


class QuantumModelKind(StrEnum):
    QUBO = "QUBO"
    BQM = "BQM"
    ISING = "ISING"
    CQM = "CQM"
    DQM = "DQM"
    QUADRATIC_PROGRAM = "QUADRATIC_PROGRAM"


@dataclass(frozen=True, slots=True)
class QuantumMappingViewV1:
    row_id: str
    model_kind: QuantumModelKind
    source_report: str
    source_schema: str
    source_owner: str = "PR162E_Q_QUANTUM_AUTOMAPPER"
    backend_execution_allowed: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.model_kind, QuantumModelKind):
            raise OwnerAdapterError(
                ReasonCode.OWNER_DATA_MALFORMED,
                "quantum model kind must be a typed allowlisted enum",
            )
        if any(
            not isinstance(value, str) or not value
            for value in (
                self.row_id,
                self.source_report,
                self.source_schema,
                self.source_owner,
            )
        ):
            raise OwnerAdapterError(
                ReasonCode.OWNER_DATA_MALFORMED,
                "quantum mapping lineage is incomplete",
            )
        if self.source_owner != "PR162E_Q_QUANTUM_AUTOMAPPER":
            raise OwnerAdapterError(
                ReasonCode.OWNER_DATA_CONTRADICTORY,
                "quantum mapping owner lineage changed",
            )
        if type(self.backend_execution_allowed) is not bool:
            raise OwnerAdapterError(
                ReasonCode.OWNER_DATA_MALFORMED,
                "backend execution flag must be a boolean",
            )
        if self.backend_execution_allowed:
            raise OwnerAdapterError(
                ReasonCode.CAPABILITY_DENIED,
                "Tranche A quantum views cannot authorize backend execution",
            )
        from .serialization import validate_relative_path

        validate_relative_path(self.source_report)


_REPORTS = {
    QuantumModelKind.QUBO: "PR162E_Q_QUBORecipe.report.json",
    QuantumModelKind.BQM: "PR162E_Q_BQMRecipe.report.json",
    QuantumModelKind.ISING: "PR162E_Q_IsingRecipe.report.json",
    QuantumModelKind.CQM: "PR162E_Q_CQMRecipe.report.json",
    QuantumModelKind.DQM: "PR162E_Q_DQMRecipe.report.json",
    QuantumModelKind.QUADRATIC_PROGRAM: (
        "PR162E_Q_QuadProgramRecipe.report.json"
    ),
}


class PR162EQuantumAdapterV1:
    def __init__(self, repo_root: str | Path) -> None:
        self._repo_root = Path(repo_root).resolve()

    def load_mappings(
        self, model_kind: QuantumModelKind
    ) -> tuple[QuantumMappingViewV1, ...]:
        from src.qtt.stage1_prediction_markets.pr162e_q_quantum_automapper.io import (
            records_from_report_payload,
        )

        if not isinstance(model_kind, QuantumModelKind):
            raise OwnerAdapterError(
                ReasonCode.OWNER_DATA_MALFORMED,
                "model_kind must be a QuantumModelKind value",
            )
        filename = _REPORTS[model_kind]
        relative = Path("docs/master_plan/generated") / filename
        try:
            payload = json.loads(
                (self._repo_root / relative).read_text(encoding="utf-8")
            )
        except (OSError, json.JSONDecodeError) as exc:
            raise OwnerAdapterError(
                ReasonCode.OWNER_DATA_MISSING,
                f"PR162E-Q report unavailable: {filename}",
            ) from exc
        if not isinstance(payload, dict):
            raise OwnerAdapterError(
                ReasonCode.OWNER_DATA_MALFORMED,
                f"PR162E-Q report must be an object: {filename}",
            )
        if payload.get("validation_status") != "PASS":
            raise OwnerAdapterError(
                ReasonCode.OWNER_DATA_STALE,
                f"PR162E-Q report is not validated: {filename}",
            )
        forbidden_counts = (
            "cloud_backend_execution_count",
            "credential_access_count",
            "live_order_authority_count",
            "private_state_fetch_count",
            "provider_api_call_count",
            "quantum_backend_execution_count",
        )
        if any(payload.get(key) != 0 for key in forbidden_counts):
            raise OwnerAdapterError(
                ReasonCode.OWNER_DATA_CONTRADICTORY,
                "PR162E-Q mapping reports exercise forbidden authority",
            )
        try:
            records = records_from_report_payload(self._repo_root, payload)
        except (OSError, KeyError, TypeError, ValueError) as exc:
            raise OwnerAdapterError(
                ReasonCode.OWNER_DATA_MALFORMED,
                f"PR162E-Q records could not be resolved: {filename}",
            ) from exc
        schema = payload.get("schema_ref")
        if not isinstance(schema, str) or not schema:
            raise OwnerAdapterError(
                ReasonCode.OWNER_DATA_MALFORMED,
                f"PR162E-Q schema lineage is missing: {filename}",
            )
        if any(not isinstance(record, dict) for record in records):
            raise OwnerAdapterError(
                ReasonCode.OWNER_DATA_MALFORMED,
                "PR162E-Q record set contains a non-object row",
            )
        views: list[QuantumMappingViewV1] = []
        for record in records:
            row_id = next(
                (
                    record[field_name]
                    for field_name in ("row_id", "mapping_id", "recipe_id")
                    if isinstance(record.get(field_name), str)
                    and record[field_name]
                ),
                "",
            )
            views.append(
                QuantumMappingViewV1(
                    row_id=row_id,
                    model_kind=model_kind,
                    source_report=relative.as_posix(),
                    source_schema=schema,
                )
            )
        if not views or len({view.row_id for view in views}) != len(views):
            raise OwnerAdapterError(
                ReasonCode.OWNER_DATA_CONTRADICTORY,
                "PR162E-Q mapping identities must be nonempty and unique",
            )
        return tuple(sorted(views, key=lambda item: item.row_id))
