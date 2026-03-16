"""Integration tests for `ch query`."""
import json
import pytest
from typer.testing import CliRunner

from clickhawk.main import app

runner = CliRunner()

pytestmark = pytest.mark.integration


def test_query_table_format(ch_client, ensure_demo_table):
    result = runner.invoke(app, ["query", "SELECT count() AS cnt FROM demo.events"])
    assert result.exit_code == 0
    assert "cnt" in result.output


def test_query_json_format(ch_client, ensure_demo_table):
    result = runner.invoke(
        app,
        ["query", "--format", "json", "SELECT event_type FROM demo.events LIMIT 1"],
    )
    assert result.exit_code == 0
    assert "event_type" in result.output


def test_query_csv_format(ch_client, ensure_demo_table):
    result = runner.invoke(
        app,
        ["query", "--format", "csv", "SELECT event_type FROM demo.events LIMIT 3"],
    )
    assert result.exit_code == 0
    lines = result.output.strip().splitlines()
    assert lines[0] == "event_type"
    assert len(lines) >= 2


def test_query_with_limit(ch_client, ensure_demo_table):
    result = runner.invoke(
        app,
        ["query", "SELECT * FROM demo.events", "--limit", "5"],
    )
    assert result.exit_code == 0
    assert "5 rows" in result.output


def test_query_format_after_sql(ch_client, ensure_demo_table):
    """--format placed after SQL should work (allow_interspersed_args fix)."""
    result = runner.invoke(
        app,
        ["query", "SELECT count() AS cnt FROM demo.events", "--format", "json"],
    )
    assert result.exit_code == 0
    assert "cnt" in result.output


def test_query_invalid_sql(ch_client):
    result = runner.invoke(app, ["query", "SELECT FROM nowhere_table_xyz"])
    assert result.exit_code != 0
