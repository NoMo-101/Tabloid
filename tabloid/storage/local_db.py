import os
import sqlite3
from tabloid.db.credentials import save_password, get_password

def get_connection():
    """Establishes and returns a connection to the local SQLite database.

    Creates the 'data' directory if it does not already exist and configures
    rows to be returned as sqlite3.Row objects (dict-like access).
    """
    os.makedirs("data", exist_ok=True)
    conn = sqlite3.connect("data/tabloid.db")
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initializes the local SQLite database schema.

    Creates tables for connections, UI layout coordinates, schema snapshots,
    and repository-to-connection mappings if they do not exist.
    """

    with get_connection() as conn:
        # Stores database connection configurations (excluding secret passwords)
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS connections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                host TEXT,
                port INTEGER,
                user TEXT,
                dbname TEXT,
                UNIQUE(name, host, port, dbname)
            );
            """
        )

        # Stores UI (x, y) coordinates for rendering database tables on a canvas
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS layouts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                connection_id INTEGER,
                table_name TEXT,
                x REAL,
                y REAL,
                UNIQUE(connection_id, table_name)
            );
            """
        )

       # TODO: Remove snapshots table once tabloid-core handles snapshot storage completely
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                connection_id INTEGER,
                branch_name TEXT,
                git_commit_hash TEXT,
                schema_json TEXT,
                captured_at TEXT
            );
            """
        )

        # Maps local Git repositories to their associated database connections
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS repo_connections (
                repo_path TEXT,
                connection_id INTEGER,
                FOREIGN KEY (connection_id) REFERENCES connections(id),
                UNIQUE(repo_path, connection_id)
            );
            """
        )


def save_layout(connection_id, table_name, x, y):
    """Saves or updates the UI grid coordinates for a specific table in a schema layout.

    Args:
        connection_id (int): ID of the target database connection.
        table_name (str): Name of the table being positioned.
        x (float): Horizontal position coordinate.
        y (float): Vertical position coordinate.
    """
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO layouts (connection_id, table_name, x, y) 
            VALUES (?, ?, ?, ?)
            ON CONFLICT(connection_id, table_name)
            DO UPDATE SET x = excluded.x, y = excluded.y;
            """,
            (connection_id, table_name, x, y)
        )


def load_layout(connection_id):
    """Retrieves all saved UI table positions for a given database connection.

    Args:
        connection_id (int): Target connection ID.

    Returns:
        list[sqlite3.Row]: List of layout rows containing table_name, x, and y values.
    """
    with get_connection() as conn:
        results = conn.execute(
            """
            SELECT * FROM layouts WHERE connection_id = ?
            """,
            (connection_id,)
        ).fetchall()

        return results
    
    
def save_connection(name, host, port, user, password, dbname, repo_path):
    """Saves a database connection config, binds it to a local repository, and stores the password securely.

    Args:
        name (str): User-defined alias for the connection.
        host (str): Database server hostname or IP.
        port (int): Database server port.
        user (str): Database username.
        password (str | None): Plaintext password to store in OS keyring.
        dbname (str): Target database name.
        repo_path (str): Local filesystem path of the associated Git repository.

    Returns:
        int: The database ID (`connection_id`) assigned to the saved connection.
    """
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO connections (name, host, port, user, dbname) 
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(name, host, port, dbname)
            DO UPDATE SET user = excluded.user;
            """,
            (name, host, port, user, dbname)
        )
        cursor = conn.execute(
            """
            SELECT id FROM connections WHERE name = ? AND host = ? AND port = ? AND dbname = ?
            """,
            (name, host, port, dbname)
        )
        row = cursor.fetchone()
        connection_id = row[0]
        conn.execute(
            """
            INSERT INTO repo_connections (repo_path, connection_id)
            VALUES (?, ?)
            ON CONFLICT (repo_path, connection_id) DO NOTHING
            """,
            (repo_path, connection_id)
        )
        if password is not None:
            save_password(str(connection_id), password)
        return connection_id
    

def load_connection(connection_id):
    """Retrieves connection metadata from SQLite and the associated password from secure keyring storage.

    Args:
        connection_id (int): Target connection ID.

    Returns:
        dict: A dictionary containing:
            - "connection" (sqlite3.Row | None): Metadata fields (name, host, port, user, dbname).
            - "password" (str | None): Decrypted password string from system keyring.
    """
    with get_connection() as conn:
        cursor = conn.execute(
            """
            SELECT name, host, port, user, dbname FROM connections WHERE id = ?
            """,
            (connection_id,)
        )
        load = cursor.fetchone()
        fetched_password = get_password(str(connection_id))
        return {"connection": load, "password": fetched_password}
    

# This function may be used for future use case (made it then got bitten by the scope creep bug)
def get_all_connections():
    """Retrieves all saved database connections across all repositories.

    Returns:
        list[sqlite3.Row]: Rows representing all connection records.
    """
    with get_connection() as conn:
        cursor = conn.execute(
            """
            SELECT * FROM connections
            """
        )
        list_of_all_connections = cursor.fetchall()
        return list_of_all_connections

def get_connections_for_repo(repo_path):
    """Fetches all connection configurations linked to a specific local Git repository.

    Args:
        repo_path (str): Local path of the Git repository.

    Returns:
        list[sqlite3.Row]: Matching connection records joined with repo link data.
    """
    with get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT repo_connections.repo_path, connections.id, connections.name, connections.host, connections.port, connections.user, connections.dbname
                FROM repo_connections
                JOIN connections ON repo_connections.connection_id = connections.id
                WHERE repo_connections.repo_path = ? 
                """,
                (repo_path,)
            )
            return cursor.fetchall()

# TODO: Remove save_snapshot once snapshotting logic migrates to tabloid-core
def save_snapshot(connection_id, branch_name, git_commit_hash, schema_json, captured_at, keep_last=200):
    """Saves a new database schema snapshot and automatically purges older snapshots beyond keep_last count.

    Args:
        connection_id (int): ID of the associated database connection.
        branch_name (str): Active Git branch name when snapshot was captured.
        git_commit_hash (str): Git commit hash at the time of capture.
        schema_json (str): Serialized JSON representing the schema structure.
        captured_at (str): ISO timestamp or Unix string of execution time.
        keep_last (int, optional): Maximum history depth per branch. Defaults to 200.
    """
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO snapshots (connection_id, branch_name, git_commit_hash, schema_json, captured_at)
            VALUES (?, ?, ?, ?, ?);
            """,
            (connection_id, branch_name, git_commit_hash, schema_json, captured_at)
        )
        conn.execute(
            """
            DELETE FROM snapshots
            WHERE connection_id = ? AND branch_name = ?
            AND id NOT IN (
                SELECT id FROM snapshots
                WHERE connection_id = ? AND branch_name = ?
                ORDER BY captured_at DESC
                LIMIT ?
            );
            """,
            (connection_id, branch_name, connection_id, branch_name, keep_last)
        )

# TODO Remove get_latest_snapshot once logic migrates to tabloid-core
def get_latest_snapshot(connection_id, branch_name):
    """Retrieves the most recent schema snapshot for a specific connection and branch.

    Args:
        connection_id (int): ID of the database connection.
        branch_name (str): Target Git branch name.

    Returns:
        sqlite3.Row | None: Latest snapshot record, or None if no snapshot exists.
    """
    with get_connection() as conn:
        return conn.execute(
            """
            SELECT * FROM snapshots
            WHERE connection_id = ? AND branch_name = ?
            ORDER BY captured_at DESC
            LIMIT 1;
            """,
            (connection_id, branch_name)
        ).fetchone()