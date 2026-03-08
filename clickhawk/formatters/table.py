import json
from rich.console import Console
from rich.table import Table

console = Console()


def print_result(result, format: str = "table") -> None:
    if format == "json":
        rows = [dict(zip(result.column_names, row)) for row in result.result_rows]
        console.print_json(json.dumps(rows, default=str))
    elif format == "csv":
        print(",".join(result.column_names))
        for row in result.result_rows:
            print(",".join(str(v) for v in row))
    else:
        t = Table(show_header=True, header_style="bold cyan")
        for col in result.column_names:
            t.add_column(col)
        for row in result.result_rows:
            t.add_row(*[str(v) for v in row])
        console.print(t)
        console.print(f"[dim]{result.row_count} rows[/dim]")
