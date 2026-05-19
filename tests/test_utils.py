import unittest
from dataclasses import FrozenInstanceError, is_dataclass

from fake_useragent import utils


class TestUtils(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_utils_load(self):
        data = utils.load()

        self.assertIsInstance(data, list)
        self.assertGreater(len(data), 1000)
        self.assertIsInstance(data[0], utils.BrowserUserAgentData)
        self.assertTrue(is_dataclass(data[0]))
        self.assertFalse(hasattr(data[0], "__dict__"))
        self.assertIsInstance(data[0].percent, float)
        self.assertIsInstance(data[0].type, str)
        self.assertIsInstance(data[0].device_brand, str)
        self.assertIsInstance(data[0].browser, str)
        self.assertIsInstance(data[0].browser_version, str)
        self.assertIsInstance(data[0].browser_version_major_minor, float)
        self.assertIsInstance(data[0].os, str)
        self.assertIsInstance(data[0].os_version, str)
        self.assertIsInstance(data[0].platform, str)

        with self.assertRaises(FrozenInstanceError):
            data[0].browser = "Changed"

    def test_browser_user_agent_data_mapping_compatibility(self):
        record = utils.load()[0]

        self.assertEqual(record["useragent"], record.useragent)
        self.assertEqual(record.get("browser"), record.browser)
        self.assertEqual(record.get("missing", "fallback"), "fallback")
        self.assertIn("browser", record)
