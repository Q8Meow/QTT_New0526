from pathlib import Path

import pytest

from tools.validate_no_runtime_artifacts import ScanOptions, scan_repository


def _strict_options() -> ScanOptions:
    return ScanOptions(
        forbid_source_retrieval=True,
        forbid_source_acceptance=True,
        forbid_connector_binding=True,
        forbid_private_state_fetch=True,
        forbid_order_execution=True,
        forbid_neural_training=True,
        forbid_neural_inference=True,
        forbid_external_repo_clone=True,
        forbid_package_install_scripts=True,
    )


def test_scanner_rejects_secret_and_runtime_artifact_names(tmp_path):
    (tmp_path / ".env").write_text("TOKEN=value\n", encoding="utf-8")
    (tmp_path / "credentials.json").write_text("{}", encoding="utf-8")
    keys = tmp_path / "keys"
    keys.mkdir()
    (keys / "live.pem").write_text("secret", encoding="utf-8")

    violations = scan_repository(tmp_path, ScanOptions())

    assert any(".env" in violation for violation in violations)
    assert any("credentials.json" in violation for violation in violations)
    assert any("live.pem" in violation for violation in violations)


def test_scanner_rejects_flagged_runtime_paths_and_install_scripts(tmp_path):
    (tmp_path / "src" / "order_execution").mkdir(parents=True)
    (tmp_path / "src" / "order_execution" / "router.py").write_text("", encoding="utf-8")
    scripts = tmp_path / "scripts"
    scripts.mkdir()
    (scripts / "install.sh").write_text("#!/bin/sh\n", encoding="utf-8")

    violations = scan_repository(
        tmp_path,
        ScanOptions(forbid_order_execution=True, forbid_package_install_scripts=True),
    )

    assert any("order-execution path" in violation for violation in violations)
    assert any("package install script" in violation for violation in violations)


def test_scanner_rejects_static_blocked_action_code(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    (src / "bad.py").write_text(
        "\n".join(
            [
                "import requests",
                "import subprocess",
                "requests.get('https://example.invalid/source')",
                "subprocess.run(['git', 'clone', 'https://example.invalid/repo.git'])",
                "submit_order()",
                "model.predict(features)",
            ]
        ),
        encoding="utf-8",
    )

    violations = scan_repository(
        tmp_path,
        ScanOptions(
            forbid_source_retrieval=True,
            forbid_external_repo_clone=True,
            forbid_order_execution=True,
            forbid_neural_inference=True,
        ),
    )

    assert any("HTTP retrieval client" in violation for violation in violations)
    assert any("subprocess git clone" in violation for violation in violations)
    assert any("order execution call" in violation for violation in violations)
    assert any("model predict call" in violation for violation in violations)


def test_scanner_rejects_static_source_acceptance_and_connector_binding(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    (src / "bad.py").write_text(
        "\n".join(
            [
                "create_accepted_source_evidence(packet)",
                "bind_connector_semantic('field', 'value')",
                "fetch_private_state(account_id)",
                "train_model(dataset)",
            ]
        ),
        encoding="utf-8",
    )

    violations = scan_repository(
        tmp_path,
        ScanOptions(
            forbid_source_acceptance=True,
            forbid_connector_binding=True,
            forbid_private_state_fetch=True,
            forbid_neural_training=True,
        ),
    )

    assert any("accepted source evidence creation" in violation for violation in violations)
    assert any("connector semantic binding call" in violation for violation in violations)
    assert any("private state fetch call" in violation for violation in violations)
    assert any("model training call" in violation for violation in violations)


def test_scanner_allows_pr40_static_connector_semantic_binding_contract_paths(tmp_path):
    allowed_paths = [
        "src/qtt/stage1_prediction_markets/connector_semantic_binding/"
        "stage1_connector_semantic_binding_ledger_record.schema.json",
        "src/qtt/stage1_prediction_markets/connector_semantic_binding/"
        "stage1_connector_semantic_value_canonicalization.schema.json",
        "src/qtt/stage1_prediction_markets/connector_semantic_binding/"
        "stage1_connector_semantic_binding_consumer_contract.schema.json",
        "tests/fixtures/source_evidence/connector_semantic_binding/"
        "synthetic_stage1_connector_semantic_binding_contracts.v1.fixture.json",
    ]
    for path_text in allowed_paths:
        path = tmp_path / path_text
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("{}", encoding="utf-8")

    violations = scan_repository(tmp_path, ScanOptions(forbid_connector_binding=True))

    assert violations == []

    runtime_file = (
        tmp_path
        / "src"
        / "qtt"
        / "stage1_prediction_markets"
        / "connector_semantic_binding"
        / "runtime_binding.py"
    )
    runtime_file.write_text("", encoding="utf-8")

    violations = scan_repository(tmp_path, ScanOptions(forbid_connector_binding=True))

    assert any("forbid-connector-binding path" in violation for violation in violations)


def test_scanner_allows_pr41_static_runtime_resolver_contract_paths_exactly(tmp_path):
    allowed_paths = [
        "src/qtt/stage1_prediction_markets/runtime_resolver/"
        "stage1_runtime_resolver_snapshot_input_lock.schema.json",
        "src/qtt/stage1_prediction_markets/runtime_resolver/"
        "stage1_runtime_resolver_snapshot_manifest.schema.json",
        "src/qtt/stage1_prediction_markets/runtime_resolver/"
        "stage1_runtime_resolver_consumer_contract.schema.json",
        "src/qtt/stage1_prediction_markets/runtime_resolver/"
        "stage1_runtime_resolver_snapshot_gate_report.schema.json",
        "tests/fixtures/source_evidence/runtime_resolver/"
        "synthetic_stage1_runtime_resolver_snapshot_contracts.v1.fixture.json",
    ]
    for path_text in allowed_paths:
        path = tmp_path / path_text
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("{}", encoding="utf-8")

    violations = scan_repository(tmp_path, _strict_options())

    assert violations == []


def test_scanner_allows_pr42_static_runtime_resolver_snapshot_handoff_paths_exactly(tmp_path):
    allowed_paths = [
        "src/qtt/stage1_prediction_markets/runtime_resolver_snapshot/"
        "stage1_runtime_resolver_snapshot_consumer_allowlist.schema.json",
        "src/qtt/stage1_prediction_markets/runtime_resolver_snapshot/"
        "stage1_runtime_resolver_to_replay_paper_handoff_contract.schema.json",
        "src/qtt/stage1_prediction_markets/runtime_resolver_snapshot/"
        "stage1_runtime_resolver_to_replay_paper_handoff_report.schema.json",
        "tests/fixtures/source_evidence/runtime_resolver_snapshot/"
        "synthetic_stage1_runtime_resolver_to_replay_paper_handoff.v1.fixture.json",
    ]
    for path_text in allowed_paths:
        path = tmp_path / path_text
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("{}", encoding="utf-8")

    violations = scan_repository(tmp_path, _strict_options())

    assert violations == []


@pytest.mark.parametrize(
    "filename",
    [
        "runtime_snapshot.py",
        "live_snapshot.py",
        "resolver_runtime.py",
        "replay_input_snapshot.json",
        "Stage1RuntimeResolverSnapshot.packet.json",
        "Stage1RuntimeResolverSnapshot.input_lock.json",
    ],
)
def test_scanner_rejects_runtime_resolver_executable_or_snapshot_artifacts(tmp_path, filename):
    runtime_dir = tmp_path / "src" / "qtt" / "stage1_prediction_markets" / "runtime_resolver"
    runtime_dir.mkdir(parents=True)
    (runtime_dir / filename).write_text("", encoding="utf-8")

    violations = scan_repository(tmp_path, _strict_options())

    assert any("runtime resolver artifact" in violation for violation in violations)


def test_scanner_rejects_arbitrary_files_under_runtime_resolver_directory(tmp_path):
    runtime_dir = tmp_path / "src" / "qtt" / "stage1_prediction_markets" / "runtime_resolver"
    runtime_dir.mkdir(parents=True)
    (runtime_dir / "extra_static_contract.json").write_text("{}", encoding="utf-8")

    violations = scan_repository(tmp_path, _strict_options())

    assert any("runtime path" in violation for violation in violations)


@pytest.mark.parametrize(
    "filename",
    [
        "runtime_resolver_to_replay_paper_runtime.py",
        "replay_execution.py",
        "paper_execution.py",
        "replay_result_packet.json",
        "paper_result_packet.json",
        "dual_result_review.packet.json",
        "live_handoff.py",
    ],
)
def test_scanner_rejects_pr42_runtime_replay_paper_and_live_handoff_artifacts(
    tmp_path, filename
):
    runtime_dir = (
        tmp_path
        / "src"
        / "qtt"
        / "stage1_prediction_markets"
        / "runtime_resolver_snapshot"
    )
    runtime_dir.mkdir(parents=True)
    (runtime_dir / filename).write_text("", encoding="utf-8")

    violations = scan_repository(tmp_path, _strict_options())

    assert any(
        "runtime resolver artifact" in violation or "runtime path" in violation
        for violation in violations
    )


def test_scanner_rejects_arbitrary_files_under_runtime_resolver_snapshot_directory(tmp_path):
    runtime_dir = (
        tmp_path
        / "src"
        / "qtt"
        / "stage1_prediction_markets"
        / "runtime_resolver_snapshot"
    )
    runtime_dir.mkdir(parents=True)
    (runtime_dir / "extra_static_contract.json").write_text("{}", encoding="utf-8")

    violations = scan_repository(tmp_path, _strict_options())

    assert any("runtime path" in violation for violation in violations)


@pytest.mark.parametrize(
    "filename",
    [
        "replay_execution.py",
        "paper_execution.py",
        "replay_result_packet.json",
        "paper_result_packet.json",
        "merged_replay_paper_result.json",
        "dual_result_review.packet.json",
        "live_promotion.py",
        "order_execution.py",
    ],
)
def test_scanner_rejects_pr43_replay_paper_runtime_execution_result_and_live_artifacts(
    tmp_path, filename
):
    replay_paper_dir = (
        tmp_path
        / "src"
        / "qtt"
        / "stage1_prediction_markets"
        / "replay_paper"
    )
    replay_paper_dir.mkdir(parents=True)
    (replay_paper_dir / filename).write_text("", encoding="utf-8")

    violations = scan_repository(tmp_path, _strict_options())

    assert any("runtime resolver artifact" in violation for violation in violations)


def test_scanner_ignores_forbidden_looking_files_inside_venv(tmp_path):
    requests_dir = tmp_path / ".venv" / "Lib" / "site-packages" / "requests"
    requests_dir.mkdir(parents=True)
    (requests_dir / "api.py").write_text(
        "\n".join(
            [
                "import requests",
                "requests.get('https://example.invalid/source')",
                "submit_order()",
                "python -m pip install requests",
            ]
        ),
        encoding="utf-8",
    )
    certifi_dir = tmp_path / ".venv" / "Lib" / "site-packages" / "certifi"
    certifi_dir.mkdir(parents=True)
    (certifi_dir / "cacert.pem").write_text("local cert bundle", encoding="utf-8")
    (tmp_path / ".venv" / ".env").write_text("TOKEN=value\n", encoding="utf-8")

    violations = scan_repository(tmp_path, _strict_options())

    assert violations == []


def test_scanner_ignores_tmp_validation_output(tmp_path):
    output_dir = tmp_path / ".tmp" / "pr2_validation"
    output_dir.mkdir(parents=True)
    (output_dir / "validation_output.json").write_text(
        '{"message":"requests.get and pip install appeared in validation output"}',
        encoding="utf-8",
    )
    (output_dir / "secrets.json").write_text("{}", encoding="utf-8")

    violations = scan_repository(tmp_path, _strict_options())

    assert violations == []


def test_scanner_still_catches_forbidden_looking_files_outside_ignored_directories(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    (src / "bad.py").write_text(
        "\n".join(
            [
                "import requests",
                "requests.get('https://example.invalid/source')",
                "python -m pip install requests",
            ]
        ),
        encoding="utf-8",
    )
    (src / "secrets.json").write_text("{}", encoding="utf-8")

    violations = scan_repository(tmp_path, _strict_options())

    assert any("HTTP retrieval client" in violation for violation in violations)
    assert any("pip install command" in violation for violation in violations)
    assert any("secrets.json" in violation for violation in violations)


def test_scanner_scans_tests_py_for_real_runtime_code(tmp_path):
    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()
    (tests_dir / "test_bad_runtime_path.py").write_text(
        "\n".join(
            [
                "import requests",
                "requests.Session().get('https://example.invalid/source')",
                "submit_order()",
            ]
        ),
        encoding="utf-8",
    )

    violations = scan_repository(tmp_path, _strict_options())

    assert any("HTTP retrieval session client" in violation for violation in violations)
    assert any("order execution call" in violation for violation in violations)


def test_scanner_allows_synthetic_negative_test_strings_in_tests_py(tmp_path):
    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()
    (tests_dir / "test_guardrail_strings.py").write_text(
        "\n".join(
            [
                "def test_guardrail_examples_are_quoted():",
                "    examples = [",
                "        'requests.Session().get(\"https://example.invalid/source\")',",
                "        'subprocess.run([\"pip\", \"install\", \"package\"]',",
                "        'submit_order()',",
                "    ]",
                "    assert examples",
            ]
        ),
        encoding="utf-8",
    )

    violations = scan_repository(tmp_path, _strict_options())

    assert violations == []


@pytest.mark.parametrize(
    "code, expected_fragment",
    [
        (
            "import requests\nrequests.Session().get('https://example.invalid/source')\n",
            "HTTP retrieval session client",
        ),
        (
            "import requests\nrequests.Session().post('https://example.invalid/source')\n",
            "HTTP retrieval session client",
        ),
        (
            "import http.client\nhttp.client.HTTPConnection('example.invalid')\n",
            "http.client import/use",
        ),
        (
            "import socket\nsocket.socket()\n",
            "socket client",
        ),
        (
            "import urllib3\nurllib3.PoolManager()\n",
            "urllib3 client",
        ),
        (
            "import subprocess\nsubprocess.run(['curl', 'https://example.invalid/source'])\n",
            "curl command",
        ),
    ],
)
def test_scanner_rejects_expanded_runtime_network_variants(
    tmp_path, code, expected_fragment
):
    src = tmp_path / "src"
    src.mkdir()
    (src / "bad.py").write_text(code, encoding="utf-8")

    violations = scan_repository(tmp_path, _strict_options())

    assert any(expected_fragment in violation for violation in violations)


@pytest.mark.parametrize(
    "filename, text, expected_fragment",
    [
        (
            "bad.py",
            "import subprocess\nsubprocess.run(['pip', 'install', 'package'])\n",
            "subprocess pip install command",
        ),
        (
            "bad.py",
            "import subprocess\nsubprocess.run(['pip3', 'install', 'package'])\n",
            "subprocess pip install command",
        ),
        (
            "bad.py",
            "import subprocess\nsubprocess.run(['python3', '-m', 'pip', 'install', 'package'])\n",
            "subprocess pip install command",
        ),
        (
            "bad.py",
            "import subprocess\nsubprocess.run(['py', '-m', 'pip', 'install', 'package'])\n",
            "subprocess pip install command",
        ),
        ("bad.sh", "pip3 install package\n", "pip install command"),
        ("bad.sh", "python3 -m pip install package\n", "pip install command"),
        ("bad.sh", "py -m pip install package\n", "pip install command"),
    ],
)
def test_scanner_rejects_expanded_package_install_variants(
    tmp_path, filename, text, expected_fragment
):
    scripts = tmp_path / "scripts"
    scripts.mkdir()
    (scripts / filename).write_text(text, encoding="utf-8")

    violations = scan_repository(tmp_path, _strict_options())

    assert any(expected_fragment in violation for violation in violations)
