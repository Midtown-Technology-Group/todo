from __future__ import annotations

from datetime import datetime

from todo_cli.models import TodoItem, TodoList


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

    def add_item(self, subject: str, list_name: str | None, star: bool) -> TodoItem:
        raw = self.repository.add_item(subject, list_name=list_name, star=star)
        return TodoItem(
            id=raw.get("id"),
            subject=raw.get("title", subject),
            is_important=raw.get("importance") == "high",
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

    @staticmethod
    def _filter_items(items: list[TodoItem], ids: list[str] | None = None, older_than: datetime | None = None) -> list[TodoItem]:
        filtered = items
        if ids:
            filtered = [item for item in filtered if item.id in ids]
        if older_than:
            filtered = [item for item in filtered if item.created and item.created < older_than]
        return filtered

