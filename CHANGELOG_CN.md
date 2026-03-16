> English version: [CHANGELOG.md](CHANGELOG.md)

# 更新日志

本项目遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/) 格式，版本号遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

---

## [未发布]

### 计划中
- `ch explain` — 彩色树形 EXPLAIN PLAN 输出
- `ch schema diff` — 对比两个 ClickHouse 环境的 schema 差异
- `ch migrate run/status` — 基于文件的 schema 迁移管理

---

## [0.1.0] — 2026-03-16

### 新增
- **`ch health`** — 集群健康检查，显示版本、uptime、数据库数量和表数量
- **`ch query <sql>`** — 执行 SQL 查询，支持 `table`（默认）/`json`/`csv` 三种输出格式，支持 `--limit` 截断行数
- **`ch profile <sql>`** — 查询性能分析，通过 `system.query_log` 提取真实执行统计（wall time、DB 耗时、读取行数/字节数、内存、parts/ranges 命中数）
- **`ch slowlog`** — 慢查询历史排行，支持 `--top`、`--threshold`（毫秒）、`--hours` 参数自定义
- **`ch schema show <table>`** — 展示表结构（列名/类型/默认值/注释），支持 `--database` 过滤
- **`ch schema tables`** — 列出所有用户表，展示数据库、引擎、磁盘大小和行数，支持 `--database` 过滤
- **`ch monitor`** — 实时 Live Dashboard，轮询 `system.processes`，超时查询以颜色区分（>5s 黄色，>30s 红色），支持 `--interval` 自定义刷新频率
- **`ch migrate run/status`** — 占位命令，v0.2 正式实现

### 技术基础
- 基于 **Typer** 构建 CLI 框架，命令入口为 `ch`
- 使用 **Rich** 渲染彩色表格和 Live 实时刷新
- 通过 **clickhouse-connect** 连接 ClickHouse（HTTP 协议）
- 使用 **Pydantic Settings v2** 管理配置，支持 `.env` 文件和环境变量
- 连接客户端采用单例模式，避免重复握手
- 支持 Python 3.13+

---

[未发布]: https://github.com/your-username/clickhawk/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/your-username/clickhawk/releases/tag/v0.1.0
