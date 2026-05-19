"""Fake User Agent retriever."""

import random
from collections.abc import Iterable, Sequence
from typing import Any, Final, TypeAlias

from fake_useragent.log import logger
from fake_useragent.utils import BrowserUserAgentData, load

BrowserLookup: TypeAlias = str | Sequence[str]

DEFAULT_UA: Final[str] = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 Edg/122.0.0.0"
)
DEFAULT_BROWSERS: Final[tuple[str, ...]] = (
    "Amazon Silk",
    "Chrome Mobile iOS",
    "Chrome Mobile WebView",
    "Chrome Mobile",
    "Chrome",
    "DuckDuckGo Mobile",
    "DuckDuckGo",
    "Ecosia iOS",
    "Edge Mobile",
    "Edge",
    "Firefox iOS",
    "Firefox Mobile",
    "Firefox",
    "Google",
    "Mobile Safari",
    "Opera",
    "Safari",
    "Samsung Internet",
    "Twitter",
)
DEFAULT_OS: Final[tuple[str, ...]] = (
    "Android",
    "Chrome OS",
    "iOS",
    "Linux",
    "Mac OS X",
    "Windows",
)
DEFAULT_PLATFORMS: Final[tuple[str, ...]] = (
    "desktop",
    "mobile",
    "tablet",
)

BROWSER_RANDOM: Final[str] = "random"
BROWSER_ALIASES: Final[dict[str, tuple[str, ...]]] = {
    "chrome": ("Chrome", "Chrome Mobile", "Chrome Mobile iOS"),
    "firefox": ("Firefox", "Firefox Mobile", "Firefox iOS"),
    "safari": ("Safari", "Mobile Safari"),
    "opera": ("Opera", "Opera Mobile"), # Opera Mobile
    "google": ("Google",),
    "edge": ("Edge", "Edge Mobile"),
    "others": (
        "Amazon Silk",
        "Chrome Mobile WebView",
        "DuckDuckGo",
        "DuckDuckGo Mobile",
        "Ecosia iOS",
        "Samsung Internet",
        "Twitter",
    ),
}
DEVICE_BRANDS = [
    "Amazon",
    "Apple",
    "Generic_Android_Tablet",
    "Generic_Android",
    "Generic",
    "Google",
    "Huawei",
    "LG",
    "Motorola",
    "Samsung",
]


def _ensure_iterable(*, default: Iterable[str], **kwarg: Iterable[str] | None) -> list[str]:
    """Ensure the given value is an Iterable and convert it to a list.

    Args:
        default (Iterable[str]): Default iterable to use if value is `None`.
        **kwarg (Optional[Iterable[str]]): A single keyword argument containing the value to check
            and convert.

    Raises:
        ValueError: If more than one keyword argument is provided.
        TypeError: If the value is not None, not a str, and not iterable.

    Returns:
        list[str]: A list containing the items from the iterable.
    """
    if len(kwarg) != 1:
        raise ValueError(f"ensure_iterable expects exactly one keyword argument but got {len(kwarg)}.")

    param_name, value = next(iter(kwarg.items()))

    if value is None:
        return list(default)
    if isinstance(value, str):
        return [value]

    try:
        return list(value)
    except TypeError as te:
        raise TypeError(
            f"'{param_name}' must be an iterable of str, a single str, or None but got {type(value).__name__}."
        ) from te


def _ensure_float(value: Any) -> float:
    """Ensure the given value is a float.

    Args:
        value (Any): The value to check and convert.

    Raises:
        ValueError: If the value is not a float.

    Returns:
        float: The float value.
    """
    try:
        return float(value)
    except ValueError as ve:
        msg = f"Value must be convertible to float but got {value}."
        raise ValueError(msg) from ve


def _is_magic_name(attribute_name: str) -> bool:
    """Judge whether the given attribute name is the name of a magic method(e.g. __iter__).

    Args:
        attribute_name (str): The attribute name to check.

    Returns:
        bool: Whether the given attribute name is magic.
    """
    magic_min_length = 2 * len("__") + 1
    return (
        len(attribute_name) >= magic_min_length
        and attribute_name.isascii()
        and attribute_name.startswith("__")
        and attribute_name.endswith("__")
    )


class FakeUserAgent:
    """Fake User Agent retriever.

    Args:
        browsers (Optional[Iterable[str]], optional): If given, will only ever return user agents
            from these browsers. If None, set to:
            `["Google", "Chrome", "Firefox", "Edge", "Opera"," Safari", "Android", "Yandex Browser", "Samsung Internet", "Opera Mobile",
              "Mobile Safari", "Firefox Mobile", "Firefox iOS", "Chrome Mobile", "Chrome Mobile iOS", "Mobile Safari UI/WKWebView",
              "Edge Mobile", "DuckDuckGo Mobile", "MiuiBrowser", "Whale", "Twitter", "Facebook", "Amazon Silk"]`.
            Defaults to None.
        os (Optional[Iterable[str]], optional): If given, will only ever return user agents from
            these operating systems. If None, set to `["Windows", "Linux", "Ubuntu", "Chrome OS", "Mac OS X", "Android","iOS"]`. Defaults to
            None.
        min_version (float, optional): Will only ever return user agents with versions greater than
            this one. Defaults to 0.0.
        min_percentage (float, optional): Filter user agents based on usage.
            Defaults to 0.0.
        platforms (Optional[Iterable[str]], optional): If given, will only return the user-agents with
            the provided platform type. If None, set to `["desktop", "mobile", "tablet"]`. Defaults to None.
        fallback (str, optional): User agent to use if there are any issues retrieving a user agent.
            Defaults to `"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like
            Gecko) Chrome/122.0.0.0 Safari/537.36 Edg/122.0.0.0"`.
        safe_attrs (Optional[Iterable[str]], optional): `FakeUserAgent` uses a custom `__getattr__`
            to facilitate retrieval of user agents by browser. If you need to prevent some
            attributes from being treated as browsers, pass them here. If None, all attributes will
            be treated as browsers. Defaults to ["shape"] to prevent unintended calls in IDEs like PyCharm.

    Raises:
        TypeError: If `fallback` isn't a `str` or `safe_attrs` contains non-`str` values.
    """

    def __init__(
        self,
        browsers: Iterable[str] | None = None,
        os: Iterable[str] | None = None,
        min_version: float = 0.0,
        min_percentage: float = 0.0,
        platforms: Iterable[str] | None = None,
        fallback: str = DEFAULT_UA,
        safe_attrs: Iterable[str] | None = None,
    ):
        self.browsers = _ensure_iterable(browsers=browsers, default=DEFAULT_BROWSERS)
        self.os = _ensure_iterable(os=os, default=DEFAULT_OS)
        self.min_percentage = _ensure_float(min_percentage)
        self.min_version = _ensure_float(min_version)
        self.platforms = _ensure_iterable(platforms=platforms, default=DEFAULT_PLATFORMS)

        if not isinstance(fallback, str):
            msg = f"fallback must be a str but got {type(fallback).__name__}."
            raise TypeError(msg)
        self.fallback = fallback

        safe_attrs = _ensure_iterable(safe_attrs=safe_attrs, default=("shape",))
        str_safe_attrs = [isinstance(attr, str) for attr in safe_attrs]
        if not all(str_safe_attrs):
            bad_indices = [idx for idx, is_str in enumerate(str_safe_attrs) if not is_str]
            msg = f"safe_attrs must be an iterable of str but indices {bad_indices} are not."
            raise TypeError(msg)
        self.safe_attrs = set(safe_attrs)

        # Next, load our local data file into memory (browsers.jsonl)
        self.data_browsers = load()

    def get_browser(self, browsers: BrowserLookup) -> BrowserUserAgentData:
        """Get a browser user agent based on the filters.

        Args:
            browsers (str): The browser name(s) to get. Special keyword "random" will return a random user-agent string.

        Returns:
            BrowserUserAgentData: The user agent with additional data.
        """
        try:
            if browsers == BROWSER_RANDOM:
                filtered_browsers = self._filter_useragents()
            else:
                filtered_browsers = self._filter_useragents(browsers_to_filter=browsers)

            return random.choice(filtered_browsers)  # noqa: S311
        except (KeyError, IndexError):
            logger.warning(f"Error occurred during getting browser(s): {browsers}, but was suppressed with fallback.")

            return BrowserUserAgentData(
                useragent=self.fallback,
                percent=100.0,
                type="desktop",
                device_brand=None,
                browser="Edge",
                browser_version="122.0.0.0",
                browser_version_major_minor=122.0,
                os="win32",
                os_version="10",
                platform="Win32",
            )

    def _filter_useragents(self, browsers_to_filter: BrowserLookup | None = None) -> list[BrowserUserAgentData]:
        """Filter the user agents based on filters set in the instance, and an optional browser name.

        User agents from the data file are filtered based on the attributes passed upon
        instantiation.

        Args:
            browsers_to_filter (Union[str, None], optional): A specific browser name you want results for in
                this particular call. If None, don't apply extra filters. Defaults to None.

        Returns:
            list[BrowserUserAgentData]: A filtered list of user agents.
        """
        filtered_useragents = [
            useragent
            for useragent in self.data_browsers
            if (
                useragent.browser in self.browsers
                and useragent.os in self.os
                and useragent.type in self.platforms
                and useragent.browser_version_major_minor >= self.min_version
                and useragent.percent >= self.min_percentage
            )
        ]

        if browsers_to_filter:
            browser_names = _ensure_iterable(browsers_to_filter=browsers_to_filter, default=())
            filtered_useragents = [useragent for useragent in filtered_useragents if useragent.browser in browser_names]

        return filtered_useragents

    def _get_browser_useragent(self, browsers: BrowserLookup) -> str:
        """Return a user-agent string for a browser lookup."""
        return self.get_browser(browsers).useragent

    def __getitem__(self, attr: str) -> str | Any:
        """Get a user agent by key lookup, as if it were a dictionary (i.e., `ua['random']`).

        Args:
            attr (str): Browser name to get.

        Returns:
            Union[str, Any]: The user agent string if not a `self.safe_attr`, otherwise the
                attribute value.
        """
        return self.__getattr__(attr)

    def __getattr__(self, attr: str) -> str | Any:
        """Get a user agent string by attribute lookup.

        Args:
            attr (str): Browser name to get. Special keyword "random" will return a user agent from
                any browser allowed by the instance's `self.browsers` filter.

        Returns:
            Union[str, Any]: The user agent string if not a `self.safe_attr`, otherwise the
                attribute value.
        """
        if _is_magic_name(attr) or attr in self.safe_attrs:
            return object.__getattribute__(self, attr)

        return self._get_browser_useragent(attr)

    @property
    def chrome(self) -> str:
        """Get a random Chrome user agent."""
        return self._get_browser_useragent(BROWSER_ALIASES["chrome"])

    @property
    def googlechrome(self) -> str:
        """Get a random Chrome user agent."""
        return self.chrome

    @property
    def ff(self) -> str:
        """Get a random Firefox user agent."""
        return self.firefox

    @property
    def firefox(self) -> str:
        """Get a random Firefox user agent."""
        return self._get_browser_useragent(BROWSER_ALIASES["firefox"])

    @property
    def safari(self) -> str:
        """Get a random Safari user agent."""
        return self._get_browser_useragent(BROWSER_ALIASES["safari"])

    @property
    def opera(self) -> str:
        """Get a random Opera user agent."""
        return self._get_browser_useragent(BROWSER_ALIASES["opera"])

    @property
    def google(self) -> str:
        """Get a random Google user agent."""
        return self._get_browser_useragent(BROWSER_ALIASES["google"])

    @property
    def edge(self) -> str:
        """Get a random Edge user agent."""
        return self._get_browser_useragent(BROWSER_ALIASES["edge"])

    @property
    def others(self) -> str:
        """Get a random Edge user agent."""
        return self._get_browser_useragent(BROWSER_ALIASES["others"])


    @property
    def random(self) -> str:
        """Get a random user agent."""
        return self._get_browser_useragent(BROWSER_RANDOM)

    @property
    def get_chrome(self) -> BrowserUserAgentData:
        """Get a random Chrome user agent, with additional data."""
        return self.get_browser(BROWSER_ALIASES["chrome"])

    @property
    def get_firefox(self) -> BrowserUserAgentData:
        """Get a random Firefox user agent, with additional data."""
        return self.get_browser("Firefox")

    @property
    def get_safari(self) -> BrowserUserAgentData:
        """Get a random Safari user agent, with additional data."""
        return self.get_browser(BROWSER_ALIASES["safari"])

    @property
    def get_opera(self) -> BrowserUserAgentData:
        """Get a random Safari user agent, with additional data."""
        return self.get_browser(BROWSER_ALIASES["opera"])

    @property
    def get_google(self) -> BrowserUserAgentData:
        """Get a random Google user agent, with additional data."""
        return self.get_browser(BROWSER_ALIASES["google"])

    @property
    def get_edge(self) -> BrowserUserAgentData:
        """Get a random Edge user agent, with additional data."""
        return self.get_browser(BROWSER_ALIASES["edge"])

    @property
    def get_random(self) -> BrowserUserAgentData:
        """Get a random user agent, with additional data."""
        return self.get_browser(BROWSER_RANDOM)


# common alias
UserAgent = FakeUserAgent
