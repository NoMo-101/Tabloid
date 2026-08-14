from dataclasses import dataclass


# Represents high-level metadata for a database table
@dataclass(frozen=True)
class TableInfo:
    table_name: str


# Represents metadata for a single column within a database table
@dataclass(frozen=True)
class ColumnInfo:
    table_name: str
    column_name: str
    data_type: str
    is_nullable: bool 


# Represents a foreign key constraint linking two database tables
@dataclass(frozen=True)
class ForeignKeyInfo:
    from_table: str
    from_column: str
    to_table: str
    to_column: str