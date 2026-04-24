from typer.testing import CliRunner

from todo_cli.cli import app
from todo_cli.models import TodoItem, TodoList


class FakeService:
    def __init__(self) -> None:
        self.added_lists: list[str] = []
        self.added_items: list[tuple[str, str | None, bool]] = []

    def list_items(self, list_name=None, include_completed=False, older_than=None):
        return [
            TodoItem(id="1", subject="Inbox item", list_id="inbox", status="notStarted"),
            TodoItem(
                id="2",
                subject="Done item",
                list_id="inbox",
                status="completed",
                is_completed=True,
            ),
        ]

    def add_list(self, name: str):
        self.added_lists.append(name)
        return TodoList(id="new", name=name)

    def add_item(self, subject: str, list_name: str | None, star: bool):
        self.added_items.append((subject, list_name, star))
        return TodoItem(id="new", subject=subject, list_id="inbox", is_important=star)

    def complete_items(self, ids=None, list_name=None, older_than=None, complete_all=False):
        return 1

    def remove_items(self, ids=None, list_name=None, older_than=None, remove_all=False, completed_only=False):
        return 1

    def remove_list(self, name: str):
        return True


def test_list_command_supports_json_output(monkeypatch):
    monkeypatch.setattr("todo_cli.cli.build_service", lambda: FakeService())
    runner = CliRunner()

    result = runner.invoke(app, ["--output", "json", "list", "--all"])

    assert result.exit_code == 0
    assert '"subject":"Inbox item"' in result.stdout
    assert '"subject":"Done item"' in result.stdout


def test_add_list_command_creates_list(monkeypatch):
    service = FakeService()
    monkeypatch.setattr("todo_cli.cli.build_service", lambda: service)
    monkeypatch.setattr("todo_cli.cli.has_write_scope", lambda: True)
    runner = CliRunner()

    result = runner.invoke(app, ["add", "list", "Projects"])

    assert result.exit_code == 0
    assert service.added_lists == ["Projects"]
    assert "Projects" in result.stdout


def test_add_item_command_passes_list_and_star(monkeypatch):
    service = FakeService()
    monkeypatch.setattr("todo_cli.cli.build_service", lambda: service)
    monkeypatch.setattr("todo_cli.cli.has_write_scope", lambda: True)
    runner = CliRunner()

    result = runner.invoke(app, ["add", "item", "Ship feature", "--list", "Projects", "--star"])

    assert result.exit_code == 0
    assert service.added_items == [("Ship feature", "Projects", True)]


def test_write_commands_explain_read_only_default(monkeypatch):
    monkeypatch.setattr("todo_cli.cli.has_write_scope", lambda: False)
    runner = CliRunner()

    result = runner.invoke(app, ["add", "list", "Projects"])

    assert result.exit_code != 0
    combined_output = f"{result.stdout}\n{result.stderr}"
    assert "Tasks.ReadWrite" in combined_output
