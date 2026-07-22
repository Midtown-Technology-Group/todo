from __future__ import annotations

import json

from rich.console import Console


class OutputRenderer:
    def __init__(self, mode: str = "interactive") -> None:
        self.mode = mode
        self.console = Console()

    def render_items(self, items) -> None:
        if self.mode == "json":
            self.console.file.write(json.dumps([item.model_dump(mode="json") for item in items], separators=(",", ":")) + "\n")
            return
        for item in items:
            bullet = "[green]✓[/green]" if item.is_completed else "-"
            suffix = " [yellow]*[/yellow]" if item.is_important else ""
            self.console.print(f"{bullet} {item.subject}{suffix}")

    def render_planner_plans(self, plans) -> None:
        if self.mode == "json":
            self.console.file.write(json.dumps([plan.model_dump(mode="json") for plan in plans], separators=(",", ":")) + "\n")
            return
        for plan in plans:
            self.console.print(f"- {plan.title} ({plan.id})")

    def render_planner_tasks(self, tasks) -> None:
        if self.mode == "json":
            self.console.file.write(json.dumps([task.model_dump(mode="json") for task in tasks], separators=(",", ":")) + "\n")
            return
        for task in tasks:
            status = "[green]✓[/green]" if task.percent_complete >= 100 else "-"
            plan = f" [{task.plan_title}]" if task.plan_title else ""
            due = f" due {task.due_at.date()}" if task.due_at else ""
            self.console.print(f"{status} {task.title}{plan}{due}")

    def success(self, message: str, data=None) -> None:
        if self.mode == "json":
            payload = {"status": "ok", "message": message}
            if data is not None:
                payload["data"] = data.model_dump(mode="json")
            self.console.file.write(json.dumps(payload, separators=(",", ":")) + "\n")
            return
        self.console.print(f"[green]{message}[/green]")
