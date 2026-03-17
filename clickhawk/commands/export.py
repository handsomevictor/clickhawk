from typing import Optional

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

app = typer.Typer(
    help="Export query results to CSV, JSON, Parquet, or S3.",
    context_settings={"allow_interspersed_args": True},
)
console = Console()


@app.callback(invoke_without_command=True)
def run(
    sql: str = typer.Argument(..., help="SQL query or bare table name to export"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Local output file (e.g. out.csv, out.parquet)"),
    s3: Optional[str] = typer.Option(
        None, "--s3",
        help="S3 destination URI  (e.g. s3://my-bucket/path/out.csv). "
             "Reads AWS credentials from env vars or ~/.aws/credentials via boto3.",
    ),
    output_format: str = typer.Option(
        "", "--format", "-f",
        help="Format: csv|json|parquet  (auto-detected from file extension when omitted)",
    ),
    limit: Optional[int] = typer.Option(None, "--limit", "-l", help="Max rows to export"),
) -> None:
    """Export the results of a SQL query (or a full table) to a local file or S3."""
    from clickhawk.core.client import get_client

    if not output and not s3:
        console.print("[red]Provide --output (local file) or --s3 (S3 URI).[/red]")
        raise typer.Exit(1)

    # Determine destination and format
    dest = s3 if s3 else output
    assert dest is not None

    fmt = output_format.lower()
    if not fmt:
        key = dest.split("?")[0]  # strip query string if any
        ext = key.rsplit(".", 1)[-1].lower() if "." in key else ""
        fmt = ext if ext in ("csv", "json", "parquet") else "csv"

    # Validate optional dependencies early — before the spinner starts
    if s3:
        try:
            import boto3  # noqa: F401
        except ImportError:
            console.print(
                "[red]boto3 is required for S3 export.[/red]\n"
                "Install it with:  pip install boto3"
            )
            raise typer.Exit(1)
    if fmt == "parquet":
        try:
            import pyarrow  # noqa: F401
        except ImportError:
            console.print(
                "[red]pyarrow is required for Parquet export.[/red]\n"
                "Install it with:  pip install pyarrow"
            )
            raise typer.Exit(1)

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
        progress.add_task(f"Exporting → {dest} ({fmt})…", total=None)

        if s3:
            _export_s3(client, query, s3, fmt)
        elif fmt == "csv":
            import csv as _csv

            result = client.query(query)
            with open(dest, "w", newline="", encoding="utf-8") as f:
                writer = _csv.writer(f)
                writer.writerow(result.column_names)
                writer.writerows(result.result_rows)
            console.print(f"[green]✓[/green] {result.row_count:,} rows → [cyan]{dest}[/cyan]")

        elif fmt == "json":
            import json

            result = client.query(query)
            rows = [dict(zip(result.column_names, row)) for row in result.result_rows]
            with open(dest, "w", encoding="utf-8") as f:
                json.dump(rows, f, default=str, indent=2)
            console.print(f"[green]✓[/green] {result.row_count:,} rows → [cyan]{dest}[/cyan]")

        elif fmt == "parquet":
            import pyarrow as pa
            import pyarrow.parquet as pq

            result = client.query(query)
            arrays = [
                pa.array([row[i] for row in result.result_rows])
                for i in range(len(result.column_names))
            ]
            tbl = pa.table(dict(zip(result.column_names, arrays)))
            pq.write_table(tbl, dest)
            console.print(f"[green]✓[/green] {result.row_count:,} rows → [cyan]{dest}[/cyan]")

        else:
            console.print(f"[red]Unknown format '{fmt}'.[/red]  Supported: csv, json, parquet")
            raise typer.Exit(1)


def _export_s3(client, query: str, s3_uri: str, fmt: str) -> None:  # type: ignore[type-arg]
    """Write query results to S3 using boto3. Streams via an in-memory buffer."""
    try:
        import boto3  # type: ignore[import-untyped]
    except ImportError:
        console.print(
            "[red]boto3 is required for S3 export.[/red]\n"
            "Install it with:  pip install boto3"
        )
        raise typer.Exit(1)

    import io
    import csv as _csv
    import json

    # Parse s3://bucket/key
    if not s3_uri.startswith("s3://"):
        console.print("[red]S3 URI must start with s3://[/red]")
        raise typer.Exit(1)

    path = s3_uri[5:]  # strip "s3://"
    bucket, _, key = path.partition("/")
    if not bucket or not key:
        console.print("[red]Invalid S3 URI. Expected: s3://bucket/key[/red]")
        raise typer.Exit(1)

    result = client.query(query)
    s3_client = boto3.client("s3")

    if fmt == "csv":
        buf = io.StringIO()
        writer = _csv.writer(buf)
        writer.writerow(result.column_names)
        writer.writerows(result.result_rows)
        body = buf.getvalue().encode("utf-8")
        content_type = "text/csv"

    elif fmt == "json":
        rows = [dict(zip(result.column_names, row)) for row in result.result_rows]
        body = json.dumps(rows, default=str, indent=2).encode("utf-8")
        content_type = "application/json"

    elif fmt == "parquet":
        try:
            import pyarrow as pa
            import pyarrow.parquet as pq
        except ImportError:
            console.print("[red]pyarrow is required for Parquet export.[/red]\n"
                          "Install it with:  pip install pyarrow")
            raise typer.Exit(1)
        arrays = [
            pa.array([row[i] for row in result.result_rows])
            for i in range(len(result.column_names))
        ]
        tbl = pa.table(dict(zip(result.column_names, arrays)))
        buf_bytes = io.BytesIO()
        pq.write_table(tbl, buf_bytes)
        body = buf_bytes.getvalue()
        content_type = "application/octet-stream"

    else:
        console.print(f"[red]Unknown format '{fmt}'.[/red]  Supported: csv, json, parquet")
        raise typer.Exit(1)

    s3_client.put_object(Bucket=bucket, Key=key, Body=body, ContentType=content_type)
    console.print(
        f"[green]✓[/green] {result.row_count:,} rows → [cyan]{s3_uri}[/cyan]"
    )
