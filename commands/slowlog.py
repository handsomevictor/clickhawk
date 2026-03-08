import typer
from rich.console import Console
from rich.table import Table

app = typer.Typer(help="Inspect slow query history.")
console = Console()


@app.callback(invoke_without_command=True)
def run(
    top: int = typer.Option(20, "--top", "-n", help="Number of queries to show"),
    threshold_ms: int = typer.Option(1000, "--threshold", "-t", help="Minimum duration in ms"),
    hours: int = typer.Option(24, "--hours", help="Look back N hours"),
) -> None:
    """Show the slowest recent queries from system.query_log."""
    from clickhawk.core.client import get_client

    client = get_client()
    result = client.query(f"""
        SELECT
            formatDateTime(query_start_time, '%H:%M:%S') AS time,
            query_duration_ms                            AS duration_ms,
            formatReadableQuantity(read_rows)            AS rows_read,
            formatReadableSize(read_bytes)               AS bytes_read,
            formatReadableSize(memory_usage)             AS memory,
            user,
            substr(replaceRegexpAll(query, '\\s+', ' '), 1, 80) AS query_preview
        FROM system.query_log
        WHERE type = 'QueryFinish'
          AND query_duration_ms >= {threshold_ms}
          AND event_time >= now() - INTERVAL {hours} HOUR
        ORDER BY query_duration_ms DESC
        LIMIT {top}
    """)

    if result.row_count == 0:
        console.print(f"[green]No queries slower than {threshold_ms}ms in the last {hours}h.[/green]")
        return

    table = Table(
        title=f"🐢 Slow Queries  (last {hours}h  ·  ≥{threshold_ms}ms  ·  top {top})",
        show_header=True,
        header_style="bold cyan",
    )
    for col in ["Time", "Duration(ms)", "Rows Read", "Bytes Read", "Memory", "User", "Query"]:
        table.add_column(col, no_wrap=(col != "Query"))

    for row in result.result_rows:
        table.add_row(*[str(v) for v in row])

    console.print(table)
    console.print(f"[dim]{result.row_count} queries found[/dim]")
