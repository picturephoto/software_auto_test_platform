"""Run a trusted Python script as a subprocess and record a smoke-test result."""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import subprocess
import sys
import time
from typing import Any


def run_python_file(file_path: str | Path, timeout: int = 10) -> dict[str, Any]:
    """Execute a locally trusted .py file with a timeout (not a security sandbox)."""
    path = Path(file_path).resolve()
    if not path.is_file() or path.suffix.lower() != '.py':
        raise ValueError('Please select an existing .py file.')
    if not 1 <= timeout <= 60:
        raise ValueError('timeout must be between 1 and 60 seconds')
    started_at = datetime.now(timezone.utc).isoformat()
    start = time.monotonic()
    try:
        result = subprocess.run(
            [sys.executable, '-I', str(path)],
            cwd=str(path.parent), capture_output=True, text=True,
            encoding='utf-8', errors='replace', timeout=timeout,
            stdin=subprocess.DEVNULL, check=False,
        )
        status = 'passed' if result.returncode == 0 else 'failed'
        return {
            'filename': path.name, 'status': status, 'return_code': result.returncode,
            'stdout': result.stdout, 'stderr': result.stderr,
            'duration_seconds': round(time.monotonic() - start, 3),
            'started_at_utc': started_at, 'timeout_seconds': timeout,
        }
    except subprocess.TimeoutExpired as exc:
        def decode(value: bytes | str | None) -> str:
            if isinstance(value, bytes):
                return value.decode('utf-8', errors='replace')
            return value or ''
        return {
            'filename': path.name, 'status': 'timeout', 'return_code': None,
            'stdout': decode(exc.stdout),
            'stderr': decode(exc.stderr) + f'\nTimeout: execution exceeded {timeout} seconds.',
            'duration_seconds': round(time.monotonic() - start, 3),
            'started_at_utc': started_at, 'timeout_seconds': timeout,
        }
    except OSError as exc:
        return {
            'filename': path.name, 'status': 'error', 'return_code': None,
            'stdout': '', 'stderr': f'{type(exc).__name__}: {exc}',
            'duration_seconds': round(time.monotonic() - start, 3),
            'started_at_utc': started_at, 'timeout_seconds': timeout,
        }
