import sys
from pathlib import Path
import unittest
from unittest.mock import patch
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from multi_engine import run_executable, test_website
from log_analyzer import analyze_result

class MultiTypeTests(unittest.TestCase):
    def test_exe_invalid_file(self):
        with self.assertRaises(ValueError):
            run_executable(ROOT / 'missing.exe')

    def test_web_invalid_url(self):
        with self.assertRaises(ValueError):
            test_website('not-a-url')

    def test_launched_analysis(self):
        self.assertEqual(analyze_result({'status':'launched', 'target_type':'exe'})['error_type'], '无启动错误')

    def test_web_error_analysis(self):
        out = analyze_result({'status':'failed', 'target_type':'website', 'console_errors':['JavaScript: demo']})
        self.assertEqual(out['error_type'], 'WebPageError')

if __name__ == '__main__':
    unittest.main()
