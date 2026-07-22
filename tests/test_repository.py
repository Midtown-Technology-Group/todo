from datetime import date, datetime

from todo.repository import TodoRepository


class FakeGraphClient:
    def __init__(self) -> None:
        self.posts = []
        self.patches = []
        self.tasks = [
            {
                "id": "item-1",
                "title": "Existing task",
                "status": "notStarted",
                "importance": "normal",
                "dueDateTime": {
                    "dateTime": "2027-01-15T00:00:00",
                    "timeZone": "Eastern Standard Time",
                },
                "reminderDateTime": {
                    "dateTime": "2027-01-15T09:00:00",
                    "timeZone": "Eastern Standard Time",
                },
                "isReminderOn": True,
                "body": {"content": "Existing note", "contentType": "html"},
                "recurrence": {
                    "pattern": {"type": "absoluteYearly", "interval": 1},
                    "range": {"type": "noEnd", "startDate": "2027-01-15"},
                },
                "hasAttachments": True,
            }
        ]

    def get(self, path):
        assert path == "/me/todo/lists"
        return {"value": [{"id": "list-1", "displayName": "Projects"}]}

    def get_all(self, path):
        assert path == "/me/todo/lists/list-1/tasks"
        return {"value": self.tasks}

    def post(self, path, payload):
        self.posts.append((path, payload))
        if path.endswith("/attachments"):
            return {
                "id": "attachment-1",
                "name": payload["name"],
                "contentType": payload["contentType"],
                "size": payload["size"],
            }
        return {"id": "item-new", "status": "notStarted", **payload}

    def patch(self, path, payload):
        self.patches.append((path, payload))
        return {**self.tasks[0], **payload}


def test_add_item_maps_richer_fields_to_graph_payload():
    client = FakeGraphClient()
    repo = TodoRepository(client)

    item = repo.add_item(
        "Renew keys",
        list_name="Projects",
        star=True,
        due=date(2027, 1, 15),
        remind=datetime(2027, 1, 15, 9, 0),
        note="A < B\nVerify fingerprint",
        repeat="yearly",
        time_zone="Eastern Standard Time",
    )

    path, payload = client.posts[0]
    assert path == "/me/todo/lists/list-1/tasks"
    assert payload["title"] == "Renew keys"
    assert payload["importance"] == "high"
    assert payload["dueDateTime"] == {
        "dateTime": "2027-01-15T00:00:00",
        "timeZone": "Eastern Standard Time",
    }
    assert payload["reminderDateTime"] == {
        "dateTime": "2027-01-15T09:00:00",
        "timeZone": "Eastern Standard Time",
    }
    assert payload["isReminderOn"] is True
    assert payload["body"] == {
        "content": "A &lt; B<br>Verify fingerprint",
        "contentType": "html",
    }
    assert payload["recurrence"] == {
        "pattern": {
            "type": "absoluteYearly",
            "interval": 1,
            "dayOfMonth": 15,
            "month": 1,
        },
        "range": {"type": "noEnd", "startDate": "2027-01-15"},
    }
    assert item.id == "item-new"
    assert item.due_at == datetime(2027, 1, 15)
    assert item.body_content == "A &lt; B<br>Verify fingerprint"


def test_update_item_uses_existing_due_date_for_recurrence():
    client = FakeGraphClient()
    repo = TodoRepository(client)

    item = repo.update_item("item-1", note="Updated note", repeat="monthly")

    path, payload = client.patches[0]
    assert path == "/me/todo/lists/list-1/tasks/item-1"
    assert payload["body"] == {"content": "Updated note", "contentType": "html"}
    assert payload["recurrence"] == {
        "pattern": {"type": "absoluteMonthly", "interval": 1, "dayOfMonth": 15},
        "range": {"type": "noEnd", "startDate": "2027-01-15"},
    }
    assert item.body_content == "Updated note"


def test_attach_file_maps_small_attachment_payload():
    client = FakeGraphClient()
    repo = TodoRepository(client)

    attachment = repo.attach_file(
        "item-1",
        name="evidence.txt",
        content_type="text/plain",
        content_bytes="cHJvb2Y=",
        size=5,
    )

    path, payload = client.posts[0]
    assert path == "/me/todo/lists/list-1/tasks/item-1/attachments"
    assert payload == {
        "@odata.type": "#microsoft.graph.taskFileAttachment",
        "name": "evidence.txt",
        "contentType": "text/plain",
        "contentBytes": "cHJvb2Y=",
        "size": 5,
    }
    assert attachment.id == "attachment-1"


def test_list_items_preserves_richer_fields_for_json_output():
    client = FakeGraphClient()
    repo = TodoRepository(client)

    item = repo.list_items(list_name="Projects")[0]

    assert item.due_at == datetime(2027, 1, 15)
    assert item.due_time_zone == "Eastern Standard Time"
    assert item.reminder_at == datetime(2027, 1, 15, 9, 0)
    assert item.reminder_time_zone == "Eastern Standard Time"
    assert item.is_reminder_on is True
    assert item.body_content == "Existing note"
    assert item.body_content_type == "html"
    assert item.recurrence["pattern"]["type"] == "absoluteYearly"
    assert item.has_attachments is True
