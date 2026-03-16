"""Integration tests for `ch migrate`."""
import pytest
from typer.testing import CliRunner

from clickhawk.main import app

runner = CliRunner()
pytestmark = pytest.mark.integration


@pytest.fixture()
def migrations_dir(tmp_path):
    """Create a temp migrations directory with uniquely-named .sql files.

    File names include the tmp_path stem so that separate test invocations
    never collide in the shared _clickhawk_migrations tracking table.
    """
    d = tmp_path / "migrations"
    d.mkdir()
    prefix = tmp_path.name  # e.g. "test_migrate_run_dry_run0" — unique per test
    (d / f"{prefix}_001_create_test.sql").write_text(
        f"CREATE TABLE IF NOT EXISTS demo.mig_{prefix}_1 (id UInt64) ENGINE = Log;"
    )
    (d / f"{prefix}_002_add_col.sql").write_text(
        f"CREATE TABLE IF NOT EXISTS demo.mig_{prefix}_2 (id UInt64, val String) ENGINE = Log;"
    )
    return str(d)


def test_migrate_status_exit_code(ch_client, ensure_demo_table, migrations_dir):
    result = runner.invoke(app, ["migrate", "status", "--dir", migrations_dir])
    assert result.exit_code == 0


def test_migrate_run_dry_run(ch_client, ensure_demo_table, migrations_dir):
    result = runner.invoke(app, ["migrate", "run", "--dir", migrations_dir, "--dry-run"])
    assert result.exit_code == 0
    assert "would apply" in result.output


def test_migrate_run_applies(ch_client, ensure_demo_table, migrations_dir):
    result = runner.invoke(app, ["migrate", "run", "--dir", migrations_dir])
    assert result.exit_code == 0


def test_migrate_run_idempotent(ch_client, ensure_demo_table, migrations_dir):
    """Running twice should report 'All migrations already applied'."""
    runner.invoke(app, ["migrate", "run", "--dir", migrations_dir])
    result = runner.invoke(app, ["migrate", "run", "--dir", migrations_dir])
    assert result.exit_code == 0
    assert "already applied" in result.output


def test_migrate_status_after_run(ch_client, ensure_demo_table, migrations_dir):
    runner.invoke(app, ["migrate", "run", "--dir", migrations_dir])
    result = runner.invoke(app, ["migrate", "status", "--dir", migrations_dir])
    assert result.exit_code == 0
    assert "applied" in result.output
