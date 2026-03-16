from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

app = typer.Typer(help="Data quality checks (nulls, cardinality).")
console = Console()


@app.command()
def nulls(
    table: str = typer.Argument(..., help="Table name"),
    database: Optional[str] = typer.Option(None, "--database", "-d", help="Database name"),
    sample: int = typer.Option(1_000_000, "--sample", "-s", help="Max rows to sample"),
) -> None:
    """Show null percentage for every column in a table."""
    from clickhawk.core.client import get_client

    client = get_client()
    db_filter = f"AND database = '{database}'" if database else ""

    cols_result = client.query(f"""
        SELECT name, type
        FROM system.columns
        WHERE table = '{table}' {db_filter}
        ORDER BY position
    """)
    if cols_result.row_count == 0:
        console.print(f"[red]Table '{table}' not found.[/red]")
        raise typer.Exit(1)

    columns = [(row[0], row[1]) for row in cols_result.result_rows]
    full_table = f"{database}.{table}" if database else table

    null_exprs = ", ".join(
        f"countIf(`{name}` IS NULL) AS `null_{i}`"
        for i, (name, _) in enumerate(columns)
    )
    null_sql = (
        f"SELECT count() AS _total, {null_exprs} "
        f"FROM (SELECT * FROM {full_table} LIMIT {sample})"
    )

    console.print(f"[dim]Scanning {full_table} (sample ≤ {sample:,} rows)...[/dim]")
    result = client.query(null_sql)
    row = result.first_row
    total = row[0]

    t = Table(title=f"Null Check: {table}  (n={total:,})", header_style="bold cyan")
    t.add_column("Column")
    t.add_column("Type", style="dim")
    t.add_column("Null Count", justify="right")
    t.add_column("Null %", justify="right")
    t.add_column("Nullable?")

    for i, (name, col_type) in enumerate(columns):
        null_count = row[i + 1]
        pct = (null_count / total * 100) if total > 0 else 0.0
        pct_str = f"{pct:.1f}%"
        if pct > 50:
            pct_str = f"[red]{pct_str}[/red]"
        elif pct > 10:
            pct_str = f"[yellow]{pct_str}[/yellow]"
        is_nullable = "yes" if col_type.startswith("Nullable") else "[dim]no[/dim]"
        t.add_row(name, col_type, f"{null_count:,}", pct_str, is_nullable)

    console.print(t)


@app.command()
def cardinality(
    table: str = typer.Argument(..., help="Table name"),
    database: Optional[str] = typer.Option(None, "--database", "-d", help="Database name"),
    sample: int = typer.Option(1_000_000, "--sample", "-s", help="Max rows to sample"),
    top: int = typer.Option(50, "--top", "-n", help="Max columns to show"),
) -> None:
    """Show approximate unique-value count (cardinality) per column."""
    from clickhawk.core.client import get_client

    client = get_client()
    db_filter = f"AND database = '{database}'" if database else ""

    cols_result = client.query(f"""
        SELECT name, type
        FROM system.columns
        WHERE table = '{table}' {db_filter}
        ORDER BY position
        LIMIT {top}
    """)
    if cols_result.row_count == 0:
        console.print(f"[red]Table '{table}' not found.[/red]")
        raise typer.Exit(1)

    columns = [(row[0], row[1]) for row in cols_result.result_rows]
    full_table = f"{database}.{table}" if database else table

    uniq_exprs = ", ".join(
        f"uniq(`{name}`) AS `uniq_{i}`" for i, (name, _) in enumerate(columns)
    )
    sql = (
        f"SELECT count() AS _total, {uniq_exprs} "
        f"FROM (SELECT * FROM {full_table} LIMIT {sample})"
    )

    console.print(f"[dim]Scanning {full_table} (sample ≤ {sample:,} rows)...[/dim]")
    result = client.query(sql)
    row = result.first_row
    total = row[0]

    rows_data = []
    for i, (name, col_type) in enumerate(columns):
        uniq = row[i + 1]
        pct = (uniq / total * 100) if total > 0 else 0.0
        if pct > 95:
            verdict = "[red]very high — consider skip index[/red]"
        elif pct > 50:
            verdict = "[yellow]high[/yellow]"
        elif pct < 1:
            verdict = "[green]low — good for LowCardinality[/green]"
        else:
            verdict = "medium"
        rows_data.append((name, col_type, uniq, pct, verdict))

    rows_data.sort(key=lambda x: x[2], reverse=True)

    t = Table(title=f"Cardinality: {table}  (n={total:,})", header_style="bold cyan")
    t.add_column("Column")
    t.add_column("Type", style="dim")
    t.add_column("Unique Values", justify="right")
    t.add_column("Cardinality %", justify="right")
    t.add_column("Verdict")

    for name, col_type, uniq, pct, verdict in rows_data:
        t.add_row(name, col_type, f"{uniq:,}", f"{pct:.1f}%", verdict)

    console.print(t)
