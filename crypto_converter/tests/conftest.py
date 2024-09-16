import asyncio
import os
from contextlib import ExitStack

import pytest
from alembic.config import Config
from alembic.migration import MigrationContext
from alembic.operations import Operations
from alembic.script import ScriptDirectory
from sqlalchemy import event, Transaction
from sqlalchemy.ext.asyncio import AsyncSession

from crypto_converter.common.settings import PG_URL
from asyncpg import Connection
from fastapi.testclient import TestClient

from crypto_converter.database.db import Base, get_db_connection, get_db_session, engine
from crypto_converter.exchange_api.exchange_api import create_fastapi_app

"""
https://medium.com/@tclaitken/setting-up-a-fastapi-app-with-async-sqlalchemy-2-0-pydantic-v2-e6c540be4308
"""

@pytest.fixture(scope="session", autouse=True)
def client():
    with ExitStack():
        app = create_fastapi_app()

        with TestClient(app) as client:
            yield client



def run_migrations(connection: Connection):
    config = Config("./alembic.ini")
    config.set_main_option("script_location", "../alembic")
    config.set_main_option("sqlalchemy.url", PG_URL)
    script = ScriptDirectory.from_config(config)

    def upgrade(rev, context):
        return script._upgrade_revs("head", rev)

    context = MigrationContext.configure(connection, opts={"target_metadata": Base.metadata, "fn": upgrade})

    with context.begin_transaction():
        with Operations.context(context):
            context.run_migrations()


@pytest.fixture(scope="session", autouse=True)
async def setup_database():
    async with get_db_connection() as connection:
        await connection.run_sync(run_migrations)
        yield connection



@pytest.fixture(scope="session")
def db_engine():
    return engine


# This is a spare fixture
@pytest.fixture(scope="function", autouse=True)
async def db_session_committed():
    """This db session is only for the test cases which need data to be committed into db"""
    async with get_db_session() as session:
        async with session.begin():
            yield session


# this is the main test fixture for test using database
@pytest.fixture
async def db_session(db_engine):
    """Fixture of SQLAlchemy session object with auto rollback after each test case"""
    # https://docs.sqlalchemy.org/en/14/orm/session_transaction.html#joining-a-session-into-an-external-transaction-such-as-for-test-suites
    connection = await db_engine.connect()
    transaction = await connection.begin()
    session = AsyncSession(bind=connection, expire_on_commit=False, future=True, autoflush=False)
    await connection.begin_nested()

    @event.listens_for(session.sync_session, "after_transaction_end")
    def end_savepoint(session: AsyncSession, transaction: Transaction) -> None:
        """async events are not implemented yet, recreates savepoints to avoid final commits"""
        # https://github.com/sqlalchemy/sqlalchemy/issues/5811#issuecomment-756269881
        if connection.closed:
            return
        if not connection.in_nested_transaction():
            connection.sync_connection.begin_nested()

    yield session
    if session.in_transaction():  # pylint: disable=no-member
        await transaction.rollback()
    await connection.close()
