> English version: [TUTORIAL.md](TUTORIAL.md)

# 本地快速上手教程

本教程带你在本地安装 ClickHouse、创建测试数据库，然后用 ClickHawk 验证所有功能。

**预计耗时：** 15 分钟
**支持平台：** macOS · Linux · Windows

> ClickHawk 本身是纯 Python 实现，通过 HTTP 协议连接 ClickHouse，**macOS、Linux、Windows 均可运行**，无任何平台相关依赖。详见 [README](README.md)。

---

## 第一步：安装并启动 ClickHouse

根据你的操作系统选择对应方式。**每种方式包含安装和启动两步。**

---

### macOS（推荐：Homebrew + 手动启动）

> **为什么不用 `./clickhouse server` 直接启动？**
> ClickHouse 26.x 在 macOS ARM64 上以无配置文件模式运行时存在已知 bug，会立即 crash（exit 91）。
>
> **为什么不用 `brew services start clickhouse`？**
> `brew tap clickhouse/clickhouse` 安装的是单文件二进制，没有注册 launchd service，`brew services` 无法管理它。
>
> 正确方式是提供完整 config.xml 手动启动，见下方。

**1. 安装**

```bash
# 必须先添加官方 tap，直接 brew install clickhouse 会报 "No available formula"
brew tap clickhouse/clickhouse
brew install clickhouse
```

**2. 解除 macOS Gatekeeper 拦截**

安装完成后，首次运行会被 macOS 以"无法验证开发者"为由拦截。执行以下命令移除隔离标记：

```bash
xattr -d com.apple.quarantine $(which clickhouse)
```

**3. 创建完整配置文件并启动**

> **为什么需要完整的 config.xml？**
> - 仅含路径和端口 → exit 180（`Settings profile 'default' not found`），必须包含 `<profiles>`、`<users>`、`<quotas>`
> - 缺少 `<query_log>` → `ch profile` 和 `ch slowlog` 报 `Unknown table 'system.query_log'`
> - 缺少 `<log_queries>1</log_queries>` → query_log 表存在但没有数据

```bash
mkdir -p ~/clickhouse-data/{data,tmp}

cat > ~/clickhouse-config.xml << 'EOF'
<clickhouse>
    <path>/Users/zhenningli/clickhouse-data/data/</path>
    <tmp_path>/Users/zhenningli/clickhouse-data/tmp/</tmp_path>
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

clickhouse server --config-file=$HOME/clickhouse-config.xml > /tmp/clickhouse.log 2>&1 &
```

**4. 验证启动成功**

```bash
sleep 2
curl http://localhost:8123/ping   # 返回 Ok. 说明成功
```

如果没有返回，检查日志：

```bash
tail -20 /tmp/clickhouse.log
```

**5. 连接客户端**

```bash
clickhouse client
```

**6. 停止服务**

```bash
pkill -f "clickhouse server"
```

---

### macOS（备选：Docker）

如果不想处理配置文件问题，Docker 是最省事的方式：

```bash
docker run -d --name clickhouse-local -p 8123:8123 -p 9000:9000 clickhouse/clickhouse-server
```

验证：

```bash
curl http://localhost:8123/ping   # 返回 Ok.
```

连接客户端：

```bash
docker exec -it clickhouse-local clickhouse-client
```

停止：

```bash
docker stop clickhouse-local
```

---

### Linux（Ubuntu / Debian）

```bash
# apt 安装
sudo apt-get install -y apt-transport-https ca-certificates curl gnupg
curl -fsSL 'https://packages.clickhouse.com/rpm/lts/repodata/repomd.xml.key' \
  | sudo gpg --dearmor -o /usr/share/keyrings/clickhouse-keyring.gpg
echo "deb [signed-by=/usr/share/keyrings/clickhouse-keyring.gpg] https://packages.clickhouse.com/deb stable main" \
  | sudo tee /etc/apt/sources.list.d/clickhouse.list
sudo apt-get update
sudo apt-get install -y clickhouse-server clickhouse-client

# 启动
sudo service clickhouse-server start

# 验证
curl http://localhost:8123/ping

# 连接客户端
clickhouse-client
```

> Linux 上也可以用官方单文件：`curl https://clickhouse.com/ | sh`，然后 `./clickhouse server &`，Linux 上无 macOS 的 config bug。

---

### Windows（WSL2，推荐）

在 WSL2（Ubuntu）终端里执行 Linux 的安装命令即可，体验与 Linux 完全一致。

**或者用 Docker（单行命令）：**

```powershell
docker run -d --name clickhouse-local -p 8123:8123 -p 9000:9000 clickhouse/clickhouse-server
```

---

## 第二步：创建测试数据库

进入 ClickHouse 客户端后，执行以下 SQL：

```sql
-- 创建数据库
CREATE DATABASE demo;

-- 创建事件表（含分区键和排序键，模拟真实生产表结构）
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

-- 插入 10 万条随机测试数据
INSERT INTO demo.events (user_id, event_type)
SELECT
    rand() % 10000,
    ['click', 'view', 'purchase', 'signup'][rand() % 4 + 1]
FROM numbers(100000);

-- 验证写入成功
SELECT count() FROM demo.events;
-- 应返回 100000
```

输入 `exit;` 或按 `Ctrl+D` 退出客户端。

---

## 第三步：安装 ClickHawk

```bash
cd /path/to/clickhawk

# 开发模式安装（代码改动立即生效）
pip install -e ".[dev]"

# 验证
ch --help
```

完整命令参考见 [README](README.md)。

---

## 第四步：配置连接

```bash
# 复制配置模板，然后将 CH_DATABASE 改为第二步创建的 demo 数据库
cp .env.example .env
```

编辑 `.env`，设置：
```env
CH_DATABASE=demo
```

> **注意：** 第二步创建的测试数据库名为 `demo`。如果 `CH_DATABASE` 保持默认的 `default`，所有表名都需要加前缀（如 `demo.events`）。设置 `CH_DATABASE=demo` 后可以省略前缀。

或者直接导出环境变量：

```bash
export CH_HOST=localhost
export CH_PORT=8123
export CH_USER=default
export CH_PASSWORD=
export CH_DATABASE=demo   # 第二步创建的测试数据库
```

---

## 第五步：验证所有功能

> **注意：** 从文档复制命令时，建议每条单独粘贴执行，不要一次粘贴多行。SQL 中使用单引号 `'` 包裹，避免引号在复制过程中变形。

---

### ✅ 健康检查

```bash
ch health
```

**预期输出：**
```
✓  ClickHouse  26.x.x.x
    Uptime   : X minutes
    Databases: 3
    Tables   : X
```

---

### ✅ 执行查询（表格格式）

```bash
ch query 'SELECT event_type, count() AS cnt FROM demo.events GROUP BY event_type ORDER BY cnt DESC'
```

---

### ✅ JSON 格式输出

```bash
ch query 'SELECT event_type, count() AS cnt FROM demo.events GROUP BY event_type' --format json
```

---

### ✅ CSV 格式输出

```bash
ch query 'SELECT user_id, count() AS cnt FROM demo.events GROUP BY user_id LIMIT 5' --format csv
```

---

### ✅ 性能分析

> **注意：** `ch profile` 依赖 `system.query_log`。需要先执行一条普通查询让该表完成初始化，再运行 profile。

```bash
# 第一步：先执行一条普通查询（让 query_log 完成初始化）
ch query 'SELECT count() FROM demo.events'

# 第二步：等待 query_log 写入（约 1 秒）
sleep 1

# 第三步：profile
ch profile 'SELECT uniq(user_id) FROM demo.events WHERE date = today()'
```

**预期输出：**
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

> 本地数据量小，数值很小是正常的。详细指标解读见 [examples/PROFILING.md](examples/PROFILING.md)。

---

### ✅ 慢查询历史

```bash
ch slowlog --threshold 1 --hours 1 --top 10
```

---

### ✅ Schema 探索

```bash
ch schema tables --database demo
```

```bash
ch schema show events --database demo
```

---

### ✅ 实时监控

在终端 1 启动监控：

```bash
ch monitor
```

在终端 2 制造一个耗时查询（让监控有内容可看）：

```bash
# macOS / Linux（Homebrew 安装）
clickhouse client --query 'SELECT sleep(3)'

# Docker
docker exec -it clickhouse-local clickhouse-client --query 'SELECT sleep(3)'
```

> **注意：** ClickHouse 限制最大 sleep 时间为 3 秒，`SELECT sleep(10)` 会报 `TOO_SLOW` 错误。

观察终端 1 中 `ch monitor` 出现该查询条目。按 `Ctrl+C` 退出监控。更多场景见 [examples/MONITORING.md](examples/MONITORING.md)。

---

## 常见报错速查

| 报错 | 原因 | 解决方案 |
|------|------|----------|
| `brew install clickhouse` → No available formula | 需要先添加官方 tap | `brew tap clickhouse/clickhouse` 后再安装 |
| macOS 提示"无法验证开发者" | Gatekeeper 隔离标记 | `xattr -d com.apple.quarantine $(which clickhouse)` |
| `brew services start clickhouse` → No available formula | tap 安装的是二进制，没有 launchd service | 改用 `clickhouse server --config-file=...` 手动启动 |
| `clickhouse server &` crash exit 91 | ClickHouse 26.x macOS ARM64 embedded config bug | 必须提供 `--config-file`，见第一步 |
| `clickhouse server` crash exit 180 / `Settings profile 'default' not found` | config.xml 缺少 profiles/users/quotas | 使用上方完整的 config.xml 模板 |
| `ch profile` / `ch slowlog` → `Unknown table 'system.query_log'` | config.xml 缺少 `<query_log>` 配置 | 使用上方完整的 config.xml 模板（含 query_log 节点） |
| `ch profile` → Stats not yet available | query_log 尚未初始化或写入延迟 | 先执行一条普通查询，等 1 秒再 profile |
| `SELECT sleep(10)` → TOO_SLOW | ClickHouse 限制最大 sleep 为 3 秒 | 改用 `SELECT sleep(3)` |
| `ch query 'SQL' --format json` → Missing argument 'SQL' | 从文档复制时引号变形，或多行一起粘贴 | 每条命令单独执行，用单引号 `'` 包裹 SQL |
| `ch health` → Connection refused | 服务端未启动或端口错误 | `curl http://localhost:8123/ping` 确认服务状态 |
| `pip install -e ".[dev]"` 报错 | 目录不对 | 确认在有 `pyproject.toml` 的项目根目录执行 |
| Windows 上 `ch` 命令找不到 | Python Scripts 不在 PATH | `python -c "import sysconfig; print(sysconfig.get_path('scripts'))"` 找到路径后加入 PATH |
