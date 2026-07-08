from textual.app import App, ComposeResult
from textual.widgets import Label
from .config import load_config
from .themes import THEMES, DEFAULT_THEME


class JumboShellApp(App):
    """The root JumboShell application."""

    def compose(self) -> ComposeResult:
        yield Label("Welcome to JumboShell!")

    def on_mount(self) -> None:
        """Called when the app starts — load and apply the saved theme."""
        config = load_config()
        self.apply_theme(config.get("theme", DEFAULT_THEME))

    def apply_theme(self, theme_name: str) -> None:
        """Apply a named theme to the app."""
        theme = THEMES.get(theme_name, THEMES[DEFAULT_THEME])
        self.screen.styles.background = theme["background"]
        self.screen.styles.color = theme["text"]


if __name__ == "__main__":
    app = JumboShellApp()
    app.run()
