from typing import Optional
import typer
from rich.console import Console
from rich.table import Table

app = typer.Typer(help="Explore table schemas.")
console = Console()


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
