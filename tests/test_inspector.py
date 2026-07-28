import pytest
from unittest.mock import Mock # pytest and mock is for testing

from tabloid.db.postgres_inspector import PostgresSchemaInspector
from tabloid.db.models import TableInfo, ColumnInfo, ForeignKeyInfo

# these two fixtures functions are for reusing objects that you (or I) gave to test
@pytest.fixture
def mock_connector():
    return Mock()

@pytest.fixture # this saves times instead of calling this every time for each test method
def inspector(mock_connector):
    return PostgresSchemaInspector(mock_connector)

def test_fetch_tables(inspector, mock_connector):
    mock_connector.execute_query.return_value = [ # completely fake or "mocked" for testing
        ("users",),
        ("orders",)
    ]

    result = inspector.fetch_tables()

    mock_connector.execute_query.assert_called_once() # checks if called exactly once
    called_sql = mock_connector.execute_query.call_args[0][0] # calls first positional argument
    assert "information_schema.tables" in called_sql
    assert "table_schema = 'public'" in called_sql
    assert "BASE TABLE" in called_sql

    # of course, this checks the output (in this case, make sure it matches the expected TableInfo objects)
    assert result == [
        TableInfo(table_name="users"), 
        TableInfo(table_name="orders"),
    ]

def test_fetch_columns(inspector, mock_connector):
    mock_connector.execute_query.return_value = [
        ("users", "id", "integer", "NO"),
        ("users", "email", "character varying", "YES")
    ]

    result = inspector.fetch_columns()
    
    mock_connector.execute_query.assert_called_once()
    called_sql = mock_connector.execute_query.call_args[0][0]
    assert "information_schema.columns" in called_sql
    assert "table_schema = 'public'" in called_sql
    assert result == [
        ColumnInfo(table_name="users", column_name="id", data_type="integer", is_nullable=False),
        ColumnInfo(table_name="users", column_name="email", data_type="character varying", is_nullable=True)
    ]

def test_fetch_foreign_keys(inspector, mock_connector):
    mock_connector.execute_query.return_value = [
        ("orders", "user_id", "users", "id")
    ]

    result = inspector.fetch_foreign_keys()

    mock_connector.execute_query.assert_called_once()
    called_sql = mock_connector.execute_query.call_args[0][0]
    assert "FOREIGN KEY" in called_sql
    assert "table_schema = 'public'" in called_sql

    assert result == [
        ForeignKeyInfo(
            from_table="orders", 
            from_column="user_id", 
            to_table="users", 
            to_column="id",
            ),
    ]

def test_nullable(inspector, mock_connector):
    mock_connector.execute_query.return_value = [
        ("users", "id", "integer", "NO"),
        ("users", "email", "character varying", "YES")
    ]

    result = inspector.fetch_columns()

    assert result[0].is_nullable == False # NO being first or index 0 is false
    assert result[1].is_nullable == True  # YES being second or index 1 is true