"""Discover trusted executable candidates under a local software directory.

Discovery is metadata-only: never starts anything. Execution requires an explicit user click and a trusted directory.
"""
from __future__ import annotations
from pathlib import Path

IGNORED = {'.git', '.venv', 'venv', 'env', '__pycache__', 'node_modules',
           'site-packages', '.mypy_cache', '.pytest_cache', 'build', 'dist'}


def scan_directory(directory: str, max_depth: int = 4, max_files: int = 2000) -> list[dict[str, str]]:
    root = Path(directory.strip().strip('"')).expanduser().resolve()
    if not root.is_dir():
        raise ValueError(f'目录不存在：{root}')
    if not 0 <= max_depth <= 8 or not 1 <= max_files <= 10000:
        raise ValueError('扫描参数无效')
    results: list[dict[str, str]] = []
    count = 0
    folders = [(root, 0)]
    while folders:
        folder, depth = folders.pop()
        try:
            children = sorted(folder.iterdir(), key=lambda v: v.name.lower())
        except (PermissionError, OSError):
            continue
        for item in children:
            if item.is_symlink():
                continue
            if item.is_dir():
                if depth < max_depth and item.name.lower() not in IGNORED:
                    folders.append((item, depth + 1))
            elif item.is_file():
                count += 1
                if count > max_files:
                    raise ValueError(f'文件数超过扫描上限 {max_files}，请缩小目录范围')
                ext = item.suffix.lower()
                if ext in {'.py', '.exe'}:
                    results.append({'name': str(item.relative_to(root)), 'path': str(item.resolve()),
                                    'type': 'python' if ext == '.py' else 'exe'})
    return sorted(results, key=lambda x: (x['type'] != 'python', x['name'].lower()))
