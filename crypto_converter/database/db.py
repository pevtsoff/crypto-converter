from contextlib import asynccontextmanager
from typing import Any, AsyncIterator, AsyncGenerator
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import declarative_base
from crypto_converter.common.common import configure_logger
from crypto_converter.common.settings import PG_URL, SQL_DEBUG


logger = configure_logger(__name__)
logger.info("Connecting to database...")
Base = declarative_base()

logger.info("Connecting to database...")
engine = create_async_engine(
    PG_URL,
    query_cache_size=0,
    echo=SQL_DEBUG
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
