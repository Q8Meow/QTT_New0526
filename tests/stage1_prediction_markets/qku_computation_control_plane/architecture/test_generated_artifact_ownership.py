import ast
import json
from pathlib import Path
import sys

import pytest

from tools import build_qku_computation_control_plane as builder

from tools.build_qku_computation_control_plane import (
    REPO_ROOT,
    build_payload,
    resolve_output_path,
)


def test_builder_is_in_memory_and_creates_no_generated_truth(tmp_path, monkeypatch, capsys) -> None:
    payload = build_payload()
    assert payload["contract_only"] is True
    assert payload["runtime_effect_authorized"] is False
    assert "output_path" not in payload
    assert payload["executed_coverage_rows"]["total_rows"] == 311
    assert payload["coverage_manifest_schema"] == "TrancheACoverageManifestV1"
    assert resolve_output_path(".tmp/st12a-builder/result.json") == (
        REPO_ROOT / ".tmp/st12a-builder/result.json"
    ).resolve()
    for unsafe in (
        "build-output.json",
        "src/generated.json",
        "../escape.json",
        ".tmp",
    ):
        with pytest.raises(ValueError):
            resolve_output_path(unsafe)

    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.validation import _lp03_published_source_readback_import_v1

    resolver_path = "src/qtt/stage1_prediction_markets/qku_computation_control_plane/input_resolver.py"
    resolver = (REPO_ROOT / resolver_path).read_text(encoding="utf-8")
    tree = ast.parse(resolver)
    selected = _lp03_published_source_readback_import_v1(resolver_path, tree)
    assert type(selected) is ast.Import and selected.names[0].name == "sqlite3"
    assert _lp03_published_source_readback_import_v1(resolver_path.replace("input_resolver","source_policy"), tree) is None
    token = "sqlite3.Connection.execute(reader, sql,"
    assert resolver.count(token) == 1
    changed = ast.parse(resolver.replace(token,"sqlite3.Connection.executescript(reader, sql,"))
    assert _lp03_published_source_readback_import_v1(resolver_path,changed) is None
    charge = "                    _EvidencePublishedSourceReadV1._charge_v1(self, owner_queries=1)\n"
    assert resolver.count(charge) == 1
    uncharged = ast.parse(resolver.replace(charge, ""))
    assert _lp03_published_source_readback_import_v1(resolver_path, uncharged) is None

    original_projection = builder.build_st12f_projections()
    original_e_projection = builder.build_st12e_projections()
    expected_names = (
        "cohort_registry.jsonl",
        "evidence_bundle_registry.jsonl",
        "evidence_metric_registry.jsonl",
        "independent_review_contracts.jsonl",
        "llm_annotation_contracts.jsonl",
        "manifest.json",
        "model_risk_adjudications.jsonl",
        "no_trade_comparisons.jsonl",
        "paper_result_contracts.jsonl",
        "parent_input_locks.jsonl",
        "quantum_benchmark_contracts.jsonl",
        "replay_result_contracts.jsonl",
        "validation_summary.json",
    )
    assert tuple(original_projection) == expected_names
    target = tmp_path / "docs/master_plan/generated/qku_control_plane/evidence"
    monkeypatch.setattr(builder, "REPO_ROOT", tmp_path)

    def unrelated_write(*args, **kwargs):
        raise AssertionError("isolated F attempted a non-F materializer")

    for name in ("materialize_st12g_projection_contract_manifest", "_materialize_st12h_reports",
                 "materialize_st12d_projections", "materialize_st12e_projections"):
        monkeypatch.setattr(builder, name, unrelated_write)
    original_d_builder = builder.build_st12d_projections
    monkeypatch.setattr(builder, "build_st12e_projections", unrelated_write)
    monkeypatch.setattr(builder, "build_st12d_projections", unrelated_write)

    def run(*args):
        monkeypatch.setattr(sys, "argv", [str(builder.__file__), *args])
        return builder.main()

    with pytest.raises(SystemExit) as conflicting:
        run("--st12f-only", "--st12g-only")
    assert conflicting.value.code == 2
    for bad in ("", "generated/export.json", "../escape.json", ".tmp"):
        assert run("--st12f-only", "--output", bad) == 2
    assert not tuple(tmp_path.iterdir())

    with monkeypatch.context() as patch:
        patch.setattr(builder, "build_st12f_projections",
            lambda: {**original_projection, expected_names[-1]: "{malformed-final-json}\n"})
        with pytest.raises(ValueError):
            run("--st12f-only")
    assert not tuple(tmp_path.iterdir())

    target.mkdir(parents=True)
    invalid_late_target = target / expected_names[-1]
    invalid_late_target.mkdir()
    with pytest.raises(ValueError, match="invalid isolated F output destination"):
        run("--st12f-only")
    assert not any(path.is_file() for path in tmp_path.rglob("*"))
    invalid_late_target.rmdir()

    expected = {target / name: original_projection[name].encode("utf-8") for name in expected_names}
    assert run("--st12f-only") == 0
    assert {path for path in tmp_path.rglob("*") if path.is_file()} == set(expected)
    assert {path:path.read_bytes() for path in expected} == expected
    assert all(raw.endswith(b"\n") and b"\r" not in raw for raw in expected.values())
    manifest = json.loads((target / "manifest.json").read_bytes())
    assert manifest["lp03_private_receiver_acceptance"] == {
        "schema": "QTT_LP03_PRIVATE_RECEIVER_ACCEPTANCE_CONTRACT_V1",
        "method": "receive_evidence_delivery_v1",
        "purpose": "EVIDENCE_RECEIVER_ACCEPTANCE_V1",
        "delivery_record_type": "EvidenceDeliveryRecordV1",
        "ack_record_type": "EvidenceReceiverAckRecordV1",
        "ack_signing_key_purpose": "RECEIVER_ACCEPTANCE",
        "receiver_role_stores": {
            "READINESS1": "READINESS_ACK",
            "PRETRADE1": "PRETRADE_ACK",
            "AGENT_ORCH1": "AGENT_ACK",
            "SVC1": "SVC_ACK",
        },
        "receiver_commit_and_original_readback_required": True,
        "exact_retransmission": "RETURN_IDENTICAL_ACK",
        "conflicting_delivery": "EVIDENCE_RECEIVER_CONFLICT",
        "missing_ack": "RECEIVER_ACKNOWLEDGEMENTS_PENDING",
        "dashboard_source": "SVC1",
        "runtime_effect_authorized": False,
        "ack_record_instance_count": 0,
    }
    isolated_console = capsys.readouterr()
    assert isolated_console.out.splitlines() == [builder.SUCCESS_MARKER]
    untouched = {path:path.stat().st_mtime_ns for path in expected}
    assert run("--st12f-only") == 0
    assert {path:path.stat().st_mtime_ns for path in expected} == untouched

    rewrite = target / "manifest.json"
    rewrite.write_bytes(expected[rewrite].replace(b"\n", b"\r\n"))
    assert run("--st12f-only") == 0
    assert {path:path.read_bytes() for path in expected} == expected
    assert {path:path.stat().st_mtime_ns for path in expected if path != rewrite} == {
        path:mtime for path,mtime in untouched.items() if path != rewrite}

    export = tmp_path / ".tmp/exports/qku.json"
    export.parent.mkdir(parents=True)
    assert run("--st12f-only", "--output", ".tmp/exports") == 2
    assert {path for path in tmp_path.rglob("*") if path.is_file()} == set(expected)
    monkeypatch.setattr(builder, "build_st12e_projections", lambda: original_e_projection)
    monkeypatch.setattr(builder, "build_st12d_projections", original_d_builder)
    assert run("--st12f-only", "--output", ".tmp/exports/qku.json") == 0
    assert {path for path in tmp_path.rglob("*") if path.is_file()} == {*expected, export}
    assert export.read_bytes() == builder._encode_build_payload(payload).encode("utf-8")
    assert json.loads(export.read_bytes())["tranche_f"]["generated_projection_count"] == 13
    successful_console = capsys.readouterr()
    assert successful_console.out.count(builder.SUCCESS_MARKER) == 3
    assert successful_console.out.count("S1_SELECTED_COMPONENT_PACKAGE_V1_VALIDATED") == 1
    assert successful_console.out.count("S1_SELECTED_COMPONENT_PACKAGE_V1_REPRODUCIBLE") == 1

    failure_root = tmp_path / "isolated_late_write"
    failure_root.mkdir()
    relative_prefix = target.relative_to(tmp_path)
    blocked = failure_root / relative_prefix / expected_names[2]
    original_write = Path.write_bytes
    def fail_third(path, raw):
        if path == blocked:
            raise OSError("controlled late write failure")
        return original_write(path, raw)

    with monkeypatch.context() as patch:
        patch.setattr(builder, "REPO_ROOT", failure_root)
        patch.setattr(Path, "write_bytes", fail_third)
        with pytest.raises(OSError, match="controlled late write failure"):
            run("--st12f-only")
    partial_console = capsys.readouterr()
    assert partial_console.out == ""
    prefix = "ST12F_GENERATION_WRITE_INCOMPLETE="
    assert partial_console.err.startswith(prefix)
    partial = json.loads(partial_console.err.removeprefix(prefix))
    assert partial == {
        "completed_write_paths": [(relative_prefix / name).as_posix() for name in expected_names[:2]],
        "failed_path": (relative_prefix / expected_names[2]).as_posix(),
        "native_error": "OSError",
    }
    actual_files = {path.relative_to(failure_root).as_posix():path.read_bytes()
                    for path in failure_root.rglob("*") if path.is_file()}
    expected_files = {(relative_prefix / name).as_posix():expected[target / name] for name in expected_names[:2]}
    assert actual_files == expected_files
