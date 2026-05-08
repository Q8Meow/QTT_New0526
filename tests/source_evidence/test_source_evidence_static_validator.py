import copy
import json
from pathlib import Path

from tools.validate_source_evidence_static import (
    CONNECTOR_SEMANTIC_POPULATION_BLOCKED_MARKER,
    EXTERNAL_FACT_AUTHORITY_BLOCKED_MARKER,
    PACKET_ACCEPTS_NO_FACTS_MARKER,
    PACKET_RETRIEVES_NO_FACTS_MARKER,
    PACKET_VERSION_MARKER,
    validate_static_surface,
)


SCHEMA_PATH = Path("schemas/source_evidence/source_evidence.schema.json")
OWNER_PACKET_PATH = Path(
    "docs/master_plan/source_evidence/QTT_OWNER_SOURCE_EVIDENCE_DEFINITIONS_PACKET.md"
)


def _schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def _write_json(path: Path, value: dict) -> Path:
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
    return path


def _write_owner_packet(path: Path, omitted_marker: str | None = None) -> Path:
    markers = [
        PACKET_VERSION_MARKER,
        EXTERNAL_FACT_AUTHORITY_BLOCKED_MARKER,
        CONNECTOR_SEMANTIC_POPULATION_BLOCKED_MARKER,
        PACKET_RETRIEVES_NO_FACTS_MARKER,
        PACKET_ACCEPTS_NO_FACTS_MARKER,
    ]
    path.write_text(
        "\n".join(marker for marker in markers if marker != omitted_marker) + "\n",
        encoding="utf-8",
    )
    return path


def test_static_validator_accepts_current_schema_and_owner_packet():
    failures = validate_static_surface(
        schema_path=SCHEMA_PATH,
        owner_packet_path=OWNER_PACKET_PATH,
    )

    assert failures == []


def test_static_validator_rejects_missing_schema(tmp_path):
    owner_packet = _write_owner_packet(tmp_path / "owner_packet.md")

    failures = validate_static_surface(
        schema_path=tmp_path / "missing.schema.json",
        owner_packet_path=owner_packet,
    )

    assert any("schema file is missing" in failure for failure in failures)


def test_static_validator_rejects_missing_owner_packet_marker(tmp_path):
    schema_path = _write_json(tmp_path / "schema.json", _schema())
    owner_packet = _write_owner_packet(
        tmp_path / "owner_packet.md",
        omitted_marker=EXTERNAL_FACT_AUTHORITY_BLOCKED_MARKER,
    )

    failures = validate_static_surface(
        schema_path=schema_path,
        owner_packet_path=owner_packet,
    )

    assert any("external fact authority blocked marker" in failure for failure in failures)


def test_static_validator_rejects_missing_required_surface(tmp_path):
    schema = _schema()
    schema["$defs"].pop("accepted_source_packet")
    schema_path = _write_json(tmp_path / "schema.json", schema)
    owner_packet = _write_owner_packet(tmp_path / "owner_packet.md")

    failures = validate_static_surface(
        schema_path=schema_path,
        owner_packet_path=owner_packet,
    )

    assert any("accepted_source_packet" in failure for failure in failures)


def test_static_validator_rejects_forbidden_authority_true(tmp_path):
    schema = copy.deepcopy(_schema())
    schema["$defs"]["no_claim_flags"]["properties"]["profit_claim_authority"][
        "const"
    ] = True
    schema_path = _write_json(tmp_path / "schema.json", schema)
    owner_packet = _write_owner_packet(tmp_path / "owner_packet.md")

    failures = validate_static_surface(
        schema_path=schema_path,
        owner_packet_path=owner_packet,
    )

    assert any("profit_claim_authority" in failure for failure in failures)
