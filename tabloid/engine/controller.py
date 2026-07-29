import json
import time
from dataclasses import asdict
from tabloid.db.postgres_connector import PostgresConnector
from tabloid.db.postgres_inspector import PostgresSchemaInspector
from tabloid.engine.layout import LayoutEngine
from tabloid.git.watcher import GitWatcher
from tabloid.engine.differ import diff_schemas
from tabloid.storage.local_db import save_connection, save_snapshot, get_latest_snapshot

class Controller:
    def __init__(self):
        pass

    def connect_and_load_schema(self, credentials):
        connector = PostgresConnector( 
            credentials["host"],      
            credentials["port"],        
            credentials["user"],       
            credentials["password"],   
            credentials["dbname"]      
        )
        if not connector.connect():
            raise ConnectionError("Could not connect to database. Check your credentials.")

        inspector = PostgresSchemaInspector(connector)
        tables = inspector.fetch_tables() 
        foreign_keys = inspector.fetch_foreign_keys()   
        layout = LayoutEngine(tables, foreign_keys)     
        positions = layout.compute_layout()             
        graph = layout.build_graph()

        connection_id = save_connection(
            credentials["dbname"], #placeholder for now the real input is 'name' refer to save_connection found in tabloid/storage/local_db.py
            credentials["host"], 
            credentials["port"], 
            credentials["user"], 
            credentials["dbname"]
        )

        self.connection_id = connection_id

        return tables, foreign_keys, positions, graph, connection_id



    def start_git_watcher(self, repo_path):
        self.git_watcher = GitWatcher(repo_path, self.on_branch_change)
        self.git_watcher.start()

    def on_branch_change(self, old_branch, new_branch):
        previous_snapshot = get_latest_snapshot(self.connection_id, old_branch)

        inspector = PostgresConnector(self.connector)
        tables = inspector.fetch_tables()
        foreign_keys = inspector.fetch_foreign_keys()
        live_schema = json.dumps({
            "tables": [asdict(t) for t in tables],
            "foreign_keys": [asdict(fk) for fk in foreign_keys]
        })

        save_snapshot(self.connection_id, new_branch, "real_commit_hash_placeholder", live_schema, str(time.time()))

        if previous_snapshot is not None:
            diff = diff_schemas(previous_snapshot["schema_json"], live_schema)
            return diff

        return None