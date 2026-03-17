import typer
from rich.console import Console

from clickhawk.commands import check, explain, export, kill, migrate, monitor, profile, query, schema, slowlog, top

app = typer.Typer(
    name="ch",
    help="🦅 ClickHawk — The ClickHouse CLI for data engineers.",
    no_args_is_help=True,
)

app.add_typer(query.app,   name="query")
app.add_typer(profile.app, name="profile")
app.add_typer(slowlog.app, name="slowlog")
app.add_typer(schema.app,  name="schema")
app.add_typer(monitor.app, name="monitor")
app.add_typer(migrate.app, name="migrate")
app.add_typer(explain.app, name="explain")
app.add_typer(check.app,   name="check")
app.add_typer(export.app,  name="export")
app.add_typer(kill.app,    name="kill")
app.add_typer(top.app,     name="top")

console = Console()


@app.command()
def health() -> None:
    """Check ClickHouse connection and cluster health."""
    from clickhawk.core.client import get_client

    client = get_client()
    version  = client.command("SELECT version()")
    uptime   = client.command("SELECT formatReadableTimeDelta(uptime())")
    dbs      = client.command("SELECT count() FROM system.databases")
    tables   = client.command("SELECT count() FROM system.tables WHERE database NOT IN ('system','information_schema')")

    console.print(f"[green]✓[/green]  ClickHouse  [bold]{version}[/bold]")
    console.print(f"    Uptime   : {uptime}")
    console.print(f"    Databases: {dbs}")
    console.print(f"    Tables   : {tables}")


if __name__ == "__main__":
    app()
