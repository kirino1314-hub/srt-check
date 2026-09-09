"""Read-only SRT checks. Python standard library only; no network access."""
from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import hashlib
import html
import json
import math
from pathlib import Path
import re
import sys
import unicodedata

VERSION = "0.1.0"
STAMP = r"([0-9]{2,6}):([0-5][0-9]):([0-5][0-9]),([0-9]{3})"
TIMING = re.compile(rf"^{STAMP}\s+-->\s+{STAMP}$")
INDEX = re.compile(r"[0-9]{1,9}")
TAGS = re.compile(r"</?(?:b|i|u|font)(?:\s[^>]*)?>", re.IGNORECASE)


@dataclass(frozen=True)
class Issue:
    code: str
    severity: str
    line: int
    cue: int | None
    message: str


@dataclass(frozen=True)
class Cue:
    number: int
    line: int
    start_ms: int
    end_ms: int
    text: str


def milliseconds(parts: tuple[str, ...]) -> int:
    hours, minutes, seconds, millis = map(int, parts)
    return ((hours * 60 + minutes) * 60 + seconds) * 1000 + millis


def parse_srt(text: str) -> tuple[list[Cue], list[Issue]]:
    """Parse numbered, blank-line-separated SRT blocks without dropping errors."""
    lines = text.lstrip("\ufeff").splitlines()
    blocks: list[list[tuple[int, str]]] = []
    block: list[tuple[int, str]] = []
    for line_no, line in enumerate(lines + [""], 1):
        if line.strip():
            block.append((line_no, line))
        elif block:
            blocks.append(block)
            block = []
    cues, issues = [], []
    if not blocks:
        issues.append(Issue("EMPTY_FILE", "error", 1, None, "No subtitle blocks found."))
    for ordinal, block in enumerate(blocks, 1):
        line_no, label = block[0]
        if not INDEX.fullmatch(label.strip()):
            issues.append(Issue("INVALID_INDEX", "error", line_no, None,
                                "Expected a numeric cue index (1 to 9 digits)."))
            continue
        number = int(label)
        if number != ordinal:
            issues.append(Issue("INDEX_SEQUENCE", "warning", line_no, number,
                                f"Expected index {ordinal}, found {number}."))
        match = TIMING.fullmatch(block[1][1].strip()) if len(block) >= 2 else None
        if not match:
            issues.append(Issue("INVALID_TIMESTAMP", "error", line_no + 1, number,
                                "Expected HH:MM:SS,mmm --> HH:MM:SS,mmm."))
            continue
        # A new index + timestamp within the body usually means a missing blank line.
        for pos in range(2, len(block) - 1):
            if INDEX.fullmatch(block[pos][1].strip()) and TIMING.fullmatch(block[pos + 1][1].strip()):
                issues.append(Issue("MISSING_SEPARATOR", "error", block[pos][0], number,
                                    "Possible next cue inside text; add a blank separator."))
        cues.append(Cue(number, line_no, milliseconds(match.groups()[:4]),
                        milliseconds(match.groups()[4:]), "\n".join(row[1] for row in block[2:])))
    return cues, issues


def visible_text(text: str) -> str:
    return unicodedata.normalize("NFC", html.unescape(TAGS.sub("", text)))


def character_count(text: str) -> int:
    return sum(not char.isspace() and unicodedata.category(char)[0] not in {"M", "C"}
               for char in text)


def line_width(text: str) -> int:
    return sum(0 if unicodedata.category(char)[0] in {"M", "C"}
               else 2 if unicodedata.east_asian_width(char) in {"W", "F"} else 1
               for char in text)


def check_text(text: str, *, max_cps: float = 15, max_width: int = 42,
               max_lines: int = 2, duration: float | None = None) -> dict:
    """Thresholds are configurable review heuristics, not universal standards."""
    if not math.isfinite(max_cps) or max_cps <= 0 or max_width <= 0 or max_lines <= 0:
        raise ValueError("Thresholds must be positive and finite.")
    if duration is not None and (not math.isfinite(duration) or duration < 0):
        raise ValueError("Duration must be finite and non-negative.")
    cues, issues = parse_srt(text)
    previous_start = -1
    for cue in cues:
        def add(code: str, severity: str, message: str) -> None:
            issues.append(Issue(code, severity, cue.line, cue.number, message))
        if cue.start_ms < previous_start:
            add("OUT_OF_ORDER", "warning", "Start time precedes the previous cue's start.")
        previous_start = cue.start_ms
        if cue.end_ms <= cue.start_ms:
            add("INVALID_DURATION", "error", "End time must be later than start time.")
        if duration is not None and cue.end_ms / 1000 > duration:
            add("BEYOND_MEDIA", "error", "Cue ends beyond the supplied media duration.")
        visible = visible_text(cue.text)
        count = character_count(visible)
        if count == 0:
            add("EMPTY_TEXT", "error", "Cue has no visible text.")
        if cue.end_ms > cue.start_ms and count * 1000 / (cue.end_ms - cue.start_ms) > max_cps:
            add("READING_SPEED", "warning", f"Reading speed exceeds {max_cps:g} characters/second.")
        if len(visible.splitlines()) > max_lines:
            add("LINE_COUNT", "warning", f"More than {max_lines} text lines.")
        if any(line_width(line) > max_width for line in visible.splitlines()):
            add("LINE_WIDTH", "warning", f"Line exceeds {max_width} width units (wide CJK=2).")
    # Retain the furthest endpoint so nested overlaps are detected as well.
    furthest: Cue | None = None
    for cue in sorted((c for c in cues if c.end_ms > c.start_ms), key=lambda c: c.start_ms):
        if furthest and cue.start_ms < furthest.end_ms:
            issues.append(Issue("OVERLAP", "warning", cue.line, cue.number,
                                f"Overlaps cue {furthest.number} at line {furthest.line}; review intent."))
        if furthest is None or cue.end_ms > furthest.end_ms:
            furthest = cue
    issues.sort(key=lambda issue: (issue.line, issue.code))
    errors = sum(issue.severity == "error" for issue in issues)
    warnings = len(issues) - errors
    return {"cue_count": len(cues), "errors": errors, "warnings": warnings,
            "issues": [asdict(issue) for issue in issues]}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("files", type=Path, nargs="+")
    parser.add_argument("--version", action="version", version=VERSION)
    parser.add_argument("--max-cps", type=float, default=15)
    parser.add_argument("--max-width", type=int, default=42)
    parser.add_argument("--max-lines", type=int, default=2)
    parser.add_argument("--duration", type=float, help="Media duration in seconds (one file only).")
    parser.add_argument("--encoding", default="utf-8-sig", help="Input encoding; default utf-8-sig.")
    parser.add_argument("--json", action="store_true", help="Print JSON instead of human-readable text.")
    parser.add_argument("--output", type=Path, help="Create a NEW JSON report; refuse existing paths.")
    parser.add_argument("--strict", action="store_true", help="Also return exit 1 for warnings.")
    args = parser.parse_args(argv)
    if args.duration is not None and len(args.files) != 1:
        parser.error("--duration requires exactly one input file.")
    options = dict(max_cps=args.max_cps, max_width=args.max_width,
                   max_lines=args.max_lines, duration=args.duration)
    try:
        check_text("", **options)
    except ValueError as error:
        parser.error(str(error))
    reports = []
    io_failed = False
    for path in args.files:
        try:
            raw = path.read_bytes()
            result = check_text(raw.decode(args.encoding), **options)
            result.update(file=path.name, sha256=hashlib.sha256(raw).hexdigest())
        except (OSError, UnicodeError, LookupError) as error:
            io_failed = True
            result = {"file": path.name, "cue_count": 0, "errors": 1, "warnings": 0,
                      "issues": [asdict(Issue("INPUT_ERROR", "error", 0, None,
                                              f"Cannot read/decode input ({type(error).__name__})."))]}
        reports.append(result)
    payload = {"tool": "srt-check", "version": VERSION, "options": options, "files": reports}
    serialized = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        try:
            with args.output.open("x", encoding="utf-8") as handle:
                handle.write(serialized)
        except OSError as error:
            print(f"Cannot create report; existing files are never replaced ({type(error).__name__}).",
                  file=sys.stderr)
            return 2
    if args.json:
        print(serialized, end="")
    else:
        for report in reports:
            print(f"{report['file']}: {report['cue_count']} cues, "
                  f"{report['errors']} errors, {report['warnings']} warnings")
            for issue in report["issues"]:
                print(f"  L{issue['line']} [{issue['severity']}] {issue['code']}: {issue['message']}")
    if io_failed:
        return 2
    return int(any(r["errors"] or (args.strict and r["warnings"]) for r in reports))


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    raise SystemExit(main())
