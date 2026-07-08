import tomllib
import tomli_w
from pathlib import Path

CONFIG_DIR = Path.home() / ".jumbo_shell"
CONFIG_FILE = CONFIG_DIR / "config.toml"

DEFAULT_CONFIG = {
    "theme": "dark",
}


def load_config() -> dict:
    """Load config from disk, returning defaults if file doesn't exist."""
    if not CONFIG_FILE.exists():
        return DEFAULT_CONFIG.copy()
    with CONFIG_FILE.open("rb") as f:
        return tomllib.load(f)


def save_config(config: dict) -> None:
    """Save config dict to disk."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with CONFIG_FILE.open("wb") as f:
        tomli_w.dump(config, f)
