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

    def success(self, message: str) -> None:
        if self.mode == "json":
            self.console.file.write(json.dumps({"status": "ok", "message": message}, separators=(",", ":")) + "\n")
            return
        self.console.print(f"[green]{message}[/green]")
