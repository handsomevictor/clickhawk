import hashlib
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

app = typer.Typer(help="File-based schema migration management.")
console = Console()

_MIGRATION_TABLE = "_clickhawk_migrations"
_INIT_SQL = f"""
CREATE TABLE IF NOT EXISTS {_MIGRATION_TABLE}
(
    version     String,
    filename    String,
    checksum    String,
    applied_at  DateTime DEFAULT now()
)
ENGINE = MergeTree()
ORDER BY version
"""


def _ensure_table(client) -> None:  # type: ignore[type-arg]
    client.command(_INIT_SQL)


def _applied_map(client) -> dict[str, str]:  # type: ignore[type-arg]
    """Return {filename: applied_at} for all applied migrations."""
    r = client.query(
        f"SELECT filename, toString(applied_at) FROM {_MIGRATION_TABLE} ORDER BY version"
    )
    return {row[0]: row[1] for row in r.result_rows}


def _split_statements(sql: str) -> list[str]:
    """Split SQL on top-level semicolons (ignores semicolons inside string literals)."""
    statements: list[str] = []
    current: list[str] = []
    in_string = False
    string_char = ""
    for ch in sql:
        if in_string:
            current.append(ch)
            if ch == string_char:
                in_string = False
        elif ch in ("'", '"'):
            in_string = True
            string_char = ch
            current.append(ch)
        elif ch == ";":
            stmt = "".join(current).strip()
            if stmt:
                statements.append(stmt)
            current = []
        else:
            current.append(ch)
    remaining = "".join(current).strip()
    if remaining:
        statements.append(remaining)
    return statements


@app.command()
def run(
    migrations_dir: str = typer.Option(
        "migrations", "--dir", "-d",
        help="Directory containing .sql migration files",
    ),
    dry_run: bool = typer.Option(
        False, "--dry-run",
        help="Preview what would be applied without executing",
    ),
) -> None:
    """Apply all pending .sql migrations in order."""
    from clickhawk.core.client import get_client

    client = get_client()
    _ensure_table(client)

    path = Path(migrations_dir)
    if not path.exists():
        console.print(f"[red]Migrations directory '{migrations_dir}' not found.[/red]")
        raise typer.Exit(1)

    files = sorted(path.glob("*.sql"))
    if not files:
        console.print(f"[yellow]No .sql files found in '{migrations_dir}'.[/yellow]")
        raise typer.Exit(0)

    applied = set(_applied_map(client).keys())
    pending = [f for f in files if f.name not in applied]

    if not pending:
        console.print("[green]✓ All migrations already applied.[/green]")
        raise typer.Exit(0)

    for f in pending:
        content = f.read_text(encoding="utf-8").strip()
        checksum = hashlib.sha256(content.encode()).hexdigest()[:16]
        version = f.stem

        if dry_run:
            console.print(f"[dim][dry-run][/dim] would apply: [cyan]{f.name}[/cyan]")
            continue

        console.print(f"  Applying [cyan]{f.name}[/cyan] ...", end=" ")
        try:
            for stmt in _split_statements(content):
                if stmt.strip():
                    client.command(stmt)
            # Record in tracking table
            client.command(
                f"INSERT INTO {_MIGRATION_TABLE} (version, filename, checksum) "
                f"VALUES ('{version}', '{f.name}', '{checksum}')"
            )
            console.print("[green]✓[/green]")
        except Exception as exc:
            console.print(f"[red]✗ {exc}[/red]")
            raise typer.Exit(1)

    if not dry_run:
        console.print(f"[green]Applied {len(pending)} migration(s).[/green]")


@app.command()
def status(
    migrations_dir: str = typer.Option(
        "migrations", "--dir", "-d",
        help="Directory containing .sql migration files",
    ),
) -> None:
    """Show which migrations have been applied and which are pending."""
    from clickhawk.core.client import get_client

    client = get_client()
    _ensure_table(client)

    path = Path(migrations_dir)
    files = sorted(path.glob("*.sql")) if path.exists() else []
    applied = _applied_map(client)

    t = Table(title="Migration Status", header_style="bold cyan")
    t.add_column("File")
    t.add_column("Status")
    t.add_column("Applied At")

    for f in files:
        if f.name in applied:
            t.add_row(f.name, "[green]✓ applied[/green]", applied[f.name])
        else:
            t.add_row(f.name, "[yellow]⏳ pending[/yellow]", "—")

    # Applied migrations whose files no longer exist on disk
    file_names = {f.name for f in files}
    for fname, applied_at in sorted(applied.items()):
        if fname not in file_names:
            t.add_row(fname, "[dim]applied (file missing)[/dim]", applied_at)

    if t.row_count == 0:
        console.print("[dim]No migrations found.[/dim]")
    else:
        console.print(t)
