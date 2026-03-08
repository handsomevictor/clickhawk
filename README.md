# 🦅 ClickHawk

> The ClickHouse CLI for data engineers — query, profile, debug, migrate.

## Installation

```bash
pip install clickhawk
```

## Quickstart

```bash
# Copy and edit connection config
cp .env.example .env

# Check connection
ch health

# Run a query
ch query "SELECT version()"

# Profile a slow query
ch profile "SELECT uniq(user_id) FROM events"

# Show slow queries from the last 24h
ch slowlog --top 20

# Watch live running queries
ch monitor
```

## Commands

| Command | Description |
|---------|-------------|
| `ch query <sql>` | Execute SQL with rich output |
| `ch profile <sql>` | Profile query performance |
| `ch slowlog` | Inspect slow query history |
| `ch schema show <table>` | Show table schema |
| `ch schema tables` | List all tables |
| `ch monitor` | Live query dashboard |
| `ch health` | Cluster health check |

## License

MIT
