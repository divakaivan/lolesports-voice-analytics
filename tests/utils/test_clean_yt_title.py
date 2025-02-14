import unittest
from include.utils import clean_yt_title


class TestCleanYTTitle(unittest.TestCase):
    def test_basic_title(self):
        self.assertEqual(clean_yt_title("Hello World"), "HelloWorld")

    def test_special_characters(self):
        self.assertEqual(clean_yt_title("Hello!!! @#World"), "HelloWorld")

    def test_truncate_long_title(self):
        self.assertEqual(
            clean_yt_title("ThisIsAVeryLongTitleForYouTube"), "ThisIsAVeryLong"
        )

    def test_whitespace_handling(self):
        self.assertEqual(clean_yt_title("   Trim This   "), "TrimThis")

    def test_numeric_title(self):
        self.assertEqual(clean_yt_title("12345678901234567890"), "123456789012345")

    def test_empty_title(self):
        with self.assertRaises(ValueError):
            clean_yt_title("")

    def test_only_special_characters(self):
        self.assertEqual(clean_yt_title("!!!@@@###"), "")


if __name__ == "__main__":
    unittest.main()
