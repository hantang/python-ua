import unittest

import pytest

from fake_useragent import FakeUserAgent, UserAgent
from fake_useragent.fake import BROWSER_ALIASES, DEFAULT_BROWSERS, DEFAULT_OS, DEFAULT_PLATFORMS
from fake_useragent.utils import BrowserUserAgentData

FILTER_MIN_VERSION = 100.0
FILTER_MIN_PERCENTAGE = 0.05


class TestFake(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_fake_init(self):
        ua = UserAgent()

        self.assertTrue(ua.chrome)
        self.assertIsInstance(ua.chrome, str)
        self.assertTrue(ua.google)
        self.assertIsInstance(ua.google, str)
        self.assertTrue(ua.firefox)
        self.assertIsInstance(ua.firefox, str)
        self.assertTrue(ua.edge)
        self.assertIsInstance(ua.edge, str)
        self.assertTrue(ua.safari)
        self.assertIsInstance(ua.safari, str)
        self.assertTrue(ua.opera)
        self.assertIsInstance(ua.opera, str)
        self.assertTrue(ua.random)
        self.assertIsInstance(ua.random, str)
        self.assertTrue(ua.others)
        self.assertIsInstance(ua.others, str)

        self.assertTrue(ua.get_chrome)
        self.assertIsInstance(ua.get_chrome, BrowserUserAgentData)
        self.assertTrue(ua.get_google)
        self.assertIsInstance(ua.get_google, BrowserUserAgentData)
        self.assertTrue(ua.get_firefox)
        self.assertIsInstance(ua.get_firefox, BrowserUserAgentData)
        self.assertTrue(ua.get_edge)
        self.assertIsInstance(ua.get_edge, BrowserUserAgentData)
        self.assertTrue(ua.get_safari)
        self.assertIsInstance(ua.get_safari, BrowserUserAgentData)
        self.assertTrue(ua.get_opera)
        self.assertIsInstance(ua.get_opera, BrowserUserAgentData)
        self.assertTrue(ua.get_random)
        self.assertIsInstance(ua.get_random, BrowserUserAgentData)

    def test_fake_probe_user_agent_browsers(self):
        ua = UserAgent()
        ua.edge  # noqa: B018
        ua.google  # noqa: B018
        ua.chrome  # noqa: B018
        ua.googlechrome  # noqa: B018
        ua.firefox  # noqa: B018
        ua.ff  # noqa: B018
        ua.safari  # noqa: B018
        ua.opera  # noqa: B018
        ua.random  # noqa: B018
        ua.others  # noqa: B018

        ua.get_edge  # noqa: B018
        ua.get_chrome  # noqa: B018
        ua.get_firefox  # noqa: B018
        ua.get_safari  # noqa: B018
        ua.get_opera  # noqa: B018
        ua.get_random  # noqa: B018

    def test_fake_data_browser_type(self):
        ua = UserAgent()
        assert isinstance(ua.data_browsers, list)

    def test_fake_fallback(self):
        fallback = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 Edg/122.0.0.0"

        ua = UserAgent()
        self.assertEqual(ua.non_existing, fallback)
        self.assertEqual(ua["non_existing"], fallback)

    def test_fake_fallback_dictionary(self):
        fallback = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 Edg/122.0.0.0"

        ua = UserAgent()
        self.assertIsInstance(ua.get_browser("non_existing"), BrowserUserAgentData)
        self.assertEqual(ua.get_browser("non_existing").useragent, fallback)

    def test_filter_useragents_combines_instance_filters(self):
        ua = UserAgent(browsers="Chrome", os="Windows", platforms="desktop", min_version=FILTER_MIN_VERSION)

        records = ua._filter_useragents()

        self.assertGreater(len(records), 0)
        self.assertTrue(all(record.browser == "Chrome" for record in records))
        self.assertTrue(all(record.os == "Windows" for record in records))
        self.assertTrue(all(record.type == "desktop" for record in records))
        self.assertTrue(all(record.browser_version_major_minor >= FILTER_MIN_VERSION for record in records))

    def test_filter_useragents_applies_specific_browser_argument(self):
        ua = UserAgent(browsers=["Chrome", "Firefox"], os="Windows", platforms="desktop")

        records = ua._filter_useragents(browsers_to_filter="Firefox")

        self.assertGreater(len(records), 0)
        self.assertTrue(all(record.browser == "Firefox" for record in records))

    def test_get_browser_accepts_tuple_browser_lookup(self):
        ua = UserAgent(browsers=["Chrome", "Firefox"], os="Windows", platforms="desktop")

        record = ua.get_browser(("Chrome", "Firefox"))

        self.assertIn(record.browser, {"Chrome", "Firefox"})

    def test_default_lookup_constants_are_immutable_tuples(self):
        self.assertIsInstance(DEFAULT_BROWSERS, tuple)
        self.assertIsInstance(DEFAULT_OS, tuple)
        self.assertIsInstance(DEFAULT_PLATFORMS, tuple)
        self.assertIsInstance(BROWSER_ALIASES["chrome"], tuple)

    def test_filter_useragents_applies_min_percentage_boundary(self):
        ua = UserAgent(min_percentage=FILTER_MIN_PERCENTAGE)
        records = ua._filter_useragents()

        self.assertGreater(len(records), 0)
        self.assertTrue(all(record.percent >= FILTER_MIN_PERCENTAGE for record in records))

    def test_empty_filter_result_returns_fallback_record(self):
        fallback = "fallback-user-agent"
        ua = UserAgent(min_percentage=101.0, fallback=fallback)
        record = ua.get_random

        self.assertIsInstance(record, BrowserUserAgentData)
        self.assertEqual(record.useragent, fallback)
        self.assertEqual(ua.random, fallback)

    def test_fake_fallback_str_types(self):
        with pytest.raises(TypeError):
            UserAgent(fallback=True)

    def test_fake_browser_str_or_list_types(self):
        with pytest.raises(TypeError):
            UserAgent(browsers=52)

    def test_fake_os_str_or_list_types(self):
        with pytest.raises(TypeError):
            UserAgent(os=23.4)

    def test_fake_platform_str_or_list_types(self):
        with pytest.raises(TypeError):
            UserAgent(platforms=5.0)

    def test_fake_percentage_float_types(self):
        with pytest.raises(ValueError):
            UserAgent(min_percentage="")

    def test_fake_min_version_float_types(self):
        with pytest.raises(ValueError):
            UserAgent(min_version="")

    def test_fake_safe_attrs_iterable_str_types(self):
        with pytest.raises(TypeError):
            UserAgent(safe_attrs=[66])

    def test_fake_safe_attrs(self):
        ua = UserAgent(safe_attrs=("__injections__",))

        with pytest.raises(AttributeError):
            ua.__injections__  # noqa: B018

    def test_fake_aliases(self):
        assert FakeUserAgent is UserAgent
