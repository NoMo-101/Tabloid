import psycopg
import logging

logger = logging.getLogger(__name__)

class DBConnector:
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
    def connect(self):
        try:
            self.connection = psycopg.connect(
                host = self.host,
                port = self.port,
                user = self.user,
                password = self.password,
                dbname = self.dbname
                )
            return True
        except psycopg.OperationalError as error:
            logger.exception(f"Connection error: {error}")
            return False
    
    # Closes the connection if one is open    
    def disconnect(self):
        if self.connection:
            self.connection.close()
        self.connection = None

    @property
    def is_connected(self):
        """Returns True if the connection exists and is alive."""
        return self.connection is not None and not self.connection.closed