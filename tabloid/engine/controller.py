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
    """Orchestrates database inspection, layout computation, and Git branch monitoring."""
    def __init__(self):
        self.connector = None
        self.connection_id = None
        self.git_watcher = None
        self.on_diff_detected = None
    
    def connect_and_load_schema(self, credentials):
        """Establishes a database connection, extracts the schema, calculates layout positions,

        and saves the connection credentials locally.

        Args:
            credentials (dict): Connection parameters including host, port, user, password,
            dbname, and repo_path.

        Returns:
            tuple: (tables, foreign_keys, columns, positions, graph, connection_id)

        Raises:
            ConnectionError: If the database is unreachable or missing the 'public' schema.
        """
        connector = PostgresConnector(
            credentials["host"],
            credentials["port"],
            credentials["user"],
            credentials["password"],
            credentials["dbname"]
        )
        if not connector.connect():
            detail = getattr(connector, "last_error", "Unknown error")
            raise ConnectionError(f"Could not connect to database. \n\n{detail}")

        # Store connector instance so branch-change callbacks can query the DB
        self.connector = connector

        tables, foreign_keys, columns, positions, graph = self._fetch_and_layout()

        connection_id = save_connection(
                    credentials["name"], 
                    credentials["host"], 
                    credentials["port"], 
                    credentials["user"],
                    credentials["password"], 
                    credentials["dbname"],
                    credentials["repo_path"]
                )
        self.connection_id = connection_id

        return tables, foreign_keys, columns, positions, graph, connection_id

    def fetch_schema_snapshot(self):
        """Re-inspects the active database and re-computes the layout.

        Designed for UI triggers when an active connection is already open.

        Raises:
            RuntimeError: If called before connect_and_load_schema().
        """
        if not getattr(self, "connector", None):
            raise RuntimeError("No active connection.")
        return self._fetch_and_layout() # returns everything in _fetch_and_layout() when active

    # separates connection and fetch from connect_and_load_schema() + columns
    def _fetch_and_layout(self): 
        """Helper to inspect Postgres tables, columns, and keys, then run the visual layout engine."""

        # check if the 'public' schema exists before fetching, adds to hardening
        try:
            inspector = PostgresSchemaInspector(self.connector)

            # Verification step: ensure public schema exists before attempting queries
            if not inspector.schema_exists("public"):
                raise ConnectionError("The 'public' schema does not exist in the connected database.")
            
            tables = inspector.fetch_tables()
            foreign_keys = inspector.fetch_foreign_keys()
            columns = inspector.fetch_columns()
        except ConnectionError:
            raise
        except Exception as error:
            raise ConnectionError(f"Lost connection to database: {error}") from error
        
        layout = LayoutEngine(tables, foreign_keys)
        positions = layout.compute_layout()
        graph = layout.build_graph()
        return tables, foreign_keys, columns, positions, graph

    def start_git_watcher(self, repo_path, on_diff_detected):
        """Starts background thread watching for Git branch switches in the user's project repo.

        Args:
            repo_path (str): Path to local Git repository.
            on_diff_detected (callable): Callback function triggered when a schema diff is calculated.
        """
        self.on_diff_detected = on_diff_detected
        try:
            self.git_watcher = GitWatcher(repo_path, self.on_branch_change)
            self.git_watcher.start()
        except ValueError as error:
            raise ValueError(f"Failed to start Git watcher: {error}") from error

    def on_branch_change(self, old_branch, new_branch):
        """Callback invoked by GitWatcher on branch checkout.

        Fetches live DB schema, saves a new snapshot under new_branch, and emits
        the diff against old_branch via on_diff_detected callback.
        """
        previous_snapshot = get_latest_snapshot(self.connection_id, old_branch)

        inspector = PostgresSchemaInspector(self.connector)
        tables = inspector.fetch_tables()
        foreign_keys = inspector.fetch_foreign_keys()
        live_schema = json.dumps({
            "tables": [asdict(t) for t in tables],
            "foreign_keys": [asdict(fk) for fk in foreign_keys]
        })

        # TODO: Replace placeholder string with actual commiit hash once Gitwatch supports it
        save_snapshot(self.connection_id, new_branch, "real_commit_hash_placeholder", live_schema, str(time.time()))

        if previous_snapshot is not None:
            try:
                diff = diff_schemas(previous_snapshot["schema_json"], live_schema)
            except Exception as error:
                if self.on_diff_detected:
                    self.on_diff_detected({"error": f"Could not compute schema diff: {error}"})
                return None

            if self.on_diff_detected:
                self.on_diff_detected(diff)

        return None