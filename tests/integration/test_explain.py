"""Integration tests for `ch explain`."""
import pytest
from typer.testing import CliRunner

from clickhawk.main import app

runner = CliRunner()
pytestmark = pytest.mark.integration


def test_explain_exit_code(ch_client, ensure_demo_table):
    result = runner.invoke(app, ["explain", "SELECT count() FROM demo.events"])
    assert result.exit_code == 0


def test_explain_shows_tree(ch_client, ensure_demo_table):
    result = runner.invoke(app, ["explain", "SELECT count() FROM demo.events"])
    assert result.exit_code == 0
    # EXPLAIN output always contains at least the root heading
    assert "EXPLAIN" in result.output


def test_explain_plan_kind(ch_client, ensure_demo_table):
    result = runner.invoke(
        app, ["explain", "SELECT count() FROM demo.events", "--kind", "plan"]
    )
    assert result.exit_code == 0


def test_explain_syntax_kind(ch_client, ensure_demo_table):
    result = runner.invoke(
        app, ["explain", "SELECT count() FROM demo.events", "--kind", "syntax"]
    )
    assert result.exit_code == 0
    assert "EXPLAIN" in result.output
