from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import Label, Collapsible
from textual.containers import Vertical, ScrollableContainer
from ..parsers.valgrind import ValgrindOutput, ValgrindIssue


class ValgrindIssueRow(Widget):
    """A collapsible card for a valgrind issue."""

    def __init__(self, valgrind_issue: ValgrindIssue):
        super().__init__()
        self.valgrind_issue = valgrind_issue

    def compose(self) -> ComposeResult:
        yield Collapsible(
            Label(self.valgrind_issue.contents),
            title=self.valgrind_issue.kind.replace("_", " ").title()
        )


class ValgrindIssuePanel(Widget):
    """A collection of collapsible valgrind issue cards."""

    def __init__(self, valgrind_output: ValgrindOutput):
        super().__init__()
        self.valgrind_output = valgrind_output

    def compose(self) -> ComposeResult:
        if self.valgrind_output.num_errors == 0:
            yield Label("No memory errors detected.")
            return

        valgrind_errors = Vertical(
            *[ValgrindIssueRow(r) for r in self.valgrind_output.issues]
        )

        yield ScrollableContainer(valgrind_errors)
        yield Label(str(self.valgrind_output.num_errors) + " errors found")
