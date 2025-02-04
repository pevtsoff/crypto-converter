import pytest
from alembic.command import downgrade, upgrade
from alembic.script import Script, ScriptDirectory
from sqlalchemy import inspect
from sqlalchemy.ext.asyncio import create_async_engine

from crypto_converter.database.db_models import (
    BinanceTickerDataModel,
    BinanceTickerAggregatedData,
    BinanceTickersModel,
)
from tests.conftest import alembic_config, run_migrations
from crypto_converter.common.settings import PG_URL


def get_revisions():
    revisions_dir = ScriptDirectory.from_config(alembic_config)
    revisions = list(revisions_dir.walk_revisions("base", "heads"))
    revisions.reverse()

    return revisions


# This is very useful test and shall be used on every sqlalchemy project
@pytest.mark.parametrize("revision", get_revisions())
def test_migrations_stairway(clean_migrations, revision: Script, create_test_database):
    upgrade(alembic_config, revision.revision)
    # -1 is used to lower the first migration (because its down_revision is None)
    downgrade(alembic_config, revision.down_revision or "-1")
    upgrade(alembic_config, revision.revision)


@pytest.mark.asyncio
async def test_migration_tables_created(create_test_database, event_loop):
    engine = create_async_engine(
        PG_URL,
        echo=True,
    )

    async with engine.connect() as connection:
        await connection.run_sync(run_migrations)

        def get_tables(conn):
            inspector = inspect(conn)
            return inspector.get_table_names()

        tables = await connection.run_sync(get_tables)

        expected_tables = [
            BinanceTickerDataModel.__tablename__,
            BinanceTickerAggregatedData.__tablename__,
            BinanceTickersModel.__tablename__,
        ]

        for table in expected_tables:
            assert table in tables, f"Table {table} not found"

    await engine.dispose()
