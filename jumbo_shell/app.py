import re
from textual.app import App, ComposeResult
from textual.screen import ModalScreen
from textual.widgets import Label, TabbedContent, TabPane, Input, Button
from textual.containers import Vertical, Horizontal
from textual import work
from textual import events
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

ANSI_ESCAPE = re.compile(r'\x1b\[[0-9;]*m')


class LoginModal(ModalScreen):
    """Modal login screen shown when not connected."""

    def __init__(self, client: SSHClient):
        super().__init__()
        self.client = client

    def compose(self) -> ComposeResult:
        yield SSHPanel(self.client)


class LogoutModal(ModalScreen):
    """Modal shown after logout, offering to log in again or exit."""

    def __init__(self, client: SSHClient):
        super().__init__()
        self.client = client

    def compose(self) -> ComposeResult:
        with Vertical(id="logout-box"):
            yield Label("[bold]JumboShell 🐘[/bold]", id="logout-title")
            yield Label("You have been logged out.")
            with Horizontal(id="logout-buttons"):
                yield Button("Log In", id="login-again", variant="primary")
                yield Button("Exit", id="exit-app", variant="error")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "login-again":
            self.app.switch_screen(LoginModal(self.client))
        elif event.button.id == "exit-app":
            self.app.exit()


class JumboShellApp(App):
    """The root JumboShell application."""

    CSS = """
    #header {
        height: 1;
        dock: top;
        background: $surface;
    }
    #header Label {
        width: 1fr;
        content-align: left middle;
        padding: 0 1;
    }
    #header Button {
        min-width: 10;
        height: 1;
        border: none;
        margin: 0;
    }
    TabbedContent {
        height: 1fr;
    }
    Tab {
        padding: 0 3;
    }
    CompilerView, ValgrindIssuePanel {
        height: auto;
        padding: 1 2;
        width: 1fr;
    }
    TestView {
        height: 1fr;
        padding: 1 2;
        width: 1fr;
    }
    TestView Horizontal {
        height: 1fr;
    }
    TestView Vertical {
        height: 1fr;
        overflow-y: auto;
        padding-right: 2;
    }
    TestResultRow {
        height: 1;
        padding: 0;
    }
    DiffView, Horizontal {
        height: 1fr;
        width: 1fr;
    }
    DiffPanel {
        width: 1fr;
        height: 1fr;
        border: solid grey;
    }
    Input#command {
        dock: bottom;
    }
    LoginModal, LogoutModal {
        align: center middle;
        background: $background 80%;
    }
    SSHPanel {
        width: 60;
        height: auto;
        padding: 2 4;
        border: solid $accent;
        background: $surface;
    }
    #logout-box {
        width: 50;
        height: auto;
        padding: 2 4;
        border: solid $accent;
        background: $surface;
        align: center middle;
    }
    #logout-title {
        text-align: center;
        width: 100%;
        margin-bottom: 1;
    }
    #logout-buttons {
        height: auto;
        align: center middle;
        margin-top: 1;
    }
    #logout-buttons Button {
        margin: 0 1;
    }
    """

    def __init__(self):
        super().__init__()
        self.client = SSHClient()
        self._history: list[str] = []
        self._history_index: int = -1

    def compose(self) -> ComposeResult:
        with Horizontal(id="header"):
            yield Label("[bold]Welcome to JumboShell! 🐘[/bold]")
            yield Button("Logout", id="btn-logout", variant="warning")
            yield Button("Exit", id="btn-exit", variant="error")
        with TabbedContent(id="tabs"):
            with TabPane("Terminal", id="terminal"):
                yield Label("", id="terminal-text")
            with TabPane("Compiler", id="compiler"):
                yield CompilerView([])
            with TabPane("Unit Tests", id="tests"):
                yield TestView(None)
            with TabPane("Valgrind", id="valgrind"):
                yield ValgrindIssuePanel(None)
        yield Input(
            placeholder="Enter command (e.g. cd cs15, g++ main.cpp, unit_test)",
            id="command"
        )

    def on_mount(self) -> None:
        config = load_config()
        self.apply_theme(config.get("theme", DEFAULT_THEME))
        if not self.client.connect():
            self.push_screen(LoginModal(self.client))
        else:
            self.notify("Auto-connected to Tufts server!")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-exit":
            self.exit()
        elif event.button.id == "btn-logout":
            self._do_logout()

    def _do_logout(self) -> None:
        from .ssh.credentials import delete_credentials
        delete_credentials()
        self.client.disconnect()
        self.push_screen(LogoutModal(self.client))

    def apply_theme(self, theme_name: str) -> None:
        theme = THEMES.get(theme_name, THEMES[DEFAULT_THEME])
        self.screen.styles.background = theme["background"]
        self.screen.styles.color = theme["text"]

    def on_key(self, event: events.Key) -> None:
        """Handle up/down arrow keys for command history."""
        cmd_input = self.query_one("#command", Input)
        if not cmd_input.has_focus or not self._history:
            return
        if event.key == "up":
            self._history_index = min(self._history_index + 1, len(self._history) - 1)
            cmd_input.value = self._history[self._history_index]
            event.prevent_default()
            event.stop()
        elif event.key == "down":
            if self._history_index > 0:
                self._history_index -= 1
                cmd_input.value = self._history[self._history_index]
            elif self._history_index == 0:
                self._history_index = -1
                cmd_input.value = ""
            event.prevent_default()
            event.stop()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        command = event.value.strip()
        if not command:
            return

        if not self.client.is_connected:
            self.push_screen(LoginModal(self.client))
            return

        if command == "logout":
            self.query_one("#command", Input).clear()
            self._do_logout()
            return

        # validate context-sensitive commands
        warning = self._validate_command(command)
        if warning:
            self.notify(warning, severity="warning", timeout=6)
            return

        # add to history and lock input while running
        self._history.insert(0, command)
        self._history_index = -1
        cmd_input = self.query_one("#command", Input)
        cmd_input.clear()
        cmd_input.placeholder = f"Running: {command}..."
        cmd_input.disabled = True

        self._run_command(command)

    def _validate_command(self, command: str) -> str | None:
        """Return a warning string if the command won't work in the current directory."""
        if command.startswith(("unit_test", "make")):
            stdout, _ = self.client.run("ls Makefile 2>/dev/null")
            if "Makefile" not in stdout:
                return (
                    f"No Makefile found in {self.client._cwd}. "
                    "Use 'cd' to navigate to your assignment folder first."
                )
        return None

    @work(thread=True)
    def _run_command(self, command: str) -> None:
        """Run SSH command in a background thread so the UI stays responsive."""
        try:
            stdout, stderr = self.client.run(command)
            raw = ANSI_ESCAPE.sub("", stdout + stderr)
        except Exception as e:
            self.call_from_thread(self._on_command_error, str(e))
            return
        self.call_from_thread(self._handle_output, command, raw)

    def _on_command_error(self, error: str) -> None:
        self._unlock_input()
        self.notify(f"Command error: {error}", severity="error")

    def _unlock_input(self) -> None:
        cmd_input = self.query_one("#command", Input)
        cmd_input.disabled = False
        cmd_input.placeholder = "Enter command (e.g. cd cs15, g++ main.cpp, unit_test)"
        cmd_input.focus()

    def _handle_output(self, command: str, raw: str) -> None:
        """Called on the main thread after SSH command completes."""
        self._unlock_input()
        tabs = self.query_one("#tabs", TabbedContent)

        if "unit_test" in command:
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
            self.query_one("#terminal-text", Label).update(raw)
            tabs.active = "terminal"


if __name__ == "__main__":
    app = JumboShellApp()
    app.run()
