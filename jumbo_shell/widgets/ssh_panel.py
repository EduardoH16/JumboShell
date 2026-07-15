from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import Label, Input, Button
from textual.containers import Vertical
from ..ssh.credentials import save_credentials, load_credentials, delete_credentials
from ..ssh.client import SSHClient


class SSHPanel(Widget):
    """Login panel for connecting to the Tufts CS server."""

    def __init__(self, client: SSHClient):
        super().__init__()
        self.client = client

    def compose(self) -> ComposeResult:
        yield Label("[bold]JumboShell - Tufts CS Server[/bold]")
        yield Label("homework.cs.tufts.edu")

        if self.client.is_connected:
            yield Label("[green]Connected[/green]")
            yield Button("Logout", id="logout")

        else:
            yield Input(placeholder="UTLN (e.g. jsmith01)", id="utln")
            yield Input(placeholder="Password", password=True, id="password")
            yield Button("Connect", id="connect")
            yield Label("", id="status")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle connect and logout button presses."""
        if event.button.id == "connect":
            self._handle_connect()
        elif event.button.id == "logout":
            self._handle_logout()

    def _handle_connect(self) -> None:
        utln = self.query_one("#utln", Input).value
        password = self.query_one("#password", Input).value
        if not utln or not password:
            self.query_one(
                "#status", Label).renderable = "[red]Invalid credentials[/red]"
            return
        save_credentials(utln, password)
        self.client.connect()
        if self.client.is_connected:
            self.query_one(
                "#status", Label).renderable = "[green]Connected[/green]"
            self.app.refresh()
        else:
            self.query_one(
                "#status", Label).renderable = "[red]Connection failed[/red]"

    def _handle_logout(self) -> None:
        delete_credentials()
        self.client.disconnect()
        self.app.refresh()
