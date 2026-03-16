import pytest


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "integration: requires a running ClickHouse instance (skipped if unavailable)",
    )


@pytest.fixture(scope="session")
def ch_client():
    """Session-scoped ClickHouse client. Skips if ClickHouse is not reachable."""
    try:
        from clickhawk.core.client import get_client
        client = get_client()
        client.command("SELECT 1")
        return client
    except Exception as e:
        pytest.skip(f"ClickHouse not available: {e}")
