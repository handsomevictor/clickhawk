> English version: [LESSONS_LEARNED.md](LESSONS_LEARNED.md)

# 调试经验记录（Lessons Learned）

开发 ClickHawk 过程中踩过的坑和学到的经验，供后续开发和贡献者参考。

---

## 1. macOS Gatekeeper 拦截 Homebrew tap 安装的 ClickHouse 二进制

**问题描述：**
通过 `brew tap clickhouse/clickhouse && brew install clickhouse` 安装后，终端执行 `clickhouse` 报错"无法打开，因为无法验证开发者"，或者直接被 macOS 静默拦截。

**根本原因：**
ClickHouse 官方 tap 安装的是预编译二进制，macOS Gatekeeper 会对未经 Apple 公证的二进制添加隔离标记（quarantine attribute），阻止其运行。

**解决方案：**
```bash
xattr -d com.apple.quarantine $(which clickhouse)
```

执行后无需重启，立即生效。

**附：`brew services start clickhouse` 报错问题**
`clickhouse/clickhouse` tap 安装的是单文件二进制，没有注册 Homebrew service（没有 launchd plist），所以 `brew services` 无法管理它。
正确的启动方式是直接运行（需提供完整 config.xml，见下一条）：
```bash
clickhouse server --config-file=$HOME/clickhouse-config.xml &
```

**`ch slowlog` / `ch profile` 报 `Unknown table 'system.query_log'`**
config.xml 缺少 `<query_log>` 配置时，ClickHouse 不会创建 `system.query_log` 表（懒加载），导致 slowlog 和 profile 命令报错。解决方案：在 config.xml 中加入 `<query_log>` 节点并在 default profile 中设置 `<log_queries>1</log_queries>`。

**最小可用 config.xml 必须包含 profiles/users/quotas**，否则会报 `Settings profile 'default' not found`（exit 180）。仅有路径和端口配置不够，ClickHouse 启动时会查找 `default` profile：
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

## 2. Typer 0.12+ 子 app 中选项不能放在位置参数之后

**问题描述：**
`ch query 'SELECT ...' --format json` 报 `Missing argument 'SQL'`，而 `ch query --format json 'SELECT ...'` 正常。

**根本原因：**
Typer 0.12+ 使用 `add_typer()` 嵌套子 app 时，子 app 的 callback 默认不允许选项（`--format`）出现在位置参数（SQL）之后，与用户直觉相反。

**解决方案：**
在每个有位置参数 + 选项组合的子 app 上加 `context_settings={"allow_interspersed_args": True}`：
```python
app = typer.Typer(help="...", context_settings={"allow_interspersed_args": True})
```
受影响的命令：`query`、`profile`、`slowlog`、`monitor`。

---

## 3. ClickHouse 26.x 在 macOS ARM64 上无配置文件启动崩溃

**问题描述：**
在 macOS Apple Silicon 上执行 `./clickhouse server &`，服务端立即 crash 并 exit 91，错误信息为：

```
DB::Exception: Poco::Exception. Code: 1000, e.code() = 0, Null pointer
DB::Context::setClustersConfig ... CANNOT_LOAD_CONFIG
```

**根本原因：**
ClickHouse 26.3（及部分 26.x 版本）在 macOS ARM64 上以 embedded config（无 `config.xml`）模式启动时，`setClustersConfig` 内部触发 null pointer crash。这是 ClickHouse 的已知 bug，不是系统或权限问题。

**解决方案：**

方案 1（推荐）：使用 Docker，完全规避配置问题：
```bash
docker run -d --name clickhouse-local \
  -p 8123:8123 -p 9000:9000 \
  --ulimit nofile=262144:262144 \
  clickhouse/clickhouse-server
```

方案 2：提供最小 `config.xml` 绕过 bug：
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

**经验：**
官方单文件二进制在 macOS 上不稳定（尤其是新版本），本地开发首选 Docker；Linux 上单文件模式通常没有此问题。

---

## 2. `system.query_log` 的延迟写入问题

**问题描述：**
在 `ch profile` 命令中，执行完查询后立即查询 `system.query_log` 会得到空结果，导致性能统计不显示。

**根本原因：**
ClickHouse 的 `query_log` 不是同步写入的，查询结束后有一段异步刷新延迟（通常 100~500ms，取决于服务器负载和配置）。

**解决方案：**
在执行完目标查询后，`time.sleep(0.3)` 等待 300ms 再查询 `system.query_log`。这是一个权衡：等待时间太短会漏掉数据，太长会影响用户体验。

```python
client.query(sql, settings={"log_queries": 1, "query_id": query_id})
time.sleep(0.3)  # 等待 query_log 异步刷新
stats = client.query(f"SELECT ... FROM system.query_log WHERE query_id = '{query_id}'")
```

**经验：**
ClickHouse 的系统表（`system.query_log`、`system.part_log` 等）通常是异步写入的，不要假设它们是实时一致的。如果遇到空结果，优先考虑写入延迟问题。

---

## 2. `ProfileEvents` 字段访问方式

**问题描述：**
`system.query_log` 中的 `ProfileEvents` 是一个 `Map(String, UInt64)` 类型字段，访问特定 key 需要用 `ProfileEvents['KeyName']` 语法，而不是点号。

**正确写法：**
```sql
SELECT
    ProfileEvents['SelectedParts'] AS parts_selected,
    ProfileEvents['SelectedRanges'] AS ranges_selected
FROM system.query_log
WHERE query_id = '...'
```

**常用的 ProfileEvents key：**
- `SelectedParts` — 查询命中的 part 数量（越少越好，说明分区剪枝有效）
- `SelectedRanges` — 命中的 range 数量
- `SelectedMarks` — 命中的 mark 数量（与 index granularity 相关）
- `RealTimeMicroseconds` — 实际耗时（微秒）
- `UserTimeMicroseconds` — 用户态 CPU 耗时

---

## 3. Typer 子命令与 `callback` 的冲突

**问题描述：**
在 Typer 中，如果一个子 app 既有 `@app.callback(invoke_without_command=True)` 又有 `@app.command()` 子命令，会出现命令路由混乱的问题。

**场景：**
`schema` 命令有两个子命令 `show` 和 `tables`，而 `query`、`profile` 等命令是直接运行的（没有子命令）。

**解决方案：**
- 直接运行型命令（`query`、`profile`、`slowlog`、`monitor`）：使用 `@app.callback(invoke_without_command=True)`
- 多子命令型命令（`schema`、`migrate`）：使用普通的 `@app.command()` 定义子命令，不用 callback

这样路由清晰，`ch query "..."` 和 `ch schema show table_name` 都能正常工作。

---

## 4. Rich `Live` 与 `Console` 的兼容性

**问题描述：**
在 `ch monitor` 中，如果在 `Live` 上下文之外调用 `console.print()`，输出会和 Live 刷新的内容混在一起，造成终端显示错乱。

**解决方案：**
所有需要在 Live 刷新期间显示的内容，都通过返回新的 `Table` 对象来更新（`live.update(new_table)`），不要在 Live 上下文内直接调用 `console.print()`。

---

## 5. `clickhouse-connect` 结果集的行访问方式

**问题描述：**
`clickhouse-connect` 的查询结果有多种访问方式，容易搞混：
- `result.result_rows` — 返回 `List[tuple]`，逐行迭代
- `result.first_row` — 返回第一行的 `tuple`（注意：结果为空时会抛 `IndexError`）
- `result.row_count` — 返回行数

**经验：**
在访问 `result.first_row` 之前，务必先检查 `result.row_count > 0`，否则在没有查询记录时（如 `profile` 命令在 `query_log` 中找不到对应记录时）会直接崩溃。

```python
if stats.row_count > 0:
    row = stats.first_row
    # 安全访问 row[0], row[1], ...
else:
    # 优雅降级处理
```

---

## 6. Pydantic Settings 的 `env_prefix` 行为

**问题描述：**
配置类使用了 `env_prefix = "CH_"`，意味着所有环境变量需要加 `CH_` 前缀（`CH_HOST`、`CH_PORT` 等）。但 `.env` 文件里有时会漏掉前缀或者写错大小写。

**经验：**
- Pydantic Settings v2 默认不区分大小写读取环境变量
- `.env` 文件中的变量名需要包含前缀（`CH_HOST=localhost`），而不是裸字段名（`HOST=localhost`）
- 建议在 `.env.example` 中把所有变量都列出来，避免用户遗漏

---

## 7. `pyproject.toml` 中 wheel 打包路径的配置

**问题描述：**
`pyproject.toml` 中的 `[tool.hatch.build.targets.wheel]` 配置了 `packages = ["src/clickhawk"]`，但实际代码结构中代码在 `clickhawk/` 目录（而不是 `src/clickhawk/`），导致 `pip install` 后找不到包。

**解决方案：**
确保打包路径与实际目录结构一致。如果代码在 `clickhawk/`（项目根目录下的同名包），则配置应为：
```toml
[tool.hatch.build.targets.wheel]
packages = ["clickhawk"]
```

**经验：**
在发布 PyPI 之前，务必用 `pip install -e .` 安装后运行 `ch --help` 验证命令是否正常注册，而不只是检查 `pyproject.toml` 的语法。
