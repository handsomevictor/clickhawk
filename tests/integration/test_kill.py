"""Integration tests for `ch kill`."""
import pytest
from typer.testing import CliRunner

from clickhawk.main import app

runner = CliRunner()
pytestmark = pytest.mark.integration


def test_kill_no_args_exits_nonzero(ch_client, ensure_demo_table):
    result = runner.invoke(app, ["kill"])
    assert result.exit_code == 1


def test_kill_nonexistent_query_id(ch_client, ensure_demo_table):
    # A random query_id prefix that almost certainly doesn't exist
    result = runner.invoke(app, ["kill", "00000000", "--yes"])
    assert result.exit_code == 0
    assert "No matching" in result.output


def test_kill_nonexistent_user(ch_client, ensure_demo_table):
    result = runner.invoke(app, ["kill", "--user", "no_such_user_xyz", "--yes"])
    assert result.exit_code == 0
    assert "No matching" in result.output
