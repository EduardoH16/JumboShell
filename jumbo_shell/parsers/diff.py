from dataclasses import dataclass, field


@dataclass
class DiffLine:
    content: str
    kind:    str


@dataclass
class DiffHunk:
    header: str
    lines:  list[DiffLine] = field(default_factory=list)


@dataclass
class DiffResult:
    file_old: str
    file_new: str
    hunks:    list[DiffHunk] = field(default_factory=list)


def parse_diff_output(raw: str) -> DiffResult | None:
    """Parse unified diff output into a structured DiffResult."""
    if not raw:
        return None

    # Find the start of the actual diff output — skip any shell echo/prompt lines
    all_lines = raw.splitlines()
    start_idx = None
    for i, line in enumerate(all_lines):
        if line.startswith("---"):
            start_idx = i
            break

    if start_idx is None or start_idx + 1 >= len(all_lines):
        return None

    lines = all_lines[start_idx:]
    old_file = lines[0].split()[1] if len(lines[0].split()) > 1 else "file_a"
    new_file = lines[1].split()[1] if len(lines[1].split()) > 1 else "file_b"

    result = DiffResult(file_old=old_file,
                        file_new=new_file,
                        hunks=[])

    current_hunk = None
    for line in lines[2:]:
        if line.startswith("@@"):
            current_hunk = DiffHunk(header=line)
            result.hunks.append(current_hunk)
        elif line.startswith("+") and current_hunk:
            current_hunk.lines.append(
                DiffLine(content=line[1:], kind="added"))
        elif line.startswith("-") and current_hunk:
            current_hunk.lines.append(
                DiffLine(content=line[1:], kind="removed"))
        elif current_hunk:
            current_hunk.lines.append(
                DiffLine(content=line[1:], kind="context"))

    return result
