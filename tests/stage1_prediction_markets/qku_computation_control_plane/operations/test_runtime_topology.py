from pathlib import Path

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
