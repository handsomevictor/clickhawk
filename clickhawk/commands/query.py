from typing import Optional
import typer
from rich.console import Console

app = typer.Typer(help="Execute SQL queries with rich output.", context_settings={"allow_interspersed_args": True})
console = Console()


@app.callback(invoke_without_command=True)
def run(
    sql: str = typer.Argument(..., help="SQL query to execute"),
    output_format: str = typer.Option("table", "--format", "-f", help="Output format: table|json|csv"),
    limit: Optional[int] = typer.Option(None, "--limit", "-l", help="Limit number of rows"),
) -> None:
    """Execute a SQL query and display the results."""
    from clickhawk.core.client import get_client
    from clickhawk.formatters.table import print_result

    if limit:
        sql = f"SELECT * FROM ({sql}) LIMIT {limit}"

    client = get_client()
    result = client.query(sql)
    print_result(result, output_format=output_format)
