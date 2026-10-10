from __future__ import annotations

from .helpers import REPO_ROOT
from src.qtt.stage1_prediction_markets.pr166_q_quantum_classical_hybrid_comparator import constants as c
from pathlib import Path


def test_pr166_q_required_reports_and_schemas_exist(tmp_path, monkeypatch):
    assert len(c.REPORT_FILENAMES) == 44
    assert len(c.SCHEMA_FILENAMES) == len(c.REPORT_FILENAMES) + 1
    for filename in c.REPORT_FILENAMES:
        assert (REPO_ROOT / c.GENERATED_DIR / filename).exists(), filename
    for filename in c.SCHEMA_FILENAMES:
        assert (REPO_ROOT / c.SCHEMA_DIR / filename).exists(), filename
    assert not list((REPO_ROOT / c.GENERATED_DIR).glob("PR166_Q_*.sha256"))
    assert not list((REPO_ROOT / c.GENERATED_DIR).glob("PR166_Q_*checksum*.json"))
    assert not list((REPO_ROOT / c.GENERATED_DIR).glob("PR166_Q_*digest*.json"))

    from copy import deepcopy
    import json
    import pytest
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.errors import SerializationSafetyError
    from src.qtt.stage1_prediction_markets.pr166_q_quantum_classical_hybrid_comparator import io as q_io, validator as q_validator
    from src.qtt.stage1_prediction_markets.pr166_qb_bounded_quantum_benchmark import io as qb_io
    from src.qtt.stage1_prediction_markets.pr166_qc_quantum_selected_replay_paper_retest import io as qc_io
    from src.qtt.stage1_prediction_markets.pr162e_q_quantum_automapper import io as map_io
    from src.qtt.stage1_prediction_markets.pr167_open_trade_simulator_integration import io as sim_io
    from src.qtt.stage1_prediction_markets.pr165_d3_quantum_aware_scenario_selection_v3 import io as d3_io

    root = tmp_path / "report-input"
    root.mkdir()
    root_report = root / "root.json"
    shard = root / "part.json"
    shard.write_text('{"records":[{"row_id":"unit-row"}]}\n', encoding="utf-8")
    valid = {"records": [], "shard_files": ["part.json", "part.json"], "sharded_flag": True}
    for reader in (q_io, qb_io, qc_io, map_io, sim_io, d3_io):
        root_report.write_text(json.dumps(valid) + "\n", encoding="utf-8")
        parsed = reader.read_json(root_report)
        assert reader.records_from_report_payload(root, parsed) == [{"row_id":"unit-row"}, {"row_id":"unit-row"}]
        for text in ('{"records":[],"records":[{}]}', '{"records":[],"value":1e999}', '{"records":[],"value":NaN}', '[]'):
            root_report.write_text(text, encoding="utf-8")
            with pytest.raises(SerializationSafetyError):
                reader.read_json(root_report)
        for invalid in ({"records": None}, {"records": [1]}, {"records": [], "shard_files":"part.json"}, {"records":[], "shard_files":["../escape.json"]}, {"records":[], "shard_files":["part.json"], "shard_paths":["other.json"]}):
            with pytest.raises(SerializationSafetyError):
                reader.records_from_report_payload(root, invalid)
        with pytest.raises(FileNotFoundError):
            reader.records_from_report_payload(root, {"records":[], "shard_files":["absent.json"]})

    # This unit boundary tests the original payload predicate, not row eligibility.
    name = "PR166_Q_FinalSummary.report.json"
    target = root / c.GENERATED_DIR / name
    target.parent.mkdir(parents=True)
    target.write_text("{}\n", encoding="utf-8")
    base = {"report_filename":name, "roadmap_pr_id":c.PR_ID, "created_by_pr":c.PR_ID,
            "authority_class":c.AUTHORITY_CLASS, "authority_boundary_ref":c.AUTHORITY_BOUNDARY_REF,
            "validation_status":c.VALIDATION_STATUS, "schema_ref":c.REPORT_SCHEMA_REFS[name], "record_count":1}
    for count in (True, 1.0, "1", 1.9, None, -1):
        changed = deepcopy(base)
        changed["record_count"] = count
        failures = []
        q_validator._validate_payload_contracts(root, {name:changed}, {name:[{}]}, failures)
        assert failures == [f"{name} record_count mismatch"]
    missing = deepcopy(base)
    del missing["record_count"]
    failures = []
    q_validator._validate_payload_contracts(root, {name:missing}, {name:[{}]}, failures)
    assert failures == [f"{name} record_count mismatch"]
    failures = []
    q_validator._validate_payload_contracts(root, {name:base}, {name:[{}]}, failures)
    assert failures == []
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.serialization import _report_manifest_consistency_v1

    # The three existing manifest layouts share these typed, in-memory invariants.
    names = ("A.report.json", "Manifest.report.json")
    manifest_name = names[1]
    schema_refs = {names[0]: "a.schema.json", names[1]: "manifest.schema.json"}
    for style in ("Q_ROOT_AND_SHARD", "ROOT_REFERENCE", "D3_ROOT_REFERENCE"):
        refs = ["part.json", "part.json"]
        payloads = {
            names[0]: {"report_filename": names[0], "report_name": names[0], "records": [],
                       "record_count": 2, "schema_ref": schema_refs[names[0]], "sharded_flag": True,
                       "records_omitted_for_sharding_flag": True, "shard_count": 2,
                       "shard_files": refs[:]},
            names[1]: {"report_filename": names[1], "report_name": names[1], "records": [],
                       "record_count": 0, "schema_ref": schema_refs[names[1]], "sharded_flag": False},
        }
        if style != "D3_ROOT_REFERENCE":
            payloads[names[0]]["shard_manifest_refs"] = [
                {"shard_index": index, "shard_path": ref, "row_count": 1}
                for index, ref in enumerate(refs, start=1)
            ]
        manifest_rows = []
        for name in names:
            source = payloads[name]
            paths = source.get("shard_files", [])
            if style == "Q_ROOT_AND_SHARD":
                manifest_rows.append({"manifest_entry_class": "ROOT_REPORT", "report_filename": name,
                    "report_name": name.removesuffix(".report.json"), "report_path": "generated/" + name,
                    "schema_path": "schemas/" + schema_refs[name], "row_count": source["record_count"],
                    "compact_or_sharded_flag": "SHARDED_COMPACT_ROOT" if paths else "ROOT_WITH_RECORDS"})
                for ref in paths:
                    manifest_rows.append({"manifest_entry_class": "SHARD_REPORT", "parent_report_filename": name,
                        "report_filename": ref, "report_name": ref.removesuffix(".report.json"),
                        "report_path": ref, "schema_path": "schemas/" + schema_refs[name], "row_count": 1,
                        "compact_or_sharded_flag": "SHARD_REPORT", "consumed_by_report": name})
            else:
                d3 = style == "D3_ROOT_REFERENCE"
                manifest_rows.append({"manifest_report_name" if d3 else "report_ref": name,
                    "root_report_path" if d3 else "report_path": "generated/" + name,
                    "referenced_schema_ref" if d3 else "schema_ref": schema_refs[name],
                    "record_count": source["record_count"], "sharded_flag": source["sharded_flag"],
                    "shard_files": paths[:]})
                if d3:
                    manifest_rows[-1].update(records_omitted_for_sharding_flag=bool(paths), shard_count=len(paths))
        count_key = "row_count" if style == "Q_ROOT_AND_SHARD" else "record_count"
        payloads[manifest_name].update(records=manifest_rows, record_count=len(manifest_rows))
        manifest_rows[-1][count_key] = len(manifest_rows)
        expanded = {names[0]: [{"row_id": "one"}, {"row_id": "one"}], manifest_name: manifest_rows}
        bindings = {"style": style, "schema_refs": schema_refs if style != "ROOT_REFERENCE" else None}
        preserved = deepcopy((payloads, expanded))
        assert _report_manifest_consistency_v1(payloads, expanded, names, manifest_name,
            "generated", "schemas", **bindings) is None
        assert (payloads, expanded) == preserved
        bad_payloads, bad_expanded = deepcopy((payloads, expanded))
        bad_expanded[manifest_name].append(deepcopy(bad_expanded[manifest_name][0]))
        bad_payloads[manifest_name]["record_count"] = len(bad_expanded[manifest_name])
        # Synchronize the manifest's own count so the duplicate is not masked by a count failure.
        bad_expanded[manifest_name][-2][count_key] = len(bad_expanded[manifest_name])
        with pytest.raises(SerializationSafetyError, match="duplicate root"):
            _report_manifest_consistency_v1(bad_payloads, bad_expanded, names, manifest_name,
                "generated", "schemas", **bindings)
        bad_payloads, bad_expanded = deepcopy((payloads, expanded))
        bad_expanded[manifest_name][0][count_key] = True
        with pytest.raises(SerializationSafetyError, match="count"):
            _report_manifest_consistency_v1(bad_payloads, bad_expanded, names, manifest_name,
                "generated", "schemas", **bindings)
        if style == "Q_ROOT_AND_SHARD":
            bad_payloads, bad_expanded = deepcopy((payloads, expanded))
            bad_expanded[manifest_name][1]["parent_report_filename"] = "unknown.report.json"
            with pytest.raises(SerializationSafetyError, match="parent"):
                _report_manifest_consistency_v1(bad_payloads, bad_expanded, names, manifest_name,
                    "generated", "schemas", **bindings)

    # Equal aggregate counts do not excuse wrong counts on individual acquisitions.
    described = {"records": [], "sharded_flag": True, "shard_files": ["part.json", "part.json"],
        "shard_manifest_refs": [{"shard_index": 1, "shard_path": "part.json", "row_count": 0},
                                {"shard_index": 2, "shard_path": "part.json", "row_count": 2}]}
    with pytest.raises(SerializationSafetyError, match="observed row count"):
        q_io.records_from_report_payload(root, described)
    described["shard_manifest_refs"][0]["row_count"] = 1
    described["shard_manifest_refs"][1]["row_count"] = 1
    for count in (True, 1.0, "1", -1, None, 2):
        shard.write_text(json.dumps({"records": [{"row_id": "unit-row"}], "record_count": count}), encoding="utf-8")
        with pytest.raises(SerializationSafetyError, match="observed count"):
            q_io.records_from_report_payload(root, described)
    shard.write_text('{"records":[{"row_id":"unit-row"}],"record_count":1}\n', encoding="utf-8")
    assert q_io.records_from_report_payload(root, described) == [{"row_id": "unit-row"}, {"row_id": "unit-row"}]

    # Schema files are contracts, not existence markers or caller-selected permissive policies.
    from types import SimpleNamespace
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.serialization import (
        _report_schema_templates_v1, _report_schema_session_v1, _report_schema_records_v1,
    )
    schema_constants = SimpleNamespace(
        REPORT_FILENAMES=("one.report.json",),
        SCHEMA_DIR=Path("schemas"), GENERATED_DIR=Path("generated"), PR_ID="PR166-QB",
    )
    fixed_name = lambda name: "one.schema.json"
    _, schema_bank = _report_schema_templates_v1(schema_constants, profile="QB", schema_name=fixed_name)
    schema_reader = lambda path: deepcopy(schema_bank[path.name])
    schema_check = _report_schema_session_v1(root, schema_constants, schema_reader,
        profile="QB", schema_name=fixed_name)
    report = {"report_filename": "one.report.json", "report_name": "one.report.json",
        "roadmap_pr_id": "PR166-QB", "created_by_pr": "PR166-QB", "schema_ref": "one.schema.json",
        "record_count": 0, "records": []}
    no_child_read = lambda path: (_ for _ in ()).throw(AssertionError("unexpected child read"))
    assert _report_schema_records_v1(root, report, no_child_read, schema_check, "one.report.json") == []
    for field, value in (("record_count", False), ("record_count", 0.0),
                         ("schema_ref", "unselected.schema.json"), ("created_by_pr", "wrong")):
        invalid_report = deepcopy(report)
        invalid_report[field] = value
        with pytest.raises(SerializationSafetyError):
            _report_schema_records_v1(root, invalid_report, no_child_read, schema_check, "one.report.json")
    for corruption in ({}, {"type": "object"}):
        schema_bank["one.schema.json"] = corruption
        with pytest.raises(SerializationSafetyError, match="source-defined contract"):
            _report_schema_session_v1(root, schema_constants, schema_reader, profile="QB", schema_name=fixed_name)

    # A missing optional leaf is not an unreadable, partial, or replaced directory.
    import os
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.serialization import _report_directory_entries_v1
    from src.qtt.stage1_prediction_markets.pr166_qb_bounded_quantum_benchmark import validator as qb_validator
    from src.qtt.stage1_prediction_markets.pr166_qc_quantum_selected_replay_paper_retest import validator as qc_validator
    from src.qtt.stage1_prediction_markets.pr162e_q_quantum_automapper import validator as map_validator
    from src.qtt.stage1_prediction_markets.pr167_open_trade_simulator_integration import validator as sim_validator
    from src.qtt.stage1_prediction_markets.pr165_d3_quantum_aware_scenario_selection_v3 import validator as d3_validator
    inventory_root = tmp_path / "directory-inventory"
    (inventory_root / c.GENERATED_DIR).mkdir(parents=True)
    modules = (q_validator, qb_validator, qc_validator, map_validator, sim_validator, d3_validator)
    for module in modules:
        check = getattr(module, "_validate_no_forbidden_sidecars", None) or module._validate_generated_forbidden_files
        failures = []
        check(inventory_root, failures)
        assert failures == []
        with monkeypatch.context() as scoped:
            def denied_scan(*args, **kwargs):
                raise PermissionError("diagnostic directory denial")
            scoped.setattr(os, "scandir", denied_scan)
            with pytest.raises(PermissionError):
                check(inventory_root, [])
    optional = inventory_root / "missing-optional-directory"
    assert _report_directory_entries_v1(optional, allow_absent=True) == ()
    with pytest.raises(FileNotFoundError):
        _report_directory_entries_v1(optional)
    with pytest.raises(SerializationSafetyError):
        _report_directory_entries_v1(optional, allow_absent=1)

    # Authority counters use the existing exact-integer domain, not numeric equality.
    count_name = "PR166_Q_FinalSummary.report.json"
    for role in ("payload", "row"):
        for key in q_validator.ZERO_AUTHORITY_KEYS:
            for value in (0, False, True, 0.0, -0.0, 1, -1, "0", None, [], {}):
                payload = {field: 0 for field in q_validator.ZERO_AUTHORITY_KEYS}
                row = dict(payload, row_id="authority-count-case")
                row.update({field: False for field in q_validator.FORBIDDEN_AUTHORITY_FLAGS})
                (payload if role == "payload" else row)[key] = value
                failures = []
                q_validator._validate_authority({count_name: payload}, {count_name: [row]}, failures)
                admissible = type(value) is int and value == 0
                prefix = (f"{count_name} authority count not zero: " if role == "payload"
                          else f"{count_name} row authority-count-case authority count not zero: ")
                assert failures == ([] if admissible else [prefix + key])

    # The three admitted report families share one reader; aliases captured
    # before binding must not bypass it or borrow another family's profile.
    import os
    import sys
    import time
    from tools import validation_reliability as reliability
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane import serialization
    for family, position, cli, module in (
        ("QB", 66, "tools/validate_pr166_qb_bounded_quantum_benchmark.py", qb_io),
        ("QC", 67, "tools/validate_pr166_qc_quantum_selected_replay_paper_retest.py", qc_io),
        ("MAPPER", 68, "tools/validate_pr162e_q_quantum_automapper.py", map_io),
    ):
        source = tmp_path / ("bound-source-" + family)
        reference = tmp_path / ("bound-reference-" + family) / "basis.bin"
        source.mkdir(); reference.parent.mkdir()
        raw = b'{"v":1}\n'
        target = source / "unit.json"; target.write_bytes(raw); reference.write_bytes(raw)
        with target.open("rb") as stream:
            target_fd_stamp = reliability._mapper_stamp_v1(os.fstat(stream.fileno()))
        with reference.open("rb") as stream:
            basis_fd_stamp = reliability._mapper_stamp_v1(os.fstat(stream.fileno()))
        profile = dict(kind="MAPPER_DISK_BASIS_V1", position=position, generation="synthetic-unit",
            root=str(source), root_chain=reliability._mapper_chain_v1(source),
            basis=str(reference), basis_chain=reliability._mapper_chain_v1(reference.parent),
            basis_lstat=reliability._mapper_stamp_v1(reference.lstat()), basis_fstat=basis_fd_stamp,
            entries=[dict(path="unit.json", offset=0, length=len(raw), attempt_limit=2,
                lstat=reliability._mapper_stamp_v1(target.lstat()), fstat=target_fd_stamp,
                parent_chain=reliability._mapper_chain_v1(source))],
            limits=dict(attempts=2, target_bytes=2*(len(raw)+1), basis_bytes=2*len(raw),
                metadata_calls=10000, single_target_buffer=len(raw)+1),
            chunk_bytes=3, deadline_ns=time.monotonic_ns()+30_000_000_000)
        binding = dict(kind="MAPPER_NATIVE_READ_BINDING_V1", run_id="synthetic-reader", phase="unit",
            command_index=1, command_count=1, original_position=position, repo_root=str(source),
            process_root=str(tmp_path/"process"), evidence_root=str(tmp_path/"evidence"),
            parent_argv=[sys.executable, cli], child_argv=None,
            run_read_limits=dict(byte_limit=1048576, node_limit=10000, depth_limit=32, profile_limit=5),
            basis=profile)
        alias = module.read_json
        with reliability._mapper_bound_reads_v1(binding) as bounded:
            assert alias(target) == {"v":1}
            for other in (qb_io, qc_io, map_io):
                if other is not module:
                    with pytest.raises(ValueError, match="REPORT_READER_FAMILY_MISMATCH"):
                        other.read_json(target)
            assert bounded.counters["attempts"] == 1
            with pytest.raises(ValueError, match="MAPPER_CONCURRENT_BINDING"):
                with reliability._mapper_bound_reads_v1(binding):
                    pass
            assert alias(target) == {"v":1}
            assert bounded.counters["target_bytes"] == bounded.counters["basis_bytes"] == 2*len(raw)
        assert bounded.closed and serialization._REPORT_READ_BINDING_V1 is None
        with monkeypatch.context() as guard:
            guard.setenv("QTT_MAPPER_READ_INDEX", "1")
            with pytest.raises(ValueError, match="WITHOUT_ACTIVE_READER"):
                alias(target)
        assert alias(target) == {"v":1}
