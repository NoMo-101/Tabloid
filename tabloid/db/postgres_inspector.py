from tabloid.db.interfaces import DBConnectorInterface
from tabloid.db.interfaces import SchemaInspectorInterface
from tabloid.db.models import TableInfo, ColumnInfo, ForeignKeyInfo

class PostgresSchemaInspector(SchemaInspectorInterface):
    def __init__(self, connector: DBConnectorInterface):
        # Save the connection so we can run queries
        self.connector = connector

    # Retrieve all tables in the 'public' schema.
    def fetch_tables(self) -> list[TableInfo]:
        sql = """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_type = 'BASE TABLE'
            ORDER BY table_name;
            """
        rows = self.connector.execute_query(sql)
        return [TableInfo(table_name = row[0]) for row in rows]
    
    # Retrieve column metadata for all tables in the 'public' schema
    def fetch_columns(self) -> list[ColumnInfo]:
            sql = """
                SELECT table_name, column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_schema = 'public'
                ORDER BY table_name, ordinal_position;
                """
            rows = self.connector.execute_query(sql)
            return [ColumnInfo(table_name = row[0], 
                               column_name = row[1], 
                               data_type = row[2],
                               is_nullable = row[3] == 'YES'
                               ) for row in rows]
        
    # Retrieves foreign key relationships between tables (table -> table links)
    # Returns (from_table, from_column, to_table, to_column)
    def fetch_foreign_keys(self) -> list[ForeignKeyInfo]:
            sql = """
                SELECT
                    tc.table_name AS from_table,
                    kcu.column_name AS from_column,
                    ccu.table_name AS to_table,
                    ccu.column_name AS to_column
                FROM information_schema.table_constraints AS tc
                JOIN information_schema.key_column_usage AS kcu
                    ON tc.constraint_name = kcu.constraint_name
                JOIN information_schema.constraint_column_usage AS ccu
                    ON ccu.constraint_name = tc.constraint_name
                WHERE tc.constraint_type = 'FOREIGN KEY'
                    AND tc.table_schema = 'public';
                """
            rows = self.connector.execute_query(sql)
            return [ForeignKeyInfo(from_table = row[0], 
                                   from_column = row[1], 
                                   to_table = row[2], 
                                   to_column = row[3]
                                   ) for row in rows]