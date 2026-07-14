from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import Label, Static
from textual.containers import Horizontal, Vertical, ScrollableContainer
from ..parsers.diff import DiffResult, DiffHunk, DiffLine


class DiffPanel(Widget):
    """One side (left or right) of the split diff view."""

    def __init__(self, title: str, lines: list[DiffLine], kinds: list[str]):
        super().__init__()
        self.title = title
        self.lines = lines
        self.kinds = kinds

    def compose(self) -> ComposeResult:
        yield Label(f"[bold]{self.title}[/bold]")
        for line in self.lines:
            if line.kind not in self.kinds and line.kind != "context":
                yield Label(" ")
            elif line.kind == "removed":
                yield Label(f"[red]{line.content}[/red]")
            elif line.kind == "added":
                yield Label(f"[green]{line.content}[/green]")
            else:
                yield Label(line.content)


class DiffView(Widget):
    """Split-screen diff viewer."""

    def __init__(self, diff: DiffResult):
        super().__init__()
        self.diff = diff

    def compose(self) -> ComposeResult:
        if not self.diff or not self.diff.hunks:
            yield Label("No differences found.")
            return

        all_lines = []
        for hunk in self.diff.hunks:
            all_lines.extend(hunk.lines)

        yield Horizontal(
            DiffPanel(self.diff.file_old, all_lines, ["removed"]),
            DiffPanel(self.diff.file_new, all_lines, ["added"]),
        )
