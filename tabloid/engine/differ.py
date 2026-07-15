import json

def diff_schemas(old_schema_json, new_schema_json):
    old_schema = json.loads(old_schema_json)
    new_schema = json.loads(new_schema_json)

    old_tables = set(old_schema["tables"])
    new_tables = set(new_schema["tables"])

    added_tables = list(new_tables - old_tables)
    removed_tables = list(old_tables - new_tables)

    return {
        "added_tables": added_tables,
        "removed_tables": removed_tables
    }