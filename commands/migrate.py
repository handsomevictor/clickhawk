import typer
from rich.console import Console

app = typer.Typer(help="Schema migrations.")
console = Console()


@app.command()
def run() -> None:
    """Run pending migrations. (coming in v0.2)"""
    console.print("[yellow]Migration support is planned for v0.2.[/yellow]")


@app.command()
def status() -> None:
    """Show migration status. (coming in v0.2)"""
    console.print("[yellow]Migration support is planned for v0.2.[/yellow]")
