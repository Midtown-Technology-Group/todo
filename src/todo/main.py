from __future__ import annotations

from datetime import datetime
from pathlib import Path

import typer
from mtg_microsoft_auth import GraphAuthSession, GraphClient

from todo.config import has_write_scope, load_auth_config
from todo.output import OutputRenderer
from todo.repository import TodoRepository
from todo.service import TodoService

app = typer.Typer(help="Manage Microsoft To Do items.")
add_app = typer.Typer(help="Add a list or item.")
remove_app = typer.Typer(help="Delete items or lists.")
update_app = typer.Typer(help="Update an item.")
attach_app = typer.Typer(help="Attach a file to an item.")
planner_app = typer.Typer(help="Inspect Microsoft Planner plans and tasks.")
app.add_typer(add_app, name="add")
app.add_typer(remove_app, name="remove")
app.add_typer(update_app, name="update")
app.add_typer(attach_app, name="attach")
app.add_typer(planner_app, name="planner")


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


def _reject_my_day(my_day: bool | None) -> None:
    if my_day is None:
        return
    raise typer.BadParameter(
        "Microsoft Graph v1.0 does not expose My Day membership for Microsoft To Do "
        "tasks. Add or remove the task from My Day in a Microsoft To Do client."
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
    due: datetime | None = typer.Option(None, "--due", help="Due date in YYYY-MM-DD format."),
    remind: datetime | None = typer.Option(
        None,
        "--remind",
        help="Reminder date and time in ISO 8601 format.",
    ),
    note: str | None = typer.Option(None, "--note", help="Plain-text task note."),
    repeat: str | None = typer.Option(
        None,
        "--repeat",
        help="Recurrence: daily, weekly, monthly, or yearly. Requires --due.",
    ),
    time_zone: str = typer.Option("UTC", "--time-zone", help="Graph/Windows time-zone name."),
    my_day: bool | None = typer.Option(
        None,
        "--my-day/--no-my-day",
        help="Request adding or removing My Day membership.",
    ),
) -> None:
    _reject_my_day(my_day)
    _require_write_scope()
    service = build_service()
    renderer = _renderer(ctx.obj["output"])
    try:
        item = service.add_item(
            subject,
            list_name=list_name,
            star=star,
            due=due,
            remind=remind,
            note=note,
            repeat=repeat,
            time_zone=time_zone,
        )
    except ValueError as exc:
        raise typer.BadParameter(str(exc)) from exc
    renderer.success(f"Item '{item.subject}' added successfully.", data=item)


@update_app.command("item")
def update_item(
    ctx: typer.Context,
    item_id: str,
    due: datetime | None = typer.Option(None, "--due", help="Due date in YYYY-MM-DD format."),
    remind: datetime | None = typer.Option(
        None,
        "--remind",
        help="Reminder date and time in ISO 8601 format.",
    ),
    note: str | None = typer.Option(None, "--note", help="Plain-text task note."),
    repeat: str | None = typer.Option(
        None,
        "--repeat",
        help="Recurrence: daily, weekly, monthly, or yearly.",
    ),
    time_zone: str = typer.Option("UTC", "--time-zone", help="Graph/Windows time-zone name."),
    my_day: bool | None = typer.Option(
        None,
        "--my-day/--no-my-day",
        help="Request adding or removing My Day membership.",
    ),
) -> None:
    _reject_my_day(my_day)
    _require_write_scope()
    if due is None and remind is None and note is None and repeat is None:
        raise typer.BadParameter("Set at least one of --due, --remind, --note, or --repeat.")
    service = build_service()
    renderer = _renderer(ctx.obj["output"])
    try:
        item = service.update_item(
            item_id,
            due=due,
            remind=remind,
            note=note,
            repeat=repeat,
            time_zone=time_zone,
        )
    except ValueError as exc:
        raise typer.BadParameter(str(exc)) from exc
    renderer.success(f"Item '{item.subject}' updated successfully.", data=item)


@attach_app.command("file")
def attach_file(
    ctx: typer.Context,
    item_id: str,
    file_path: Path = typer.Argument(
        ...,
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        resolve_path=True,
    ),
) -> None:
    _require_write_scope()
    service = build_service()
    renderer = _renderer(ctx.obj["output"])
    try:
        attachment = service.attach_file(item_id, file_path)
    except ValueError as exc:
        raise typer.BadParameter(str(exc)) from exc
    renderer.success(f"Attached '{attachment.name}' successfully.", data=attachment)


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


@planner_app.command("plans")
def list_planner_plans(ctx: typer.Context) -> None:
    service = build_service()
    renderer = _renderer(ctx.obj["output"])
    renderer.render_planner_plans(service.list_planner_plans())


@planner_app.command("tasks")
def list_planner_tasks(
    ctx: typer.Context,
    plan_id: str | None = typer.Option(None, "--plan-id"),
    all_items: bool = typer.Option(False, "--all", "-a"),
) -> None:
    service = build_service()
    renderer = _renderer(ctx.obj["output"])
    renderer.render_planner_tasks(
        service.list_planner_tasks(plan_id=plan_id, include_completed=all_items)
    )


def main() -> None:
    app()


if __name__ == "__main__":
    main()
