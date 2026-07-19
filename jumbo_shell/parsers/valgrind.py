import re
from dataclasses import dataclass, field


@dataclass
class ValgrindIssue:
    kind:     str
    contents: str


@dataclass
class ValgrindOutput:
    num_errors:   int = 0
    bytes_leaked: int = 0   # definitely + indirectly lost (real leaks)
    bytes_in_use: int = 0   # in use at exit (often C++ runtime overhead)
    no_errors:    bool = False
    issues:       list[ValgrindIssue] = field(default_factory=list)


def _parse_bytes(line: str) -> int:
    """Extract the first byte count from a LEAK/HEAP summary line."""
    match = re.search(r"([\d,]+) bytes", line)
    if match:
        return int(match.group(1).replace(",", ""))
    return 0


def parse_valgrind_output(raw: str) -> ValgrindOutput:
    """Parse Valgrind output into a structured result."""
    result = ValgrindOutput()
    pid_prefix = re.compile(r"^==\d+==\s?")

    current_lines: list[str] = []
    current_type = "other"

    for line in raw.splitlines():
        line = line.rstrip("\r")
        line = pid_prefix.sub("", line)

        if not line.strip():
            if current_lines:
                result.issues.append(ValgrindIssue(current_type, " ".join(current_lines)))
                current_lines = []
                current_type = "other"
            continue

        # Classify error type for the issue grouper
        if "Invalid read" in line:
            current_type = "invalid_read"
        elif "Invalid write" in line:
            current_type = "invalid_write"
        elif "definitely lost" in line:
            current_type = "leak"
            result.bytes_leaked += _parse_bytes(line)
        elif "indirectly lost" in line:
            current_type = "leak"
            result.bytes_leaked += _parse_bytes(line)
        elif "in use at exit" in line:
            result.bytes_in_use = _parse_bytes(line)
        elif "ERROR SUMMARY" in line:
            match = re.search(r"\d+", line)
            if match:
                result.num_errors = int(match.group())

        current_lines.append(line)

    result.no_errors = (result.num_errors == 0 and result.bytes_leaked == 0)
    return result
