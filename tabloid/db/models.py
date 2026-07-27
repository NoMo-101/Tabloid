from dataclasses import dataclass

@dataclass(frozen=True)
class TableInfo:
    table_name: str

@dataclass(frozen=True)
class ColumnInfo:
    table_name: str
    column_name: str
    data_type: str
    is_nullable: bool 

@dataclass(frozen=True)
class ForeignKeyInfo:
    from_table: str
    from_column: str
    to_table: str
    to_column: str