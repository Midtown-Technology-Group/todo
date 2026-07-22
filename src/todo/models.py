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
    due_at: datetime | None = None
    due_time_zone: str | None = None
    reminder_at: datetime | None = None
    reminder_time_zone: str | None = None
    is_reminder_on: bool = False
    body_content: str | None = None
    body_content_type: str | None = None
    recurrence: dict | None = None
    has_attachments: bool = False


class TodoAttachment(BaseModel):
    id: str | None = None
    name: str
    content_type: str | None = None
    size: int | None = None


class TodoList(BaseModel):
    id: str | None = None
    name: str
    tasks: list[TodoItem] = Field(default_factory=list)


class PlannerPlan(BaseModel):
    id: str | None = None
    title: str
    owner: str | None = None


class PlannerTask(BaseModel):
    id: str | None = None
    title: str
    plan_id: str | None = None
    plan_title: str | None = None
    bucket_id: str | None = None
    percent_complete: int = 0
    due_at: datetime | None = None
    created: datetime | None = None
    completed: datetime | None = None
