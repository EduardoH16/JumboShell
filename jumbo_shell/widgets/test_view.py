from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import Label
from textual.containers import Horizontal, Vertical
from ..parsers.unit_test import UnitTestOutput, TestResult


class TestResultRow(Widget):
    """Test result with a pass/fail indicator"""

    def __init__(self, test_result: TestResult):
        super().__init__()
        self.test_result = test_result

    def compose(self) -> ComposeResult:
        if self.test_result.passed:
            label = f"[green]✓ {self.test_result.name}[/green]"
        else:
            label = f"[red]✗ {self.test_result.name}[/red]"
        if not self.test_result.valgrind_passed:
            label += " [yellow]⚠ valgrind[/yellow]"
        yield Label(label)


class TestView(Widget):
    """Split-screen unit test viewer."""

    def __init__(self, test: UnitTestOutput):
        super().__init__()
        self.test = test

    def compose(self) -> ComposeResult:
        if not self.test:
            yield Label("No tests were written.")
            return

        left = Vertical(
            *[TestResultRow(r) for r in self.test.results]
        )

        if self.test.compiler_lines:
            right = Vertical(
                *[Label(line) for line in self.test.compiler_lines]
            )
        else:
            right = Vertical(Label("No warnings or errors."))

        yield Horizontal(left, right)
