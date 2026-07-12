import re
from dataclasses import dataclass

DIAGNOSTIC_PATTERN = re.compile(
    r"^(.+?):(\d+):(\d+):\s*(error|warning|note):\s*(.+)$"
)


@dataclass
class CompilerDiagnostic:
    filename: str
    line:     int
    col:      int
    severity: str
    message:  str


def parse_compiler_output(raw: str) -> list[CompilerDiagnostic]:
    """Parse raw g++/clang++ output into a list of diagnostics."""
    diagnostics = []
    for line in raw.splitlines():
        match = DIAGNOSTIC_PATTERN.match(line)
        if not match:
            continue
        diagnostics.append(CompilerDiagnostic(
            filename=match.group(1),
            line=int(match.group(2)),
            col=int(match.group(3)),
            severity=match.group(4),
            message=match.group(5)
        ))
    return diagnostics
