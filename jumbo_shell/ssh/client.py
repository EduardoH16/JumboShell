import time
import paramiko
from .credentials import load_credentials, TUFTS_HOST

SENTINEL = "___JUMBOSHELL_DONE___"


class SSHClient:
    """Manages a persistent interactive SSH shell session."""

    def __init__(self):
        self._connected = False
        self._shell = None
        self._cwd = "~"
        self._paramiko = None

    def _fresh_client(self) -> paramiko.SSHClient:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        return client

    def connect(self, utln: str = None, password: str = None) -> bool:
        if utln and password:
            creds = (utln, password)
        else:
            creds = load_credentials()

        if not creds:
            return False

        utln, password = creds
        self._paramiko = self._fresh_client()

        try:
            self._paramiko.connect(
                TUFTS_HOST,
                username=utln,
                password=password,
                timeout=3,
                banner_timeout=3,
                auth_timeout=3,
                look_for_keys=False,
                allow_agent=False,
            )
        except paramiko.AuthenticationException:
            return False
        except Exception:
            return False

        self._shell = self._paramiko.invoke_shell(width=220, height=50)
        self._connected = True

        # Wait for shell ready, max 2s
        deadline = time.time() + 2.0
        while time.time() < deadline:
            if self._shell.recv_ready():
                time.sleep(0.05)
                break
            time.sleep(0.05)

        # Drain banner/MOTD
        while self._shell.recv_ready():
            self._shell.recv(65535)

        return True

    def send(self, text: str) -> None:
        if self._shell:
            self._shell.send(text + "\n")

    def send_ctrl_c(self) -> None:
        if self._shell:
            self._shell.send("\x03")

    def read_available(self) -> str:
        output = ""
        if self._shell:
            while self._shell.recv_ready():
                output += self._shell.recv(4096).decode(errors="replace")
        return output

    def disconnect(self) -> None:
        if self._shell:
            self._shell.close()
            self._shell = None
        if self._paramiko:
            self._paramiko.close()
            self._paramiko = None
        self._connected = False

    @property
    def is_connected(self) -> bool:
        return self._connected
