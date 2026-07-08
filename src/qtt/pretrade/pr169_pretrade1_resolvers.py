from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Iterable


GENERATED_PREFIX = Path("docs/master_plan/generated/pr169_pretrade1")
REGISTRY_REF = "docs/master_plan/generated/pr169_pretrade1/pretrade_decision_registry.jsonl"


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _read_jsonl(path: Path) -> tuple[dict, ...]:
    rows: list[dict] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                payload = json.loads(line)
                if isinstance(payload, dict):
                    rows.append(payload)
    return tuple(rows)


@dataclass(frozen=True)
class PreTradeRegistryView:
    rows: tuple[dict, ...]

    def candidate_ids(self) -> tuple[str, ...]:
        return tuple(str(row["candidate_id"]) for row in self.rows)

    def by_candidate_id(self, candidate_id: str) -> dict:
        for row in self.rows:
            if row.get("candidate_id") == candidate_id:
                return dict(row)
        raise KeyError(candidate_id)

    def decision_packets(self) -> tuple[dict, ...]:
        return tuple(
            {
                "candidate_id": row["candidate_id"],
                "pretrade_decision_candidate_id": row["pretrade_decision_candidate_id"],
                "pretrade_decision_state": row["pretrade_decision_state"],
                "no_trade_candidate_ref_or_gap": row["no_trade_candidate_ref_or_gap"],
                "owner_review_route_ref_or_gap": row["pretrade_owner_view_handoff_ref_or_gap"],
                "agent_access_path_audit_ref_or_gap": row["pretrade_agent_access_path_audit_ref_or_gap"],
                "edge_alpha_capture_map_ref_or_gap": row["pretrade_edge_alpha_capture_map_ref_or_gap"],
                "submit_authority_created": row["submit_authority_created"],
                "order_authority_created": row["order_authority_created"],
                "profit_claim_created": row["profit_claim_created"],
            }
            for row in self.rows
        )

    def provider_pending_packets(self) -> tuple[dict, ...]:
        return tuple(
            packet
            for packet in self.decision_packets()
            if packet["pretrade_decision_state"] == "PRETRADE_PASS_PROVIDER_PENDING"
        )

    def downstream_consumers(self) -> tuple[str, ...]:
        consumers: set[str] = set()
        for row in self.rows:
            consumers.update(str(ref) for ref in row.get("downstream_consumer_refs", ()))
        return tuple(sorted(consumers))

    def authority_false_fields(self) -> tuple[str, ...]:
        fields: set[str] = set()
        for row in self.rows:
            for key, value in row.items():
                if key.endswith("_created") and value is False:
                    fields.add(key)
        return tuple(sorted(fields))


def load_registry(
    *,
    repo_root: str | Path | None = None,
    rows: Iterable[dict] | None = None,
) -> PreTradeRegistryView:
    if rows is not None:
        return PreTradeRegistryView(tuple(dict(row) for row in rows))
    root = Path(repo_root) if repo_root is not None else _repo_root()
    registry_path = root / REGISTRY_REF
    return PreTradeRegistryView(_read_jsonl(registry_path))
