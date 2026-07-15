from tabloid.engine.differ import diff_schemas
import json

def test_no_schema_change():
    old_schema = json.dumps({"tables": ["trips", "users"], "foreign_keys": []})
    new_schema = json.dumps({"tables": ["trips", "users"], "foreign_keys": []})

    result = diff_schemas(old_schema, new_schema)

    assert result == {"added_tables": [], "removed_tables": []}

def test_removed_table():
    old_schema = json.dumps({"tables": ["trips", "users", "test_table"], "foreign_keys": []})
    new_schema = json.dumps({"tables": ["trips", "users"], "foreign_keys": []})

    result = diff_schemas(old_schema, new_schema)

    assert result == {"added_tables": [], "removed_tables": ["test_table"]}