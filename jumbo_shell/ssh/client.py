import paramiko
from .credentials import load_credentials, TUFTS_HOST


class SSHClient:
    """Manages the SSH connection to the Tufts CS server."""

    def __init__(self):
        self._client = paramiko.SSHClient()
        self._client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self._connected = False

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
        """Run a command. Returns (stdout, stderr) as strings."""
        if not self._connected:
            return ("", "")
        _, stdout, stderr = self._client.exec_command(command)
        output = stdout.read().decode()
        errors = stderr.read().decode()
        return (output, errors)

    def disconnect(self) -> None:
        """Close the connection."""
        self._client.close()
        self._connected = False

    @property
    def is_connected(self) -> bool:
        """Returns True if currently connected."""
        return self._connected
