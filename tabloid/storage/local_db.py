import sqlite3

def get_connection():
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
        # Stores a 'snapshot' of the schema layout
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                connection_id INTEGER,
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