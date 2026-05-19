"""General utils for the fake_useragent package."""

import json
from collections.abc import Iterator, Mapping
from dataclasses import asdict, dataclass
from importlib import resources
from pathlib import Path
from typing import Any

from fake_useragent.errors import FakeUserAgentError
from fake_useragent.log import logger

# PACKAGE_DATA_PATH = "fake_useragent.data"
BROWSER_DATA_PATH = "data"
BROWSER_DATA_FILENAME = "browsers.jsonl"
BrowserUserAgentValue = str | float | None


@dataclass(frozen=True, slots=True)
class BrowserUserAgentData(Mapping[str, BrowserUserAgentValue]):
    """The schema for the browser user agent data that the `browsers.jsonl` file must follow."""

    useragent: str
    """The user agent string."""
    percent: float
    """The usage percentage of the user agent."""
    type: str
    """The device type for this user agent (eg. mobile or desktop)."""
    device_brand: str | None
    """Brand name for the device (eg. Generic_Android)."""
    browser: str | None
    """Browser name for the user agent (eg. Chrome Mobile)."""
    browser_version: str
    """Version of the browser (eg. "100.0.4896.60")."""
    browser_version_major_minor: float
    """Major and minor version of the browser (eg. 100.0)."""
    os: str | None
    """OS name for the user agent (eg. Android)."""
    os_version: str | None
    """OS version (eg. 10)."""
    platform: str
    """Platform for the user agent (eg. Linux armv81)."""

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> "BrowserUserAgentData":
        """Create a browser user-agent record from parsed JSON mapping data."""
        return cls(
            useragent=data["useragent"],
            percent=data["percent"],
            type=data["type"],
            device_brand=data["device_brand"],
            browser=data["browser"],
            browser_version=data["browser_version"],
            browser_version_major_minor=data["browser_version_major_minor"],
            os=data["os"],
            os_version=data["os_version"],
            platform=data["platform"],
        )

    def __getitem__(self, key: str) -> BrowserUserAgentValue:
        """Return a field value by key for backward-compatible read-only access."""
        try:
            return getattr(self, key)
        except AttributeError as exc:
            raise KeyError(key) from exc

    def __iter__(self) -> Iterator[str]:
        """Return field names for mapping-compatible iteration."""
        return iter(asdict(self))

    def __len__(self) -> int:
        """Return the number of schema fields."""
        return len(asdict(self))

    def as_dict(self) -> dict[str, BrowserUserAgentValue]:
        """Return this record as a plain dictionary."""
        return asdict(self)


def find_browser_json_path() -> Path:
    """Find the path to the browsers.json file.

    Returns:
        Path: Path to the browsers.json file.

    Raises:
        FakeUserAgentError: If unable to find the file.
    """
    try:
        # file_path = ilr.files(PACKAGE_DATA_PATH).joinpath(BROWSER_DATA_FILENAME)
        file_path = resources.files(__package__).joinpath(BROWSER_DATA_PATH, BROWSER_DATA_FILENAME)
        return Path(str(file_path))
    except Exception as exc:
        logger.warning("Unable to find local data/jsonl file using importlib.resources.", exc_info=exc)
        raise FakeUserAgentError(f"Could not locate {BROWSER_DATA_FILENAME} file") from exc


def load() -> list[BrowserUserAgentData]:
    """Load the included `browser.json` file into memory.

    Raises:
        FakeUserAgentError: If unable to load or parse the data.

    Returns:
        list[BrowserUserAgentData]: The list of browser user agent data, following the
            `BrowserUserAgentData` schema.
    """
    data = []
    try:
        json_path = find_browser_json_path()
        with open(json_path, encoding="utf-8") as f:
            for line in f:
                value = json.loads(line)
                data.append(BrowserUserAgentData.from_mapping(value))
    except Exception as exc:
        raise FakeUserAgentError("Failed to load or parse browsers.json") from exc

    if not data:
        raise FakeUserAgentError("Data list is empty", data)

    if not isinstance(data, list):
        raise FakeUserAgentError("Data is not a list", data)
    return data
