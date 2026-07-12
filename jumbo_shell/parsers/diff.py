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
    if not raw or raw[0:3] != "---":
        return None

    lines = raw.splitlines()
    old_file = lines[0].split()[1]
    new_file = lines[1].split()[1]

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
