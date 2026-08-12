import ast
from dataclasses import fields
from pathlib import Path

from src.qtt.stage1_prediction_markets.qku_computation_control_plane.existing_owner_projection import (
    ExistingOwnerProjectionCompilerV2,
    ExistingOwnerProjectionCoordinatorV2,
)

from tools.independent_validate_qku_computation_control_plane_operations import (
    main,
    validate_runtime_topology_source,
)


def test_no_runtime_topology_is_implemented() -> None:
    root = Path(__file__).resolve().parents[4]
    package = (
        root
        / "src"
        / "qtt"
        / "stage1_prediction_markets"
        / "qku_computation_control_plane"
    )
    forbidden = {"runtime.py", "database.py", "backup.py", "supervision.py"}
    assert forbidden.isdisjoint(path.name for path in package.glob("*.py"))
    assert (package / "service.py").is_file()
    cases = (
        (
            "exact-reference-exception",
            "sqlite_reference.py",
            """
import sqlite3
class SQLiteReferenceAdapterV1:
    is_production_adapter = False
    def open(self):
        return sqlite3.connect(':memory:')
""",
            (),
        ),
        (
            "sqlite-import-outside-reference",
            "another.py",
            "import sqlite3\n",
            ("runtime import",),
        ),
        (
            "from-import-rejected",
            "sqlite_reference.py",
            """
from sqlite3 import connect
class SQLiteReferenceAdapterV1:
    is_production_adapter = False
def open_database():
    return connect(':memory:')
""",
            ("runtime import", "runtime call"),
        ),
        (
            "aliased-import-rejected",
            "sqlite_reference.py",
            """
import sqlite3 as another_name
class SQLiteReferenceAdapterV1:
    is_production_adapter = False
def open_database():
    return another_name.connect(':memory:')
""",
            ("runtime import sqlite3", "runtime call another_name.connect"),
        ),
        (
            "bare-connect-rejected",
            "sqlite_reference.py",
            """
import sqlite3
class SQLiteReferenceAdapterV1:
    is_production_adapter = False
def open_database():
    return connect(':memory:')
""",
            ("runtime call connect",),
        ),
        (
            "network-call-remains-rejected",
            "sqlite_reference.py",
            """
import sqlite3
import socket
class SQLiteReferenceAdapterV1:
    is_production_adapter = False
def open_database():
    sqlite3.connect(':memory:')
    return socket.create_connection(('example.invalid', 443))
""",
            ("runtime import socket", "runtime call socket.create_connection"),
        ),
        (
            "missing-production-marker",
            "sqlite_reference.py",
            "import sqlite3\nsqlite3.connect(':memory:')\n",
            ("must be literal False",),
        ),
        (
            "second-reference-connect-rejected",
            "sqlite_reference.py",
            """
import sqlite3
class SQLiteReferenceAdapterV1:
    is_production_adapter = False
sqlite3.connect(':memory:')
sqlite3.connect(':memory:')
""",
            ("requires exactly one call sqlite3.connect",),
        ),
        (
            "non-false-production-marker",
            "sqlite_reference.py",
            """
import sqlite3
class SQLiteReferenceAdapterV1:
    is_production_adapter = True
sqlite3.connect(':memory:')
""",
            ("must be literal False",),
        ),
    )
    for label, file_name, source, expected_fragments in cases:
        failures = validate_runtime_topology_source(
            file_name=file_name,
            source=source,
        )
        if not expected_fragments:
            assert failures == (), f"{label}: {failures!r}"
        else:
            assert all(
                any(fragment in failure for failure in failures)
                for fragment in expected_fragments
            ), f"{label}: {failures!r}"
    assert main() == 0


def test_st12g_adds_no_runtime_owner_or_effect_topology() -> None:
    root = Path(__file__).resolve().parents[4]
    central_path = (
        root
        / "src/qtt/stage1_prediction_markets/qku_computation_control_plane/"
        "existing_owner_projection.py"
    )
    tree = ast.parse(central_path.read_text(encoding="utf-8"))
    assert ExistingOwnerProjectionCompilerV2.__slots__ == ()
    assert tuple(field.name for field in fields(ExistingOwnerProjectionCoordinatorV2)) == (
        "evidence_service",
        "owner_views",
        "compiler",
    )
    class_names = {
        node.name.casefold()
        for node in tree.body
        if isinstance(node, ast.ClassDef)
    }
    assert not any(
        token in name
        for name in class_names
        for token in ("database", "queue", "cache", "registry", "runtime_service")
    )
    imported_roots = {
        alias.name.split(".", 1)[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    } | {
        node.module.split(".", 1)[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module
    }
    assert imported_roots.isdisjoint(
        {"sqlite3", "socket", "requests", "httpx", "openai", "subprocess"}
    )
    compiler = next(
        node
        for node in tree.body
        if isinstance(node, ast.ClassDef)
        and node.name == "ExistingOwnerProjectionCompilerV2"
    )
    assert not any(isinstance(node, (ast.Global, ast.Nonlocal)) for node in ast.walk(compiler))
    assert not any(
        isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign))
        and any(
            isinstance(target, ast.Attribute)
            and isinstance(target.value, ast.Name)
            and target.value.id == "self"
            for target in (
                node.targets if isinstance(node, ast.Assign) else (node.target,)
            )
        )
        for node in ast.walk(compiler)
    )
