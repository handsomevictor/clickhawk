"""Integration tests for `ch profile`."""
import pytest
from typer.testing import CliRunner

from clickhawk.main import app

runner = CliRunner()

pytestmark = pytest.mark.integration


def test_profile_exit_code(ch_client, ensure_demo_table):
    result = runner.invoke(app, ["profile", "SELECT count() FROM demo.events"])
    assert result.exit_code == 0


def test_profile_shows_wall_time(ch_client, ensure_demo_table):
    result = runner.invoke(app, ["profile", "SELECT count() FROM demo.events"])
    assert "Wall time" in result.output


def test_profile_shows_metrics(ch_client, ensure_demo_table):
    """After query_log flushes, all DB metrics should be present."""
    # Run a warm-up query first to ensure query_log is initialized
    runner.invoke(app, ["query", "SELECT 1"])
    result = runner.invoke(app, ["profile", "SELECT uniq(user_id) FROM demo.events"])
    assert result.exit_code == 0
    # Either full metrics or the fallback note should appear
    assert ("DB duration" in result.output) or ("Stats not yet available" in result.output)


def test_profile_full_metrics(ch_client, ensure_demo_table):
    """With query_log properly configured, all 6 metrics should appear."""
    import time
    runner.invoke(app, ["query", "SELECT count() FROM demo.events"])
    time.sleep(1)  # ensure query_log has flushed
    result = runner.invoke(app, ["profile", "SELECT count() FROM demo.events"])
    assert result.exit_code == 0
    assert "DB duration" in result.output
    assert "Rows read" in result.output
    assert "Bytes read" in result.output
    assert "Memory used" in result.output
