from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import Label
from textual.containers import Horizontal
from ..parsers.diff import DiffResult, DiffLine


def _align_pairs(lines: list[DiffLine]) -> list[tuple]:
    """
    Convert a flat list of DiffLines into (left, right) pairs for true
    side-by-side alignment.

    Within each removed/added block, removed lines are paired with added
    lines. Excess lines on either side get None on the other side.
    Context lines are paired with themselves (shown identically on both sides).
    """
    pairs = []
    i = 0
    while i < len(lines):
        line = lines[i]

        if line.kind in ("context", "header"):
            pairs.append((line, line))
            i += 1

        elif line.kind == "removed":
            # Collect the entire block of consecutive removed lines
            removed_block = []
            while i < len(lines) and lines[i].kind == "removed":
                removed_block.append(lines[i])
                i += 1
            # Skip any "\ No newline at end of file" markers stored as context
            # (they appear between removed and added blocks in unified diff)
            peek = i
            while peek < len(lines) and lines[peek].kind == "context":
                peek += 1
            if peek < len(lines) and lines[peek].kind == "added":
                i = peek
            # Collect the following block of added lines
            added_block = []
            while i < len(lines) and lines[i].kind == "added":
                added_block.append(lines[i])
                i += 1
            # Pair them up; shorter side gets None
            length = max(len(removed_block), len(added_block))
            for j in range(length):
                left = removed_block[j] if j < len(removed_block) else None
                right = added_block[j] if j < len(added_block) else None
                pairs.append((left, right))

        elif line.kind == "added":
            pairs.append((None, line))
            i += 1

        else:
            i += 1

    return pairs


def _fmt(line: DiffLine | None, side: str) -> str:
    """Format a DiffLine for display, trimming carriage returns."""
    if line is None:
        return " "
    content = line.content.rstrip("\r")
    if side == "left":
        if line.kind == "removed":
            return f"[red]{content}[/red]"
        return content
    else:
        if line.kind == "added":
            return f"[green]{content}[/green]"
        return content


class DiffColumn(Widget):
    """One column of the split diff view, rendered from pre-aligned pairs."""

    def __init__(self, title: str, pairs: list[tuple], side: str):
        super().__init__()
        self.title = title
        self.pairs = pairs
        self.side = side  # "left" or "right"

    def compose(self) -> ComposeResult:
        yield Label(f"[bold]{self.title}[/bold]")
        for left, right in self.pairs:
            line = left if self.side == "left" else right
            yield Label(_fmt(line, self.side))


class DiffView(Widget):
    """Split-screen diff viewer with proper side-by-side alignment."""

    def __init__(self, diff: DiffResult):
        super().__init__()
        self.diff = diff

    def compose(self) -> ComposeResult:
        if not self.diff or not self.diff.hunks:
            yield Label("No differences found.")
            return

        all_lines: list[DiffLine] = []
        for hunk in self.diff.hunks:
            all_lines.extend(hunk.lines)

        pairs = _align_pairs(all_lines)

        yield Horizontal(
            DiffColumn(self.diff.file_old, pairs, "left"),
            DiffColumn(self.diff.file_new, pairs, "right"),
        )
