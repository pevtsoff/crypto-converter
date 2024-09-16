import asyncio
from contextlib import ExitStack

import pytest
from alembic.config import Config
from alembic.migration import MigrationContext
from alembic.operations import Operations
from alembic.script import ScriptDirectory
from crypto_converter.common.settings import PG_URL
from asyncpg import Connection
from fastapi.testclient import TestClient

from crypto_converter.database.db import Base, async_session, get_db_connection, get_db_session
from crypto_converter.exchange_api.exchange_api import create_fastapi_app

"""
https://medium.com/@tclaitken/setting-up-a-fastapi-app-with-async-sqlalchemy-2-0-pydantic-v2-e6c540be4308
"""


@pytest.fixture(autouse=True)
def app():
    with ExitStack():
        yield create_fastapi_app()


@pytest.fixture
def client(app):
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="session")
def event_loop(request):
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


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
    # Run alembic migrations on test DB
    async with get_db_connection() as connection:
        await connection.run_sync(run_migrations)

        yield



# Each test function is a clean slate
@pytest.fixture(scope="function", autouse=True)
async def db_session():
    async with get_db_session() as session:
        async with session.begin():
            yield session




@pytest.fixture(scope="function", autouse=True)
async def session_override(app, db_session):
    async def get_db_session_override():
        yield db_session[0]

    app.dependency_overrides[get_db_session] = get_db_session_override