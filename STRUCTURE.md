> 中文版: [STRUCTURE_CN.md](STRUCTURE_CN.md)

# Project Structure

```
clickhawk/
├── clickhawk/                    # Main package directory
│   ├── __init__.py
│   ├── main.py                   # CLI entry point: registers all sub-commands, defines ch health
│   │
│   ├── core/                     # Core infrastructure
│   │   ├── __init__.py
│   │   ├── client.py             # ClickHouse connection management (singleton pattern)
│   │   └── config.py             # Configuration management (Pydantic Settings, reads .env / env vars)
│   │
│   ├── commands/                 # One file per CLI command
│   │   ├── __init__.py
│   │   ├── query.py              # ch query — SQL execution with table/json/csv output
│   │   ├── profile.py            # ch profile — query performance analysis (system.query_log)
│   │   ├── slowlog.py            # ch slowlog — slow query history ranking
│   │   ├── schema.py             # ch schema show/tables — table schema and table listing
│   │   ├── monitor.py            # ch monitor — real-time query monitoring (Live refresh)
│   │   └── migrate.py            # ch migrate — schema migrations (v0.2 placeholder)
│   │
│   ├── formatters/               # Output formatters
│   │   ├── __init__.py
│   │   ├── table.py              # Rich table / JSON / CSV formatted output
│   │   └── tree.py               # EXPLAIN tree output (planned for v0.2)
│   │
│   └── utils/                    # Utility functions
│       ├── __init__.py
│       └── sql.py                # SQL utilities: query normalization, parameter binding, etc. (planned for v0.2)
│
├── tests/                        # Test suite
│   ├── __init__.py
│   ├── unit/                     # Unit tests (no ClickHouse connection required)
│   │   └── __init__.py
│   └── integration/              # Integration tests (requires a live ClickHouse instance)
│       └── __init__.py
│
├── examples/                     # Usage examples
│   ├── BASIC_QUERY.md            # Basic query examples
│   ├── BASIC_QUERY_CN.md         # Basic query examples (Chinese)
│   ├── PROFILING.md              # Performance profiling examples
│   ├── PROFILING_CN.md           # Performance profiling examples (Chinese)
│   ├── SCHEMA_EXPLORATION.md     # Schema exploration examples
│   ├── SCHEMA_EXPLORATION_CN.md  # Schema exploration examples (Chinese)
│   ├── MONITORING.md             # Real-time monitoring examples
│   └── MONITORING_CN.md          # Real-time monitoring examples (Chinese)
│
├── pyproject.toml                # Project metadata, dependencies, build configuration
├── .env.example                  # Environment variable configuration template
├── .gitignore
├── .gitattributes
├── README.md                     # Main project documentation (English)
├── README_CN.md                  # Main project documentation (Chinese)
├── CHANGELOG.md                  # Version history (English)
├── CHANGELOG_CN.md               # Version history (Chinese)
├── TUTORIAL.md                   # Local setup and feature verification guide (English)
├── TUTORIAL_CN.md                # Local setup and feature verification guide (Chinese)
├── STRUCTURE.md                  # This file: project structure reference (English)
├── STRUCTURE_CN.md               # Project structure reference (Chinese)
├── LESSONS_LEARNED.md            # Development and debugging lessons learned (English)
└── LESSONS_LEARNED_CN.md         # Development and debugging lessons learned (Chinese)
```

---

## Module Responsibilities

### `main.py` — Application Entry Point

Registers all sub-command apps and defines the `ch health` command (kept here rather than in a dedicated command file due to its simplicity). The Typer app's `name="ch"` corresponds to the terminal command entry point.

```python
app = typer.Typer(name="ch", ...)
app.add_typer(query.app,   name="query")
app.add_typer(profile.app, name="profile")
# ...
```

### `core/config.py` — Configuration Management

Built on Pydantic Settings v2, reads environment variables via `env_prefix="CH_"`. Supports `.env` files (via `python-dotenv`) and direct environment variables, with environment variables taking priority over `.env` files.

```python
class ClickHouseConfig(BaseSettings):
    host: str = "localhost"
    port: int = 8123
    # ...
    model_config = {"env_prefix": "CH_", "env_file": ".env"}
```

### `core/client.py` — Connection Management

Uses a global singleton pattern (module-level `_client` variable) to avoid re-establishing an HTTP connection on every command invocation. `get_client()` is the unified entry point for all commands to obtain a ClickHouse client.

### `commands/` — Command Modules

Each command file defines a `app = typer.Typer()`, in one of two modes:
- **Direct-execution** (`query`, `profile`, `slowlog`, `monitor`): uses `@app.callback(invoke_without_command=True)` to define the main function, invoked directly via `ch query "..."`
- **Multi-sub-command** (`schema`, `migrate`): defines multiple sub-commands using `@app.command()`, routing `ch schema show` and `ch schema tables` separately

### `formatters/table.py` — Output Formatting

`print_result(result, format)` handles three output formats uniformly:
- `table`: Rich colorized table (default)
- `json`: JSON array output via `console.print_json()` (with syntax highlighting)
- `csv`: Standard CSV, pipeable (`ch query "..." --format csv > output.csv`)

---

## Data Flow

```
User input: ch profile "SELECT uniq(user_id) FROM events"
         │
         ▼
    main.py (Typer app)
         │  routes to profile command
         ▼
    commands/profile.py
         │  1. generate query_id
         │  2. call get_client()
         │  3. execute SQL (with log_queries=1 and query_id)
         │  4. sleep(0.3) to wait for query_log write
         │  5. query system.query_log for performance stats
         │  6. build Rich Table and output
         ▼
    core/client.py → clickhouse-connect → ClickHouse HTTP API
         │
         ▼
    Terminal output (Rich colorized table)
```

---

## Dependencies

```
typer              — CLI framework, argument parsing, help generation
rich               — Terminal UI: tables, colors, Live refresh, JSON highlighting
clickhouse-connect — ClickHouse HTTP client (officially maintained)
pydantic v2        — Data validation and configuration type definitions
pydantic-settings  — Read configuration from environment variables / files
python-dotenv      — .env file parsing
```

**Development dependencies:**
```
pytest             — Testing framework
pytest-asyncio     — Async test support
ruff               — Fast Python linter (replaces flake8 + isort)
mypy               — Static type checking
```
