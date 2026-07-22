from datetime import datetime

from typer.testing import CliRunner

from todo.main import app
from todo.models import PlannerPlan, PlannerTask, TodoAttachment, TodoItem, TodoList


class FakeService:
    def __init__(self) -> None:
        self.added_lists: list[str] = []
        self.added_items: list[dict] = []
        self.updated_items: list[dict] = []
        self.attached_files: list[tuple[str, str]] = []

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

    def add_item(
        self,
        subject: str,
        list_name: str | None,
        star: bool,
        due=None,
        remind=None,
        note=None,
        repeat=None,
        time_zone="UTC",
    ):
        self.added_items.append(
            {
                "subject": subject,
                "list_name": list_name,
                "star": star,
                "due": due,
                "remind": remind,
                "note": note,
                "repeat": repeat,
                "time_zone": time_zone,
            }
        )
        return TodoItem(
            id="new",
            subject=subject,
            list_id="inbox",
            is_important=star,
            due_at=due,
            due_time_zone=time_zone if due else None,
            reminder_at=remind,
            reminder_time_zone=time_zone if remind else None,
            is_reminder_on=remind is not None,
            body_content=note,
            body_content_type="html" if note is not None else None,
        )

    def update_item(
        self,
        item_id,
        due=None,
        remind=None,
        note=None,
        repeat=None,
        time_zone="UTC",
    ):
        self.updated_items.append(
            {
                "item_id": item_id,
                "due": due,
                "remind": remind,
                "note": note,
                "repeat": repeat,
                "time_zone": time_zone,
            }
        )
        return TodoItem(id=item_id, subject="Updated", due_at=due)

    def attach_file(self, item_id, file_path):
        self.attached_files.append((item_id, file_path.name))
        return TodoAttachment(id="attachment-1", name=file_path.name, size=file_path.stat().st_size)

    def complete_items(self, ids=None, list_name=None, older_than=None, complete_all=False):
        return 1

    def remove_items(self, ids=None, list_name=None, older_than=None, remove_all=False, completed_only=False):
        return 1

    def remove_list(self, name: str):
        return True

    def list_planner_plans(self):
        return [PlannerPlan(id="plan-1", title="Ops")]

    def list_planner_tasks(self, plan_id=None, include_completed=False):
        return [
            PlannerTask(
                id="task-1",
                title="Review stale queue",
                plan_id=plan_id or "plan-1",
                plan_title="Ops",
            )
        ]


def test_list_command_supports_json_output(monkeypatch):
    monkeypatch.setattr("todo.main.build_service", lambda: FakeService())
    runner = CliRunner()

    result = runner.invoke(app, ["--output", "json", "list", "--all"])

    assert result.exit_code == 0
    assert '"subject":"Inbox item"' in result.stdout
    assert '"subject":"Done item"' in result.stdout


def test_add_list_command_creates_list(monkeypatch):
    service = FakeService()
    monkeypatch.setattr("todo.main.build_service", lambda: service)
    monkeypatch.setattr("todo.main.has_write_scope", lambda: True)
    runner = CliRunner()

    result = runner.invoke(app, ["add", "list", "Projects"])

    assert result.exit_code == 0
    assert service.added_lists == ["Projects"]
    assert "Projects" in result.stdout


def test_add_item_command_passes_list_and_star(monkeypatch):
    service = FakeService()
    monkeypatch.setattr("todo.main.build_service", lambda: service)
    monkeypatch.setattr("todo.main.has_write_scope", lambda: True)
    runner = CliRunner()

    result = runner.invoke(app, ["add", "item", "Ship feature", "--list", "Projects", "--star"])

    assert result.exit_code == 0
    assert service.added_items == [
        {
            "subject": "Ship feature",
            "list_name": "Projects",
            "star": True,
            "due": None,
            "remind": None,
            "note": None,
            "repeat": None,
            "time_zone": "UTC",
        }
    ]


def test_add_item_command_passes_richer_fields_and_returns_json(monkeypatch):
    service = FakeService()
    monkeypatch.setattr("todo.main.build_service", lambda: service)
    monkeypatch.setattr("todo.main.has_write_scope", lambda: True)
    runner = CliRunner()

    result = runner.invoke(
        app,
        [
            "--output",
            "json",
            "add",
            "item",
            "Renew keys",
            "--star",
            "--due",
            "2027-01-15",
            "--remind",
            "2027-01-15T09:00:00",
            "--note",
            "Verify fingerprint",
            "--repeat",
            "yearly",
            "--time-zone",
            "Eastern Standard Time",
        ],
    )

    assert result.exit_code == 0
    assert service.added_items[0]["due"] == datetime(2027, 1, 15)
    assert service.added_items[0]["remind"] == datetime(2027, 1, 15, 9, 0)
    assert service.added_items[0]["note"] == "Verify fingerprint"
    assert service.added_items[0]["repeat"] == "yearly"
    assert service.added_items[0]["time_zone"] == "Eastern Standard Time"
    assert '"status":"ok"' in result.stdout
    assert '"due_at":"2027-01-15T00:00:00"' in result.stdout
    assert '"body_content":"Verify fingerprint"' in result.stdout


def test_update_item_command_passes_richer_fields(monkeypatch):
    service = FakeService()
    monkeypatch.setattr("todo.main.build_service", lambda: service)
    monkeypatch.setattr("todo.main.has_write_scope", lambda: True)
    runner = CliRunner()

    result = runner.invoke(
        app,
        ["update", "item", "task-1", "--due", "2027-02-01", "--note", "New note"],
    )

    assert result.exit_code == 0
    assert service.updated_items[0]["item_id"] == "task-1"
    assert service.updated_items[0]["due"] == datetime(2027, 2, 1)
    assert service.updated_items[0]["note"] == "New note"


def test_my_day_options_report_graph_limitation_without_creating_item(monkeypatch):
    service = FakeService()
    monkeypatch.setattr("todo.main.build_service", lambda: service)
    monkeypatch.setattr("todo.main.has_write_scope", lambda: True)
    runner = CliRunner()

    for option in ("--my-day", "--no-my-day"):
        result = runner.invoke(app, ["add", "item", "Plan day", option])
        assert result.exit_code != 0
        assert "does not expose My Day membership" in result.output
    assert service.added_items == []


def test_attach_file_command_passes_file_and_returns_json(monkeypatch, tmp_path):
    service = FakeService()
    monkeypatch.setattr("todo.main.build_service", lambda: service)
    monkeypatch.setattr("todo.main.has_write_scope", lambda: True)
    attachment = tmp_path / "evidence.txt"
    attachment.write_text("proof", encoding="utf-8")
    runner = CliRunner()

    result = runner.invoke(
        app,
        ["--output", "json", "attach", "file", "task-1", str(attachment)],
    )

    assert result.exit_code == 0
    assert service.attached_files == [("task-1", "evidence.txt")]
    assert '"name":"evidence.txt"' in result.stdout


def test_write_commands_explain_read_only_default(monkeypatch):
    monkeypatch.setattr("todo.main.has_write_scope", lambda: False)
    runner = CliRunner()

    result = runner.invoke(app, ["add", "list", "Projects"])

    assert result.exit_code != 0
    combined_output = f"{result.stdout}\n{result.stderr}"
    assert "Tasks.ReadWrite" in combined_output


def test_planner_plans_command_supports_json_output(monkeypatch):
    monkeypatch.setattr("todo.main.build_service", lambda: FakeService())
    runner = CliRunner()

    result = runner.invoke(app, ["--output", "json", "planner", "plans"])

    assert result.exit_code == 0
    assert '"title":"Ops"' in result.stdout


def test_planner_tasks_command_supports_plan_filter(monkeypatch):
    monkeypatch.setattr("todo.main.build_service", lambda: FakeService())
    runner = CliRunner()

    result = runner.invoke(app, ["--output", "json", "planner", "tasks", "--plan-id", "plan-1"])

    assert result.exit_code == 0
    assert '"title":"Review stale queue"' in result.stdout
    assert '"plan_id":"plan-1"' in result.stdout
