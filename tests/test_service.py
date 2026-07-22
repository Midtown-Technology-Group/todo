from datetime import date, datetime

import pytest

from todo.models import PlannerPlan, PlannerTask, TodoAttachment, TodoItem
from todo.service import MAX_SIMPLE_ATTACHMENT_BYTES, TodoService


class FakeRepository:
    def __init__(self) -> None:
        self.completed = []
        self.removed = []
        self.added = []
        self.updated = []
        self.attachments = []

    def list_items(self, list_name=None, include_completed=False):
        return [
            TodoItem(id="1", subject="Old open", list_id="inbox", created="2024-01-01T00:00:00Z"),
            TodoItem(
                id="2",
                subject="Done",
                list_id="inbox",
                is_completed=True,
                status="completed",
                completed="2024-01-02T00:00:00Z",
            ),
        ]

    def add_list(self, name):
        return {"id": "list-1", "displayName": name}

    def add_item(self, subject, list_name=None, star=False, **fields):
        self.added.append((subject, list_name, star, fields))
        return TodoItem(id="item-1", subject=subject, is_important=star)

    def update_item(self, item_id, **fields):
        self.updated.append((item_id, fields))
        return TodoItem(id=item_id, subject="Updated")

    def attach_file(self, item_id, **fields):
        self.attachments.append((item_id, fields))
        return TodoAttachment(
            id="attachment-1",
            name=fields["name"],
            content_type=fields["content_type"],
            size=fields["size"],
        )

    def complete_item(self, item_id):
        self.completed.append(item_id)

    def remove_item(self, item_id):
        self.removed.append(item_id)

    def remove_list(self, name):
        return True

    def list_planner_plans(self):
        return [PlannerPlan(id="plan-1", title="Ops")]

    def list_planner_tasks(self, plan_id=None, include_completed=False):
        return [
            PlannerTask(
                id="task-1",
                title="Review stale queue",
                plan_id=plan_id or "plan-1",
                percent_complete=100 if include_completed else 0,
            )
        ]


def test_complete_items_filters_by_id():
    repo = FakeRepository()
    service = TodoService(repo)

    count = service.complete_items(ids=["1"])

    assert count == 1
    assert repo.completed == ["1"]


def test_remove_items_can_limit_to_completed():
    repo = FakeRepository()
    service = TodoService(repo)

    count = service.remove_items(completed_only=True, remove_all=True)

    assert count == 1
    assert repo.removed == ["2"]


def test_list_planner_tasks_delegates_to_repository():
    repo = FakeRepository()
    service = TodoService(repo)

    tasks = service.list_planner_tasks(plan_id="plan-1")

    assert tasks[0].title == "Review stale queue"
    assert tasks[0].plan_id == "plan-1"


def test_add_item_delegates_richer_fields():
    repo = FakeRepository()
    service = TodoService(repo)

    item = service.add_item(
        "Renew keys",
        list_name="Projects",
        star=True,
        due=date(2027, 1, 15),
        remind=datetime(2027, 1, 15, 9, 0),
        note="Verify fingerprint",
        repeat="yearly",
        time_zone="Eastern Standard Time",
    )

    assert item.id == "item-1"
    assert repo.added[0][0:3] == ("Renew keys", "Projects", True)
    assert repo.added[0][3]["due"] == date(2027, 1, 15)
    assert repo.added[0][3]["repeat"] == "yearly"


def test_attach_file_encodes_small_file(tmp_path):
    repo = FakeRepository()
    service = TodoService(repo)
    file_path = tmp_path / "evidence.txt"
    file_path.write_bytes(b"proof")

    attachment = service.attach_file("item-1", file_path)

    assert attachment.name == "evidence.txt"
    assert repo.attachments[0][1]["content_type"] == "text/plain"
    assert repo.attachments[0][1]["content_bytes"] == "cHJvb2Y="
    assert repo.attachments[0][1]["size"] == 5


def test_attach_file_reports_large_file_limit(tmp_path):
    repo = FakeRepository()
    service = TodoService(repo)
    file_path = tmp_path / "large.bin"
    file_path.write_bytes(b"0" * MAX_SIMPLE_ATTACHMENT_BYTES)

    with pytest.raises(ValueError, match="under 3 MB"):
        service.attach_file("item-1", file_path)

    assert repo.attachments == []
