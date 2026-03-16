import time
import uuid
import typer
from rich.console import Console
from rich.table import Table

app = typer.Typer(help="Profile query performance.", context_settings={"allow_interspersed_args": True})
console = Console()


@app.callback(invoke_without_command=True)
def run(
    sql: str = typer.Argument(..., help="SQL query to profile"),
) -> None:
    """Run a query and show detailed performance metrics."""
    from clickhawk.core.client import get_client

    client = get_client()
    query_id = str(uuid.uuid4())

    console.print(f"[dim]Profiling... (query_id={query_id[:8]})[/dim]")

    start = time.perf_counter()
    client.query(sql, settings={"log_queries": 1, "query_id": query_id})
    wall_time = time.perf_counter() - start

    # Give query_log a moment to flush (flush_interval default ~1s)
    time.sleep(1.2)

    stats = client.query(f"""
        SELECT
            query_duration_ms,
            read_rows,
            read_bytes,
            memory_usage,
            ProfileEvents['SelectedParts'] AS parts_selected,
            ProfileEvents['SelectedRanges'] AS ranges_selected
        FROM system.query_log
        WHERE query_id = '{query_id}'
          AND type = 'QueryFinish'
        LIMIT 1
    """)

    table = Table(title="🔍 Query Profile", show_header=True)
    table.add_column("Metric", style="cyan", min_width=20)
    table.add_column("Value", style="green")

    table.add_row("Wall time", f"{wall_time:.3f}s")

    if stats.row_count > 0:
        row = stats.first_row
        table.add_row("DB duration",    f"{row[0]} ms")
        table.add_row("Rows read",      f"{row[1]:,}")
        table.add_row("Bytes read",     f"{row[2] / 1024 / 1024:.2f} MB")
        table.add_row("Memory used",    f"{row[3] / 1024 / 1024:.2f} MB")
        table.add_row("Parts selected", str(row[4]))
        table.add_row("Ranges selected", str(row[5]))
    else:
        table.add_row("Note", "Stats not yet available in query_log")

    console.print(table)
