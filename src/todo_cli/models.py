from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class TodoItem(BaseModel):
    id: str | None = None
    subject: str
    list_id: str | None = None
    is_completed: bool = False
    is_important: bool = False
    status: str = "notStarted"
    completed: datetime | None = None
    created: datetime | None = None


class TodoList(BaseModel):
    id: str | None = None
    name: str
    tasks: list[TodoItem] = Field(default_factory=list)

