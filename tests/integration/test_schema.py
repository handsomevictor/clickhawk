"""Integration tests for `ch schema`."""
import pytest
from typer.testing import CliRunner

from clickhawk.main import app

runner = CliRunner()

pytestmark = pytest.mark.integration


def test_schema_tables_exit_code(ch_client, ensure_demo_table):
    result = runner.invoke(app, ["schema", "tables"])
    assert result.exit_code == 0


def test_schema_tables_shows_demo(ch_client, ensure_demo_table):
    result = runner.invoke(app, ["schema", "tables", "--database", "demo"])
    assert result.exit_code == 0
    assert "events" in result.output


def test_schema_tables_shows_engine(ch_client, ensure_demo_table):
    result = runner.invoke(app, ["schema", "tables", "--database", "demo"])
    assert "MergeTree" in result.output


def test_schema_show_exit_code(ch_client, ensure_demo_table):
    result = runner.invoke(app, ["schema", "show", "events", "--database", "demo"])
    assert result.exit_code == 0


def test_schema_show_columns(ch_client, ensure_demo_table):
    result = runner.invoke(app, ["schema", "show", "events", "--database", "demo"])
    assert "user_id" in result.output
    assert "event_type" in result.output
    assert "created_at" in result.output


def test_schema_show_nonexistent_table(ch_client):
    result = runner.invoke(app, ["schema", "show", "nonexistent_table_xyz"])
    assert result.exit_code == 1
    assert "not found" in result.output
