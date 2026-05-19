"""Up-to-date simple useragent faker with real world database."""

import importlib.metadata as importlib_metadata  # Python 3.8+

from fake_useragent.errors import FakeUserAgentError, UserAgentError
from fake_useragent.fake import FakeUserAgent, UserAgent


def get_version(pkg_name: str, default="0.0.1") -> str:
    try:
        return importlib_metadata.version(pkg_name)
    except importlib_metadata.PackageNotFoundError:
        return default


__version__ = get_version("fake-useragent")

__all__ = [
    "FakeUserAgent",
    "UserAgent",
    "FakeUserAgentError",
    "UserAgentError",
    "__version__",
]
