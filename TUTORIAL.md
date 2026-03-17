> 中文版: [TUTORIAL_CN.md](TUTORIAL_CN.md)

# Local Quick-Start Tutorial

This tutorial walks you through installing ClickHouse locally, creating a test database, and verifying every ClickHawk feature.

**Estimated time:** 15 minutes
**Supported platforms:** macOS · Linux · Windows

> ClickHawk is pure Python and connects to ClickHouse over HTTP — it runs on **macOS, Linux, and Windows** with no platform-specific dependencies. See [README](README.md) for details.

---

## Step 1: Install and Start ClickHouse

Choose the section that matches your operating system. **Each section covers both installation and startup.**

---

### macOS (Recommended: Homebrew + manual start)

> **Why not `./clickhouse server` directly?**
> ClickHouse 26.x has a known bug on macOS ARM64 where it crashes immediately (exit 91) when started without a config file.
>
> **Why not `brew services start clickhouse`?**
> The `brew tap clickhouse/clickhouse` tap installs a single-file binary with no launchd service registered — `brew services` cannot manage it.
>
> The correct approach is to provide a complete `config.xml` and start it manually, as shown below.

**1. Install**

```bash
# You must add the official tap first — bare `brew install clickhouse` returns "No available formula"
brew tap clickhouse/clickhouse
brew install clickhouse
```

**2. Remove macOS Gatekeeper quarantine**

After installation, the first run is blocked by macOS with "cannot verify developer". Remove the quarantine attribute:

```bash
xattr -d com.apple.quarantine $(which clickhouse)
```

**3. Create a complete config file and start**

> **Why does config.xml need to be complete?**
> - Paths and ports only → exit 180 (`Settings profile 'default' not found`): `<profiles>`, `<users>`, and `<quotas>` are required
> - Missing `<query_log>` → `ch profile` and `ch slowlog` report `Unknown table 'system.query_log'`
> - Missing `<log_queries>1</log_queries>` → the query_log table exists but contains no data

```bash
mkdir -p ~/clickhouse-data/{data,tmp}

cat > ~/clickhouse-config.xml << 'EOF'
<clickhouse>
    <path>/Users/YOUR_USERNAME/clickhouse-data/data/</path>
    <tmp_path>/Users/YOUR_USERNAME/clickhouse-data/tmp/</tmp_path>
    <tcp_port>9000</tcp_port>
    <http_port>8123</http_port>
    <listen_host>127.0.0.1</listen_host>

    <query_log>
        <database>system</database>
        <table>query_log</table>
        <flush_interval_milliseconds>200</flush_interval_milliseconds>
    </query_log>

    <profiles>
        <default>
            <max_memory_usage>10000000000</max_memory_usage>
            <log_queries>1</log_queries>
        </default>
    </profiles>

    <users>
        <default>
            <password></password>
            <networks>
                <ip>::/0</ip>
            </networks>
            <profile>default</profile>
            <quota>default</quota>
        </default>
    </users>

    <quotas>
        <default>
            <interval>
                <duration>3600</duration>
                <queries>0</queries>
                <errors>0</errors>
                <result_rows>0</result_rows>
                <read_rows>0</read_rows>
                <execution_time>0</execution_time>
            </interval>
        </default>
    </quotas>
</clickhouse>
EOF

# Replace YOUR_USERNAME with your actual macOS username (run: echo $USER)
sed -i '' "s/YOUR_USERNAME/$(whoami)/g" ~/clickhouse-config.xml

clickhouse server --config-file=$HOME/clickhouse-config.xml > /tmp/clickhouse.log 2>&1 &
```

**4. Verify startup**

```bash
sleep 2
curl http://localhost:8123/ping   # Returns: Ok.
```

If nothing is returned, check the log:

```bash
tail -20 /tmp/clickhouse.log
```

**5. Connect a client**

```bash
clickhouse client
```

**6. Stop the server**

```bash
pkill -f "clickhouse server"
```

---

### macOS (Alternative: Docker)

If you prefer to skip config file management, Docker is the easiest option:

```bash
docker run -d --name clickhouse-local -p 8123:8123 -p 9000:9000 clickhouse/clickhouse-server
```

Verify:

```bash
curl http://localhost:8123/ping   # Returns: Ok.
```

Connect a client:

```bash
docker exec -it clickhouse-local clickhouse-client
```

Stop:

```bash
docker stop clickhouse-local
```

---

### Linux (Ubuntu / Debian)

```bash
# Install via apt
sudo apt-get install -y apt-transport-https ca-certificates curl gnupg
curl -fsSL 'https://packages.clickhouse.com/rpm/lts/repodata/repomd.xml.key' \
  | sudo gpg --dearmor -o /usr/share/keyrings/clickhouse-keyring.gpg
echo "deb [signed-by=/usr/share/keyrings/clickhouse-keyring.gpg] https://packages.clickhouse.com/deb stable main" \
  | sudo tee /etc/apt/sources.list.d/clickhouse.list
sudo apt-get update
sudo apt-get install -y clickhouse-server clickhouse-client

# Start
sudo service clickhouse-server start

# Verify
curl http://localhost:8123/ping

# Connect
clickhouse-client
```

> You can also use the official single-file binary on Linux: `curl https://clickhouse.com/ | sh`, then `./clickhouse server &`. The macOS ARM64 config bug does not affect Linux.

---

### Windows (WSL2, recommended)

Run the Linux installation commands above inside a WSL2 (Ubuntu) terminal — the experience is identical to native Linux.

**Or use Docker (single command):**

```powershell
docker run -d --name clickhouse-local -p 8123:8123 -p 9000:9000 clickhouse/clickhouse-server
```

---

## Step 2: Create a Test Database

Inside the ClickHouse client, run the following SQL:

```sql
-- Create a database
CREATE DATABASE demo;

-- Create an events table (with partition key and sort key, simulating a real production table)
CREATE TABLE demo.events
(
    event_id   UUID                 DEFAULT generateUUIDv4(),
    user_id    UInt64,
    event_type LowCardinality(String),
    created_at DateTime64(3)        DEFAULT now64(),
    date       Date                 DEFAULT toDate(created_at)
)
ENGINE = MergeTree()
PARTITION BY date
ORDER BY (user_id, created_at);

-- Insert 100,000 random test rows
INSERT INTO demo.events (user_id, event_type)
SELECT
    rand() % 10000,
    ['click', 'view', 'purchase', 'signup'][rand() % 4 + 1]
FROM numbers(100000);

-- Verify the insert succeeded
SELECT count() FROM demo.events;
-- Should return 100000
```

Type `exit;` or press `Ctrl+D` to leave the client.

---

## Step 3: Install ClickHawk

```bash
cd /path/to/clickhawk

# Development install (changes take effect immediately)
pip install -e ".[dev]"

# Verify
ch --help
```

See [README](README.md) for the full command reference.

---

## Step 4: Configure the Connection

```bash
# Copy the config template, then set CH_DATABASE=demo to match the test database from Step 2
cp .env.example .env
```

Then edit `.env` and set:
```env
CH_DATABASE=demo
```

> **Important:** The test database created in Step 2 is named `demo`. If `CH_DATABASE` stays as `default`, you must prefix all table names with `demo.` (e.g., `demo.events`). Setting `CH_DATABASE=demo` lets you omit the prefix.

Or export environment variables directly:

```bash
export CH_HOST=localhost
export CH_PORT=8123
export CH_USER=default
export CH_PASSWORD=
export CH_DATABASE=demo   # set to the demo database created in Step 2
```

---

## Step 5: Verify All Features

> **Tip:** When copying commands from this document, paste and run them one at a time. Wrap SQL in single quotes `'` to avoid quote corruption during copy-paste.

---

### `ch health` — Health check

```bash
ch health
```

**Expected output:**
```
✓  ClickHouse  26.3.x.x
    Uptime   : 42 minutes
    Databases: 3
    Tables   : 13
```

---

### `ch query` — Execute queries

**Table format (default):**

```bash
ch query 'SELECT event_type, count() AS cnt FROM demo.events GROUP BY event_type ORDER BY cnt DESC'
```

**Expected output:**
```
┌────────────┬─────┐
│ event_type │ cnt │
├────────────┼─────┤
│ view       │ 254 │
│ click      │ 251 │
│ signup     │ 249 │
│ purchase   │ 246 │
└────────────┴─────┘
4 rows
```

**JSON format:**

```bash
ch query 'SELECT event_type, count() AS cnt FROM demo.events GROUP BY event_type' --format json
```

**Expected output:**
```json
[
  {"event_type": "view", "cnt": 254},
  {"event_type": "click", "cnt": 251},
  {"event_type": "signup", "cnt": 249},
  {"event_type": "purchase", "cnt": 246}
]
```

**CSV format:**

```bash
ch query 'SELECT user_id, count() AS cnt FROM demo.events GROUP BY user_id ORDER BY cnt DESC LIMIT 5' --format csv
```

**Expected output:**
```
user_id,cnt
412,7
88,6
531,6
774,6
203,5
```

**Limit rows:**

```bash
ch query 'SELECT * FROM demo.events' --limit 3
```

**Expected output:**
```
┌──────────────────────────────────────┬─────────┬────────────┬────────────────────────────┬────────────┐
│ event_id                             │ user_id │ event_type │ created_at                 │ date       │
├──────────────────────────────────────┼─────────┼────────────┼────────────────────────────┼────────────┤
│ 3e1a2b4c-...                         │ 412     │ click      │ 2026-03-17 10:23:01.123    │ 2026-03-17 │
│ 7f8d9e0a-...                         │ 88      │ view       │ 2026-03-17 10:23:01.124    │ 2026-03-17 │
│ 1c2d3e4f-...                         │ 531     │ purchase   │ 2026-03-17 10:23:01.125    │ 2026-03-17 │
└──────────────────────────────────────┴─────────┴────────────┴────────────────────────────┴────────────┘
3 rows
```

---

### `ch profile` — Query performance analysis

> **Note:** `ch profile` depends on `system.query_log`. Run a plain query first to initialize the table, then profile.

```bash
# Step 1: warm-up query (initializes query_log)
ch query 'SELECT count() FROM demo.events'

# Step 2: wait for flush
sleep 1

# Step 3: profile
ch profile 'SELECT uniq(user_id) FROM demo.events WHERE date = today()'
```

**Expected output:**
```
🔍 Query Profile
┌──────────────────┬──────────┐
│ Metric           │ Value    │
├──────────────────┼──────────┤
│ Wall time        │ 0.043s   │
│ DB duration      │ 12 ms    │
│ Rows read        │ 1,000    │
│ Bytes read       │ 0.02 MB  │
│ Memory used      │ 0.10 MB  │
│ Parts selected   │ 1        │
│ Ranges selected  │ 4        │
└──────────────────┴──────────┘
```

> Values will be small with local data — that is expected. See [examples/PROFILING.md](examples/PROFILING.md) for metric explanations.

---

### `ch slowlog` — Slow query history

```bash
ch slowlog --threshold 1 --hours 1 --top 10
```

**Expected output:**
```
🐢 Slow Queries  (last 1h  ·  ≥1ms  ·  top 10)
┌──────────┬─────────────┬───────────┬───────────┬──────────┬──────────┬──────────────────────────────────────────────┐
│ Time     │ Duration(ms)│ Rows Read │ Bytes Read│ Memory   │ User     │ Query                                        │
├──────────┼─────────────┼───────────┼───────────┼──────────┼──────────┼──────────────────────────────────────────────┤
│ 10:24:01 │ 43          │ 1,000     │ 19.5 KiB  │ 98.3 KiB │ default  │ SELECT uniq(user_id) FROM demo.events ...    │
│ 10:23:55 │ 12          │ 1,000     │ 4.0 KiB   │ 0 B      │ default  │ SELECT count() FROM demo.events              │
└──────────┴─────────────┴───────────┴───────────┴──────────┴──────────┴──────────────────────────────────────────────┘
2 queries found
```

---

### `ch schema` — Schema exploration

```bash
ch schema tables --database demo
```

**Expected output:**
```
           Tables
┌──────────┬────────┬───────────┬──────────┬────────┐
│ Database │ Table  │ Engine    │ Size     │ Rows   │
├──────────┼────────┼───────────┼──────────┼────────┤
│ demo     │ events │ MergeTree │ 57.00 KiB│ 1.00 K │
└──────────┴────────┴───────────┴──────────┴────────┘
1 tables
```

```bash
ch schema show events --database demo
```

**Expected output:**
```
              Schema: events
┌────────────┬──────────────────────────┬────────────────────┬─────────┐
│ Column     │ Type                     │ Default            │ Comment │
├────────────┼──────────────────────────┼────────────────────┼─────────┤
│ event_id   │ UUID                     │ generateUUIDv4()   │         │
│ user_id    │ UInt64                   │                    │         │
│ event_type │ LowCardinality(String)   │                    │         │
│ created_at │ DateTime64(3)            │ now64()            │         │
│ date       │ Date                     │ toDate(created_at) │         │
└────────────┴──────────────────────────┴────────────────────┴─────────┘
```

---

### `ch monitor` — Live query monitoring

In **terminal 1**, start the monitor:

```bash
ch monitor
```

In **terminal 2**, run a slow query to give the monitor something to show:

```bash
# macOS / Linux (Homebrew)
clickhouse client --query 'SELECT sleep(3)'

# Docker
docker exec -it clickhouse-local clickhouse-client --query 'SELECT sleep(3)'
```

> **Note:** ClickHouse limits `sleep()` to 3 seconds maximum. `SELECT sleep(10)` raises `TOO_SLOW`.

**Expected output in terminal 1:**
```
⚡ Live Queries  (Ctrl+C to exit)
┌──────────┬─────────┬───────────┬───────────┬──────────┬──────────────────────┐
│ ID       │ User    │ Elapsed(s)│ Rows Read │ Memory   │ Query                │
├──────────┼─────────┼───────────┼───────────┼──────────┼──────────────────────┤
│ 3a7f1c2b │ default │ 1.4       │ 0         │ 0 B      │ SELECT sleep(3)      │  ← yellow (>5s turns red)
└──────────┴─────────┴───────────┴───────────┴──────────┴──────────────────────┘
```

Press `Ctrl+C` to exit. See [examples/MONITORING.md](examples/MONITORING.md) for more scenarios.

---

### `ch explain` — Colorized EXPLAIN plan (v0.2+)

```bash
ch explain 'SELECT uniq(user_id) FROM demo.events WHERE date = today()'
```

**Expected output:**
```
EXPLAIN PLAN
└── Expression
    └── Aggregating
        └── Expression
            └── Filter
                └── ReadFromMergeTree
                    └── indexes: ...
```

Node types are color-coded: `ReadFromMergeTree` in cyan, `Filter` in yellow, `Aggregating` in magenta.

---

### `ch check` — Data quality checks (v0.2+)

```bash
ch check nulls events --database demo --sample 100000
```

**Expected output:**
```
Null Check: events  (n=1,000)
┌────────────┬──────────────────────────┬─────────────┬────────┬───────────┐
│ Column     │ Type                     │ Null Count  │ Null % │ Nullable? │
├────────────┼──────────────────────────┼─────────────┼────────┼───────────┤
│ event_id   │ UUID                     │ 0           │ 0.0%   │ no        │
│ user_id    │ UInt64                   │ 0           │ 0.0%   │ no        │
│ event_type │ LowCardinality(String)   │ 0           │ 0.0%   │ no        │
│ created_at │ DateTime64(3)            │ 0           │ 0.0%   │ no        │
│ date       │ Date                     │ 0           │ 0.0%   │ no        │
└────────────┴──────────────────────────┴─────────────┴────────┴───────────┘
```

```bash
ch check cardinality events --database demo --sample 100000
```

**Expected output:**
```
Cardinality: events  (n=1,000)
┌────────────┬──────────────────────────┬───────────────┬──────────────┬────────────────────────────────────┐
│ Column     │ Type                     │ Unique Values │ Cardinality %│ Verdict                            │
├────────────┼──────────────────────────┼───────────────┼──────────────┼────────────────────────────────────┤
│ event_id   │ UUID                     │ 1,000         │ 100.0%       │ very high — consider skip index    │
│ user_id    │ UInt64                   │ 874           │ 87.4%        │ high                               │
│ created_at │ DateTime64(3)            │ 1,000         │ 100.0%       │ very high — consider skip index    │
│ date       │ Date                     │ 1             │ 0.1%         │ low — good for LowCardinality      │
│ event_type │ LowCardinality(String)   │ 4             │ 0.4%         │ low — good for LowCardinality      │
└────────────┴──────────────────────────┴───────────────┴──────────────┴────────────────────────────────────┘
```

---

### `ch export` — Export data (v0.2+)

```bash
ch export 'SELECT event_type, count() AS cnt FROM demo.events GROUP BY event_type' --output counts.csv
```

**Expected output:**
```
✓ 4 rows → counts.csv
```

```bash
ch export 'SELECT event_type, count() AS cnt FROM demo.events GROUP BY event_type' --output counts.json
```

**Expected output:**
```
✓ 4 rows → counts.json
```

**Upload to S3 (requires `pip install boto3`):**

```bash
ch export 'SELECT * FROM demo.events' --s3 s3://my-bucket/clickhawk/events.csv
```

**Expected output:**
```
✓ 1,000 rows → s3://my-bucket/clickhawk/events.csv
```

---

### `ch kill` — Kill a running query (v0.3+)

In **terminal 2**, start a slow query:

```bash
clickhouse client --query 'SELECT sleep(3)'
```

In **terminal 1**, find the query ID with `ch monitor`, then kill it:

```bash
ch kill 3a7f1c2b --yes
```

**Expected output:**
```
┌──────────────────────────────────────┬─────────┬───────────┬──────────────────────┐
│ Query ID                             │ User    │ Elapsed(s)│ Query                │
├──────────────────────────────────────┼─────────┼───────────┼──────────────────────┤
│ 3a7f1c2b-...                         │ default │ 1.2       │ SELECT sleep(3)      │
└──────────────────────────────────────┴─────────┴───────────┴──────────────────────┘
✓ Kill signal sent to 1 query/queries.
```

---

### `ch top` — Top queries by resource (v0.3+)

```bash
ch top --sort memory
```

**Expected output (live, refreshes every 2s):**
```
╭─────────────────────────────────────────────── ch top ────────────────────────────────────────────────╮
│ Running: 1   Mem total: 45.0 MiB   Rows total: 1.00 K   Sort: Memory   Ctrl+C to exit                │
│ ┌──────────┬─────────┬───────────┬───────────┬──────────┬────────┬─────────────────────────────────┐ │
│ │ ID       │ User    │ Elapsed(s)│ Rows Read │ Memory   │ CPU(μs)│ Query                           │ │
│ ├──────────┼─────────┼───────────┼───────────┼──────────┼────────┼─────────────────────────────────┤ │
│ │ 3a7f1c2b │ default │ 1.4       │ 0         │ 45.0 MiB │ 12000  │ SELECT sleep(3)                 │ │
│ └──────────┴─────────┴───────────┴───────────┴──────────┴────────┴─────────────────────────────────┘ │
╰───────────────────────────────────────────────────────────────────────────────────────────────────────╯
```

Press `Ctrl+C` to exit.

---

### `ch migrate` — Schema migrations (v0.2+)

Create a migrations directory:

```bash
mkdir migrations
echo "CREATE TABLE demo.my_feature (id UInt64, val String) ENGINE = Log;" > migrations/001_my_feature.sql
```

Check status then apply:

```bash
ch migrate status --dir migrations/
```

**Expected output:**
```
       Migration Status
┌──────────────────────────┬───────────────┬────────────┐
│ File                     │ Status        │ Applied At │
├──────────────────────────┼───────────────┼────────────┤
│ 001_my_feature.sql       │ ⏳ pending    │ —          │
└──────────────────────────┴───────────────┴────────────┘
```

```bash
ch migrate run --dir migrations/
```

**Expected output:**
```
  Applying 001_my_feature.sql ... ✓
Applied 1 migration(s).
```

---

## Common Error Quick Reference

| Error | Cause | Fix |
|-------|-------|-----|
| `brew install clickhouse` → No available formula | Official tap not added | Run `brew tap clickhouse/clickhouse` first |
| macOS "cannot verify developer" | Gatekeeper quarantine attribute | `xattr -d com.apple.quarantine $(which clickhouse)` |
| `brew services start clickhouse` → No available formula | Tap installs a binary with no launchd service | Use `clickhouse server --config-file=...` instead |
| `clickhouse server &` crashes exit 91 | ClickHouse 26.x macOS ARM64 embedded-config bug | Must provide `--config-file`, see Step 1 |
| `clickhouse server` crashes exit 180 / `Settings profile 'default' not found` | config.xml missing profiles/users/quotas | Use the complete config.xml template above |
| `ch profile` / `ch slowlog` → `Unknown table 'system.query_log'` | config.xml missing `<query_log>` block | Use the complete config.xml template above |
| `ch profile` → Stats not yet available | query_log not yet initialized or write delay | Run a plain query first, wait 1 second, then profile |
| `SELECT sleep(10)` → TOO_SLOW | ClickHouse max sleep is 3 seconds | Use `SELECT sleep(3)` instead |
| `ch query 'SQL' --format json` → Missing argument 'SQL' | Quotes corrupted or multiple lines pasted at once | Run each command separately, use single quotes `'` |
| `ch health` → Connection refused | Server not running or wrong port | `curl http://localhost:8123/ping` to check server status |
| `pip install -e ".[dev]"` fails | Wrong directory | Ensure you are in the project root (where `pyproject.toml` lives) |
| `ch` command not found on Windows | Python Scripts directory not in PATH | Run `python -c "import sysconfig; print(sysconfig.get_path('scripts'))"` and add the output to PATH |
