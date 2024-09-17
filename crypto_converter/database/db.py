from contextlib import asynccontextmanager
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
    AsyncConnection,
)
from sqlalchemy.orm import declarative_base
from crypto_converter.common.common import configure_logger
from crypto_converter.common.settings import (
    PG_URL,
    SQL_DEBUG,
    DB_POOL_SIZE,
    DB_MAX_OVERFLOW,
    SQL_ALCHEMY_CACHE_SIZE,
)

logger = configure_logger(__name__)
logger.info("Connecting to database...")

Base = declarative_base()
engine = create_async_engine(
    PG_URL,
    query_cache_size=SQL_ALCHEMY_CACHE_SIZE,
    echo=SQL_DEBUG,
    pool_size=DB_POOL_SIZE,
    max_overflow=DB_MAX_OVERFLOW,
)


async_session = async_sessionmaker(
    engine, expire_on_commit=False, class_=AsyncSession, future=True, autoflush=False
)


# fastapi option
@asynccontextmanager
async def get_db_session() -> AsyncSession:
    db = async_session()
    try:
        yield db
    finally:
        await db.close()


@asynccontextmanager
async def get_db_connection() -> AsyncConnection:
    """Factory that returns an async connection."""
    async with engine.connect() as connection:
        yield connection


# This option works alone fine without using transaction context manager below
# async def get_db_session() -> AsyncSession:
#     async with async_session() as session:
#         yield session
#

#
# #this option works fine with transaction context manager
# async def get_db_session() -> AsyncSession:
#     async with async_session.begin() as transaction:
#         yield transaction


@asynccontextmanager
async def transaction(db: AsyncSession) -> AsyncGenerator[None, None]:
    if not db.in_transaction():
        async with db.begin():
            logger.debug("explicit transaction begin")
            yield
        logger.debug("explicit transaction commit")
    else:
        logger.debug("already in transaction")

        try:
            yield

        except Exception:
            await db.rollback()
            raise

        if db.in_transaction():
            await db.commit()
            logger.debug("implicit transaction commit")
