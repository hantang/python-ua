"""Description: Convert the user-agents.json file to JSONlines and directly remaps the keys.

user-agents.json.gz Example:
{
    "appName": "Netscape",
    "connection": {
        "downlink": 9.2,
        "effectiveType": "4g",
        "rtt": 0
    },
    "language": "en-US",
    "platform": "Linux x86_64",
    "pluginsLength": 0,
    "screenHeight": 812,
    "screenWidth": 375,
    "userAgent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2292.1719 Mobile Safari/537.36",
    "vendor": "Google Inc.",
    "viewportHeight": 812,
    "viewportWidth": 375,
    "weight": 0.0005058268529541256,
    "deviceCategory": "mobile"
},
"""

import argparse
import gzip
import json
import os
from collections.abc import Iterable, Mapping
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import Any

# import requests
from ua_parser import parse

from fake_useragent.utils import BrowserUserAgentData, find_browser_json_path

# DEFAULT_URL = "https://raw.githubusercontent.com/intoli/user-agents/main/src/user-agents.json.gz"
DEFAULT_FILE = "temp/src/user-agents.json.gz"


@dataclass(slots=True, frozen=True)
class SourceItem:
    """The schema for the source item that the source file must (at least) follow."""

    user_agent: str
    weight: float
    device_category: str
    platform: str

    @classmethod
    def from_mapping(cls, item: Mapping[str, Any]) -> "SourceItem":
        """Create a SourceItem from parsed JSON mapping data."""
        return cls(
            user_agent=item["userAgent"],
            weight=item["weight"],
            device_category=item["deviceCategory"],
            platform=item["platform"],
        )


def read_and_extract(data_file: str | Path) -> list[SourceItem]:
    """Read the user-agents.json file from the given file path and extract it if necessary.

    Args:
        data_file (str|Path): The the user-agents.json file path.

    Returns:
        list[SourceItem]: The source file loaded as a list of `SourceItem`s.
    """
    data_path = Path(data_file)
    if not data_path.exists():
        print("No file = {data_file}, exit")
        return []

    raw_data = []
    if data_path.suffix == ".gz":
        print(f"Reading archive data from {data_file}")
        with gzip.open(data_file, "rb") as intermediate:
            contents = intermediate.read()
            raw_data = json.loads(contents)
    elif data_path.suffix == ".json":
        print(f"Reading json data from {data_file}")
        with open(data_file, "r", encoding="utf-8") as f:
            raw_data = json.load(f)

    return [SourceItem.from_mapping(item) for item in raw_data]


def _join_version_parts(*parts: str | None) -> str:
    """Join non-None version segments with dots."""
    return ".".join(p for p in parts if p is not None)


def process_item(item: SourceItem) -> BrowserUserAgentData | None:
    """Process a single item and return the transformed item."""
    ua_result = parse(item.user_agent)

    if not ua_result.user_agent:
        return None  # Skip this user-agent string

    ua = ua_result.user_agent
    if ua.major is None or ua.minor is None:
        return None  # Skip this user-agent string

    browser_version = _join_version_parts(ua.major, ua.minor, ua.patch, ua.patch_minor)
    browser_version_major_minor = float(f"{ua.major}.{ua.minor}")

    os_version = None
    if ua_result.os:
        os_version = _join_version_parts(
            ua_result.os.major,
            ua_result.os.minor,
            ua_result.os.patch,
            ua_result.os.patch_minor,
        )

    return BrowserUserAgentData(
        useragent=item.user_agent,
        percent=item.weight * 100,
        type=item.device_category,
        device_brand=ua_result.device.brand if ua_result.device else None,
        browser=ua.family,
        browser_version=browser_version,
        browser_version_major_minor=browser_version_major_minor,
        os=ua_result.os.family if ua_result.os else None,
        os_version=os_version,
        platform=item.platform,
    )


def convert_useragents_formats(
    data_list: Iterable[SourceItem], *, max_workers: int = 0, step: int = 1000
) -> list[BrowserUserAgentData]:
    """Convert source items to BrowserUserAgentData records in parallel.

    Args:
        data_list: Source items to process.
        max_workers: Number of worker processes. Defaults to CPU count.
        step: Print step

    Returns:
        Converted records with ``None`` results filtered out.
    """
    items = list(data_list)
    if not items:
        return []

    worker_count = max_workers or os.cpu_count() or 1
    print(f"Converting {len(items)} items with {worker_count} workers ...")

    results: list[BrowserUserAgentData] = []
    with ProcessPoolExecutor(max_workers=worker_count) as executor:
        futures = [executor.submit(process_item, item) for item in items]
        total = len(futures)
        for completed, future in enumerate(as_completed(futures), start=1):
            result = future.result()
            if result is not None:
                results.append(result)
            if completed % step == 0 or completed == total:
                done = len(results)
                stats = f"Progress: {completed:5d}/{total}\t(total: {done}, skipped: {completed - done})"
                print("\t" + stats)

    results = sorted(results, key=lambda x: x.percent, reverse=True)
    print(f"Done: {len(results)} valid records from {total} source items")
    return results


def main(data_file: str | Path, save_file: str | Path, limit: int = 0, workers: int = 0):
    data = read_and_extract(data_file)
    if not data:
        return

    if limit > 0:
        print(f"Parsing only the first {limit} items")
        data = data[:limit]

    print("Processing data...")
    jsonl_converted = convert_useragents_formats(data, max_workers=workers)

    if not jsonl_converted:
        return

    save_parent = Path(save_file).parent
    if not save_parent.exists():
        print("Create save dir = {save_parent}")
        save_parent.mkdir(parents=True)

    print(f"Writing data to {save_file}")
    with open(save_file, "w", encoding="utf-8") as fw:
        for entry in jsonl_converted:
            fw.write(json.dumps(entry.as_dict()) + "\n")

    print("Done!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert Intoli's user agent data to our JSONL format.")

    input_group = parser.add_argument_group("Input source", "Define where to get the source data from.")
    exclusive_group = input_group.add_mutually_exclusive_group(required=True)
    exclusive_group.add_argument(
        "-i",
        "--input",
        help="Input JSON file path (default: %(const)s)",
        nargs="?",
        const="user-agents.json",
        type=str,
    )
    exclusive_group.add_argument(
        "-d",
        "--download",
        help=("Download source file from URL. Supports gzipped and non-gzipped files (default: %(const)s)"),
        nargs="?",
        const=DEFAULT_FILE,
        type=str,
    )

    parser.add_argument(
        "-o",
        "--output",
        help="Output JSONL file. Default overwrites current package file (default: %(default)s)",
        default=find_browser_json_path(),
        type=Path,
    )

    parser.add_argument(
        "-l",
        "--parse-limit",
        help="How many of the fetched user agent lines to parse (default: %(default)s)",
        default=0,
        type=int,
    )

    parser.add_argument(
        "-w",
        "--workers",
        help="Number of worker processes (default: CPU count)",
        default=0,
        type=int,
    )

    args = parser.parse_args()
    main(args.download or args.input, args.output, limit=args.parse_limit, workers=args.workers)
