import pytest
from argparse import Namespace
from alembic.command import downgrade, upgrade
from alembic.config import Config
from alembic.script import Script, ScriptDirectory
from crypto_converter.common.settings import PG_URL

cmd_opts = Namespace(config="../alembic.ini", name="alembic", db_url=PG_URL, raiseerr=False, x=None)
config = Config(file_=cmd_opts.config, ini_section=cmd_opts.name, cmd_opts=cmd_opts)  # pylint: disable=E1101
config.set_main_option("script_location", "../alembic")
config.set_main_option("sqlalchemy.url", str(PG_URL) + "?async_fallback=true")


def get_revisions():
    # Get directory with alembic migrations
    revisions_dir = ScriptDirectory.from_config(config)

    # Get migrations and sort them in order from first to last
    revisions = list(revisions_dir.walk_revisions("base", "heads"))
    revisions.reverse()
    return revisions


@pytest.fixture
def clean_migrations():
    downgrade(config, "base")


@pytest.mark.parametrize("revision", get_revisions())
def test_migrations_stairway(clean_migrations, revision: Script):
    upgrade(config, revision.revision)
    # -1 is used to lower the first migration (because its down_revision is None)
    downgrade(config, revision.down_revision or "-1")
    upgrade(config, revision.revision)