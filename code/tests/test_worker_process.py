import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from multi_engine import test_website

class WorkerTests(unittest.TestCase):
    def test_worker_json_roundtrip(self):
        payload = {'status':'failed','target_type':'website','stdout':'loaded','stderr':'JavaScript error'}
        with patch('multi_engine.subprocess.run') as run:
            run.return_value.returncode = 0
            run.return_value.stdout = json.dumps(payload)
            run.return_value.stderr = ''
            out = test_website('http://127.0.0.1:8765/page.html', 5)
        self.assertEqual(out['status'], 'failed')
        self.assertTrue(run.call_args.args[0][0].endswith('python') or 'python' in run.call_args.args[0][0].lower())
        self.assertEqual(Path(run.call_args.args[0][1]).name, 'web_worker.py')

    def test_invalid_worker_output(self):
        with patch('multi_engine.subprocess.run') as run:
            run.return_value.returncode = 0
            run.return_value.stdout = 'not json'
            run.return_value.stderr = 'debug'
            with self.assertRaisesRegex(RuntimeError, 'JSON'):
                test_website('https://example.com', 5)

if __name__ == '__main__': unittest.main()
