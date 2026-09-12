import contextlib
from sqlalchemy import create_engine
import asyncpg
from app.config import settings

def get_sync_engine():
    return create_engine(settings.DATABASE_URL)

@contextlib.asynccontextmanager
async def get_async_session():
    pool = await asyncpg.create_pool(settings.READ_ONLY_DATABASE_URL)
    async with pool.acquire() as conn:
        yield conn
    await pool.close()
