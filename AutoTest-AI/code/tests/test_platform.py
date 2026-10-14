import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from test_engine import run_python_file
from log_analyzer import analyze_result

class PlatformTests(unittest.TestCase):
    def test_success(self):
        result = run_python_file(ROOT / 'examples/normal_demo.py', 5)
        self.assertEqual(result['status'], 'passed')
        self.assertEqual(result['return_code'], 0)
        self.assertIn('Test passed', result['stdout'])

    def test_error(self):
        result = run_python_file(ROOT / 'examples/error_demo.py', 5)
        self.assertEqual(result['status'], 'failed')
        self.assertEqual(analyze_result(result)['error_type'], 'ZeroDivisionError')

    def test_timeout(self):
        result = run_python_file(ROOT / 'examples/timeout_demo.py', 1)
        self.assertEqual(result['status'], 'timeout')
        self.assertIn('Timeout:', result['stderr'])

    def test_reject_invalid(self):
        with self.assertRaises(ValueError):
            run_python_file(ROOT / 'examples/does_not_exist.py')

if __name__ == '__main__':
    unittest.main()
