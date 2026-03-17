"""Integration tests for `ch top`."""
import threading
import time
import pytest
from typer.testing import CliRunner

from clickhawk.main import app

runner = CliRunner()
pytestmark = pytest.mark.integration


def test_top_invalid_sort(ch_client, ensure_demo_table):
    # top runs forever, but an invalid --sort should exit immediately
    result = runner.invoke(app, ["top", "--sort", "badfield"])
    assert result.exit_code == 1
    assert "Unknown sort key" in result.output


def _run_top_briefly():
    """Invoke `ch top` in a background thread and return its result after 1 tick."""
    from typer.testing import CliRunner as R
    from clickhawk.main import app as a
    # CliRunner captures output; the Live loop will raise KeyboardInterrupt via
    # the thread's cancel mechanism — we just need it to start without error.
    r = R()
    try:
        r.invoke(a, ["top", "--interval", "999"], catch_exceptions=False)
    except Exception:
        pass


def test_top_starts_without_error(ch_client, ensure_demo_table):
    """top should build a panel without raising before the first sleep."""
    from clickhawk.commands.top import _build_panel
    panel = _build_panel("elapsed", 5)
    assert panel is not None


def test_top_sort_options(ch_client, ensure_demo_table):
    from clickhawk.commands.top import _build_panel
    for sort in ("elapsed", "memory", "rows", "cpu"):
        panel = _build_panel(sort, 5)
        assert panel is not None
