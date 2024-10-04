from backend.db_models import Base
import asyncio
from backend.utils.db_connection import async_engine


async def create_scheme():
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


if __name__ == '__main__':
    asyncio.run(create_scheme())
