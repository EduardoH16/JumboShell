import re
from dataclasses import dataclass, field


@dataclass
class TestResult:
    name:            str
    passed:          bool
    valgrind_passed: bool
    diff_passed:     bool | None = None


@dataclass
class UnitTestOutput:
    compiled:       bool = False
    results:        list[TestResult] = field(default_factory=list)
    compiler_lines: list[str] = field(default_factory=list)


def parse_unit_test_output(raw: str) -> UnitTestOutput:
    """Parse Tufts unit_test output into structured results."""

    unit_test_output = UnitTestOutput()
    pattern = re.compile(r"^\s+(\S+)\s+(y|n)\s+(y|n)")
    section = None
    for line in raw.splitlines():
        # check if line is a section header
        if "passing tests" in line and "@@" not in line:
            section = "passing"
        elif "failing tests" in line and "@@" not in line:
            section = "failing"
        elif "compiling tests" in line:
            section = "compiling"
        elif "tests compiled successfully" in line:
            unit_test_output.compiled = True
        # check if line is a data row
        elif match := pattern.match(line):
            if section in ("passing", "failing"):
                test_name, passed_status, valgrind_status = match.groups()
                passed = passed_status == "y"
                valgrind = valgrind_status == "y"
                unit_test_output.results.append(TestResult(
                    test_name, passed, valgrind, None))
            elif section == "compiling":
                if any(kw in line for kw in ("clang++", "error:", "warning:")):
                    unit_test_output.compiler_lines.append(line)
        else:
            continue
    return unit_test_output
