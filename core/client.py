import clickhouse_connect
from clickhouse_connect.driver.client import Client
from clickhawk.core.config import ClickHouseConfig

_client: Client | None = None


def get_client() -> Client:
    global _client
    if _client is None:
        cfg = ClickHouseConfig()
        _client = clickhouse_connect.get_client(
            host=cfg.host,
            port=cfg.port,
            username=cfg.user,
            password=cfg.password,
            database=cfg.database,
            secure=cfg.secure,
        )
    return _client
