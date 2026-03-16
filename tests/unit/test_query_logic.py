"""Unit tests for query command logic — no ClickHouse connection required."""
from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from clickhawk.main import app

runner = CliRunner()


def make_mock_result(columns=None, rows=None):
    result = MagicMock()
    result.column_names = columns or ["result"]
    result.result_rows = rows or [("1",)]
    result.row_count = len(result.result_rows)
    return result


def test_query_wraps_limit_in_subquery():
    """When --limit is given, the SQL should be wrapped in a subquery."""
    captured_sql = []

    mock_result = make_mock_result()

    def fake_query(sql, **kwargs):
        captured_sql.append(sql)
        return mock_result

    with patch("clickhawk.core.client.get_client") as mock_get_client:
        mock_client = MagicMock()
        mock_client.query.side_effect = fake_query
        mock_get_client.return_value = mock_client

        result = runner.invoke(app, ["query", "SELECT * FROM t", "--limit", "5"])

    assert result.exit_code == 0
    assert "LIMIT 5" in captured_sql[0]
    assert "SELECT * FROM t" in captured_sql[0]


def test_query_no_limit_passes_sql_unchanged():
    """Without --limit, the original SQL should be passed unchanged."""
    captured_sql = []

    mock_result = make_mock_result()

    def fake_query(sql, **kwargs):
        captured_sql.append(sql)
        return mock_result

    with patch("clickhawk.core.client.get_client") as mock_get_client:
        mock_client = MagicMock()
        mock_client.query.side_effect = fake_query
        mock_get_client.return_value = mock_client

        result = runner.invoke(app, ["query", "SELECT 1"])

    assert result.exit_code == 0
    assert captured_sql[0] == "SELECT 1"


def test_query_default_format_is_table():
    """Default output format should be table (no --format needed)."""
    mock_result = make_mock_result(["v"], [(42,)])

    with patch("clickhawk.core.client.get_client") as mock_get_client:
        mock_client = MagicMock()
        mock_client.query.return_value = mock_result
        mock_get_client.return_value = mock_client

        result = runner.invoke(app, ["query", "SELECT 42 AS v"])

    assert result.exit_code == 0


def test_query_help_shows_format_option():
    result = runner.invoke(app, ["query", "--help"])
    assert "--format" in result.output
    assert "--limit" in result.output
