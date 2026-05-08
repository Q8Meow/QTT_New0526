import json
from pathlib import Path


SCHEMA_ROOT = Path("schemas")
FIXTURE_ROOT = Path("tests/fixtures")


def _top_level_directory_names(root: Path) -> list[str]:
    assert root.is_dir(), f"expected directory to exist: {root}"
    return sorted(path.name for path in root.iterdir() if path.is_dir())


def _fixture_json_paths(family_name: str) -> list[Path]:
    return sorted((FIXTURE_ROOT / family_name).rglob("*.json"))


def _load_fixture(path: Path) -> dict:
    with path.open(encoding="utf-8") as fixture_file:
        parsed = json.load(fixture_file)
    assert isinstance(parsed, dict), f"fixture JSON must be an object: {path}"
    return parsed


def test_schema_and_fixture_families_match():
    schema_families = _top_level_directory_names(SCHEMA_ROOT)
    fixture_families = _top_level_directory_names(FIXTURE_ROOT)

    missing_fixture_families = sorted(set(schema_families) - set(fixture_families))
    extra_fixture_families = sorted(set(fixture_families) - set(schema_families))

    assert missing_fixture_families == [] and extra_fixture_families == [], (
        "schema/fixture family mismatch: "
        f"missing fixture families={missing_fixture_families}; "
        f"extra fixture families={extra_fixture_families}"
    )


def test_fixture_families_contain_source_required_disabled_json():
    for family_name in _top_level_directory_names(FIXTURE_ROOT):
        fixture_paths = _fixture_json_paths(family_name)
        assert fixture_paths, f"fixture family has no JSON files: {family_name}"

        for path in fixture_paths:
            fixture = _load_fixture(path)
            assert fixture.get("mode") == "SOURCE_REQUIRED", (
                f"fixture must declare mode=SOURCE_REQUIRED: {path}"
            )
            assert fixture.get("execution") == "DISABLED", (
                f"fixture must declare execution=DISABLED: {path}"
            )
