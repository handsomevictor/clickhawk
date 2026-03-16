"""Integration tests for `ch export`."""
import json
import os
import tempfile

import pytest
from typer.testing import CliRunner

from clickhawk.main import app

runner = CliRunner()
pytestmark = pytest.mark.integration


def test_export_csv_exit_code(ch_client, ensure_demo_table, tmp_path):
    out = str(tmp_path / "out.csv")
    result = runner.invoke(
        app, ["export", "SELECT count() FROM demo.events", "--output", out]
    )
    assert result.exit_code == 0
    assert os.path.exists(out)


def test_export_csv_has_header(ch_client, ensure_demo_table, tmp_path):
    out = str(tmp_path / "out.csv")
    runner.invoke(
        app,
        ["export", "SELECT event_type, count() AS cnt FROM demo.events GROUP BY event_type",
         "--output", out],
    )
    with open(out) as f:
        header = f.readline()
    assert "event_type" in header


def test_export_json_exit_code(ch_client, ensure_demo_table, tmp_path):
    out = str(tmp_path / "out.json")
    result = runner.invoke(
        app,
        ["export", "SELECT event_type, count() AS cnt FROM demo.events GROUP BY event_type",
         "--output", out],
    )
    assert result.exit_code == 0
    with open(out) as f:
        data = json.load(f)
    assert isinstance(data, list)
    assert len(data) > 0


def test_export_format_flag(ch_client, ensure_demo_table, tmp_path):
    out = str(tmp_path / "result")
    result = runner.invoke(
        app,
        ["export", "SELECT count() FROM demo.events", "--output", out, "--format", "json"],
    )
    assert result.exit_code == 0
    assert os.path.exists(out)


def test_export_with_limit(ch_client, ensure_demo_table, tmp_path):
    out = str(tmp_path / "out.csv")
    result = runner.invoke(
        app,
        ["export", "SELECT * FROM demo.events", "--output", out, "--limit", "5"],
    )
    assert result.exit_code == 0
