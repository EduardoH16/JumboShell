from textual.app import App, ComposeResult
from textual.widgets import Label, TabbedContent, TabPane, Input, ContentSwitcher
from textual.containers import Vertical
from .config import load_config
from .themes import THEMES, DEFAULT_THEME
from .ssh.client import SSHClient
from .widgets.ssh_panel import SSHPanel
from .widgets.compiler_view import CompilerView
from .widgets.diff_view import DiffView
from .widgets.test_view import TestView
from .widgets.valgrind_view import ValgrindIssuePanel
from .parsers.compiler import parse_compiler_output
from .parsers.diff import parse_diff_output
from .parsers.unit_test import parse_unit_test_output
from .parsers.valgrind import parse_valgrind_output
import re


class JumboShellApp(App):
    """The root JumboShell application."""

    CSS = """
    TabbedContent {
        height: 1fr;
    }
    SSHPanel {
        height: auto;
        padding: 1 2;
    }
    CompilerView {
        height: auto;
        padding: 1 2;
    }
    TestView, ValgrindIssuePanel {
        height: 1fr;
        padding: 1 2;
    }
    """

    def __init__(self):
        super().__init__()
        self.client = SSHClient()

    def compose(self) -> ComposeResult:
        yield Label("Welcome to JumboShell! 🐘")
        with TabbedContent(id="tabs"):
            with TabPane("Login", id="login"):
                yield SSHPanel(self.client)
            with TabPane("Compiler", id="compiler"):
                yield CompilerView([])
            with TabPane("Diff", id="diff"):
                yield Label("Run: jumbo-shell diff <file1> <file2>")
            with TabPane("Unit Tests", id="tests"):
                yield TestView(None)
            with TabPane("Valgrind", id="valgrind"):
                yield ValgrindIssuePanel(None)
            with TabPane("Output", id="output"):
                yield Label("", id="output-text")
        yield Input(placeholder="Enter command (e.g. g++ main.cpp, unit_test, valgrind ./main)", id="command")

    def on_mount(self) -> None:
        """Called when the app starts — load and apply the saved theme."""
        config = load_config()
        self.apply_theme(config.get("theme", DEFAULT_THEME))

    def apply_theme(self, theme_name: str) -> None:
        """Apply a named theme to the app."""
        theme = THEMES.get(theme_name, THEMES[DEFAULT_THEME])
        self.screen.styles.background = theme["background"]
        self.screen.styles.color = theme["text"]

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Run a command and route output to the correct tab."""
        command = event.value.strip()
        if not command:
            return

        if not self.client.is_connected:
            self.notify("Not connected. Please log in first.",
                        severity="error")
            return

        stdout, stderr = self.client.run(command)
        raw = stdout + stderr
        raw = re.sub(r'\x1b\[[0-9;]*m', '', raw)

        tabs = self.query_one("#tabs", TabbedContent)

        if command.startswith("diff"):
            result = parse_diff_output(raw)
            tabs.get_pane("diff").query_one(DiffView).remove()
            tabs.get_pane("diff").mount(DiffView(result))
            tabs.active = "diff"
        elif "unit_test" in command:
            result = parse_unit_test_output(raw)
            tabs.get_pane("tests").query_one(TestView).remove()
            tabs.get_pane("tests").mount(TestView(result))
            tabs.active = "tests"
        elif "valgrind" in command:
            result = parse_valgrind_output(raw)
            tabs.get_pane("valgrind").query_one(ValgrindIssuePanel).remove()
            tabs.get_pane("valgrind").mount(ValgrindIssuePanel(result))
            tabs.active = "valgrind"
        elif command.startswith(("g++", "clang++", "gcc", "make")):
            result = parse_compiler_output(raw)
            tabs.get_pane("compiler").query_one(CompilerView).remove()
            tabs.get_pane("compiler").mount(CompilerView(result))
            tabs.active = "compiler"
        else:
            self.query_one("#output-text", Label).update(raw)
            tabs.active = "output"

        self.query_one("#command", Input).clear()


if __name__ == "__main__":
    app = JumboShellApp()
    app.run()
