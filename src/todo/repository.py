from __future__ import annotations

from todo.models import PlannerPlan, PlannerTask, TodoItem, TodoList


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

    def add_item(self, subject: str, list_name: str | None = None, star: bool = False):
        list_id = self._resolve_list_id(list_name)
        return self.graph_client.post(
            f"/me/todo/lists/{list_id}/tasks",
            {
                "title": subject,
                "importance": "high" if star else "normal",
            },
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

    @staticmethod
    def _map_item(raw: dict, list_id: str | None) -> TodoItem:
        status = raw.get("status", "notStarted")
        completed = raw.get("completedDateTime", {})
        created = raw.get("createdDateTime")
        return TodoItem(
            id=raw.get("id"),
            subject=raw.get("title", ""),
            list_id=list_id,
            is_completed=status == "completed",
            is_important=raw.get("importance") == "high",
            status=status,
            completed=completed.get("dateTime") if isinstance(completed, dict) else None,
            created=created,
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
