import re
import time
from textual.app import App, ComposeResult
from textual.screen import ModalScreen
from textual.widgets import Label, TabbedContent, TabPane, Input, Button, RichLog
from textual.containers import Vertical, Horizontal
from textual import work
from textual import events
from .config import load_config
from .themes import THEMES, DEFAULT_THEME
from .ssh.client import SSHClient, SENTINEL
from .widgets.ssh_panel import SSHPanel
from .widgets.compiler_view import CompilerView
from .widgets.test_view import TestView
from .widgets.valgrind_view import ValgrindIssuePanel
from .parsers.compiler import parse_compiler_output
from .parsers.unit_test import parse_unit_test_output
from .parsers.valgrind import parse_valgrind_output

ANSI_ESCAPE = re.compile(r'\x1b\[[0-9;]*[a-zA-Z]')


class LoginModal(ModalScreen):
    def __init__(self, client: SSHClient):
        super().__init__()
        self.client = client

    def compose(self) -> ComposeResult:
        yield SSHPanel(self.client)


class LogoutModal(ModalScreen):
    def __init__(self, client: SSHClient):
        super().__init__()
        self.client = client

    def compose(self) -> ComposeResult:
        with Vertical(id="logout-box"):
            yield Label("[bold]JumboShell 🐘[/bold]", id="logout-title")
            yield Label("You have been logged out.")
            with Horizontal(id="logout-buttons"):
                yield Button("Log In", id="login-again", variant="primary")
                yield Button("Exit",   id="exit-app",   variant="error")

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
    TabbedContent { height: 1fr; }
    Tab { padding: 0 3; }
    RichLog {
        height: 1fr;
        padding: 0 1;
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
    TestView Horizontal { height: 1fr; }
    TestView Vertical {
        height: 1fr;
        overflow-y: auto;
        padding-right: 2;
    }
    TestResultRow { height: 1; padding: 0; }
    DiffView, Horizontal { height: 1fr; width: 1fr; }
    DiffPanel { width: 1fr; height: 1fr; border: solid grey; }
    Input#command { dock: bottom; }
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
    #logout-title { text-align: center; width: 100%; margin-bottom: 1; }
    #logout-buttons { height: auto; align: center middle; margin-top: 1; }
    #logout-buttons Button { margin: 0 1; }
    """

    def __init__(self):
        super().__init__()
        self.client = SSHClient()
        self._history: list[str] = []
        self._history_index: int = -1
        self._pending_command: str | None = None
        self._accumulating: bool = False
        self._accumulated: list[str] = []
        self._polling_started: bool = False

    def compose(self) -> ComposeResult:
        with Horizontal(id="header"):
            yield Label("[bold]Welcome to JumboShell! 🐘[/bold]")
            yield Button("Logout", id="btn-logout", variant="warning")
            yield Button("Exit",   id="btn-exit",   variant="error")
        with TabbedContent(id="tabs"):
            with TabPane("Terminal", id="terminal"):
                yield RichLog(id="terminal-log", highlight=False, markup=False)
            with TabPane("Compiler", id="compiler"):
                yield CompilerView([])
            with TabPane("Unit Tests", id="tests"):
                yield TestView(None)
            with TabPane("Valgrind", id="valgrind"):
                yield ValgrindIssuePanel(None)
        yield Input(
            placeholder="Enter command or program input...",
            id="command"
        )

    def on_mount(self) -> None:
        config = load_config()
        self.apply_theme(config.get("theme", DEFAULT_THEME))
        if not self.client.connect():
            self.push_screen(LoginModal(self.client))
        else:
            self.notify("Auto-connected to Tufts server!")
            self._start_output_poll()

    def on_screen_resume(self) -> None:
        """Called when returning from a modal — start polling if now connected."""
        self._start_output_poll()

    def _start_output_poll(self) -> None:
        """Start the background worker that reads shell output every 50ms."""
        if self.client.is_connected and not self._polling_started:
            self._polling_started = True
            self._poll_output()

    @work(thread=True)
    def _poll_output(self) -> None:
        """Continuously read shell output and push it to the terminal display."""
        while self.client.is_connected:
            output = self.client.read_available()
            if output:
                clean = ANSI_ESCAPE.sub("", output)
                self.call_from_thread(self._append_output, clean)
            time.sleep(0.05)

    def _append_output(self, text: str) -> None:
        """Append text to the terminal log and handle sentinel detection."""
        log = self.query_one("#terminal-log", RichLog)

        if SENTINEL in text:
            # Strip the sentinel line from display
            display = text.replace(SENTINEL, "").strip()
            if display:
                log.write(display)
            self._on_command_done()
        else:
            if text.strip():
                log.write(text)
            if self._accumulating:
                self._accumulated.append(text)

    def _on_command_done(self) -> None:
        """Called when a tracked command finishes (sentinel received)."""
        if not self._pending_command:
            return
        raw = ANSI_ESCAPE.sub("", "".join(self._accumulated))
        command = self._pending_command
        self._pending_command = None
        self._accumulating = False
        self._accumulated.clear()
        self._route_output(command, raw)

    def _route_output(self, command: str, raw: str) -> None:
        """Parse and route output to the appropriate analysis tab."""
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

    def on_input_submitted(self, event: Input.Submitted) -> None:
        text = event.value.strip()
        if not text:
            return

        if not self.client.is_connected:
            self.push_screen(LoginModal(self.client))
            return

        if text == "logout":
            self.query_one("#command", Input).clear()
            self._do_logout()
            return

        # Add to history
        self._history.insert(0, text)
        self._history_index = -1
        self.query_one("#command", Input).clear()

        # For special commands, track output for analysis tab routing
        is_special = (
            "unit_test" in text or
            "valgrind" in text or
            text.startswith(("g++", "clang++", "gcc", "make"))
        )
        if is_special:
            self._pending_command = text
            self._accumulating = True
            self._accumulated.clear()
            # Append sentinel so we know when the command finishes
            self.client.send(f"{text} ; echo {SENTINEL}")
        else:
            # Regular command or program stdin — send as-is
            self.client.send(text)

    def on_key(self, event: events.Key) -> None:
        cmd_input = self.query_one("#command", Input)

        if event.key == "ctrl+c":
            self.client.send_ctrl_c()
            if self._accumulating:
                self._pending_command = None
                self._accumulating = False
                self._accumulated.clear()
            return

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


if __name__ == "__main__":
    app = JumboShellApp()
    app.run()
