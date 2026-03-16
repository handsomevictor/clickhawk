"""Integration test fixtures — require a running ClickHouse instance."""
import pytest


@pytest.fixture(scope="session", autouse=True)
def ensure_demo_table(ch_client):
    """Create demo.events table if it does not exist, insert sample rows."""
    ch_client.command("CREATE DATABASE IF NOT EXISTS demo")
    ch_client.command("""
        CREATE TABLE IF NOT EXISTS demo.events
        (
            event_id   UUID                 DEFAULT generateUUIDv4(),
            user_id    UInt64,
            event_type LowCardinality(String),
            created_at DateTime64(3)        DEFAULT now64(),
            date       Date                 DEFAULT toDate(created_at)
        )
        ENGINE = MergeTree()
        PARTITION BY date
        ORDER BY (user_id, created_at)
    """)
    count = ch_client.command("SELECT count() FROM demo.events")
    if int(count) < 1000:
        ch_client.command("""
            INSERT INTO demo.events (user_id, event_type)
            SELECT rand() % 1000,
                   ['click','view','purchase','signup'][rand() % 4 + 1]
            FROM numbers(1000)
        """)
    yield
