import time
import typer
from rich.console import Console
from rich.live import Live
from rich.table import Table

app = typer.Typer(help="Live query monitoring dashboard.")
console = Console()


def _build_table() -> Table:
    from clickhawk.core.client import get_client

    result = get_client().query("""
        SELECT
            substr(query_id, 1, 8)              AS id,
            user,
            round(elapsed, 1)                   AS elapsed_s,
            formatReadableQuantity(read_rows)   AS rows_read,
            formatReadableSize(memory_usage)    AS memory,
            substr(replaceRegexpAll(query, '\\s+', ' '), 1, 60) AS query
        FROM system.processes
        ORDER BY elapsed DESC
    """)

    t = Table(
        title="⚡ Live Queries  (Ctrl+C to exit)",
        header_style="bold cyan",
        expand=True,
    )
    for col in ["ID", "User", "Elapsed(s)", "Rows Read", "Memory", "Query"]:
        t.add_column(col, no_wrap=(col != "Query"))

    for row in result.result_rows:
        elapsed = float(row[2])
        style = "red" if elapsed > 30 else ("yellow" if elapsed > 5 else "")
        t.add_row(*[str(v) for v in row], style=style)

    if result.row_count == 0:
        t.add_row("—", "—", "—", "—", "—", "[dim]No active queries[/dim]")

    return t


@app.callback(invoke_without_command=True)
def run(
    interval: float = typer.Option(2.0, "--interval", "-i", help="Refresh interval in seconds"),
) -> None:
    """Watch currently running queries in real time."""
    with Live(_build_table(), refresh_per_second=2, screen=False) as live:
        while True:
            time.sleep(interval)
            live.update(_build_table())
