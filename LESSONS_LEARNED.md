> 中文版: [LESSONS_LEARNED_CN.md](LESSONS_LEARNED_CN.md)

# Lessons Learned

Pitfalls encountered and lessons learned during ClickHawk development, for reference by future developers and contributors.

---

## 1. macOS Gatekeeper Blocking ClickHouse Binaries Installed via Homebrew Tap

**Problem:**
After installing via `brew tap clickhouse/clickhouse && brew install clickhouse`, executing `clickhouse` in the terminal produces an error stating "cannot be opened because the developer cannot be verified", or the binary is silently blocked by macOS.

**Root Cause:**
The official ClickHouse tap installs a pre-compiled binary. macOS Gatekeeper adds a quarantine attribute to binaries that have not been notarized by Apple, preventing them from running.

**Solution:**
```bash
xattr -d com.apple.quarantine $(which clickhouse)
```

Takes effect immediately without requiring a restart.

**Appendix: `brew services start clickhouse` Error**
The `clickhouse/clickhouse` tap installs a single-file binary without registering a Homebrew service (no launchd plist), so `brew services` cannot manage it.
The correct way to start it is to run it directly (a complete config.xml must be provided — see next item):
```bash
clickhouse server --config-file=$HOME/clickhouse-config.xml &
```

**`ch slowlog` / `ch profile` Reporting `Unknown table 'system.query_log'`**
When `config.xml` lacks a `<query_log>` configuration block, ClickHouse does not create the `system.query_log` table (lazy initialization), causing slowlog and profile commands to fail. Solution: add a `<query_log>` node to `config.xml` and set `<log_queries>1</log_queries>` in the default profile.

**A minimal working `config.xml` must include profiles/users/quotas**, otherwise the error `Settings profile 'default' not found` (exit 180) will occur. Path and port configuration alone is insufficient — ClickHouse looks for the `default` profile at startup:
```xml
<clickhouse>
    <path>...</path>
    <tmp_path>...</tmp_path>
    <tcp_port>9000</tcp_port>
    <http_port>8123</http_port>
    <listen_host>127.0.0.1</listen_host>
    <profiles>
        <default><max_memory_usage>10000000000</max_memory_usage></default>
    </profiles>
    <users>
        <default>
            <password></password>
            <networks><ip>::/0</ip></networks>
            <profile>default</profile>
            <quota>default</quota>
        </default>
    </users>
    <quotas>
        <default>
            <interval>
                <duration>3600</duration>
                <queries>0</queries><errors>0</errors>
                <result_rows>0</result_rows><read_rows>0</read_rows>
                <execution_time>0</execution_time>
            </interval>
        </default>
    </quotas>
</clickhouse>
```

---

## 2. Typer 0.12+: Options Cannot Follow Positional Arguments in Sub-Apps

**Problem:**
`ch query 'SELECT ...' --format json` reports `Missing argument 'SQL'`, while `ch query --format json 'SELECT ...'` works correctly.

**Root Cause:**
In Typer 0.12+ when using `add_typer()` for nested sub-apps, the sub-app's callback does not allow options (e.g., `--format`) to appear after positional arguments (e.g., SQL) by default — which is counter-intuitive.

**Solution:**
Add `context_settings={"allow_interspersed_args": True}` to each sub-app that combines positional arguments with options:
```python
app = typer.Typer(help="...", context_settings={"allow_interspersed_args": True})
```
Affected commands: `query`, `profile`, `slowlog`, `monitor`.

---

## 3. ClickHouse 26.x Crashes on macOS ARM64 Without a Config File

**Problem:**
Running `./clickhouse server &` on macOS Apple Silicon causes the server to crash immediately with exit code 91 and the error:

```
DB::Exception: Poco::Exception. Code: 1000, e.code() = 0, Null pointer
DB::Context::setClustersConfig ... CANNOT_LOAD_CONFIG
```

**Root Cause:**
ClickHouse 26.3 (and some 26.x versions) triggers a null pointer crash in `setClustersConfig` when starting in embedded config mode (without a `config.xml`) on macOS ARM64. This is a known ClickHouse bug, not a system or permissions issue.

**Solutions:**

Option 1 (recommended): Use Docker to avoid configuration issues entirely:
```bash
docker run -d --name clickhouse-local \
  -p 8123:8123 -p 9000:9000 \
  --ulimit nofile=262144:262144 \
  clickhouse/clickhouse-server
```

Option 2: Provide a minimal `config.xml` to work around the bug:
```bash
mkdir -p ~/clickhouse-data/{data,logs,tmp}
cat > config.xml << 'EOF'
<clickhouse>
    <path>clickhouse-data/data/</path>
    <tmp_path>clickhouse-data/tmp/</tmp_path>
    <tcp_port>9000</tcp_port>
    <http_port>8123</http_port>
    <listen_host>127.0.0.1</listen_host>
</clickhouse>
EOF
./clickhouse server --config-file=config.xml &
```

**Takeaway:**
The official single-file binary is unstable on macOS (especially newer versions). Docker is the preferred approach for local development. On Linux, single-file mode generally works without this issue.

---

## 4. Delayed Writes to `system.query_log`

**Problem:**
In the `ch profile` command, querying `system.query_log` immediately after executing a query returns empty results, causing performance statistics to not display.

**Root Cause:**
ClickHouse's `query_log` is not written synchronously. There is an asynchronous flush delay after a query completes (typically 100–500ms, depending on server load and configuration).

**Solution:**
After executing the target query, call `time.sleep(0.3)` to wait 300ms before querying `system.query_log`. This is a trade-off: too short a wait risks missing data, while too long a wait degrades user experience.

```python
client.query(sql, settings={"log_queries": 1, "query_id": query_id})
time.sleep(0.3)  # wait for async query_log flush
stats = client.query(f"SELECT ... FROM system.query_log WHERE query_id = '{query_id}'")
```

**Takeaway:**
ClickHouse system tables (`system.query_log`, `system.part_log`, etc.) are typically written asynchronously. Do not assume they are immediately consistent. If you encounter empty results, delayed writes should be the first thing to investigate.

---

## 5. Accessing `ProfileEvents` Fields

**Problem:**
The `ProfileEvents` field in `system.query_log` is of type `Map(String, UInt64)`. Accessing a specific key requires the `ProfileEvents['KeyName']` syntax, not dot notation.

**Correct usage:**
```sql
SELECT
    ProfileEvents['SelectedParts'] AS parts_selected,
    ProfileEvents['SelectedRanges'] AS ranges_selected
FROM system.query_log
WHERE query_id = '...'
```

**Commonly used ProfileEvents keys:**
- `SelectedParts` — number of parts hit by the query (fewer is better, indicating effective partition pruning)
- `SelectedRanges` — number of ranges hit
- `SelectedMarks` — number of marks hit (related to index granularity)
- `RealTimeMicroseconds` — actual elapsed time in microseconds
- `UserTimeMicroseconds` — user-space CPU time

---

## 6. Conflict Between Typer Sub-Commands and `callback`

**Problem:**
In Typer, if a sub-app has both `@app.callback(invoke_without_command=True)` and `@app.command()` sub-commands, command routing becomes confused.

**Context:**
The `schema` command has two sub-commands `show` and `tables`, while `query`, `profile`, and other commands run directly (no sub-commands).

**Solution:**
- Direct-execution commands (`query`, `profile`, `slowlog`, `monitor`): use `@app.callback(invoke_without_command=True)`
- Multi-sub-command commands (`schema`, `migrate`): define sub-commands using standard `@app.command()`, without a callback

This keeps routing clean, and both `ch query "..."` and `ch schema show table_name` work correctly.

---

## 7. Rich `Live` and `Console` Compatibility

**Problem:**
In `ch monitor`, calling `console.print()` outside the `Live` context causes output to intermix with Live-refreshed content, resulting in a garbled terminal display.

**Solution:**
All content that needs to be shown during a Live refresh should be delivered by returning a new `Table` object via `live.update(new_table)`. Do not call `console.print()` directly inside a `Live` context.

---

## 8. `clickhouse-connect` Result Set Row Access

**Problem:**
`clickhouse-connect` query results support multiple access patterns that are easy to confuse:
- `result.result_rows` — returns `List[tuple]`, iterable row by row
- `result.first_row` — returns the first row as a `tuple` (note: raises `IndexError` if the result is empty)
- `result.row_count` — returns the number of rows

**Takeaway:**
Always check `result.row_count > 0` before accessing `result.first_row`, otherwise the command will crash when no query record exists (e.g., when `profile` cannot find the corresponding record in `query_log`).

```python
if stats.row_count > 0:
    row = stats.first_row
    # safe access to row[0], row[1], ...
else:
    # handle gracefully
```

---

## 9. Pydantic Settings `env_prefix` Behavior

**Problem:**
The configuration class uses `env_prefix = "CH_"`, meaning all environment variables must be prefixed with `CH_` (`CH_HOST`, `CH_PORT`, etc.). The `.env` file can sometimes be missing the prefix or use incorrect casing.

**Takeaway:**
- Pydantic Settings v2 reads environment variables case-insensitively by default
- Variables in the `.env` file must include the prefix (`CH_HOST=localhost`), not the bare field name (`HOST=localhost`)
- It is recommended to list all variables in `.env.example` to prevent users from missing any

---

## 10. Wheel Package Path Configuration in `pyproject.toml`

**Problem:**
`pyproject.toml` had `[tool.hatch.build.targets.wheel]` configured with `packages = ["src/clickhawk"]`, but the actual code structure places the code in `clickhawk/` (not `src/clickhawk/`), causing the package to not be found after `pip install`.

**Solution:**
Ensure the package path matches the actual directory structure. If the code is in `clickhawk/` (a same-name package at the project root), the configuration should be:
```toml
[tool.hatch.build.targets.wheel]
packages = ["clickhawk"]
```

**Takeaway:**
Before publishing to PyPI, always install with `pip install -e .` and run `ch --help` to verify that commands are registered correctly — do not rely solely on checking `pyproject.toml` syntax.
