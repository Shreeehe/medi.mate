import unittest
import sys
from unittest.mock import MagicMock

# Mock external dependencies that might not be installed
sys.modules['google'] = MagicMock()
sys.modules['google.generativeai'] = MagicMock()
sys.modules['src.config'] = MagicMock()
sys.modules['src.utils'] = MagicMock()

# Now import the class to test
# We need to do a little trick because src.extractor imports these at top level
# We ensure source file is readable by python path
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# We need to carefuly reload or make sure we import after mocking
# Since we haven't imported src.extractor yet in this process, it should pick up the mocks
from src.extractor import PrescriptionExtractor

class TestExtractorUtils(unittest.TestCase):
    def setUp(self):
        # We Mock the initialization to avoid API key checks
        PrescriptionExtractor.__init__ = MagicMock(return_value=None)
        self.extractor = PrescriptionExtractor()

    def test_clean_json(self):
        raw_text = '{"key": "value"}'
        result = self.extractor._extract_json_from_text(raw_text)
        self.assertEqual(result, {"key": "value"})

    def test_markdown_json(self):
        raw_text = '```json\n{"key": "value"}\n```'
        result = self.extractor._extract_json_from_text(raw_text)
        self.assertEqual(result, {"key": "value"})

    def test_dirty_json(self):
        raw_text = 'Here is the data: {"key": "value"} Hope this helps.'
        result = self.extractor._extract_json_from_text(raw_text)
        self.assertEqual(result, {"key": "value"})
        
    def test_nested_dirty_json(self):
        raw_text = 'Sure! ``` {"key": {"nested": "value"}} ``` '
        result = self.extractor._extract_json_from_text(raw_text)
        self.assertEqual(result, {"key": {"nested": "value"}})

    def test_complex_newlines(self):
        raw_text = """
        Okay found it:
        {
            "key": "value",
            "list": [1, 2, 3]
        }
        """
        result = self.extractor._extract_json_from_text(raw_text)
        self.assertEqual(result['list'], [1, 2, 3])

if __name__ == '__main__':
    unittest.main()
