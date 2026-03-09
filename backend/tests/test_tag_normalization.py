import unittest

from services.tag_normalization_service import tag_normalization_service


class TagNormalizationTests(unittest.TestCase):
    def test_detect_and_normalize_variants(self) -> None:
        text = "LT2001 LIT 2001 FIT-2301 DPIT2101 LSLL-2001"
        detected = tag_normalization_service.detect_tags(text)
        normalized = {item["normalized_tag"] for item in detected}

        self.assertIn("LT-2001", normalized)
        self.assertIn("LIT-2001", normalized)
        self.assertIn("FIT-2301", normalized)
        self.assertIn("DPIT-2101", normalized)
        self.assertIn("LSLL-2001", normalized)


if __name__ == "__main__":
    unittest.main()
