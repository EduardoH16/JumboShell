import time
import paramiko
from .credentials import load_credentials, TUFTS_HOST

SENTINEL = "___JUMBOSHELL_DONE___"


class SSHClient:
    """Manages a persistent interactive SSH shell session."""

    def __init__(self):
        self._client = paramiko.SSHClient()
        self._client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self._connected = False
        self._shell = None
        self._cwd = "~"

    def connect(self) -> bool:
        """Connect using saved credentials and open an interactive shell."""
        credentials = load_credentials()
        if not credentials:
            return False
        utln, password = credentials
        try:
            self._client.connect(TUFTS_HOST, username=utln, password=password)
        except paramiko.AuthenticationException:
            return False
        except Exception:
            return False

        # Open a real interactive PTY shell — supports stdin, interactive programs
        self._shell = self._client.invoke_shell(width=220, height=50)
        self._connected = True
        time.sleep(0.8)
        # Drain the initial banner/MOTD so it doesn't pollute output
        while self._shell.recv_ready():
            self._shell.recv(65535)
        return True

    def send(self, text: str) -> None:
        """Send a line to the shell — works as a command OR as program stdin."""
        if self._shell:
            self._shell.send(text + "\n")

    def send_ctrl_c(self) -> None:
        """Interrupt the currently running program."""
        if self._shell:
            self._shell.send("\x03")

    def read_available(self) -> str:
        """Non-blocking read of whatever output is currently available."""
        output = ""
        if self._shell:
            while self._shell.recv_ready():
                output += self._shell.recv(4096).decode(errors="replace")
        return output

    def disconnect(self) -> None:
        if self._shell:
            self._shell.close()
            self._shell = None
        self._client.close()
        self._connected = False

    @property
    def is_connected(self) -> bool:
        return self._connected
