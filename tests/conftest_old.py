import asyncio

import pytest
from alembic.command import downgrade
from alembic.config import Config
from alembic.operations import Operations
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from asyncpg import Connection
from sqlalchemy import event, Transaction
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy_utils import create_database, database_exists, drop_database
from crypto_converter.common.common import logger
from crypto_converter.common.settings import PG_URL
from fastapi.testclient import TestClient
from argparse import Namespace
from crypto_converter.database.db import get_db_session, Base
from crypto_converter.api.app import create_fastapi_app


"""
https://medium.com/@tclaitken/setting-up-a-fastapi-app-with-async-sqlalchemy-2-0-pydantic-v2-e6c540be4308
"""


def get_alembic_config():
    cmd_opts = Namespace(
        config="../alembic.ini", name="alembic", db_url=PG_URL, raiseerr=False, x=None
    )
    config = Config(
        file_=cmd_opts.config, ini_section=cmd_opts.name, cmd_opts=cmd_opts
    )  # pylint: disable=E1101
    config.set_main_option("script_location", "../alembic")
    config.set_main_option("sqlalchemy.url", str(PG_URL) + "?async_fallback=true")

    return config


alembic_config = get_alembic_config()


@pytest.fixture
def clean_migrations():
    downgrade(alembic_config, "base")


@pytest.fixture(scope="session", autouse=True)
def client():
    app = create_fastapi_app()

    with TestClient(app) as client:
        yield client


@pytest.fixture(scope="session")
def create_test_database():
    """Create the test database asynchronously before any tests run."""
    PG_URL = "postgresql://postgres:postgres@postgres:5432/test_db"

    if database_exists(PG_URL):
        drop_database(PG_URL)
        logger.info("Test database dropped")

    create_database(PG_URL)
    logger.info(f"Test database {PG_URL} created.")

    yield

    drop_database(PG_URL)
    logger.info("Test database dropped")


# Example of creating test db before the tests using just psycopg2. Otherwize you will get error
# Cannot run Create database within transaction in postgres, as postgres doesnt support sucha a call
# def create_test_database():
#     """Create the test database synchronously before any tests run."""
#     try:
#         conn = psycopg2.connect(dsn="postgresql://postgres:postgres@postgres:5432")
#         conn.autocommit = True
#         cursor = conn.cursor()
#
#         cursor.execute("DROP DATABASE IF EXISTS test_db;")
#         cursor.execute("CREATE DATABASE test_db;")
#         cursor.execute("GRANT ALL PRIVILEGES ON DATABASE test_db TO postgres;")
#
#         cursor.close()
#         conn.close()
#
#     except DuplicateDatabaseError as e:
#         logger.exception(e)


def run_migrations(connection: Connection):
    config = Config("app/alembic.ini")
    config.set_main_option("script_location", "../alembic")
    config.set_main_option("sqlalchemy.url", PG_URL)
    script = ScriptDirectory.from_config(config)

    def upgrade(rev, context):
        return script._upgrade_revs("head", rev)

    context = MigrationContext.configure(
        connection, opts={"target_metadata": Base.metadata, "fn": upgrade}
    )

    with context.begin_transaction():
        with Operations.context(context):
            context.run_migrations()


def event_loop():
    """Create an event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def db_engine(event_loop, create_test_database):
    engine = create_async_engine(
        PG_URL,
        echo=True,
    )
    async with engine.begin() as conn:
        await conn.run_sync(run_migrations)
        # await conn.run_sync(Base.metadata.create_all)

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
    session = AsyncSession(
        bind=connection, expire_on_commit=False, future=True, autoflush=False
    )
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
