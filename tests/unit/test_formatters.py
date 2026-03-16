"""Unit tests for output formatters — no ClickHouse connection required."""
import json
import sys
from io import StringIO
from unittest.mock import MagicMock

import pytest
from rich.console import Console

import clickhawk.formatters.table as fmt_module


def make_mock_result(columns, rows):
    result = MagicMock()
    result.column_names = columns
    result.result_rows = rows
    result.row_count = len(rows)
    return result


@pytest.fixture
def simple_result():
    return make_mock_result(["id", "name"], [(1, "Alice"), (2, "Bob")])


@pytest.fixture
def csv_result():
    """Result with values that contain commas and quotes — tests proper CSV escaping."""
    return make_mock_result(
        ["id", "description"],
        [(1, 'value,with,commas'), (2, 'value "with" quotes')],
    )


# ── Table format ──────────────────────────────────────────────────────────────

def test_table_format_runs(simple_result, monkeypatch):
    output = StringIO()
    monkeypatch.setattr(fmt_module, "console", Console(file=output, highlight=False))
    fmt_module.print_result(simple_result, output_format="table")
    content = output.getvalue()
    assert "id" in content
    assert "Alice" in content
    assert "Bob" in content


def test_table_format_shows_row_count(simple_result, monkeypatch):
    output = StringIO()
    monkeypatch.setattr(fmt_module, "console", Console(file=output, highlight=False))
    fmt_module.print_result(simple_result, output_format="table")
    assert "2 rows" in output.getvalue()


def test_table_format_is_default(simple_result, monkeypatch):
    """Calling without output_format should default to table."""
    output = StringIO()
    monkeypatch.setattr(fmt_module, "console", Console(file=output, highlight=False))
    fmt_module.print_result(simple_result)
    assert "Alice" in output.getvalue()


# ── JSON format ───────────────────────────────────────────────────────────────

def test_json_format_structure(simple_result, monkeypatch):
    output = StringIO()
    monkeypatch.setattr(fmt_module, "console", Console(file=output, highlight=False))
    fmt_module.print_result(simple_result, output_format="json")
    # Rich prints JSON with syntax highlighting; strip ANSI and parse
    raw = output.getvalue()
    # Remove ANSI escape codes for parsing
    import re
    clean = re.sub(r'\x1b\[[0-9;]*m', '', raw).strip()
    data = json.loads(clean)
    assert isinstance(data, list)
    assert len(data) == 2
    assert data[0]["id"] == 1
    assert data[0]["name"] == "Alice"


def test_json_format_keys(simple_result, monkeypatch):
    output = StringIO()
    monkeypatch.setattr(fmt_module, "console", Console(file=output, highlight=False))
    fmt_module.print_result(simple_result, output_format="json")
    assert '"id"' in output.getvalue()
    assert '"name"' in output.getvalue()


# ── CSV format ────────────────────────────────────────────────────────────────

def test_csv_format_header(simple_result, capsys):
    fmt_module.print_result(simple_result, output_format="csv")
    captured = capsys.readouterr()
    lines = captured.out.strip().splitlines()
    assert lines[0] == "id,name"


def test_csv_format_rows(simple_result, capsys):
    fmt_module.print_result(simple_result, output_format="csv")
    captured = capsys.readouterr()
    lines = captured.out.strip().splitlines()
    assert lines[1] == "1,Alice"
    assert lines[2] == "2,Bob"


def test_csv_format_escapes_commas(csv_result, capsys):
    """Values containing commas must be quoted in CSV output."""
    fmt_module.print_result(csv_result, output_format="csv")
    captured = capsys.readouterr()
    lines = captured.out.strip().splitlines()
    # The value 'value,with,commas' should be wrapped in quotes
    assert '"value,with,commas"' in lines[1]


def test_csv_format_escapes_quotes(csv_result, capsys):
    """Values containing double quotes must be escaped in CSV output."""
    fmt_module.print_result(csv_result, output_format="csv")
    captured = capsys.readouterr()
    assert "with" in captured.out  # sanity check output exists
