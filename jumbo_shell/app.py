import re
import time
from textual.app import App, ComposeResult
from textual.screen import ModalScreen
from textual.widgets import Label, TabbedContent, TabPane, Input, Button, RichLog
from textual.containers import Vertical, Horizontal
from textual import work
from textual import events
from .config import load_config, save_config
from .themes import THEMES, DEFAULT_THEME
from .ssh.client import SSHClient, SENTINEL
from .widgets.ssh_panel import SSHPanel
from .widgets.diff_view import DiffView
from .widgets.test_view import TestView
from .parsers.diff import parse_diff_output
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


class ThemeModal(ModalScreen):
    """Theme picker — lets the user switch between available themes."""

    THEME_LABELS = {
        "dark":          "Dark",
        "light":         "Light",
        "grey":          "Grey",
        "high_contrast": "High Contrast",
    }

    def compose(self) -> ComposeResult:
        with Vertical(id="theme-box"):
            yield Label("[bold]Choose a Theme[/bold]", id="theme-title")
            for key, label in self.THEME_LABELS.items():
                yield Button(label, id=f"theme-{key}")
            yield Button("Cancel", id="theme-cancel", variant="default")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "theme-cancel":
            self.dismiss()
            return
        if event.button.id.startswith("theme-"):
            name = event.button.id[len("theme-"):]
            self.dismiss(name)


class JumboShellApp(App):
    """The root JumboShell application."""

    CSS = """
    /* ── Structure (layout only, no theme colours) ────────────────── */
    #header {
        height: 1;
        dock: top;
        background: transparent;
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
    #btn-theme       { background: #1a7fd4; color: #ffffff; }
    #btn-theme:hover { background: #1568b3; color: #ffffff; }

    TabbedContent { height: 1fr; }
    Tab           { padding: 0 3; }

    RichLog {
        height: 1fr;
        padding: 0 1;
        scrollbar-size: 1 1;
        scrollbar-size-horizontal: 0;
    }

    /* ── Theme colours via CSS class on Screen ────────────────────── */
    /* dark (default) */
    Screen.theme-dark               { background: #1e1e1e; color: #f8f8f2; }
    Screen.theme-dark RichLog       { background: #1e1e1e; color: #f8f8f2; }
    Screen.theme-dark Input#command { background: #2d2d2d; color: #f8f8f2; }
    Screen.theme-dark TabPane       { background: #1e1e1e; color: #f8f8f2; }
    Screen.theme-dark Tab           { color: #f8f8f2; }

    /* light */
    Screen.theme-light               { background: #e8e4dc; color: #2a2a2a; }
    Screen.theme-light RichLog       { background: #e8e4dc; color: #2a2a2a; }
    Screen.theme-light Input#command { background: #d8d4cc; color: #2a2a2a; }
    Screen.theme-light TabPane       { background: #e8e4dc; color: #2a2a2a; }
    Screen.theme-light Tab           { color: #2a2a2a; }

    /* grey */
    Screen.theme-grey               { background: #3a3a3a; color: #e0e0e0; }
    Screen.theme-grey RichLog       { background: #3a3a3a; color: #e0e0e0; }
    Screen.theme-grey Input#command { background: #4a4a4a; color: #e0e0e0; }
    Screen.theme-grey TabPane       { background: #3a3a3a; color: #e0e0e0; }
    Screen.theme-grey Tab           { color: #e0e0e0; }

    /* high contrast */
    Screen.theme-high-contrast               { background: #000000; color: #ffffff; }
    Screen.theme-high-contrast RichLog       { background: #000000; color: #ffffff; }
    Screen.theme-high-contrast Input#command { background: #1a1a1a; color: #ffffff; }
    Screen.theme-high-contrast TabPane       { background: #000000; color: #ffffff; }
    Screen.theme-high-contrast Tab           { color: #ffffff; }
    
    TestView {
        height: 1fr;
        padding: 1 2;
        width: 1fr;
    }
    TestView Horizontal { height: 1fr; }
    TestView Vertical {
        height: 1fr;
        overflow-y: auto;
        overflow-x: hidden;
        padding-right: 2;
        scrollbar-size: 1 1;
        scrollbar-size-horizontal: 0;
    }
    TestResultRow { height: 1; padding: 0; }
    DiffView {
        height: 1fr;
        width: 1fr;
    }
    DiffView Horizontal {
        height: 1fr;
        width: 1fr;
    }
    DiffColumn {
        width: 1fr;
        height: 1fr;
        border: solid grey;
        overflow-y: auto;
        overflow-x: hidden;
        scrollbar-size: 1 1;
        scrollbar-size-horizontal: 0;
    }
    DiffColumn Label {
        width: 100%;
    }
    Input#command { dock: bottom; }
    LoginModal, LogoutModal, ThemeModal {
        align: center middle;
        background: $background 80%;
    }
    #theme-box {
        width: 40;
        height: auto;
        padding: 2 4;
        border: solid $accent;
        background: $surface;
        align: center middle;
    }
    #theme-title { text-align: center; width: 100%; margin-bottom: 1; }
    #theme-box Button { width: 100%; margin-bottom: 1; }
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
    #login-again:focus { border: tall $primary; }
    #exit-app:focus   { border: tall $error; }
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
        self._login_panel = None

    def compose(self) -> ComposeResult:
        with Horizontal(id="header"):
            yield Label("[bold]Welcome to JumboShell! 🐘[/bold]")
            yield Button("Theme",  id="btn-theme",  variant="default")
            yield Button("Logout", id="btn-logout", variant="warning")
            yield Button("Exit",   id="btn-exit",   variant="error")
        with TabbedContent(id="tabs"):
            with TabPane("Terminal", id="terminal"):
                yield RichLog(id="terminal-log", highlight=False, markup=False, wrap=True)
            with TabPane("Diff", id="diff"):
                yield Label("Run: diff file1 file2", id="diff-placeholder")
            with TabPane("Unit Tests", id="tests"):
                yield TestView(None)
        yield Input(
            placeholder="Enter command or program input...",
            id="command"
        )

    def on_mount(self) -> None:
        config = load_config()
        self.apply_theme(config.get("theme", DEFAULT_THEME))
        # Connect in background so UI appears immediately
        self._auto_connect()

    @work(thread=True)
    def _auto_connect(self) -> None:
        if self.client.connect():
            self.call_from_thread(self._on_auto_connected)
        else:
            self.call_from_thread(self.push_screen, LoginModal(self.client))

    def _on_auto_connected(self) -> None:
        self.notify("Auto-connected to Tufts server!")
        self.start_polling()

    def attempt_login(self, utln: str, password: str) -> None:
        """Called by SSHPanel. Store panel ref then run connection in background."""
        panels = self.screen.query(SSHPanel)
        self._login_panel = panels.first() if panels else None
        self._login_worker(utln, password)

    @work(thread=True)
    def _login_worker(self, utln: str, password: str) -> None:
        try:
            success = self.client.connect(utln=utln, password=password)
        except Exception:
            self.call_from_thread(self._on_login_result, utln, password, False)
            return
        self.call_from_thread(self._on_login_result, utln, password, success)

    def _on_login_result(self, utln: str, password: str, success: bool) -> None:
        if success:
            from .ssh.credentials import save_credentials
            save_credentials(utln, password)
            self._login_panel = None
            self.pop_screen()
            self.call_after_refresh(self.start_polling)
            self.notify("Connected to Tufts server!")
        else:
            if self._login_panel:
                self._login_panel.show_error(
                    "Invalid credentials. Please try again."
                )

    def start_polling(self) -> None:
        """Start the output poll if not already running."""
        if self.client.is_connected and not self._polling_started:
            self._polling_started = True
            self._poll_output()

    @work(thread=True)
    def _poll_output(self) -> None:
        while self.client.is_connected:
            output = self.client.read_available()
            if output:
                clean = ANSI_ESCAPE.sub("", output)
                self.call_from_thread(self._append_output, clean)
            time.sleep(0.05)

    def _append_output(self, text: str) -> None:
        log = self.query_one("#terminal-log", RichLog)
        complete_now = False

        if SENTINEL in text:
            before = text[:text.index(SENTINEL)]
            if before.strip():
                log.write(before)
                if self._accumulating:
                    self._accumulated.append(before)
            complete_now = True
        else:
            if text.strip():
                log.write(text)
            if self._accumulating:
                self._accumulated.append(text)
                # Valgrind always ends with ERROR SUMMARY as its final line.
                # When Ctrl+C interrupts a program, bash cancels the sentinel
                # echo. Detect ERROR SUMMARY to trigger routing without sentinel.
                if (self._pending_command and
                        "valgrind" in self._pending_command and
                        "ERROR SUMMARY" in text):
                    complete_now = True

        if complete_now:
            self._on_command_done()

    def _on_command_done(self) -> None:
        if not self._pending_command:
            return
        raw = ANSI_ESCAPE.sub("", "".join(self._accumulated))
        command = self._pending_command
        self._pending_command = None
        self._accumulating = False
        self._accumulated.clear()
        self._route_output(command, raw)

    def _route_output(self, command: str, raw: str) -> None:
        tabs = self.query_one("#tabs", TabbedContent)
        log = self.query_one("#terminal-log", RichLog)

        if "unit_test" in command:
            if "passing tests" in raw or "failing tests" in raw:
                result = parse_unit_test_output(raw)
                tabs.get_pane("tests").query_one(TestView).remove()
                tabs.get_pane("tests").mount(TestView(result))
                tabs.active = "tests"
            else:
                self.notify("unit_test did not produce results. Are you in the right directory?", severity="warning")

        elif "valgrind" in command:
            # Parse valgrind output and display a summary in the terminal tab
            if "Memcheck" in raw or "ERROR SUMMARY" in raw:
                result = parse_valgrind_output(raw)
                log.write("─" * 40)
                if result.no_errors and result.bytes_in_use == 0:
                    log.write("Valgrind: Clean — no memory errors or leaks.")
                elif result.no_errors:
                    # No actual errors/leaks but memory was in use at exit
                    # (common with C++ runtime; not a real leak)
                    log.write(
                        f"Valgrind: No leaks detected. "
                        f"({result.bytes_in_use:,} bytes in use at exit — "
                        f"typically C++ runtime overhead)"
                    )
                else:
                    if result.num_errors:
                        log.write(f"Valgrind: {result.num_errors} memory error(s) found.")
                    if result.bytes_leaked:
                        log.write(f"Valgrind: {result.bytes_leaked:,} bytes leaked.")
                    if result.bytes_in_use:
                        log.write(f"Valgrind: {result.bytes_in_use:,} bytes in use at exit.")
                    for issue in result.issues:
                        if issue.kind != "other":
                            log.write(f"  [{issue.kind}] {issue.contents[:120]}")
                log.write("─" * 40)
            tabs.active = "terminal"

        elif command.startswith("diff "):
            result = parse_diff_output(raw)
            if result:
                pane = tabs.get_pane("diff")
                pane.query("*").exclude("DiffView").remove()
                try:
                    pane.query_one(DiffView).remove()
                except Exception:
                    pass
                pane.mount(DiffView(result))
                tabs.active = "diff"
            else:
                self.notify("No differences found or files are identical.", severity="warning")
                tabs.active = "terminal"

    def on_input_submitted(self, event: Input.Submitted) -> None:
        # Only handle the command bar — ignore input events bubbling from login forms
        if event.input.id != "command":
            return
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

        self._history.insert(0, text)
        self._history_index = -1
        self.query_one("#command", Input).clear()

        is_special = (
            "unit_test" in text or
            "valgrind" in text or
            text.startswith("diff ")
        )
        if is_special:
            self._pending_command = text
            self._accumulating = True
            self._accumulated.clear()
            # Split the sentinel across two adjacent shell strings so the literal
            # SENTINEL never appears in the echoed command line, preventing false
            # sentinel detection when the PTY echoes back what we sent.
            sentinel_cmd = 'echo "___JUMBOSHELL_""DONE___"'
            # Force unified diff format so the parser can handle the output
            send_text = text
            if text.startswith("diff ") and "-u" not in text.split():
                parts = text.split(None, 1)
                send_text = f"diff -u {parts[1]}" if len(parts) > 1 else text
            self.client.send(f"{send_text} ; {sentinel_cmd}")
        else:
            self.client.send(text)

    def on_key(self, event: events.Key) -> None:
        cmd_input = self.query_one("#command", Input)

        if event.key == "ctrl+c":
            self.client.send_ctrl_c()
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
        elif event.button.id == "btn-theme":
            self.push_screen(ThemeModal(), self._on_theme_chosen)

    def _on_theme_chosen(self, theme_name: str | None) -> None:
        if not theme_name:
            return
        self.apply_theme(theme_name)
        config = load_config()
        config["theme"] = theme_name
        save_config(config)

    def _do_logout(self) -> None:
        from .ssh.credentials import delete_credentials
        delete_credentials()
        self.client.disconnect()
        self._polling_started = False
        self.push_screen(LogoutModal(self.client))

    def apply_theme(self, theme_name: str) -> None:
        # Remove every theme class then add the new one.
        # CSS cascade handles all descendant colours — no inline styles needed.
        for key in THEMES:
            self.screen.remove_class(f"theme-{key.replace('_', '-')}")
        self.screen.add_class(f"theme-{theme_name.replace('_', '-')}")
        # Keep Textual's dark/light rendering mode in sync so markup inside
        # RichLog and focus rings render correctly.
        self.dark = (theme_name != "light")


if __name__ == "__main__":
    app = JumboShellApp()
    app.run()
