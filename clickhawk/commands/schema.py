from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

app = typer.Typer(help="Explore table schemas.")
console = Console()


def _fetch_columns(client, table: str, database: Optional[str]) -> dict[str, tuple]:  # type: ignore[type-arg]
    """Return {col_name: (type, default_expr, comment)} for a table."""
    db_filter = f"AND database = '{database}'" if database else ""
    r = client.query(f"""
        SELECT name, type, default_expression, comment
        FROM system.columns
        WHERE table = '{table}' {db_filter}
        ORDER BY position
    """)
    return {row[0]: (row[1], row[2], row[3]) for row in r.result_rows}


@app.command()
def show(
    table: str = typer.Argument(..., help="Table name"),
    database: Optional[str] = typer.Option(None, "--database", "-d", help="Database name"),
) -> None:
    """Show the schema for a table."""
    from clickhawk.core.client import get_client

    client = get_client()
    db_filter = f"AND database = '{database}'" if database else ""
    result = client.query(f"""
        SELECT
            name,
            type,
            default_expression,
            comment
        FROM system.columns
        WHERE table = '{table}' {db_filter}
        ORDER BY position
    """)

    if result.row_count == 0:
        console.print(f"[red]Table '{table}' not found.[/red]")
        raise typer.Exit(1)

    t = Table(title=f"Schema: {table}", header_style="bold cyan")
    for col in ["Column", "Type", "Default", "Comment"]:
        t.add_column(col)
    for row in result.result_rows:
        t.add_row(*[str(v) for v in row])
    console.print(t)


@app.command()
def tables(
    database: Optional[str] = typer.Option(None, "--database", "-d", help="Filter by database"),
) -> None:
    """List all tables with size and row count."""
    from clickhawk.core.client import get_client

    client = get_client()
    if database:
        db_filter = f"WHERE database = '{database}'"
    else:
        db_filter = "WHERE database NOT IN ('system', 'information_schema', 'INFORMATION_SCHEMA')"

    result = client.query(f"""
        SELECT
            database,
            name,
            engine,
            formatReadableSize(total_bytes)     AS size,
            formatReadableQuantity(total_rows)  AS rows
        FROM system.tables
        {db_filter}
        ORDER BY database, name
    """)

    t = Table(title="Tables", header_style="bold cyan")
    for col in ["Database", "Table", "Engine", "Size", "Rows"]:
        t.add_column(col)
    for row in result.result_rows:
        t.add_row(*[str(v) for v in row])
    console.print(t)
    console.print(f"[dim]{result.row_count} tables[/dim]")


@app.command()
def diff(
    table: str = typer.Argument(..., help="Table name to compare"),
    host2: str = typer.Option(..., "--host2", help="Second ClickHouse host"),
    port2: int = typer.Option(8123, "--port2", help="Second host HTTP port"),
    user2: str = typer.Option("default", "--user2", help="Second host username"),
    password2: str = typer.Option("", "--password2", help="Second host password"),
    database: Optional[str] = typer.Option(None, "--database", "-d", help="Database on host 1"),
    database2: Optional[str] = typer.Option(None, "--database2", help="Database on host 2 (defaults to --database)"),
) -> None:
    """Compare a table's schema between two ClickHouse environments."""
    import clickhouse_connect
    from clickhawk.core.client import get_client
    from clickhawk.core.config import ClickHouseConfig

    cfg = ClickHouseConfig()
    client1 = get_client()
    client2 = clickhouse_connect.get_client(
        host=host2,
        port=port2,
        username=user2,
        password=password2,
        database=database2 or database or cfg.database,
    )

    db1 = database
    db2 = database2 or database

    cols1 = _fetch_columns(client1, table, db1)
    cols2 = _fetch_columns(client2, table, db2)

    if not cols1 and not cols2:
        console.print(f"[red]Table '{table}' not found on either host.[/red]")
        raise typer.Exit(1)

    all_cols = sorted(set(cols1) | set(cols2))
    diff_found = False
    rows = []

    for col in all_cols:
        if col in cols1 and col not in cols2:
            rows.append((col, cols1[col][0], "—", "[red]removed on host2[/red]"))
            diff_found = True
        elif col not in cols1 and col in cols2:
            rows.append((col, "—", cols2[col][0], "[green]added on host2[/green]"))
            diff_found = True
        else:
            t1, t2 = cols1[col][0], cols2[col][0]
            if t1 != t2:
                rows.append((col, t1, t2, "[yellow]type changed[/yellow]"))
                diff_found = True

    if not diff_found:
        console.print(
            f"[green]✓ No schema differences found for '{table}'[/green]  "
            f"([dim]{cfg.host}[/dim] ↔ [dim]{host2}[/dim])"
        )
        return

    t = Table(
        title=f"Schema diff: {table}  ({cfg.host} ↔ {host2})",
        header_style="bold cyan",
    )
    t.add_column("Column")
    t.add_column(f"Type on {cfg.host}")
    t.add_column(f"Type on {host2}")
    t.add_column("Diff")
    for row in rows:
        t.add_row(*row)
    console.print(t)
