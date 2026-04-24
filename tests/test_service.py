from todo_cli.models import TodoItem
from todo_cli.service import TodoService


class FakeRepository:
    def __init__(self) -> None:
        self.completed = []
        self.removed = []

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

    def add_item(self, subject, list_name=None, star=False):
        return {"id": "item-1", "title": subject, "importance": "high" if star else "normal"}

    def complete_item(self, item_id):
        self.completed.append(item_id)

    def remove_item(self, item_id):
        self.removed.append(item_id)

    def remove_list(self, name):
        return True


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
