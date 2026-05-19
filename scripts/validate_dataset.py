#!/usr/bin/env python3
"""Validate the bundled browser user-agent JSONL dataset."""

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from fake_useragent.utils import find_browser_json_path

REQUIRED_STRING_FIELDS = (
    "useragent",
    "type",
    "browser",
    "browser_version",
    "os",
    "os_version",
    "platform",
)
NON_EMPTY_STRING_FIELDS = (
    "useragent",
    "type",
    "browser",
    "browser_version",
    "os",
    "platform",
)
OPTIONAL_STRING_FIELDS = ("device_brand",)
NUMERIC_FIELDS = ("percent", "browser_version_major_minor")
SCHEMA_FIELDS = REQUIRED_STRING_FIELDS + OPTIONAL_STRING_FIELDS + NUMERIC_FIELDS
VERSION_RE = re.compile(r"^\d+(?:\.\d+)*$")


@dataclass(frozen=True, slots=True)
class ValidationError:
    """A dataset validation error with line context."""

    line_number: int
    message: str

    def __str__(self) -> str:
        """Format the error for command-line output."""
        return f"line {self.line_number}: {self.message}"


def _is_number(value: Any) -> bool:
    """Return whether a value is a real JSON number and not a bool."""
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def validate_record(record: Any, line_number: int) -> list[ValidationError]:
    """Validate one parsed JSONL record."""
    errors: list[ValidationError] = []

    if not isinstance(record, dict):
        return [ValidationError(line_number, "record must be a JSON object")]

    for field in SCHEMA_FIELDS:
        if field not in record:
            errors.append(ValidationError(line_number, f"missing required field: {field}"))

    for field in REQUIRED_STRING_FIELDS:
        value = record.get(field)
        if not isinstance(value, str):
            errors.append(ValidationError(line_number, f"{field} must be a string"))

    for field in NON_EMPTY_STRING_FIELDS:
        value = record.get(field)
        if isinstance(value, str) and not value:
            errors.append(ValidationError(line_number, f"{field} must be a non-empty string"))

    for field in OPTIONAL_STRING_FIELDS:
        value = record.get(field)
        if value is not None and not isinstance(value, str):
            errors.append(ValidationError(line_number, f"{field} must be a string or null"))

    percent = record.get("percent")
    if not _is_number(percent):
        errors.append(ValidationError(line_number, "percent must be int or float"))
    elif not 0 <= percent <= 100:
        errors.append(ValidationError(line_number, "percent must be between 0 and 100"))

    major_minor = record.get("browser_version_major_minor")
    if not _is_number(major_minor):
        errors.append(ValidationError(line_number, "browser_version_major_minor must be int or float"))

    browser_version = record.get("browser_version")
    if isinstance(browser_version, str) and browser_version and not VERSION_RE.fullmatch(browser_version):
        errors.append(ValidationError(line_number, "browser_version must be a dotted numeric version"))

    return errors


def validate_file(path: Path) -> list[ValidationError]:
    """Validate every JSON object in a JSONL dataset file."""
    errors: list[ValidationError] = []
    print(f"Read file = {path}")

    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line:
            errors.append(ValidationError(line_number, "line must not be empty"))
            continue

        try:
            record = json.loads(line)
        except json.JSONDecodeError as exc:
            errors.append(ValidationError(line_number, f"invalid JSON: {exc.msg}"))
            continue

        errors.extend(validate_record(record, line_number))

    if not path.read_text(encoding="utf-8").splitlines():
        errors.append(ValidationError(0, "dataset must contain at least one record"))

    return errors


def main(argv: list[str] | None = None) -> int:
    """Run dataset validation from the command line."""
    parser = argparse.ArgumentParser(description="Validate the bundled browser user-agent JSONL dataset.")
    parser.add_argument(
        "path",
        nargs="?",
        default=find_browser_json_path(),
        type=Path,
        help="Path to a browsers.jsonl file. Defaults to the bundled dataset.",
    )
    args = parser.parse_args(argv)

    errors = validate_file(args.path)
    for error in errors:
        print(error, file=sys.stderr)

    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
