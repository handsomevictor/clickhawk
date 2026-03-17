from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

app = typer.Typer(
    help="Kill running ClickHouse queries.",
    context_settings={"allow_interspersed_args": True},
)
console = Console()


@app.callback(invoke_without_command=True)
def run(
    query_id: Optional[str] = typer.Argument(
        None, help="Query ID to kill (prefix match, from `ch monitor` or `ch top`)"
    ),
    user: Optional[str] = typer.Option(
        None, "--user", "-u", help="Kill all running queries from a specific user"
    ),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation prompt"),
) -> None:
    """Kill one or more running ClickHouse queries.

    Examples:

      ch kill 3a7f1c2b              # kill by query_id prefix\n
      ch kill --user analyst        # kill all queries by user\n
      ch kill --user etl --yes      # skip confirmation
    """
    from clickhawk.core.client import get_client

    if not query_id and not user:
        console.print("[red]Provide a query_id or --user.[/red]")
        raise typer.Exit(1)

    client = get_client()

    # --- Find matching processes ---
    if query_id:
        result = client.query(f"""
            SELECT query_id, user, round(elapsed, 1) AS elapsed_s,
                   substr(replaceRegexpAll(query, '\\s+', ' '), 1, 80) AS query
            FROM system.processes
            WHERE startsWith(query_id, '{query_id}')
        """)
    else:
        result = client.query(f"""
            SELECT query_id, user, round(elapsed, 1) AS elapsed_s,
                   substr(replaceRegexpAll(query, '\\s+', ' '), 1, 80) AS query
            FROM system.processes
            WHERE user = '{user}'
        """)

    if result.row_count == 0:
        console.print("[yellow]No matching queries found.[/yellow]")
        raise typer.Exit(0)

    # --- Show what will be killed ---
    t = Table(header_style="bold cyan")
    t.add_column("Query ID")
    t.add_column("User")
    t.add_column("Elapsed(s)", justify="right")
    t.add_column("Query")
    for row in result.result_rows:
        t.add_row(*[str(v) for v in row])
    console.print(t)

    # --- Confirm ---
    if not yes:
        confirmed = typer.confirm(
            f"Kill {result.row_count} query/queries?", default=False
        )
        if not confirmed:
            console.print("[dim]Aborted.[/dim]")
            raise typer.Exit(0)

    # --- Execute KILL ---
    killed = 0
    for row in result.result_rows:
        qid = row[0]
        try:
            client.command(f"KILL QUERY WHERE query_id = '{qid}' ASYNC")
            killed += 1
        except Exception as exc:
            console.print(f"[red]Failed to kill {qid[:8]}: {exc}[/red]")

    console.print(f"[green]✓[/green] Kill signal sent to {killed} query/queries.")
