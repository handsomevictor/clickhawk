# 项目结构说明

```
clickhawk/
├── clickhawk/                    # 主包目录
│   ├── __init__.py
│   ├── main.py                   # CLI 入口：注册所有子命令，定义 ch health
│   │
│   ├── core/                     # 核心基础设施
│   │   ├── __init__.py
│   │   ├── client.py             # ClickHouse 连接管理（单例模式）
│   │   └── config.py             # 配置管理（Pydantic Settings，读取 .env / 环境变量）
│   │
│   ├── commands/                 # 每个 CLI 命令对应一个文件
│   │   ├── __init__.py
│   │   ├── query.py              # ch query — SQL 执行，支持 table/json/csv 输出
│   │   ├── profile.py            # ch profile — 查询性能分析（system.query_log）
│   │   ├── slowlog.py            # ch slowlog — 慢查询历史排行
│   │   ├── schema.py             # ch schema show/tables — 表结构和表列表
│   │   ├── monitor.py            # ch monitor — 实时查询监控（Live 刷新）
│   │   └── migrate.py            # ch migrate — schema 迁移（v0.2 占位）
│   │
│   ├── formatters/               # 输出格式化器
│   │   ├── __init__.py
│   │   ├── table.py              # Rich 表格 / JSON / CSV 格式化输出
│   │   └── tree.py               # EXPLAIN 树形输出（v0.2 计划）
│   │
│   └── utils/                    # 工具函数
│       ├── __init__.py
│       └── sql.py                # SQL 工具：查询标准化、参数绑定等（v0.2 计划）
│
├── tests/                        # 测试套件
│   ├── __init__.py
│   ├── unit/                     # 单元测试（不依赖 ClickHouse 连接）
│   │   └── __init__.py
│   └── integration/              # 集成测试（需要真实 ClickHouse 实例）
│       └── __init__.py
│
├── examples/                     # 使用示例
│   ├── basic_query.md            # 基础查询示例
│   ├── profiling.md              # 性能分析示例
│   ├── schema_exploration.md     # Schema 探索示例
│   └── monitoring.md             # 实时监控示例
│
├── pyproject.toml                # 项目元数据、依赖、构建配置
├── .env.example                  # 环境变量配置模板
├── .gitignore
├── .gitattributes
├── README.md                     # 项目主文档
├── CHANGELOG.md                  # 版本更新记录
├── structure.md                  # 本文件：项目结构说明
└── lessons_learned.md            # 开发调试经验记录
```

---

## 模块职责说明

### `main.py` — 程序入口

注册所有子命令 app，定义 `ch health` 命令（因为 health 比较简单，直接放在入口文件而非单独命令文件）。Typer app 的 `name="ch"` 对应终端命令入口。

```python
app = typer.Typer(name="ch", ...)
app.add_typer(query.app,   name="query")
app.add_typer(profile.app, name="profile")
# ...
```

### `core/config.py` — 配置管理

基于 Pydantic Settings v2，通过 `env_prefix="CH_"` 读取环境变量。支持 `.env` 文件（`python-dotenv`）和直接环境变量，环境变量优先级高于 `.env` 文件。

```python
class ClickHouseConfig(BaseSettings):
    host: str = "localhost"
    port: int = 8123
    # ...
    model_config = {"env_prefix": "CH_", "env_file": ".env"}
```

### `core/client.py` — 连接管理

使用全局单例模式（module-level `_client` 变量），避免每次命令调用都重新建立 HTTP 连接。`get_client()` 是所有命令获取 ClickHouse 客户端的统一入口。

### `commands/` — 命令模块

每个命令文件定义一个 `app = typer.Typer()`，分两种模式：
- **直接执行型**（`query`、`profile`、`slowlog`、`monitor`）：用 `@app.callback(invoke_without_command=True)` 定义主函数，`ch query "..."` 直接调用
- **多子命令型**（`schema`、`migrate`）：用 `@app.command()` 定义多个子命令，`ch schema show`、`ch schema tables` 分别路由

### `formatters/table.py` — 输出格式化

`print_result(result, format)` 统一处理三种输出格式：
- `table`：Rich 彩色表格（默认）
- `json`：JSON 数组，通过 `console.print_json()` 输出（语法高亮）
- `csv`：标准 CSV，可接管道（`ch query "..." --format csv > output.csv`）

---

## 数据流示意

```
用户输入: ch profile "SELECT uniq(user_id) FROM events"
         │
         ▼
    main.py (Typer app)
         │  路由到 profile 命令
         ▼
    commands/profile.py
         │  1. 生成 query_id
         │  2. 调用 get_client()
         │  3. 执行 SQL（带 log_queries=1 和 query_id）
         │  4. sleep(0.3) 等待 query_log 写入
         │  5. 查询 system.query_log 获取性能统计
         │  6. 构建 Rich Table 并输出
         ▼
    core/client.py → clickhouse-connect → ClickHouse HTTP API
         │
         ▼
    终端输出（Rich 彩色表格）
```

---

## 依赖关系

```
typer          — CLI 框架，参数解析，help 生成
rich           — 终端 UI：表格、颜色、Live 刷新、JSON 高亮
clickhouse-connect — ClickHouse HTTP 客户端（官方维护）
pydantic v2    — 数据验证和配置类型定义
pydantic-settings — 从环境变量/文件读取配置
python-dotenv  — .env 文件解析
```

**开发依赖：**
```
pytest         — 测试框架
pytest-asyncio — 异步测试支持
ruff           — 极快的 Python linter（替代 flake8 + isort）
mypy           — 静态类型检查
```
