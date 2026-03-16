import csv
import json
import sys
from rich.console import Console
from rich.table import Table

console = Console()


def print_result(result, output_format: str = "table") -> None:
    if output_format == "json":
        rows = [dict(zip(result.column_names, row)) for row in result.result_rows]
        console.print_json(json.dumps(rows, default=str))
    elif output_format == "csv":
        writer = csv.writer(sys.stdout)
        writer.writerow(result.column_names)
        for row in result.result_rows:
            writer.writerow([str(v) for v in row])
    else:
        t = Table(show_header=True, header_style="bold cyan")
        for col in result.column_names:
            t.add_column(col)
        for row in result.result_rows:
            t.add_row(*[str(v) for v in row])
        console.print(t)
        console.print(f"[dim]{result.row_count} rows[/dim]")
