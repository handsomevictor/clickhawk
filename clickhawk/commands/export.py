from typing import Optional

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

app = typer.Typer(
    help="Export query results to CSV, JSON, or Parquet.",
    context_settings={"allow_interspersed_args": True},
)
console = Console()


@app.callback(invoke_without_command=True)
def run(
    sql: str = typer.Argument(..., help="SQL query or bare table name to export"),
    output: str = typer.Option(..., "--output", "-o", help="Output file (e.g. out.csv, out.json, out.parquet)"),
    output_format: str = typer.Option(
        "", "--format", "-f",
        help="Format: csv|json|parquet  (auto-detected from file extension when omitted)",
    ),
    limit: Optional[int] = typer.Option(None, "--limit", "-l", help="Max rows to export"),
) -> None:
    """Export the results of a SQL query (or a full table) to a file."""
    from clickhawk.core.client import get_client

    # Detect format from extension when not explicitly provided
    fmt = output_format.lower()
    if not fmt:
        ext = output.rsplit(".", 1)[-1].lower() if "." in output else ""
        fmt = ext if ext in ("csv", "json", "parquet") else "csv"

    # Bare table name → SELECT *
    query = sql if " " in sql.strip() else f"SELECT * FROM {sql}"
    if limit:
        query = f"SELECT * FROM ({query}) LIMIT {limit}"

    client = get_client()

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        progress.add_task(f"Exporting → {output} ({fmt})…", total=None)

        if fmt == "csv":
            import csv as _csv

            result = client.query(query)
            with open(output, "w", newline="", encoding="utf-8") as f:
                writer = _csv.writer(f)
                writer.writerow(result.column_names)
                writer.writerows(result.result_rows)
            console.print(
                f"[green]✓[/green] {result.row_count:,} rows → [cyan]{output}[/cyan]"
            )

        elif fmt == "json":
            import json

            result = client.query(query)
            rows = [dict(zip(result.column_names, row)) for row in result.result_rows]
            with open(output, "w", encoding="utf-8") as f:
                json.dump(rows, f, default=str, indent=2)
            console.print(
                f"[green]✓[/green] {result.row_count:,} rows → [cyan]{output}[/cyan]"
            )

        elif fmt == "parquet":
            try:
                import pyarrow as pa
                import pyarrow.parquet as pq
            except ImportError:
                console.print(
                    "[red]pyarrow is required for Parquet export.[/red]\n"
                    "Install it with:  pip install pyarrow"
                )
                raise typer.Exit(1)

            result = client.query(query)
            arrays = [
                pa.array([row[i] for row in result.result_rows])
                for i in range(len(result.column_names))
            ]
            tbl = pa.table(dict(zip(result.column_names, arrays)))
            pq.write_table(tbl, output)
            console.print(
                f"[green]✓[/green] {result.row_count:,} rows → [cyan]{output}[/cyan]"
            )

        else:
            console.print(
                f"[red]Unknown format '{fmt}'.[/red]  Supported: csv, json, parquet"
            )
            raise typer.Exit(1)
