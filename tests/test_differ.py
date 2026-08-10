from tabloid.engine.differ import diff_schemas
import json
import pytest


def make_schema(table_names, foreign_keys=None):
    return json.dumps({
        "tables": [{"table_name": name} for name in table_names],
        "foreign_keys": foreign_keys or []
    })


def test_no_schema_change():
    old_schema = make_schema(["trips", "users"])
    new_schema = make_schema(["trips", "users"])

    result = diff_schemas(old_schema, new_schema)

    assert result == {"added_tables": [], "removed_tables": []}


def test_removed_table():
    old_schema = make_schema(["trips", "users", "test_table"])
    new_schema = make_schema(["trips", "users"])

    result = diff_schemas(old_schema, new_schema)

    assert result == {"added_tables": [], "removed_tables": ["test_table"]}


def test_added_table():
    old_schema = make_schema(["trips", "users"])
    new_schema = make_schema(["trips", "users", "invoices"])

    result = diff_schemas(old_schema, new_schema)

    assert result == {"added_tables": ["invoices"], "removed_tables": []}


def test_added_and_removed_together():
    old_schema = make_schema(["trips", "users", "legacy_table"])
    new_schema = make_schema(["trips", "users", "invoices"])

    result = diff_schemas(old_schema, new_schema)

    assert sorted(result["added_tables"]) == ["invoices"]
    assert sorted(result["removed_tables"]) == ["legacy_table"]


def test_multiple_added_tables_order_independent():
    """set-based diffing doesn't guarantee list order — sort before asserting
    so this test doesn't flake depending on Python's set iteration order."""
    old_schema = make_schema(["users"])
    new_schema = make_schema(["users", "invoices", "payments"])

    result = diff_schemas(old_schema, new_schema)

    assert sorted(result["added_tables"]) == ["invoices", "payments"]
    assert result["removed_tables"] == []


def test_empty_old_schema_all_tables_added():
    old_schema = make_schema([])
    new_schema = make_schema(["trips", "users"])

    result = diff_schemas(old_schema, new_schema)

    assert sorted(result["added_tables"]) == ["trips", "users"]
    assert result["removed_tables"] == []


def test_empty_new_schema_all_tables_removed():
    old_schema = make_schema(["trips", "users"])
    new_schema = make_schema([])

    result = diff_schemas(old_schema, new_schema)

    assert result["added_tables"] == []
    assert sorted(result["removed_tables"]) == ["trips", "users"]


def test_both_schemas_empty():
    old_schema = make_schema([])
    new_schema = make_schema([])

    result = diff_schemas(old_schema, new_schema)

    assert result == {"added_tables": [], "removed_tables": []}


def test_renamed_table_shows_as_add_and_remove():
    """diff_schemas has no rename detection — a rename is indistinguishable
    from a drop + create. Documenting that as current, intentional behavior."""
    old_schema = make_schema(["users_old"])
    new_schema = make_schema(["users_new"])

    result = diff_schemas(old_schema, new_schema)

    assert result == {"added_tables": ["users_new"], "removed_tables": ["users_old"]}


def test_malformed_json_raises():
    old_schema = "not valid json{"
    new_schema = make_schema(["users"])

    with pytest.raises(json.JSONDecodeError):
        diff_schemas(old_schema, new_schema)


def test_missing_tables_key_raises():
    old_schema = json.dumps({"foreign_keys": []})  # no "tables" key at all
    new_schema = make_schema(["users"])

    with pytest.raises(KeyError):
        diff_schemas(old_schema, new_schema)


def test_duplicate_table_names_deduplicated():
    """sets collapse duplicates — confirms that's actually happening,
    not silently producing wrong counts."""
    old_schema = make_schema(["users", "users"])
    new_schema = make_schema(["users"])

    result = diff_schemas(old_schema, new_schema)

    assert result == {"added_tables": [], "removed_tables": []}