import pytest
from alembic.command import downgrade, upgrade
from alembic.script import Script, ScriptDirectory
from crypto_converter.tests.conftest import alembic_config


def get_revisions():
    revisions_dir = ScriptDirectory.from_config(alembic_config)
    revisions = list(revisions_dir.walk_revisions("base", "heads"))
    revisions.reverse()

    return revisions


@pytest.mark.parametrize("revision", get_revisions())
def test_migrations_stairway(clean_migrations, revision: Script):
    upgrade(alembic_config, revision.revision)
    # -1 is used to lower the first migration (because its down_revision is None)
    downgrade(alembic_config, revision.down_revision or "-1")
    upgrade(alembic_config, revision.revision)
