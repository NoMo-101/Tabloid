class SchemaInspector:
    def __init__(self, connection):
        # Save the connection so we can run queries
        self.connection = connection

    # Retrieve all tables in the 'public' schema.
    def fetch_tables(self):
        with self.connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_type = 'BASE TABLE'
                ORDER BY table_name;
                """
                )
            table_results = cursor.fetchall()
            return [row[0] for row in table_results]
    
    # Retrieve column metadata for all tables in the 'public' schema
    def fetch_columns(self):
        with self.connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT table_name, column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_schema = 'public'
                ORDER BY table_name, ordinal_position;
                """
            )
            column_results = cursor.fetchall()
            return column_results
        
    # Retrieves foreign key relationships between tables (table -> table links)
    # Returns (from_table, from_column, to_table, to_column)
    def fetch_foreign_keys(self):
        with self.connection.cursor() as cursor:
            cursor.execute(
                """
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
            )
            foreign_key_results = cursor.fetchall()
            return foreign_key_results