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

MIN_PERCENT = 0
MAX_PERCENT = 100


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


def _validate_schema_fields(record: dict[str, Any], line_number: int) -> list[ValidationError]:
    """Validate required field presence and string fields."""
    errors: list[ValidationError] = []
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

    return errors


def _validate_numeric_fields(record: dict[str, Any], line_number: int) -> list[ValidationError]:
    """Validate numeric fields and numeric ranges."""
    errors: list[ValidationError] = []

    percent = record.get("percent")
    if not _is_number(percent):
        errors.append(ValidationError(line_number, "percent must be int or float"))
    elif percent and not MIN_PERCENT <= percent <= MAX_PERCENT:
        errors.append(ValidationError(line_number, "percent must be between 0 and 100"))

    major_minor = record.get("browser_version_major_minor")
    if not _is_number(major_minor):
        errors.append(ValidationError(line_number, "browser_version_major_minor must be int or float"))

    return errors


def _validate_version_fields(record: dict[str, Any], line_number: int) -> list[ValidationError]:
    """Validate browser version string format."""
    browser_version = record.get("browser_version")
    if isinstance(browser_version, str) and browser_version and not VERSION_RE.fullmatch(browser_version):
        return [ValidationError(line_number, "browser_version must be a dotted numeric version")]
    return []


def validate_record(record: Any, line_number: int) -> list[ValidationError]:
    """Validate one parsed JSONL record."""
    if not isinstance(record, dict):
        return [ValidationError(line_number, "record must be a JSON object")]

    errors: list[ValidationError] = []
    errors.extend(_validate_schema_fields(record, line_number))
    errors.extend(_validate_numeric_fields(record, line_number))
    errors.extend(_validate_version_fields(record, line_number))
    return errors


def validate_file(path: Path) -> list[ValidationError]:
    """Validate every JSON object in a JSONL dataset file."""
    errors: list[ValidationError] = []
    print(f"Read file = {path}")

    with open(path, encoding="utf-8") as f:
        line_number = 0
        for line in f:
            line_number += 1

            if not line:
                errors.append(ValidationError(line_number, "line must not be empty"))
                continue

            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                errors.append(ValidationError(line_number, f"invalid JSON: {exc.msg}"))
                continue

            errors.extend(validate_record(record, line_number))

    if line_number == 0:
        errors.append(ValidationError(0, "dataset must contain at least one record"))

    print(f"Errors = {len(errors)}")
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
