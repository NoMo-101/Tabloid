from tabloid.db.connector import DBConnector
from tabloid.db.inspector import SchemaInspector
from tabloid.engine.layout import LayoutEngine
from tabloid.storage.local_db import init_db, save_connection, save_layout, load_layout, save_snapshot, get_latest_snapshot
from tabloid.git.watcher import GitWatcher
import time
import json


# Test for Module 1: DBConnector; Filename: connector.py
# conn = DBConnector("localhost", 5433, "postgres", "tabloid123", "postgres")
# result = conn.connect()
# print(f"Connected: {result}")
# conn.disconnect()


# Test for Module 2: SchemaInspector; Filename: inspector.py
# conn = DBConnector("127.0.0.1", 5432, "tripuser", "trippassword123", "tripplanner")
# conn.connect()
# inspector = SchemaInspector(conn.connection)
# print("Tables: ", inspector.fetch_tables())
# print("Columns: ", inspector.fetch_columns())
# print("Foreign Keys: ", inspector.fetch_foreign_keys())
# conn.disconnect()

# Test for Module 3: LayoutEngine; Filename: layout.py
# conn = DBConnector("127.0.0.1", 5432, "tripuser", "trippassword123", "tripplanner")
# conn.connect()
# inspector = SchemaInspector(conn.connection)

# tables = inspector.fetch_tables()
# foreign_keys = inspector.fetch_foreign_keys()

# layout = LayoutEngine(tables, foreign_keys)
# positions = layout.compute_layout()

# print("Positions: ", positions)

# Test for Module 4: SQLite local storage; Filename: local_db.py
# init_db()
# save_connection("Travel App", "127.0.0.1", 5432, "tripuser", "tripplanner")
# save_layout(1, "users", 100.0, 200.0)
# save_layout(1, "trips", 400.0, 200.0)

# positions = load_layout(1)
# for row in positions:
#     print(f"Table: {row['table_name']} X: {row['x']} Y: {row['y']}")

# Test for Module 5: Git Watcher; File name watcher.py
# def on_branch_change():
#     print("Branch changed!")

# watcher = GitWatcher("/home/noah/projects/tabloid", on_branch_change)

# print(f"Current branch: {watcher.get_current_branch()}")
# watcher.start()
# print(f"Observer type: {type(watcher.observer)}")
# print(f"Watching for branch changes... switch branches in another terminal")
# time.sleep(30)
# watcher.stop()
# print("Done watching")


# Test for Module 5 (Part 2): Git Watcher; File name watcher.py
init_db()

conn = DBConnector("127.0.0.1", 5432, "tripuser", "trippassword123", "tripplanner")
conn.connect()
inspector = SchemaInspector(conn.connection)

connection_id = save_connection("Travel App", "127.0.0.1", 5432, "tripuser", "tripplanner")
print(f"connection_id: {connection_id}")

def on_git_branch_change(old_branch, new_branch):
    print(f"Switched: {old_branch} -> {new_branch}")

    previous_snapshot = get_latest_snapshot(connection_id, old_branch)
    print(f"Previous snapshot for {old_branch}: {previous_snapshot["branch_name"], previous_snapshot["schema_json"]}")

    tables = inspector.fetch_tables()
    foreign_keys = inspector.fetch_foreign_keys()
    live_schema = json.dumps({"tables": tables, "foreign_keys": foreign_keys})

    save_snapshot(connection_id, new_branch, "real_commit_hash_placeholder", live_schema, str(time.time()))
    print(f"Saved new snapshot for {new_branch}")

watcher = GitWatcher("/home/noah/projects/tabloid", on_git_branch_change)
print(f"Initial branch: {watcher.current_branch}")

watcher.start()
print("Watching for branch changes... switch branches in another terminal")
time.sleep(30)
watcher.stop()
conn.disconnect()
print("Done watching")