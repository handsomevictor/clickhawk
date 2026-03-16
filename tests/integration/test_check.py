"""Integration tests for `ch check`."""
import pytest
from typer.testing import CliRunner

from clickhawk.main import app

runner = CliRunner()
pytestmark = pytest.mark.integration


def test_check_nulls_exit_code(ch_client, ensure_demo_table):
    result = runner.invoke(
        app, ["check", "nulls", "events", "--database", "demo", "--sample", "100"]
    )
    assert result.exit_code == 0


def test_check_nulls_shows_columns(ch_client, ensure_demo_table):
    result = runner.invoke(
        app, ["check", "nulls", "events", "--database", "demo", "--sample", "100"]
    )
    assert "user_id" in result.output
    assert "event_type" in result.output


def test_check_nulls_nonexistent_table(ch_client, ensure_demo_table):
    result = runner.invoke(app, ["check", "nulls", "no_such_table_xyz"])
    assert result.exit_code == 1
    assert "not found" in result.output


def test_check_cardinality_exit_code(ch_client, ensure_demo_table):
    result = runner.invoke(
        app, ["check", "cardinality", "events", "--database", "demo", "--sample", "100"]
    )
    assert result.exit_code == 0


def test_check_cardinality_shows_columns(ch_client, ensure_demo_table):
    result = runner.invoke(
        app, ["check", "cardinality", "events", "--database", "demo", "--sample", "100"]
    )
    assert "user_id" in result.output
    assert "event_type" in result.output


def test_check_cardinality_nonexistent_table(ch_client, ensure_demo_table):
    result = runner.invoke(app, ["check", "cardinality", "no_such_table_xyz"])
    assert result.exit_code == 1
