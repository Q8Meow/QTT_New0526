from __future__ import annotations

import copy
import json
from pathlib import Path
import subprocess

import pytest

from tools.validate_source_fact_binding_connector_semantic_readiness_static import (
    ACCEPTED_PACKET_REQUIRED,
    BLOCKED_PENDING_PACKET,
    REQUIRED_TYPED_ARTIFACTS,
    SOURCE_REQUIRED,
    TARGET_FIELDS,
    VENUE_IDS,
    validate_connector_semantic_target_field_matrix_fixture,
    validate_readiness_gate_report_fixture,
    validate_source_to_connector_matrix_fixture,
    validate_static_surface,
)


SOURCE_MATRIX_SCHEMA = Path(
    "schemas/source_fact_binding_readiness/stage1_source_to_connector_field_binding_matrix.schema.json"
)
SOURCE_MATRIX_FIXTURE = Path(
    "tests/fixtures/source_fact_binding_readiness/"
    "synthetic_stage1_source_to_connector_field_binding_matrix.v1.fixture.json"
)
CONNECTOR_MATRIX_SCHEMA = Path(
    "schemas/source_fact_binding_readiness/stage1_connector_semantic_target_field_matrix.schema.json"
)
CONNECTOR_MATRIX_FIXTURE = Path(
    "tests/fixtures/source_fact_binding_readiness/"
    "synthetic_stage1_connector_semantic_target_field_matrix.v1.fixture.json"
)
GATE_REPORT_SCHEMA = Path(
    "schemas/source_fact_binding_readiness/stage1_connector_semantic_readiness_gate_report.schema.json"
)
GATE_REPORT_FIXTURE = Path(
    "tests/fixtures/source_fact_binding_readiness/"
    "synthetic_stage1_connector_semantic_readiness_gate_report.v1.fixture.json"
)
VALIDATOR = Path(
    "tools/validate_source_fact_binding_connector_semantic_readiness_static.py"
)


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _source_matrix() -> dict:
    return _load(SOURCE_MATRIX_FIXTURE)


def _connector_matrix() -> dict:
    return _load(CONNECTOR_MATRIX_FIXTURE)


def _gate_report() -> dict:
    return _load(GATE_REPORT_FIXTURE)


def _assert_failure_contains(failures: list[str], fragment: str) -> None:
    assert any(fragment in failure for failure in failures), failures


def test_pr38_readiness_artifacts_exist():
    for path in [
        SOURCE_MATRIX_SCHEMA,
        SOURCE_MATRIX_FIXTURE,
        CONNECTOR_MATRIX_SCHEMA,
        CONNECTOR_MATRIX_FIXTURE,
        GATE_REPORT_SCHEMA,
        GATE_REPORT_FIXTURE,
        VALIDATOR,
    ]:
        assert path.exists(), path

    report = _gate_report()
    assert report["required_typed_artifacts_represented"] == REQUIRED_TYPED_ARTIFACTS


def test_source_to_connector_field_binding_matrix_is_schema_valid():
    assert (
        validate_static_surface(
            repo_root=Path("."),
            source_to_connector_schema_path=SOURCE_MATRIX_SCHEMA,
            source_to_connector_fixture_path=SOURCE_MATRIX_FIXTURE,
            connector_target_schema_path=CONNECTOR_MATRIX_SCHEMA,
            connector_target_fixture_path=CONNECTOR_MATRIX_FIXTURE,
            gate_report_schema_path=GATE_REPORT_SCHEMA,
            gate_report_fixture_path=GATE_REPORT_FIXTURE,
            scan_python_usage=False,
        )
        == []
    )
    assert validate_source_to_connector_matrix_fixture(_source_matrix()) == []


def test_connector_semantic_target_field_matrix_is_schema_valid():
    assert validate_connector_semantic_target_field_matrix_fixture(_connector_matrix()) == []


def test_readiness_gate_report_is_schema_valid():
    assert validate_readiness_gate_report_fixture(_gate_report(), repo_root=Path(".")) == []


def test_all_target_fields_remain_source_required_or_accepted_packet_required():
    source_matrix = _source_matrix()
    connector_matrix = _connector_matrix()

    assert [row["venue_id"] for row in source_matrix["venue_rows"]] == VENUE_IDS
    assert [row["venue_id"] for row in connector_matrix["venue_rows"]] == VENUE_IDS

    for row in source_matrix["venue_rows"]:
        assert row["target_field_paths"] == TARGET_FIELDS
        assert row["source_dependency_state"] == SOURCE_REQUIRED
        assert row["accepted_packet_requirement_state"] == ACCEPTED_PACKET_REQUIRED
        assert row["readiness_state"] == BLOCKED_PENDING_PACKET
        assert row["connector_semantic_value_state"] == SOURCE_REQUIRED
        assert row["connector_semantic_value_populated"] is False

    for row in connector_matrix["venue_rows"]:
        assert row["target_field_paths"] == TARGET_FIELDS
        assert row["target_field_state"] == SOURCE_REQUIRED
        assert row["accepted_packet_requirement_state"] == ACCEPTED_PACKET_REQUIRED
        assert row["readiness_state"] == BLOCKED_PENDING_PACKET
        assert row["connector_semantic_value_state"] == SOURCE_REQUIRED
        assert row["connector_semantic_value_populated"] is False


def test_validator_blocks_accepted_source_facts():
    report = _gate_report()
    report["source_fact_binding_readiness_report"][
        "accepted_source_fact_created_count"
    ] = 1
    report["no_claim_flags"]["accepts_source_facts"] = True

    failures = validate_readiness_gate_report_fixture(report, repo_root=Path("."))

    _assert_failure_contains(failures, "accepted_source_fact_created_count")
    _assert_failure_contains(failures, "accepts_source_facts")


def test_validator_blocks_connector_semantic_value_population():
    matrix = _connector_matrix()
    row = matrix["venue_rows"][0]
    row["connector_semantic_value_state"] = "CONNECTOR_SEMANTIC_VALUE_POPULATED"
    row["connector_semantic_value_populated"] = True

    failures = validate_connector_semantic_target_field_matrix_fixture(matrix)

    _assert_failure_contains(failures, "connector_semantic_value_state")
    _assert_failure_contains(failures, "connector_semantic_value_populated")


def test_validator_blocks_runtime_resolver_snapshot_claims():
    matrix = _connector_matrix()
    matrix["venue_rows"][0]["runtime_resolver_snapshot_created"] = True

    failures = validate_connector_semantic_target_field_matrix_fixture(matrix)

    _assert_failure_contains(failures, "runtime_resolver_snapshot_created")


def test_validator_blocks_replay_paper_live_order_and_profit_claims():
    report = _gate_report()
    report["connector_semantic_readiness_summary"][
        "replay_paper_execution_violation_count"
    ] = 1
    report["connector_semantic_readiness_summary"][
        "live_reachability_violation_count"
    ] = 1
    report["forbidden_action_flags"]["order_authority_enabled"] = True
    report["forbidden_action_flags"]["profit_evidence_creation_enabled"] = True
    report["no_claim_flags"]["creates_profit_evidence"] = True

    failures = validate_readiness_gate_report_fixture(report, repo_root=Path("."))

    _assert_failure_contains(failures, "replay_paper_execution_violation_count")
    _assert_failure_contains(failures, "live_reachability_violation_count")
    _assert_failure_contains(failures, "order_authority_enabled")
    _assert_failure_contains(failures, "profit_evidence_creation_enabled")
    _assert_failure_contains(failures, "creates_profit_evidence")


def test_validator_blocks_atomicrows_bundle_hash_creation_or_mutation(tmp_path):
    bundle = tmp_path / "docs" / "master_plan" / "atomic_rows" / "AtomicRows.bundle.jsonl"
    bundle.parent.mkdir(parents=True)
    bundle.write_text("", encoding="utf-8")

    failures = validate_readiness_gate_report_fixture(_gate_report(), repo_root=tmp_path)

    _assert_failure_contains(failures, "canonical AtomicRows bundle must remain absent")


@pytest.mark.parametrize(
    "script_name",
    [
        "playwright_pr169_dash1_ui1_r1_visual_smoke.py",
        "playwright_pr169_dash1_ui1_r2_visual_smoke.py",
        "playwright_pr169_dash1_ui1_r2_r1_visual_smoke.py",
        "playwright_pr169_dash1_ui1_r2_r2_visual_smoke.py",
        "playwright_pr169_dash1_ui1_r2_r3_visual_smoke.py",
        "playwright_pr169_dash1_ui1_r2_r4_visual_smoke.py",
    ],
)
def test_python_usage_scan_allows_exact_local_visual_qa_playwright_path(tmp_path, script_name):
    script = tmp_path / "tools" / script_name
    script.parent.mkdir(parents=True)
    script.write_text(
        "\n".join(
            [
                "from playwright.sync_api import sync_playwright",
                "def main():",
                "    return sync_playwright",
            ]
        ),
        encoding="utf-8",
    )

    failures = validate_static_surface(
        repo_root=tmp_path,
        source_to_connector_schema_path=SOURCE_MATRIX_SCHEMA,
        source_to_connector_fixture_path=SOURCE_MATRIX_FIXTURE,
        connector_target_schema_path=CONNECTOR_MATRIX_SCHEMA,
        connector_target_fixture_path=CONNECTOR_MATRIX_FIXTURE,
        gate_report_schema_path=GATE_REPORT_SCHEMA,
        gate_report_fixture_path=GATE_REPORT_FIXTURE,
    )

    assert failures == []


def test_python_usage_scan_rejects_unregistered_playwright_path(tmp_path):
    _assert_f14_shared_native_admission(tmp_path / "f14")
    _assert_kalshi_shared_native_admission(tmp_path / "kalshi")
    script = tmp_path / "tools" / "bad_browser_fetch.py"
    script.parent.mkdir(parents=True)
    script.write_text(
        "from playwright.sync_api import sync_playwright\n",
        encoding="utf-8",
    )

    failures = validate_static_surface(
        repo_root=tmp_path,
        source_to_connector_schema_path=SOURCE_MATRIX_SCHEMA,
        source_to_connector_fixture_path=SOURCE_MATRIX_FIXTURE,
        connector_target_schema_path=CONNECTOR_MATRIX_SCHEMA,
        connector_target_fixture_path=CONNECTOR_MATRIX_FIXTURE,
        gate_report_schema_path=GATE_REPORT_SCHEMA,
        gate_report_fixture_path=GATE_REPORT_FIXTURE,
    )

    _assert_failure_contains(
        failures,
        "tools/bad_browser_fetch.py imports forbidden network/client module playwright.sync_api",
    )


def test_validator_does_not_mutate_inputs_or_create_atomicrows_files(tmp_path):
    source_before = SOURCE_MATRIX_FIXTURE.read_bytes()
    connector_before = CONNECTOR_MATRIX_FIXTURE.read_bytes()
    report_before = GATE_REPORT_FIXTURE.read_bytes()
    source = _source_matrix()
    connector = _connector_matrix()
    report = _gate_report()
    frozen = (copy.deepcopy(source), copy.deepcopy(connector), copy.deepcopy(report))

    assert validate_source_to_connector_matrix_fixture(source) == []
    assert validate_connector_semantic_target_field_matrix_fixture(connector) == []
    assert validate_readiness_gate_report_fixture(report, repo_root=tmp_path) == []

    assert SOURCE_MATRIX_FIXTURE.read_bytes() == source_before
    assert CONNECTOR_MATRIX_FIXTURE.read_bytes() == connector_before
    assert GATE_REPORT_FIXTURE.read_bytes() == report_before
    assert (source, connector, report) == frozen
    assert not (
        tmp_path
        / "docs"
        / "master_plan"
        / "atomic_rows"
        / "AtomicRows.bundle.jsonl"
    ).exists()
    assert not (
        tmp_path
        / "docs"
        / "master_plan"
        / "atomic_rows"
        / "AtomicRows.bundle.sha256"
    ).exists()


def test_master_plan_remains_unchanged():
    completed = subprocess.run(
        ["git", "diff", "--", "docs/master_plan/QTT_MasterPlan_Current.md"],
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0
    assert completed.stdout == ""


_F14_INDEPENDENT_NATIVE_TEMPLATE = 'class RetailPrivateIngressV1:\n    def read_rest_once(self, request):\n        prepared = self._prepare_rest_v1(request)\n        import http.client\n        connection = http.client.HTTPSConnection("api.polymarket.us", 443, timeout=prepared.timeout_seconds, context=prepared.tls_context)\n        try:\n            self._recheck_and_charge_v1(prepared)\n            connection.request("GET", prepared.target, body=None, headers=prepared.headers)\n            response = connection.getresponse()\n            self._validate_response_headers_v1(prepared, response)\n            raw = response.read(prepared.maximum_raw_bytes + 1)\n            received = self._observe_clock_v1()\n            self._validate_response_body_v1(prepared, response, raw)\n            return self._retain_received_v1(prepared, raw, received, 200)\n        finally:\n            connection.close()\n\n    def read_private_message_once(self, request):\n        prepared = self._prepare_ws_v1(request)\n        import websockets.sync.client\n        with websockets.sync.client.connect("wss://api.polymarket.us/v1/ws/private", ssl=prepared.tls_context, additional_headers=prepared.headers, proxy=None, compression=None, open_timeout=prepared.timeout_seconds, ping_interval=20, ping_timeout=20, close_timeout=10, max_size=prepared.maximum_raw_bytes, max_queue=16, logger=prepared.quiet_logger) as connection:\n            self._verify_handshake_v1(prepared, connection.response)\n            self._recheck_subscription_v1(prepared)\n            connection.send(prepared.subscription_json)\n            state = self._initial_ws_state_v1()\n            for unused in range(prepared.maximum_application_messages):\n                message = connection.recv(timeout=self._remaining_seconds_v1(prepared))\n                received = self._observe_clock_v1()\n                state, disposition, raw = self._classify_ws_message_v1(prepared, state, message)\n                if disposition == "SELECTED_UPDATE":\n                    return self._retain_received_v1(prepared, raw, received, 101)\n            self._raise_message_budget_v1()\n'


_KALSHI_INDEPENDENT_NATIVE_TEMPLATE = "class KalshiFeeObservationOwnerV1:\n    def _read_rest_once_v1(self, role, ticker):\n        prepared = self._prepare_read_v1(role, ticker)\n        import http.client\n        connection = http.client.HTTPSConnection(\"external-api.kalshi.com\", 443, timeout=prepared.timeout_seconds, context=prepared.tls_context)\n        try:\n            self._recheck_and_charge_v1(prepared)\n            connection.request(\"GET\", prepared.target, body=None, headers=prepared.headers)\n            response = connection.getresponse()\n            self._validate_response_headers_v1(prepared, response)\n            raw = response.read(prepared.maximum_raw_bytes + 1)\n            received = self._observe_clock_v1()\n            self._validate_response_body_v1(prepared, response, raw)\n            return self._retain_received_v1(prepared, raw, received)\n        except (OSError, http.client.HTTPException) as error:\n            self._raise_transport_v1(error)\n        finally:\n            try:\n                connection.close()\n            except OSError as error:\n                self._raise_transport_v1(error)\n"


def _assert_source_use_native_boundaries(root):
    import ast
    from pathlib import Path, PurePosixPath
    from tools import validate_no_runtime_artifacts as runtime
    from tools import validate_source_fact_binding_connector_semantic_readiness_static as readiness

    repo = Path(__file__).resolve().parents[2]
    relative = 'src/qtt/service/owner_source_use_windows.py'
    source = (repo / relative).read_text(encoding='utf-8')
    tree = ast.parse(source)
    # Independent expected DLL set, not the mutable scanner's permission table.
    dlls = [n.args[0].value for n in ast.walk(tree) if isinstance(n, ast.Call)
            and ast.unparse(n.func) == 'ctypes.WinDLL']
    assert sorted(dlls) == sorted(('kernel32.dll', 'advapi32.dll', 'shell32.dll',
                                  'ole32.dll', 'user32.dll', 'webauthn.dll'))
    target = root / relative
    target.parent.mkdir(parents=True)
    mutations = [
        source + '\nrun_owner_source_use_local_v1()\n',
        source + '\nlaunch = run_owner_source_use_local_v1\nlaunch()\n',
        source + '\nlaunch = _bootstrap_owner_source_use_v1\nlaunch()\n',
        source + '\ndef alternate_entry():\n    return run_owner_source_use_local_v1()\n',
        source.replace('root = _bootstrap_owner_source_use_v1()', 'root = object()'),
        source + '\nimport ctypes as native_api\nnative_api.WinDLL("unapproved.dll")\n',
        source + '\nloader = ctypes.WinDLL\nloader("unapproved.dll")\n',
        source + '\ngetattr(ctypes, "WinDLL")("unapproved.dll")\n',
        source + '\nctypes.WinDLL("webauthn.dll", use_last_error=True, winmode=0x800)\n',
        source.replace('"webauthn.dll"', '"unapproved.dll"'),
        source.replace('winmode=0x800', 'winmode=0'),
        source.replace('table.WebAuthNAuthenticatorGetAssertion(', 'table.UnapprovedNativeOperation('),
        source.replace('api = _native_system_v1()', 'api = object()'),
        source.replace('        _check_interpreter_v1(installation)', '        _require(True)'),
        source.replace('anchor / "QTT" / "OwnerControl"', 'anchor / "UNOWNED"'),
        source + '\ndef alternate_caller():\n    return _webauthn_table_v1(None)\n',
        source.replace('from fido2.client import win_api', 'from fido2.client import windows as win_api'),
        source + '\nfrom fido2.client import win_api\n',
    ]
    assert runtime.source_use_native_contract_v1(relative, tree) == ()
    for candidate in (source, *mutations):
        target.write_text(candidate, encoding='utf-8')
        expected = candidate != source
        assert bool(runtime._scan_python_content(PurePosixPath(relative), candidate, ['forbid_source_retrieval'])) is expected
        assert bool(readiness._scan_forbidden_python_usage(root)) is expected
    target.write_text(source, encoding='utf-8')
    assert runtime.source_use_native_contract_v1('src/qtt/service/alternate.py', tree)
    policy_path = 'src/qtt/stage1_prediction_markets/qku_computation_control_plane/source_policy.py'
    policy = (repo / policy_path).read_text(encoding='utf-8')
    assert runtime.source_use_native_contract_v1(policy_path, ast.parse(policy)) == ()
    missing_binding = policy.replace('binding._authority._check_binding_v1(binding, self)', 'pass')
    assert missing_binding != policy
    assert runtime.source_use_native_contract_v1(policy_path, ast.parse(missing_binding))
    # The existing exact HTTP templates remain independent transport oracles.
    assert len(runtime.kalshi_fee_native_admission_v1(policy_path, ast.parse(policy))[0]) == 2
    _assert_source_use_independent_censuses(repo)
    _assert_source_use_operations_thread_sites(repo)


def _assert_source_use_operations_thread_sites(repo):
    from tools import independent_validate_qku_computation_control_plane_operations as operations

    # Literal independent expectations: only these two direct method imports.
    exact = """
class KalshiFeeObservationOwnerV1:
    def _prepare_read_v1(self):
        from threading import current_thread
        return current_thread()
    def _require_pending_v1(self):
        from threading import current_thread
        return current_thread()
"""
    check = operations.validate_runtime_topology_source
    assert check(file_name="source_policy.py", source=exact) == ()
    actual = (repo / "src/qtt/stage1_prediction_markets/qku_computation_control_plane/source_policy.py").read_text(encoding="utf-8")
    assert check(file_name="source_policy.py", source=actual) == ()
    for name in ("another.py", "source_policy.py.bak", "other/source_policy.py"):
        assert check(file_name=name, source=exact)
    for mutated in (
        exact.replace("KalshiFeeObservationOwnerV1", "AnotherOwnerV1"),
        exact.replace("_prepare_read_v1", "another_method"),
        exact.replace("_require_pending_v1", "another_method"),
        exact.replace("from threading import current_thread", "from threading import current_thread as alias", 1),
        exact.replace("from threading import current_thread", "from threading import current_thread, Thread", 1),
        exact.replace("from threading import current_thread", "from .threading import current_thread", 1),
        exact.replace("from threading import current_thread", "from threading import current_thread\n        from threading import current_thread", 1),
        exact.replace("from threading import current_thread", "def nested():\n            from threading import current_thread", 1),
        exact + "\nfrom threading import current_thread\n",
        exact + "\nclass AnotherOwner:\n    from threading import current_thread\n",
        exact + "\nclass KalshiFeeObservationOwnerV1:\n    pass\n",
        exact + "    def _prepare_read_v1(self):\n        from threading import current_thread\n",
        exact.replace("def _prepare_read_v1", "async def _prepare_read_v1"),
        exact + "    async def _prepare_read_v1(self):\n        pass\n",
        exact + "\nimport threading\n",
        exact + "\nfrom threading import Lock\n",
    ):
        assert any("runtime import" in item for item in check(file_name="source_policy.py", source=mutated))


def _assert_source_use_independent_censuses(repo):
    import ast
    from types import SimpleNamespace
    from tools import independent_validate_qku_computation_control_plane_source as source
    from tools import independent_validate_qku_computation_control_plane_execution as execution
    # Execute the actual standalone validator function without importing its
    # CLI-only sibling import graph or any production/native code.
    security_tree = ast.parse((repo / "tools/independent_validate_qku_computation_control_plane_security.py").read_text(encoding="utf-8"))
    security_node = next(n for n in security_tree.body if isinstance(n, ast.FunctionDef) and n.name == "_source_use_security_failures_v1")
    security_namespace = {"ast": ast}
    exec(compile(ast.Module(body=[security_node], type_ignores=[]), "<independent-security-census>", "exec"), security_namespace)
    security = SimpleNamespace(_source_use_security_failures_v1=security_namespace[security_node.name])

    class ObservedRoot:
        def __init__(self, replacements):
            self.replacements = replacements
        def __truediv__(self, relative):
            value = self.replacements.get(relative)
            if value is None:
                value = (repo / relative).read_text(encoding="utf-8")
            return SimpleNamespace(read_text=lambda **unused: value)

    policy = "src/qtt/stage1_prediction_markets/qku_computation_control_plane/source_policy.py"
    pretrade = "src/qtt/pretrade/pr169_pretrade1_resolvers.py"
    native = "src/qtt/service/owner_source_use_windows.py"
    assert source._source_use_admission_failures_v1(ObservedRoot({})) == []
    for path, old, new in (
        (policy, "self._valid_completion is pending", "True"),
        (policy, "prepared.originating_thread is current_thread()", "True"),
        (policy, "len(rows) + 2 <= 256", "len(rows) + 2 <= 257"),
        (policy, "+ 2 * 65536 <= 16 * 1024 * 1024", "+ 2 * 65536 <= 17 * 1024 * 1024"),
        (pretrade, "owner.revoke()", "None"),
        ("src/qtt/service/owner_source_use.py", "with self._authority._lock:", "with self._root.operation_lock:"),
    ):
        original = (repo / path).read_text(encoding="utf-8")
        changed = original.replace(old, new)
        assert changed != original
        failures = source._source_use_admission_failures_v1(ObservedRoot({path: changed}))
        assert failures and all(type(value) is str for value in failures)

    files = ("receipts.py", "persistence.py", "transaction.py", "sqlite_reference.py")
    package = repo / "src/qtt/stage1_prediction_markets/qku_computation_control_plane"
    originals = {name: (package / name).read_text(encoding="utf-8") for name in files}
    assert execution._source_use_execution_contract_failures_v1({name: ast.parse(value) for name, value in originals.items()}) == []
    for name, old, new in (
        ("persistence.py", "_source_action_reserved_v1(record)", "False"),
        ("sqlite_reference.py", '"SOURCE_ACTION::"', '"UNRELATED::"'),
        ("transaction.py", "transaction.rollback()", "None"),
        ("transaction.py", "verified_action._attempted = True", "verified_action._attempted = False"),
        ("transaction.py", "adapter._prepare_action_batch_v1(", "adapter.unregistered_batch("),
    ):
        changed = originals[name].replace(old, new)
        assert changed != originals[name]
        trees = {file: ast.parse(changed if file == name else value) for file, value in originals.items()}
        assert execution._source_use_execution_contract_failures_v1(trees)
    assert security._source_use_security_failures_v1(ObservedRoot({})) == []
    original = (repo / native).read_text(encoding="utf-8")
    for old, new in (('"webauthn.dll"', '"unapproved.dll"'),
                     ("winmode=0x800", "winmode=0"),
                     ("WebAuthNFreeAssertion(pointer)", "UnapprovedFree(pointer)")):
        changed = original.replace(old, new)
        assert changed != original
        assert security._source_use_security_failures_v1(ObservedRoot({native: changed}))


def _assert_kalshi_shared_native_admission(root):
    import ast
    from pathlib import PurePosixPath
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane import validation as operations
    from tools import validate_no_runtime_artifacts as runtime
    from tools import validate_source_fact_binding_connector_semantic_readiness_static as readiness

    _assert_source_use_native_boundaries(root / 'source-use')

    relative = 'src/qtt/stage1_prediction_markets/qku_computation_control_plane/source_policy.py'
    target = root / relative
    target.parent.mkdir(parents=True)
    source = _KALSHI_INDEPENDENT_NATIVE_TEMPLATE
    assert runtime.kalshi_fee_native_admission_v1(relative, ast.parse('x = 1')) == (frozenset(), ())
    positions, errors = runtime.kalshi_fee_native_admission_v1(relative, ast.parse(source))
    assert len(positions) == 2 and errors == ()
    assert {position[0] for position in positions} == {'Import', 'Call'}
    target.write_text(source, encoding='utf-8')
    assert runtime._scan_python_content(PurePosixPath(relative), source, ['forbid_source_retrieval']) == []
    assert readiness._scan_forbidden_python_usage(root) == []
    evidence_relative = 'src/qtt/stage1_prediction_markets/qku_computation_control_plane/evidence.py'
    evidence_source = (
        'from threading import Lock\n'
        'class Evidence:\n'
        '    def __init__(self):\n'
        '        self._cache_publication_lock = Lock()\n'
        '    def publish(self):\n'
        '        with self._cache_publication_lock:\n'
        '            pass\n'
    )

    def operations_admits(candidate, owner_relative=relative, extra_source=None):
        trees = (
            (root / owner_relative, ast.parse(candidate)),
            (root / evidence_relative, ast.parse(evidence_source)),
        )
        if extra_source is not None:
            trees += ((root / 'src/qtt/elsewhere.py', ast.parse(extra_source)),)
        with pytest.MonkeyPatch.context() as patch:
            patch.setattr(operations, 'REPO_ROOT', root)
            patch.setattr(operations, '_package_ast', lambda: trees)
            return operations._no_runtime_topology()

    assert operations_admits('x = 1')
    assert operations_admits(source)
    quote_import = 'from urllib.parse import quote\n'
    with_quote = quote_import + source
    assert operations_admits(with_quote)
    positions, errors = runtime.kalshi_fee_native_admission_v1(relative, ast.parse(with_quote))
    assert len(positions) == 2 and errors == ()
    assert {position[0] for position in positions} == {'Import', 'Call'}
    assert not operations_admits(quote_import + 'x = 1')
    for malformed in (
        source.replace('"GET"', '"POST"'),
        source.replace('import http.client', 'pass'),
        source.replace('connection.close()', 'pass'),
        source + source,
    ):
        assert not operations_admits(malformed)
        assert not operations_admits(quote_import + malformed)
    for invalid_quote in (
        quote_import + quote_import,
        'from urllib.parse import quote as quote\n',
        'from urllib.parse import quote as encoded\n',
        'from urllib.parse import quote, urlencode\n',
        'from urllib.parse import quote, quote\n',
        'from .urllib.parse import quote\n',
        'from urllib.parse import *\n',
        'import urllib\n',
        'import urllib.parse\n',
        'from urllib import parse\n',
    ):
        assert not operations_admits(invalid_quote + source)
    assert not operations_admits(source, extra_source=quote_import)
    for extra in ('\nimport urllib.request\n', '\nfrom urllib.request import urlopen\n',
                  '\nimport socket\n', '\nimport http.client\n'):
        assert not operations_admits(with_quote + extra)
    for extra in ('\nimport http.client\n', '\nimport socket\n', '\nfrom http import client\n'):
        assert not operations_admits(source + extra)
    assert not operations_admits(source, 'src/qtt/elsewhere.py')
    for old, new in (
        ('external-api.kalshi.com','other.example'), ('"GET"','"POST"'),
        ('body=None','body=b"secret"'), ('headers=prepared.headers','headers={}'),
        ('self._prepare_read_v1(role, ticker)','self._prepare_read_v1("SERIES", ticker)'),
        ('self._recheck_and_charge_v1(prepared)','self._observe_clock_v1()'),
        ('connection.close()','pass'), ('finally:','except ValueError:'),
        ('def _read_rest_once_v1','async def _read_rest_once_v1'),
        ('def _read_rest_once_v1','def renamed_read'),
        ('class KalshiFeeObservationOwnerV1','class WrongOwner'),
        ('import http.client','import http.client as hidden'),
        ('import http.client','http = __import__("http.client")'),
        ('    def _read_rest_once_v1','    @staticmethod\n    def _read_rest_once_v1'),
    ):
        bad = source.replace(old,new)
        target.write_text(bad,encoding='utf-8')
        assert runtime._scan_python_content(PurePosixPath(relative),bad,['forbid_source_retrieval'])
        assert readiness._scan_forbidden_python_usage(root)
        admitted, _ = runtime.kalshi_fee_native_admission_v1(relative,ast.parse(bad))
        assert not admitted
    for bad in (source+source, source+source.split('\n',1)[1],
                source+'\nimport socket\nsocket.socket()\n',
                source+'\nimport http.client\nhttp.client.HTTPSConnection("other.example")\n',
                source+'\ndef other():\n    import urllib.request\n    urllib.request.urlopen("https://other.example")\n'):
        target.write_text(bad,encoding='utf-8')
        assert runtime._scan_python_content(PurePosixPath(relative),bad,['forbid_source_retrieval'])
        assert readiness._scan_forbidden_python_usage(root)
    for wrong in ('src/qtt/elsewhere.py',relative+'.copy',relative.upper()):
        assert runtime.kalshi_fee_native_admission_v1(wrong,ast.parse(source)) == (frozenset(), ())
        assert runtime._scan_python_content(PurePosixPath(wrong),source,['forbid_source_retrieval'])
    target.unlink()
    other = root/'src/qtt/elsewhere.py'
    other.write_text(source,encoding='utf-8')
    assert readiness._scan_forbidden_python_usage(root)


def _assert_f14_shared_native_admission(root):
    import ast
    from pathlib import Path, PurePosixPath
    from tools import validate_no_runtime_artifacts as runtime
    from tools import validate_source_fact_binding_connector_semantic_readiness_static as readiness
    relative='src/qtt/stage1_prediction_markets/private_state_receipts/request.py'
    target=root/relative;target.parent.mkdir(parents=True)
    source=_F14_INDEPENDENT_NATIVE_TEMPLATE
    target.write_text(source,encoding='utf-8')
    positions,failures=runtime.f14_native_admission_v1(relative,ast.parse(source))
    assert len(positions) == 4 and failures == ()
    assert runtime._scan_python_content(PurePosixPath(relative),source,['forbid_source_retrieval']) == []
    assert readiness._scan_forbidden_python_usage(root) == []
    for bad in (source.replace('proxy=None','proxy=True'),source.replace('max_queue=16','max_queue=None'),
            source.replace('"GET", prepared.target','"POST", prepared.target'),
            source.replace('self._recheck_and_charge_v1(prepared)','self._recheck_subscription_v1(prepared)'),
            source+source,source+'\nimport socket\nsocket.socket()\n',
            source+'\nimport websockets.sync.client\nwebsockets.sync.client.connect("wss://other.example")\n'):
        target.write_text(bad,encoding='utf-8')
        assert runtime._scan_python_content(PurePosixPath(relative),bad,['forbid_source_retrieval'])
        assert readiness._scan_forbidden_python_usage(root)
