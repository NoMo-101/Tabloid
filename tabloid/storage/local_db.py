import os
import sqlite3

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
    
def save_connection(name, host, port, user, dbname):
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
        return row[0]

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