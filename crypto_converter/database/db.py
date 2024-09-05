import contextlib
from typing import Any, AsyncIterator

from sqlalchemy.ext.asyncio import (
    AsyncConnection,
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


class DatabaseSessionManager:
    def __init__(self, host: str, engine_kwargs: dict[str, Any] = {}):
        self._engine = create_async_engine(host, **engine_kwargs)
        self._sessionmaker = async_sessionmaker(autocommit=False, bind=self._engine)

    async def close(self):
        if self._engine is None:
            raise Exception("DatabaseSessionManager is not initialized")
        await self._engine.dispose()

        self._engine = None
        self._sessionmaker = None

    @contextlib.asynccontextmanager
    async def connect(self) -> AsyncIterator[AsyncConnection]:
        if self._engine is None:
            raise Exception("DatabaseSessionManager is not initialized")

        async with self._engine.begin() as connection:
            try:
                yield connection
            except Exception:
                await connection.rollback()
                raise

    @contextlib.asynccontextmanager
    async def session(self) -> AsyncIterator[AsyncSession]:
        if self._sessionmaker is None:
            raise Exception("DatabaseSessionManager is not initialized")

        session = self._sessionmaker()

        try:
            yield session
        except Exception:
            logger.warning(f'rolling back')
            await session.rollback()
            raise

sessionmanager = DatabaseSessionManager(PG_URL, {"echo": SQL_DEBUG})


async def get_db_session() -> AsyncIterator[AsyncSession]:
    async with sessionmanager.session() as session:
        yield session


# engine = create_async_engine(
#     PG_URL,
#     query_cache_size=0,
#     echo=True
# )
# async def get_db_session() -> AsyncIterator[AsyncSession]:
#     async_session = async_sessionmaker(autocommit=False, autoflush=True, bind=engine, class_=AsyncSession, expire_on_commit=False)
#     async with async_session() as session:
#         yield session