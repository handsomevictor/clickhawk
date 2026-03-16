"""Unit tests for ClickHouseConfig — no ClickHouse connection required."""
import pytest
from clickhawk.core.config import ClickHouseConfig


def test_default_values():
    cfg = ClickHouseConfig()
    assert cfg.host == "localhost"
    assert cfg.port == 8123
    assert cfg.user == "default"
    assert cfg.password == ""
    assert cfg.database == "default"
    assert cfg.secure is False


def test_env_prefix_host(monkeypatch):
    monkeypatch.setenv("CH_HOST", "myhost.internal")
    cfg = ClickHouseConfig()
    assert cfg.host == "myhost.internal"


def test_env_prefix_port(monkeypatch):
    monkeypatch.setenv("CH_PORT", "9440")
    cfg = ClickHouseConfig()
    assert cfg.port == 9440


def test_env_prefix_secure(monkeypatch):
    monkeypatch.setenv("CH_SECURE", "true")
    cfg = ClickHouseConfig()
    assert cfg.secure is True


def test_env_prefix_database(monkeypatch):
    monkeypatch.setenv("CH_DATABASE", "analytics")
    cfg = ClickHouseConfig()
    assert cfg.database == "analytics"


def test_env_prefix_credentials(monkeypatch):
    monkeypatch.setenv("CH_USER", "analyst")
    monkeypatch.setenv("CH_PASSWORD", "secret")
    cfg = ClickHouseConfig()
    assert cfg.user == "analyst"
    assert cfg.password == "secret"
