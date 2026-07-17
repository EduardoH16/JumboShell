from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import Label, Input, Button
from ..ssh.client import SSHClient


class SSHPanel(Widget):
    """Login panel — collects credentials and delegates connection to the App."""

    def __init__(self, client: SSHClient):
        super().__init__()
        self.client = client

    def compose(self) -> ComposeResult:
        yield Label("[bold]JumboShell — Tufts CS Server[/bold]")
        yield Label("homework.cs.tufts.edu")
        yield Input(placeholder="UTLN (e.g. jsmith01)", id="utln")
        yield Input(placeholder="Password", password=True, id="password")
        yield Button("Connect", id="connect", variant="primary")
        yield Label("", id="status")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "connect":
            self._handle_connect()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        event.stop()  # prevent bubbling to App's on_input_submitted
        self._handle_connect()

    def _handle_connect(self) -> None:
        # Guard against double-submit while a connection attempt is in progress
        btn = self.query_one("#connect", Button)
        if btn.disabled:
            return

        utln = self.query_one("#utln", Input).value.strip()
        password = self.query_one("#password", Input).value
        status = self.query_one("#status", Label)

        if not utln:
            status.update("[red]Please enter your UTLN[/red]")
            return
        if not password:
            status.update("[red]Please enter your password[/red]")
            return

        status.update("[yellow]Connecting...[/yellow]")
        btn.disabled = True

        # Delegate to the App which runs the actual connection in a worker thread
        self.app.attempt_login(utln, password)

    def show_error(self, message: str) -> None:
        """Called by the App when login fails."""
        self.query_one("#connect", Button).disabled = False
        self.query_one("#status", Label).update(f"[red]{message}[/red]")
