import asyncpg
import time
import decimal
import datetime
from dataclasses import dataclass
from app.config import settings

def _normalize_dsn(url: str) -> str:
    """Strip SQLAlchemy dialect prefix so asyncpg can use the DSN directly."""
    return url.replace("postgresql+asyncpg://", "postgresql://")

def _serialize_value(v):
    """Make PostgreSQL return types JSON-safe."""
    if isinstance(v, decimal.Decimal):
        return float(v)
    if isinstance(v, (datetime.datetime, datetime.date)):
        return v.isoformat()
    return v

@dataclass
class ExecutionResult:
    rows: list[dict]
    columns: list[str]
    row_count: int
    execution_time_ms: float
    truncated: bool

class ExecutionError(Exception):
    pass

class QueryExecutor:
    def __init__(self, read_only_url: str):
        self.read_only_url = read_only_url
        self.pool = None

    async def initialize(self):
        self.pool = await asyncpg.create_pool(_normalize_dsn(self.read_only_url))

    async def close(self):
        if self.pool:
            await self.pool.close()

    async def execute(self, sql: str, timeout_seconds: float = 30.0) -> ExecutionResult:
        if not self.pool:
            await self.initialize()

        start_time = time.time()
        try:
            async with self.pool.acquire() as conn:
                async with conn.transaction():
                    await conn.execute("SET TRANSACTION READ ONLY;")
                    
                    # Set statement timeout
                    await conn.execute(f"SET statement_timeout = {int(timeout_seconds * 1000)};")
                    
                    records = await conn.fetch(sql)
                    
                    execution_time_ms = (time.time() - start_time) * 1000
                    
                    if not records:
                        return ExecutionResult([], [], 0, execution_time_ms, False)
                        
                    columns = list(records[0].keys())
                    rows = [{k: _serialize_value(v) for k, v in dict(record).items()} for record in records]
                    
                    return ExecutionResult(
                        rows=rows,
                        columns=columns,
                        row_count=len(rows),
                        execution_time_ms=execution_time_ms,
                        truncated=len(rows) >= settings.MAX_RESULT_ROWS
                    )
        except asyncpg.PostgresError as e:
            raise ExecutionError(f"Database error: {str(e)}")
        except Exception as e:
            raise ExecutionError(f"Execution error: {str(e)}")
