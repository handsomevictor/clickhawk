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
# Copy the config template (defaults to localhost:8123 — no changes needed for local setup)
cp .env.example .env
```

Or export environment variables directly:

```bash
export CH_HOST=localhost
export CH_PORT=8123
export CH_USER=default
export CH_PASSWORD=
export CH_DATABASE=default
```

---

## Step 5: Verify All Features

> **Tip:** When copying commands from this document, paste and run them one at a time. Wrap SQL in single quotes `'` to avoid quote corruption during copy-paste.

---

### Health check

```bash
ch health
```

**Expected output:**
```
✓  ClickHouse  26.x.x.x
    Uptime   : X minutes
    Databases: 3
    Tables   : X
```

---

### Execute a query (table format)

```bash
ch query 'SELECT event_type, count() AS cnt FROM demo.events GROUP BY event_type ORDER BY cnt DESC'
```

---

### JSON output

```bash
ch query 'SELECT event_type, count() AS cnt FROM demo.events GROUP BY event_type' --format json
```

---

### CSV output

```bash
ch query 'SELECT user_id, count() AS cnt FROM demo.events GROUP BY user_id LIMIT 5' --format csv
```

---

### Query profiling

> **Note:** `ch profile` depends on `system.query_log`. Run a plain query first to initialize the table, then profile.

```bash
# Step 1: run a warm-up query (initializes query_log)
ch query 'SELECT count() FROM demo.events'

# Step 2: wait for query_log to flush (~1 second)
sleep 1

# Step 3: profile
ch profile 'SELECT uniq(user_id) FROM demo.events WHERE date = today()'
```

**Expected output:**
```
🔍 Query Profile
┌──────────────────────┬──────────────┐
│ Metric               │ Value        │
├──────────────────────┼──────────────┤
│ Wall time            │ 0.00Xs       │
│ DB duration          │ X ms         │
│ Rows read            │ XXX          │
│ Bytes read           │ X.XX MB      │
│ Memory used          │ X.XX MB      │
│ Parts selected       │ X            │
│ Ranges selected      │ X            │
└──────────────────────┴──────────────┘
```

> Values will be small with local data — that is expected. See [examples/PROFILING.md](examples/PROFILING.md) for metric explanations.

---

### Slow query history

```bash
ch slowlog --threshold 1 --hours 1 --top 10
```

---

### Schema exploration

```bash
ch schema tables --database demo
```

```bash
ch schema show events --database demo
```

---

### Live monitoring

In terminal 1, start the monitor:

```bash
ch monitor
```

In terminal 2, create a long-running query so the monitor has something to show:

```bash
# macOS / Linux (Homebrew install)
clickhouse client --query 'SELECT sleep(3)'

# Docker
docker exec -it clickhouse-local clickhouse-client --query 'SELECT sleep(3)'
```

> **Note:** ClickHouse limits `sleep()` to a maximum of 3 seconds. `SELECT sleep(10)` raises a `TOO_SLOW` error.

Watch terminal 1 for the query to appear in `ch monitor`. Press `Ctrl+C` to exit. See [examples/MONITORING.md](examples/MONITORING.md) for more scenarios.

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
