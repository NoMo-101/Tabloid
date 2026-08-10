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

    """
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
    """
    
    def connect_and_load_schema(self, credentials):
        connector = PostgresConnector(
            credentials["host"],
            credentials["port"],
            credentials["user"],
            credentials["password"],
            credentials["dbname"]
        )
        if not connector.connect():
            detail = getattr(connector, "last_error", "Unknown error")
            raise ConnectionError("Could not connect to database. \n\n{detail}")

        self.connector = connector # on branch needs this

        tables, foreign_keys, columns, positions, graph = self._fetch_and_layout()

        connection_id = save_connection(
                    credentials["name"], 
                    credentials["host"], 
                    credentials["port"], 
                    credentials["user"], 
                    credentials["dbname"]
                )
        self.connection_id = connection_id

        return tables, foreign_keys, columns, positions, graph, connection_id

    def fetch_schema_snapshot(self): # this snapshot method is for calling in the UI
        if not getattr(self, "connector", None):
            raise RuntimeError("No active connection.")
        return self._fetch_and_layout() # returns everything in _fetch_and_layout() when active

    def _fetch_and_layout(self): # separates connection and fetch from connect_and_load_schema() + columns

        # check if the 'public' schema exists before fetching, adds to hardening
        try:
            inspector = PostgresSchemaInspector(self.connector)
            if not inspector.schema_exists("public"):
                raise ConnectionError("The 'public' schema does not exist in the connected database.")
            tables = inspector.fetch_tables()
            foreign_keys = inspector.fetch_foreign_keys()
            columns = inspector.fetch_columns()
        except ConnectionError:
            raise
        except Exception as error:
            raise ConnectionError(f"Lost connection to database: {error}") from error
        
        inspector = PostgresSchemaInspector(self.connector)
        tables = inspector.fetch_tables()
        foreign_keys = inspector.fetch_foreign_keys()
        columns = inspector.fetch_columns()
        layout = LayoutEngine(tables, foreign_keys)
        positions = layout.compute_layout()
        graph = layout.build_graph()
        return tables, foreign_keys, columns, positions, graph

    def start_git_watcher(self, repo_path, on_diff_detected):
        self.on_diff_detected = on_diff_detected
        try:
            self.git_watcher = GitWatcher(repo_path, self.on_branch_change)
            self.git_watcher.start()
        except ValueError as error:
            raise ValueError(f"Failed to start Git watcher: {error}") from error

    def on_branch_change(self, old_branch, new_branch):
        previous_snapshot = get_latest_snapshot(self.connection_id, old_branch)

        inspector = PostgresSchemaInspector(self.connector)
        tables = inspector.fetch_tables()
        foreign_keys = inspector.fetch_foreign_keys()
        live_schema = json.dumps({
            "tables": [asdict(t) for t in tables],
            "foreign_keys": [asdict(fk) for fk in foreign_keys]
        })

        save_snapshot(self.connection_id, new_branch, "real_commit_hash_placeholder", live_schema, str(time.time()))

        if previous_snapshot is not None:
            diff = diff_schemas(previous_snapshot["schema_json"], live_schema)
            if self.on_diff_detected:
                self.on_diff_detected({"error": f"Could not fetch schema on branch change: {diff}"})

        # if previous_snapshot is not None:
        #     diff = diff_schemas(previous_snapshot["schema_json"], live_schema)
        #     print(f"Schema diff: {diff}") #temporary, just to see it working
        #     return diff

        return None