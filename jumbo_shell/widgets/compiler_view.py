from textual.app import ComposeResult
from textual.widgets import Static, Label
from textual.widget import Widget
from ..parsers.compiler import CompilerDiagnostic

SEVERITY_COLORS = {
    "error": "red",
    "warning": "yellow",
    "note": "grey",
}


class DiagnosticRow(Widget):
    """Displays a single compiler diagnostic."""

    def __init__(self, diagnostic: CompilerDiagnostic):
        super().__init__()
        self.diagnostic = diagnostic

    def compose(self) -> ComposeResult:
        color = SEVERITY_COLORS.get(self.diagnostic.severity, "white")
        label = (
            f"[{color}]{self.diagnostic.severity.upper()}[/{color}] "
            f"{self.diagnostic.filename}:{self.diagnostic.line}:{self.diagnostic.col} "
            f"- {self.diagnostic.message}"
        )
        yield Label(label)


class CompilerView(Widget):
    """Panel showing all compiler diagnostics grouped by severity."""

    def __init__(self, diagnostics: list[CompilerDiagnostic]):
        super().__init__()
        self.diagnostics = diagnostics

    def compose(self) -> ComposeResult:
        if not self.diagnostics:
            yield Label("No compiler errors or warnings")
            return

        errors = [d for d in self.diagnostics if d.severity == "error"]
        warnings = [d for d in self.diagnostics if d.severity == "warning"]
        notes = [d for d in self.diagnostics if d.severity == "note"]

        for group in [errors, warnings, notes]:
            if not group:
                continue
            for diagnostic in group:
                yield DiagnosticRow(diagnostic)
