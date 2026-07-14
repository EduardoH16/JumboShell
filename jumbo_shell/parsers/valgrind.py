import re
from dataclasses import dataclass, field


@dataclass
class ValgrindIssue:
    kind:       str
    contents:    str


@dataclass
class ValgrindOutput:
    num_errors: int = 0
    no_errors:  bool = False
    issues:     list[ValgrindIssue] = field(default_factory=list)


def parse_valgrind_output(raw: str) -> ValgrindOutput:
    """Parse Valgrind output into a structured result."""

    valgrind_output = ValgrindOutput()
    pattern = re.compile(r"^==\d+==\s?")

    current_lines = []
    current_type = "other"

    for line in raw.splitlines():
        line = pattern.sub("", line)
        # handle empty lines
        if not line.strip():
            if current_lines:
                valgrind_output.issues.append(ValgrindIssue(
                    current_type, " ".join(current_lines)))
                current_lines = []
                current_type = "other"
            continue
        if "Invalid read" in line:
            current_type = "invalid_read"
        elif "Invalid write" in line:
            current_type = "invalid_write"
        elif "definitely lost" in line or "indirectly lost" in line:
            current_type = "leak"
        elif "ERROR SUMMARY" in line:
            match = re.search(r"\d+", line)
            if match:
                valgrind_output.num_errors = int(match.group())

        current_lines.append(line)

    if valgrind_output.num_errors == 0:
        valgrind_output.no_errors = True

    return valgrind_output
