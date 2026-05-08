from pathlib import Path

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
