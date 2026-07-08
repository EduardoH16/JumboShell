from textual.app import App, ComposeResult
from textual.widgets import Label


class JumboShellApp(App):
    """The root JumboShell application."""

    def compose(self) -> ComposeResult:
        yield Label("Welcome to JumboShell!")


if __name__ == "__main__":
    app = JumboShellApp()
    app.run()
