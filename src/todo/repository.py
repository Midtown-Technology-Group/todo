from __future__ import annotations

from datetime import date, datetime, time, timezone
from html import escape

from todo.models import PlannerPlan, PlannerTask, TodoAttachment, TodoItem, TodoList


class TodoRepository:
    def __init__(self, graph_client) -> None:
        self.graph_client = graph_client

    def list_lists(self) -> list[TodoList]:
        payload = self.graph_client.get("/me/todo/lists")
        return [
            TodoList(id=item["id"], name=item["displayName"])
            for item in payload.get("value", [])
        ]

    def list_items(self, list_name: str | None = None, include_completed: bool = False) -> list[TodoItem]:
        lists = self.list_lists()
        target_lists = [todo_list for todo_list in lists if list_name is None or todo_list.name == list_name]
        items: list[TodoItem] = []
        for todo_list in target_lists:
            payload = self.graph_client.get_all(f"/me/todo/lists/{todo_list.id}/tasks")
            for raw in payload.get("value", []):
                item = self._map_item(raw, todo_list.id)
                if include_completed or not item.is_completed:
                    items.append(item)
        return items

    def add_list(self, name: str):
        return self.graph_client.post("/me/todo/lists", {"displayName": name})

    def add_item(
        self,
        subject: str,
        list_name: str | None = None,
        star: bool = False,
        due: date | None = None,
        remind: datetime | None = None,
        note: str | None = None,
        repeat: str | None = None,
        time_zone: str = "UTC",
    ) -> TodoItem:
        list_id = self._resolve_list_id(list_name)
        payload = {
            "title": subject,
            "importance": "high" if star else "normal",
        }
        payload.update(
            self._task_field_payload(
                due=due,
                remind=remind,
                note=note,
                repeat=repeat,
                time_zone=time_zone,
            )
        )
        raw = self.graph_client.post(
            f"/me/todo/lists/{list_id}/tasks",
            payload,
        )
        return self._map_item(raw, list_id)

    def update_item(
        self,
        item_id: str,
        due: date | None = None,
        remind: datetime | None = None,
        note: str | None = None,
        repeat: str | None = None,
        time_zone: str = "UTC",
    ) -> TodoItem:
        item = self._resolve_item(item_id)
        payload = self._task_field_payload(
            due=due,
            remind=remind,
            note=note,
            repeat=repeat,
            time_zone=time_zone,
            existing_due=item.due_at,
        )
        if not payload:
            raise ValueError("Set at least one of --due, --remind, --note, or --repeat.")
        raw = self.graph_client.patch(
            f"/me/todo/lists/{item.list_id}/tasks/{item_id}",
            payload,
        )
        return self._map_item(raw, item.list_id)

    def attach_file(
        self,
        item_id: str,
        name: str,
        content_type: str,
        content_bytes: str,
        size: int,
    ) -> TodoAttachment:
        item = self._resolve_item(item_id)
        raw = self.graph_client.post(
            f"/me/todo/lists/{item.list_id}/tasks/{item_id}/attachments",
            {
                "@odata.type": "#microsoft.graph.taskFileAttachment",
                "name": name,
                "contentType": content_type,
                "contentBytes": content_bytes,
                "size": size,
            },
        )
        return TodoAttachment(
            id=raw.get("id"),
            name=raw.get("name", name),
            content_type=raw.get("contentType", content_type),
            size=raw.get("size", size),
        )

    def complete_item(self, item_id: str) -> None:
        list_id = self._resolve_item(item_id).list_id
        self.graph_client.patch(
            f"/me/todo/lists/{list_id}/tasks/{item_id}",
            {"status": "completed"},
        )

    def remove_item(self, item_id: str) -> None:
        list_id = self._resolve_item(item_id).list_id
        self.graph_client.delete(f"/me/todo/lists/{list_id}/tasks/{item_id}")

    def remove_list(self, name: str) -> bool:
        list_id = self._resolve_list_id(name)
        self.graph_client.delete(f"/me/todo/lists/{list_id}")
        return True

    def list_planner_plans(self) -> list[PlannerPlan]:
        payload = self.graph_client.get_all("/me/planner/plans")
        return [
            PlannerPlan(
                id=raw.get("id"),
                title=raw.get("title", ""),
                owner=raw.get("owner"),
            )
            for raw in payload.get("value", [])
        ]

    def list_planner_tasks(
        self,
        plan_id: str | None = None,
        include_completed: bool = False,
    ) -> list[PlannerTask]:
        plans = self.list_planner_plans()
        plan_titles = {plan.id: plan.title for plan in plans}
        target_plans = [plan for plan in plans if plan_id is None or plan.id == plan_id]
        if plan_id and not target_plans:
            raise ValueError(f"No Planner plan found with id '{plan_id}'.")

        tasks: list[PlannerTask] = []
        for plan in target_plans:
            payload = self.graph_client.get_all(f"/planner/plans/{plan.id}/tasks")
            for raw in payload.get("value", []):
                task = self._map_planner_task(raw, plan_titles.get(plan.id))
                if include_completed or task.percent_complete < 100:
                    tasks.append(task)
        return tasks

    def _resolve_list_id(self, list_name: str | None) -> str:
        lists = self.list_lists()
        if list_name:
            for todo_list in lists:
                if todo_list.name == list_name:
                    return todo_list.id or ""
            raise ValueError(f"No list found with the name '{list_name}'.")
        if not lists:
            raise ValueError("No To Do lists were found.")
        return lists[0].id or ""

    def _resolve_item(self, item_id: str) -> TodoItem:
        for item in self.list_items(include_completed=True):
            if item.id == item_id:
                return item
        raise ValueError(f"No item found with id '{item_id}'.")

    @classmethod
    def _task_field_payload(
        cls,
        due: date | None = None,
        remind: datetime | None = None,
        note: str | None = None,
        repeat: str | None = None,
        time_zone: str = "UTC",
        existing_due: datetime | None = None,
    ) -> dict:
        payload: dict = {}
        if due is not None:
            payload["dueDateTime"] = cls._date_time_time_zone(due, time_zone)
        if remind is not None:
            payload["isReminderOn"] = True
            payload["reminderDateTime"] = cls._date_time_time_zone(remind, time_zone)
        if note is not None:
            payload["body"] = {
                "content": escape(note).replace("\n", "<br>"),
                "contentType": "html",
            }
        if repeat is not None:
            recurrence_start = due or (existing_due.date() if existing_due else None)
            if recurrence_start is None:
                raise ValueError("--repeat requires --due or an existing task due date.")
            if isinstance(recurrence_start, datetime):
                recurrence_start = recurrence_start.date()
            payload["recurrence"] = cls._recurrence(repeat, recurrence_start)
        return payload

    @staticmethod
    def _date_time_time_zone(value: date | datetime, time_zone: str) -> dict[str, str]:
        if not time_zone.strip():
            raise ValueError("--time-zone cannot be empty.")
        if isinstance(value, datetime):
            date_time = value
        else:
            date_time = datetime.combine(value, time.min)
        target_time_zone = time_zone
        if date_time.tzinfo is not None:
            date_time = date_time.astimezone(timezone.utc).replace(tzinfo=None)
            target_time_zone = "UTC"
        return {
            "dateTime": date_time.isoformat(timespec="seconds"),
            "timeZone": target_time_zone,
        }

    @staticmethod
    def _recurrence(frequency: str, start_date: date) -> dict:
        normalized = frequency.lower()
        if normalized == "daily":
            pattern = {"type": "daily", "interval": 1}
        elif normalized == "weekly":
            pattern = {
                "type": "weekly",
                "interval": 1,
                "daysOfWeek": [start_date.strftime("%A").lower()],
                "firstDayOfWeek": "monday",
            }
        elif normalized == "monthly":
            pattern = {
                "type": "absoluteMonthly",
                "interval": 1,
                "dayOfMonth": start_date.day,
            }
        elif normalized == "yearly":
            pattern = {
                "type": "absoluteYearly",
                "interval": 1,
                "dayOfMonth": start_date.day,
                "month": start_date.month,
            }
        else:
            raise ValueError("--repeat must be daily, weekly, monthly, or yearly.")
        return {
            "pattern": pattern,
            "range": {"type": "noEnd", "startDate": start_date.isoformat()},
        }

    @staticmethod
    def _map_item(raw: dict, list_id: str | None) -> TodoItem:
        status = raw.get("status", "notStarted")
        completed = raw.get("completedDateTime", {})
        created = raw.get("createdDateTime")
        due = raw.get("dueDateTime") or {}
        reminder = raw.get("reminderDateTime") or {}
        body = raw.get("body") or {}
        return TodoItem(
            id=raw.get("id"),
            subject=raw.get("title", ""),
            list_id=list_id,
            is_completed=status == "completed",
            is_important=raw.get("importance") == "high",
            status=status,
            completed=completed.get("dateTime") if isinstance(completed, dict) else None,
            created=created,
            due_at=due.get("dateTime") if isinstance(due, dict) else None,
            due_time_zone=due.get("timeZone") if isinstance(due, dict) else None,
            reminder_at=reminder.get("dateTime") if isinstance(reminder, dict) else None,
            reminder_time_zone=reminder.get("timeZone") if isinstance(reminder, dict) else None,
            is_reminder_on=raw.get("isReminderOn", False),
            body_content=body.get("content") if isinstance(body, dict) else None,
            body_content_type=body.get("contentType") if isinstance(body, dict) else None,
            recurrence=raw.get("recurrence"),
            has_attachments=raw.get("hasAttachments", False),
        )

    @staticmethod
    def _map_planner_task(raw: dict, plan_title: str | None = None) -> PlannerTask:
        completed = raw.get("completedDateTime")
        created = raw.get("createdDateTime")
        due = raw.get("dueDateTime")
        return PlannerTask(
            id=raw.get("id"),
            title=raw.get("title", ""),
            plan_id=raw.get("planId"),
            plan_title=plan_title,
            bucket_id=raw.get("bucketId"),
            percent_complete=raw.get("percentComplete") or 0,
            due_at=due,
            created=created,
            completed=completed,
        )
