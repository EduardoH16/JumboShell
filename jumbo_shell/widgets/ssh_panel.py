from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import Label, Input, Button
from ..ssh.credentials import save_credentials
from ..ssh.client import SSHClient


class SSHPanel(Widget):
    """Login panel for connecting to the Tufts CS server."""

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
        self._handle_connect()

    def _handle_connect(self) -> None:
        utln = self.query_one("#utln", Input).value
        password = self.query_one("#password", Input).value
        status = self.query_one("#status", Label)

        if not utln or not password:
            status.update("[red]Please enter your UTLN and password[/red]")
            return

        status.update("[yellow]Connecting...[/yellow]")
        self.refresh()

        try:
            save_credentials(utln, password)
            self.client.connect()
        except Exception as e:
            status.update(f"[red]Error: {e}[/red]")
            return

        if self.client.is_connected:
            self.app.pop_screen()
            self.app.notify("Connected to Tufts server!")
        else:
            status.update("[red]Connection failed. Check credentials or VPN.[/red]")
