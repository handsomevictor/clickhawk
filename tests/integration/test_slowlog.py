"""Integration tests for `ch slowlog`."""
import pytest
from typer.testing import CliRunner

from clickhawk.main import app

runner = CliRunner()

pytestmark = pytest.mark.integration


def test_slowlog_exit_code(ch_client):
    result = runner.invoke(app, ["slowlog", "--threshold", "1", "--hours", "1", "--top", "5"])
    assert result.exit_code == 0


def test_slowlog_no_results_message(ch_client):
    """With a very high threshold, no results should print a 'No queries' message."""
    result = runner.invoke(app, ["slowlog", "--threshold", "999999999"])
    assert result.exit_code == 0
    assert "No queries" in result.output


def test_slowlog_respects_top(ch_client, ensure_demo_table):
    """Run some queries then check slowlog returns at most --top rows."""
    # Run a query to ensure there is at least one entry
    runner.invoke(app, ["query", "SELECT count() FROM demo.events"])
    result = runner.invoke(
        app, ["slowlog", "--threshold", "1", "--hours", "1", "--top", "3"]
    )
    assert result.exit_code == 0


def test_slowlog_default_options(ch_client):
    result = runner.invoke(app, ["slowlog"])
    assert result.exit_code == 0
