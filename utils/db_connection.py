from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from conf import settings
from conf.secrets import db_address, db_user, db_password, db_name
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor


def get_connection_string(address, user, password, db_name) -> str:
    return f'postgresql+asyncpg://{user}:{password}@{address}/{db_name}'


async_engine = create_async_engine(get_connection_string(db_address, db_user, db_password, db_name),
                                   echo=not settings.IS_PROD)
AsyncMainSession = async_sessionmaker(async_engine)

SQLAlchemyInstrumentor().instrument(
    engine=async_engine.sync_engine
)
