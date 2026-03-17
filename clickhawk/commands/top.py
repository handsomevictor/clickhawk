import time
from typing import Optional

import typer
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

app = typer.Typer(
    help="Live top-queries dashboard sorted by resource usage.",
    context_settings={"allow_interspersed_args": True},
)
console = Console()

_SORT_COLS = {
    "elapsed":  ("elapsed DESC",  "Elapsed(s)"),
    "memory":   ("memory_usage DESC", "Memory"),
    "rows":     ("read_rows DESC", "Rows Read"),
    "cpu":      ("ProfileEvents['OSCPUVirtualTimeMicroseconds'] DESC", "CPU(μs)"),
}


def _build_panel(sort: str, n: int) -> Panel:
    from clickhawk.core.client import get_client

    order_expr, sort_label = _SORT_COLS.get(sort, _SORT_COLS["elapsed"])

    result = get_client().query(f"""
        SELECT
            substr(query_id, 1, 8)                                          AS id,
            user,
            round(elapsed, 1)                                               AS elapsed_s,
            formatReadableQuantity(read_rows)                               AS rows_read,
            formatReadableSize(memory_usage)                                AS memory,
            ProfileEvents['OSCPUVirtualTimeMicroseconds']                   AS cpu_us,
            substr(replaceRegexpAll(query, '\\s+', ' '), 1, 55)             AS query
        FROM system.processes
        ORDER BY {order_expr}
        LIMIT {n}
    """)

    # Summary line
    summary_res = get_client().query("""
        SELECT
            count()                           AS running,
            formatReadableSize(sum(memory_usage)) AS total_mem,
            formatReadableQuantity(sum(read_rows)) AS total_rows
        FROM system.processes
    """)
    s = summary_res.first_row if summary_res.row_count > 0 else (0, "0 B", "0")
    summary = Text(
        f"Running: {s[0]}   Mem total: {s[1]}   Rows total: {s[2]}   "
        f"Sort: [bold]{sort_label}[/bold]   Ctrl+C to exit",
        style="dim",
    )

    t = Table(header_style="bold cyan", expand=True, show_edge=False)
    t.add_column("ID", no_wrap=True)
    t.add_column("User", no_wrap=True)
    t.add_column("Elapsed(s)", justify="right", no_wrap=True)
    t.add_column("Rows Read", justify="right", no_wrap=True)
    t.add_column("Memory", justify="right", no_wrap=True)
    t.add_column("CPU(μs)", justify="right", no_wrap=True)
    t.add_column("Query")

    for row in result.result_rows:
        elapsed = float(row[2])
        style = "red" if elapsed > 30 else ("yellow" if elapsed > 5 else "")
        t.add_row(*[str(v) for v in row], style=style)

    if result.row_count == 0:
        t.add_row("—", "—", "—", "—", "—", "—", "[dim]No active queries[/dim]")

    from rich.console import Group  # type: ignore[attr-defined]
    return Panel(Group(summary, t), title="🦅 ch top", border_style="bright_black")


@app.callback(invoke_without_command=True)
def run(
    sort: str = typer.Option(
        "elapsed", "--sort", "-s",
        help="Sort by: elapsed|memory|rows|cpu",
    ),
    n: int = typer.Option(20, "--top", "-n", help="Max rows to display"),
    interval: float = typer.Option(2.0, "--interval", "-i", help="Refresh interval in seconds"),
) -> None:
    """Live dashboard of top queries by resource usage (elapsed / memory / rows / cpu)."""
    if sort not in _SORT_COLS:
        console.print(f"[red]Unknown sort key '{sort}'. Use: {', '.join(_SORT_COLS)}[/red]")
        raise typer.Exit(1)

    with Live(_build_panel(sort, n), refresh_per_second=2, screen=False) as live:
        while True:
            time.sleep(interval)
            live.update(_build_panel(sort, n))
