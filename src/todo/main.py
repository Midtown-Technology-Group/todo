from __future__ import annotations

from datetime import datetime

import typer
from mtg_microsoft_auth import GraphAuthSession, GraphClient

from todo.config import has_write_scope, load_auth_config
from todo.output import OutputRenderer
from todo.repository import TodoRepository
from todo.service import TodoService

app = typer.Typer(help="Manage Microsoft To Do items.")
add_app = typer.Typer(help="Add a list or item.")
remove_app = typer.Typer(help="Delete items or lists.")
app.add_typer(add_app, name="add")
app.add_typer(remove_app, name="remove")


def build_service() -> TodoService:
    session = GraphAuthSession(load_auth_config())
    client = GraphClient(session)
    repo = TodoRepository(client)
    return TodoService(repo)


def _renderer(output: str) -> OutputRenderer:
    return OutputRenderer(mode=output)


def _require_write_scope() -> None:
    if has_write_scope():
        return
    raise typer.BadParameter(
        "This command needs Tasks.ReadWrite. Set TODO_SCOPES=Tasks.Read,Tasks.ReadWrite "
        "after you are ready to request elevated consent."
    )


@app.callback()
def root(
    ctx: typer.Context,
    output: str = typer.Option("interactive", "--output", "-o"),
) -> None:
    ctx.obj = {"output": output}


@app.command("list")
def list_items(
    ctx: typer.Context,
    list_name: str | None = typer.Argument(None),
    all_items: bool = typer.Option(False, "--all", "-a"),
    no_status: bool = typer.Option(False, "--no-status"),
    older_than: datetime | None = typer.Option(None, "--older-than"),
) -> None:
    del no_status
    service = build_service()
    renderer = _renderer(ctx.obj["output"])
    items = service.list_items(list_name=list_name, include_completed=all_items, older_than=older_than)
    renderer.render_items(items)


@add_app.command("list")
def add_list(ctx: typer.Context, name: str) -> None:
    _require_write_scope()
    service = build_service()
    renderer = _renderer(ctx.obj["output"])
    todo_list = service.add_list(name)
    renderer.success(f"List '{todo_list.name}' created successfully.")


@add_app.command("item")
def add_item(
    ctx: typer.Context,
    subject: str,
    list_name: str | None = typer.Option(None, "--list"),
    star: bool = typer.Option(False, "--star"),
) -> None:
    _require_write_scope()
    service = build_service()
    renderer = _renderer(ctx.obj["output"])
    item = service.add_item(subject, list_name=list_name, star=star)
    renderer.success(f"Item '{item.subject}' added successfully.")


@app.command("complete")
def complete_items(
    ctx: typer.Context,
    ids: list[str] = typer.Argument(None),
    list_name: str | None = typer.Option(None, "--list", "-l"),
    older_than: datetime | None = typer.Option(None, "--older-than"),
    complete_all: bool = typer.Option(False, "--all", "-a"),
) -> None:
    _require_write_scope()
    service = build_service()
    renderer = _renderer(ctx.obj["output"])
    count = service.complete_items(ids=ids or None, list_name=list_name, older_than=older_than, complete_all=complete_all)
    renderer.success(f"Completed {count} items.")


@remove_app.command("item")
def remove_item(
    ctx: typer.Context,
    ids: list[str] = typer.Argument(None),
    list_name: str | None = typer.Option(None, "--list", "-l"),
    older_than: datetime | None = typer.Option(None, "--older-than"),
    remove_all: bool = typer.Option(False, "--all", "-a"),
    completed_only: bool = typer.Option(False, "--completed", "-c"),
) -> None:
    _require_write_scope()
    service = build_service()
    renderer = _renderer(ctx.obj["output"])
    count = service.remove_items(
        ids=ids or None,
        list_name=list_name,
        older_than=older_than,
        remove_all=remove_all,
        completed_only=completed_only,
    )
    renderer.success(f"Deleted {count} items.")


@remove_app.command("list")
def remove_list(ctx: typer.Context, name: str) -> None:
    _require_write_scope()
    service = build_service()
    renderer = _renderer(ctx.obj["output"])
    service.remove_list(name)
    renderer.success(f"List '{name}' removed successfully.")


def main() -> None:
    app()


if __name__ == "__main__":
    main()
