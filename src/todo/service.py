from __future__ import annotations

import base64
import mimetypes
from datetime import date, datetime
from pathlib import Path

from todo.models import TodoAttachment, TodoItem, TodoList

MAX_SIMPLE_ATTACHMENT_BYTES = 3 * 1024 * 1024


class TodoService:
    def __init__(self, repository) -> None:
        self.repository = repository

    def list_items(
        self,
        list_name: str | None = None,
        include_completed: bool = False,
        older_than: datetime | None = None,
    ) -> list[TodoItem]:
        items = self.repository.list_items(list_name=list_name, include_completed=include_completed)
        if older_than is None:
            return items
        return [
            item
            for item in items
            if item.is_completed and item.completed and item.completed < older_than
        ]

    def add_list(self, name: str) -> TodoList:
        raw = self.repository.add_list(name)
        return TodoList(id=raw.get("id"), name=raw.get("displayName", name))

    def add_item(
        self,
        subject: str,
        list_name: str | None,
        star: bool,
        due: date | None = None,
        remind: datetime | None = None,
        note: str | None = None,
        repeat: str | None = None,
        time_zone: str = "UTC",
    ) -> TodoItem:
        return self.repository.add_item(
            subject,
            list_name=list_name,
            star=star,
            due=due,
            remind=remind,
            note=note,
            repeat=repeat,
            time_zone=time_zone,
        )

    def update_item(
        self,
        item_id: str,
        due: date | None = None,
        remind: datetime | None = None,
        note: str | None = None,
        repeat: str | None = None,
        time_zone: str = "UTC",
    ) -> TodoItem:
        return self.repository.update_item(
            item_id,
            due=due,
            remind=remind,
            note=note,
            repeat=repeat,
            time_zone=time_zone,
        )

    def attach_file(self, item_id: str, file_path: Path) -> TodoAttachment:
        if not file_path.is_file():
            raise ValueError(f"Attachment file not found: {file_path}")
        size = file_path.stat().st_size
        if size >= MAX_SIMPLE_ATTACHMENT_BYTES:
            raise ValueError(
                "Attachments must be under 3 MB. Graph upload sessions for larger files "
                "are not supported by this CLI yet."
            )
        content_type = mimetypes.guess_type(file_path.name)[0] or "application/octet-stream"
        content_bytes = base64.b64encode(file_path.read_bytes()).decode("ascii")
        return self.repository.attach_file(
            item_id,
            name=file_path.name,
            content_type=content_type,
            content_bytes=content_bytes,
            size=size,
        )

    def complete_items(
        self,
        ids: list[str] | None = None,
        list_name: str | None = None,
        older_than: datetime | None = None,
        complete_all: bool = False,
    ) -> int:
        items = self.repository.list_items(list_name=list_name, include_completed=False)
        selected = self._filter_items(items, ids=ids, older_than=older_than)
        if ids or complete_all:
            for item in selected:
                self.repository.complete_item(item.id)
            return len(selected)
        for item in selected[:1]:
            self.repository.complete_item(item.id)
        return len(selected[:1])

    def remove_items(
        self,
        ids: list[str] | None = None,
        list_name: str | None = None,
        older_than: datetime | None = None,
        remove_all: bool = False,
        completed_only: bool = False,
    ) -> int:
        items = self.repository.list_items(list_name=list_name, include_completed=True)
        if completed_only:
            items = [item for item in items if item.is_completed]
        if older_than:
            items = [item for item in items if item.completed and item.completed < older_than]
        selected = self._filter_items(items, ids=ids)
        if ids or remove_all:
            for item in selected:
                self.repository.remove_item(item.id)
            return len(selected)
        for item in selected[:1]:
            self.repository.remove_item(item.id)
        return len(selected[:1])

    def remove_list(self, name: str) -> bool:
        return self.repository.remove_list(name)

    def list_planner_plans(self):
        return self.repository.list_planner_plans()

    def list_planner_tasks(
        self,
        plan_id: str | None = None,
        include_completed: bool = False,
    ):
        return self.repository.list_planner_tasks(
            plan_id=plan_id,
            include_completed=include_completed,
        )

    @staticmethod
    def _filter_items(items: list[TodoItem], ids: list[str] | None = None, older_than: datetime | None = None) -> list[TodoItem]:
        filtered = items
        if ids:
            filtered = [item for item in filtered if item.id in ids]
        if older_than:
            filtered = [item for item in filtered if item.created and item.created < older_than]
        return filtered
