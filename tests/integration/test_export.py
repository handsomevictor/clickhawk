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


def test_export_no_output_or_s3_fails(ch_client, ensure_demo_table):
    result = runner.invoke(app, ["export", "SELECT 1"])
    assert result.exit_code == 1


def test_export_s3_mocked(ch_client, ensure_demo_table, monkeypatch, tmp_path):
    """Verify S3 export path by monkeypatching boto3.client.put_object."""
    uploads = []

    class _FakeS3:
        def put_object(self, **kwargs):
            uploads.append(kwargs)

    import sys
    import types

    fake_boto3 = types.ModuleType("boto3")
    fake_boto3.client = lambda svc: _FakeS3()  # type: ignore[assignment]
    monkeypatch.setitem(sys.modules, "boto3", fake_boto3)

    result = runner.invoke(
        app,
        ["export", "SELECT count() FROM demo.events", "--s3", "s3://test-bucket/out.csv"],
    )
    assert result.exit_code == 0
    assert len(uploads) == 1
    assert uploads[0]["Bucket"] == "test-bucket"
    assert uploads[0]["Key"] == "out.csv"
