import os
import sqlite3
from tabloid.db.credentials import save_password, get_password

def get_connection():
    os.makedirs("data", exist_ok=True)
    conn = sqlite3.connect("data/tabloid.db")
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_connection() as conn:
        # Stores database connection configs
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
        # Stores UI positions of tables in graph
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
        # Delete/ Remove this later as this is in tabloid-core
        # Stores a 'snapshot' of the schema layout
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
    with get_connection() as conn:
        results = conn.execute(
            """
            SELECT * FROM layouts WHERE connection_id = ?
            """,
            (connection_id,)
        ).fetchall()

        return results
    
def save_connection(name, host, port, user, password, dbname, repo_path):
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
    with get_connection() as conn:
        cursor = conn.execute(
            """
            SELECT * FROM connections
            """
        )
        list_of_all_connections = cursor.fetchall()
        return list_of_all_connections

def get_connections_for_repo(repo_path):
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

# Delete/ Remove this later as this is in tabloid-core
def save_snapshot(connection_id, branch_name, git_commit_hash, schema_json, captured_at, keep_last=200):
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

# Delete/ Remove this later as this is in tabloid-core
def get_latest_snapshot(connection_id, branch_name):
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