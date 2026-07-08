import keyring
from ..config import load_config, save_config

SERVICE_NAME = "jumbo-shell"
TUFTS_HOST = "homework.cs.tufts.edu"


def save_credentials(utln: str, password: str) -> None:
    """Save password to keychain and UTLN to config."""

    # store password in keychain
    keyring.set_password(SERVICE_NAME, utln, password)

    # store utln in config
    config = load_config()
    config["utln"] = utln
    save_config(config)


def load_credentials() -> tuple[str, str] | None:
    """Return (utln, password) if saved, else None."""

    # get utln from config
    config = load_config()
    utln = config.get("utln")
    if not utln:
        return None

    # get password from keychain
    password = keyring.get_password(SERVICE_NAME, utln)

    # if either is missing, return None
    if not password:
        return None
    return (utln, password)


def delete_credentials() -> None:
    """Remove saved credentials (logout)."""

    # delete from keychain
    config = load_config()
    utln = config.get("utln")
    if not utln:
        return
    keyring.delete_password(SERVICE_NAME, utln)

    # remove utln from config
    del config["utln"]
    save_config(config)


def get_saved_utln() -> str | None:
    """Return the saved UTLN, or None if not logged in."""
    config = load_config()
    return config.get("utln")
