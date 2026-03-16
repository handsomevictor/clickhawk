import typer
from rich.console import Console
from rich.tree import Tree

app = typer.Typer(
    help="Show colorized EXPLAIN plan.",
    context_settings={"allow_interspersed_args": True},
)
console = Console()

_NODE_COLORS: dict[str, str] = {
    "ReadFromMergeTree": "cyan",
    "ReadFromStorage": "cyan",
    "MergeTree": "cyan",
    "Filter": "yellow",
    "Aggregating": "magenta",
    "Sorting": "blue",
    "MergingSorted": "blue",
    "Join": "red",
    "Limit": "green",
    "Union": "bright_blue",
    "CreatingSet": "yellow",
    "Expression": "dim",
    "SettingQuotaAndLimits": "dim",
}


def _colorize(label: str) -> str:
    for keyword, color in _NODE_COLORS.items():
        if keyword in label:
            return f"[{color}]{label}[/{color}]"
    return label


@app.callback(invoke_without_command=True)
def run(
    sql: str = typer.Argument(..., help="SQL query to explain"),
    kind: str = typer.Option(
        "plan", "--kind", "-k", help="Explain type: plan|pipeline|syntax"
    ),
    actions: bool = typer.Option(True, "--actions/--no-actions", help="Show actions (plan only)"),
    indexes: bool = typer.Option(True, "--indexes/--no-indexes", help="Show indexes (plan only)"),
) -> None:
    """Show a colorized EXPLAIN output as an indented tree."""
    from clickhawk.core.client import get_client

    client = get_client()

    if kind == "syntax":
        explain_sql = f"EXPLAIN SYNTAX {sql}"
    elif kind == "pipeline":
        explain_sql = f"EXPLAIN PIPELINE {sql}"
    else:
        flags = []
        if actions:
            flags.append("actions=1")
        if indexes:
            flags.append("indexes=1")
        explain_sql = f"EXPLAIN PLAN {', '.join(flags)} {sql}"

    result = client.query(explain_sql)
    lines = [row[0] for row in result.result_rows if row[0].strip()]

    if not lines:
        console.print("[yellow]No EXPLAIN output.[/yellow]")
        return

    # Parse indentation and build a Rich Tree
    root = Tree(f"[bold]EXPLAIN {kind.upper()}[/bold]")
    # stack entries: (indent_level, tree_node)
    stack: list[tuple[int, Tree]] = [(-1, root)]

    for line in lines:
        stripped = line.lstrip()
        indent = len(line) - len(stripped)
        label = _colorize(stripped)

        while len(stack) > 1 and stack[-1][0] >= indent:
            stack.pop()

        child = stack[-1][1].add(label)
        stack.append((indent, child))

    console.print(root)
