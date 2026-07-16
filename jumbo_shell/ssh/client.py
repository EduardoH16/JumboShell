import paramiko
from .credentials import load_credentials, TUFTS_HOST


class SSHClient:
    """Manages the SSH connection to the Tufts CS server."""

    def __init__(self):
        self._client = paramiko.SSHClient()
        self._client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self._connected = False
        self._cwd = "~"

    def connect(self) -> bool:
        """Connect using saved credentials. Returns True on success."""
        credentials = load_credentials()
        if not credentials:
            return False

        utln, password = credentials
        try:
            self._client.connect(TUFTS_HOST, username=utln, password=password)
        except paramiko.AuthenticationException:
            print("Authentication failed. Please check your credentials.")
            return False
        self._connected = True
        return True

    def run(self, command: str) -> tuple[str, str]:
        if not self._connected:
            return ("", "")
        if command.strip().startswith("cd"):
            # update tracked directory and confirm it exists
            new_dir = command.strip()[3:].strip() or "~"
            _, stdout, stderr = self._client.exec_command(
                f"cd {self._cwd} && cd {new_dir} && pwd"
            )
            result = stdout.read().decode().strip()
            err = stderr.read().decode().strip()
            if result:
                self._cwd = result
                return (f"Changed directory to {self._cwd}", "")

            return ("", f"cd: {err}")

        full_command = f"cd {self._cwd} && {command}"
        _, stdout, stderr = self._client.exec_command(full_command)
        return (stdout.read().decode(), stderr.read().decode())

    def disconnect(self) -> None:
        """Close the connection."""
        self._client.close()
        self._connected = False

    @property
    def is_connected(self) -> bool:
        """Returns True if currently connected."""
        return self._connected
