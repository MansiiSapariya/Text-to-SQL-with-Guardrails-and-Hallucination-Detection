import logging
from dataclasses import dataclass, field
from sqlalchemy import inspect
from app.database.connection import get_sync_engine

logger = logging.getLogger(__name__)

@dataclass
class TableDescription:
    table_name: str
    description: str
    columns_summary: str

@dataclass
class SchemaContext:
    tables: dict
    relationships: dict
    total_tables: int
    sample_values: dict = field(default_factory=dict)

class SchemaExtractor:
    def __init__(self):
        self.engine = get_sync_engine()
        self._schema_cache = None

    def get_full_schema(self) -> dict:
        inspector = inspect(self.engine)
        schema = {}
        for table_name in inspector.get_table_names():
            columns = []
            for col in inspector.get_columns(table_name):
                columns.append({
                    "name": col["name"],
                    "type": str(col["type"]),
                    "nullable": col["nullable"],
                })
            pk = inspector.get_pk_constraint(table_name)
            fks = inspector.get_foreign_keys(table_name)
            schema[table_name] = {
                "columns": columns,
                "primary_keys": pk.get("constrained_columns", []),
                "foreign_keys": fks
            }
        return schema

    def get_sample_values(self, table: str, col: str, limit: int = 8) -> list:
        try:
            with self.engine.connect() as conn:
                result = conn.execute(
                    self.engine.dialect.statement_compiler.statement_cls(
                        f"SELECT DISTINCT {col} FROM {table} WHERE {col} IS NOT NULL LIMIT {limit}"
                    )
                )
                return [row[0] for row in result]
        except Exception as e:
            logger.error(f"Error fetching sample values for {table}.{col}: {e}")
            return []

    def get_schema_context(self) -> SchemaContext:
        if self._schema_cache:
            return self._schema_cache

        schema = self.get_full_schema()
        relationships = {}
        sample_values = {}

        for table, details in schema.items():
            relationships[table] = details["foreign_keys"]
            # Auto-detect low cardinality logic can be added here
            
        self._schema_cache = SchemaContext(
            tables=schema,
            relationships=relationships,
            total_tables=len(schema),
            sample_values=sample_values
        )
        return self._schema_cache

    def get_table_descriptions(self) -> list[TableDescription]:
        context = self.get_schema_context()
        descriptions = []
        for table_name, details in context.tables.items():
            cols = [f"{c['name']} ({c['type']})" for c in details["columns"]]
            columns_summary = ", ".join(cols)
            desc = f"Table {table_name} with columns: {columns_summary}"
            descriptions.append(TableDescription(
                table_name=table_name,
                description=desc,
                columns_summary=columns_summary
            ))
        return descriptions
