from abc import ABC, abstractmethod
from tabloid.db.models import TableInfo, ColumnInfo, ForeignKeyInfo

#TODO: Separate the interfaces later into their own files

class DBConnectorInterface(ABC):
    @abstractmethod
    def connect(self) -> bool:
        """Attempt to open a connection to the database. Returns True on success, False on failure."""
        pass

    @abstractmethod
    def disconnect(self) -> None:
        """Close the connection if one is open."""
        pass

    @abstractmethod
    def execute_query(self, sql, params=None) -> list[tuple]:
        """Run a SQL query with optional parameters and return the resulting rows as raw tuples."""
        pass

    @property
    @abstractmethod
    def is_connected(self) -> bool:
        """True if a connection currently exists and is still alive, without attempting to reconnect."""
        pass

class SchemaInspectorInterface(ABC):
    @abstractmethod
    def fetch_tables(self) -> list[TableInfo]:
        """Retrieve all tables"""
        pass

    @abstractmethod
    def fetch_columns(self) -> list[ColumnInfo]:
        """Retrieve column metadata for all tables"""
        pass

    @abstractmethod
    def fetch_foreign_keys(self) -> list[ForeignKeyInfo]:
        """Retrieves foreign key relationships between tables (table -> table links)"""
        pass