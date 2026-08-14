import psycopg
import logging
from tabloid.db.interfaces import DBConnectorInterface

logger = logging.getLogger(__name__)

class PostgresConnector(DBConnectorInterface):
    """PostgreSQL database driver implementing DBConnectorInterface using `psycopg3`.

    Handles database connection lifecycles, liveness health checks, and parameterized query execution.
    """
    def __init__(self, host, port, user, password, dbname):
        self.host = host or "localhost"
        self.user = user
        self.password = password
        self.dbname = dbname
        self.connection = None

        try:
            self.port = int(str(port).strip()) if port else 5432
        except ValueError:
            self.port = 5432

    # Opens a connection to the Postgres database
    def connect(self) -> bool:
        """Establishes a active connection to the PostgreSQL target database.

        Returns:
            bool: True if connection succeeded; False if an OperationalError occurred.
        """
        try:
            self.connection = psycopg.connect(
                host = self.host,
                port = self.port,
                user = self.user,
                password = self.password,
                dbname = self.dbname,
                connect_timeout = 5 # quick fail if the database is unreachable
                )
            return True
        except psycopg.OperationalError as error:
            logger.exception(f"Connection error: {error}")
            self.last_error = str(error)
            self.connection = None
            return False
    
    # Closes the connection if one is open
    def disconnect(self) -> None:
        """Closes active PostgreSQL connection if open and resets connection handle."""
        if self.connection:
            self.connection.close()
        self.connection = None

    @property
    def is_connected(self) -> bool:
        """Checks if connection handle exists and validates connection health via a ping query (`SELECT 1`).

        Returns:
            bool: True if connection is alive and capable of executing queries; False otherwise.
        """
        # return self.connection is not None and not self.connection.closed
        if self.connection is None or self.connection.closed:
            return False
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            return True
        except psycopg.Error:
            self.connection = None
            return False

    def execute_query(self, sql, params=None) -> list[tuple]:
            """Executes a SQL query against PostgreSQL database and returns fetched raw tuples.

        Args:
            sql (str): SQL statement to execute.
            params (tuple | dict | None): Optional parameters for query substitution.

        Returns:
            list[tuple]: Query results formatted as list of raw row tuples.

        Raises:
            ConnectionError: If connection is missing/dead or drops mid-execution.
        """
            if not self.is_connected:
                raise ConnectionError("Cannot execute query: not connected to database.")
            try:
                with self.connection.cursor() as cursor:
                    cursor.execute(sql, params)
                    return cursor.fetchall()
            except psycopg.OperationalError as error:
                logger.exception(f"Connection dropped during query execution: {error}")
                self.connection = None
                raise ConnectionError(
                    f"Lost connection to database: {error}"
                ) from error
            except psycopg.Error as error:
                logger.exception(f"Query execution failed: {error}")
                raise
                