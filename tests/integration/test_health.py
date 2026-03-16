"""Integration tests for `ch health`."""
import pytest
from typer.testing import CliRunner

from clickhawk.main import app

runner = CliRunner()

pytestmark = pytest.mark.integration


def test_health_exit_code(ch_client):
    result = runner.invoke(app, ["health"])
    assert result.exit_code == 0


def test_health_shows_version(ch_client):
    result = runner.invoke(app, ["health"])
    assert "ClickHouse" in result.output


def test_health_shows_uptime(ch_client):
    result = runner.invoke(app, ["health"])
    assert "Uptime" in result.output


def test_health_shows_databases(ch_client):
    result = runner.invoke(app, ["health"])
    assert "Databases" in result.output


def test_health_shows_tables(ch_client):
    result = runner.invoke(app, ["health"])
    assert "Tables" in result.output
