import sys
from pathlib import Path
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from directory_scanner import scan_directory
from test_engine import run_python_file

class DirectoryModeTests(unittest.TestCase):
    def test_scan_and_execute(self):
        with tempfile.TemporaryDirectory() as t:
            root = Path(t)
            (root / 'good.py').write_text('print("hello")', encoding='utf-8')
            (root / 'bad.py').write_text('raise ValueError("demo")', encoding='utf-8')
            (root / 'note.txt').write_text('ignore', encoding='utf-8')
            options = scan_directory(str(root))
            self.assertEqual(len(options), 2)
            self.assertEqual(run_python_file(root / 'good.py', 5)['status'], 'passed')
            self.assertEqual(run_python_file(root / 'bad.py', 5)['status'], 'failed')

    def test_ignore_virtualenv(self):
        with tempfile.TemporaryDirectory() as t:
            root = Path(t)
            (root / '.venv').mkdir()
            (root / '.venv' / 'hidden.py').write_text('print(1)', encoding='utf-8')
            (root / 'main.py').write_text('print(1)', encoding='utf-8')
            self.assertEqual([x['name'] for x in scan_directory(str(root))], ['main.py'])

    def test_invalid_folder(self):
        with self.assertRaises(ValueError):
            scan_directory('this-folder-does-not-exist-927142')

if __name__ == '__main__':
    unittest.main()
