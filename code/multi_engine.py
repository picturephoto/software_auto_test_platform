"""EXE launch checks and Playwright-based website smoke testing.
Run only locally trusted executables, never on a public upload service.
"""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import os
import subprocess
import sys
import time
from typing import Any


def run_executable(path: str | Path, timeout: int = 10, mode: str = 'launch', args: list[str] | None = None) -> dict[str, Any]:
    """Run a trusted Windows EXE. launch observes then stops it; cli waits for exit."""
    target = Path(path).resolve()
    if not target.is_file() or target.suffix.lower() != '.exe':
        raise ValueError('请选择存在的 Windows .exe 文件')
    if os.name != 'nt':
        raise RuntimeError('EXE 测试仅支持在 Windows 系统上运行')
    if mode not in ('launch', 'cli') or not 1 <= timeout <= 60:
        raise ValueError('模式或超时参数不正确')
    started = datetime.now(timezone.utc).isoformat()
    t0 = time.monotonic()
    command = [str(target), *(args or [])]
    if mode == 'cli':
        try:
            result = subprocess.run(command, cwd=str(target.parent), capture_output=True,
                                    text=True, encoding='utf-8', errors='replace',
                                    stdin=subprocess.DEVNULL, timeout=timeout, check=False)
            return dict(filename=target.name, target_type='exe', status='passed' if result.returncode == 0 else 'failed',
                        return_code=result.returncode, stdout=result.stdout, stderr=result.stderr,
                        duration_seconds=round(time.monotonic() - t0, 3), started_at_utc=started,
                        timeout_seconds=timeout, note='CLI 模式：根据退出码检测结果。')
        except subprocess.TimeoutExpired as exc:
            def dec(v):
                return v.decode('utf-8', 'replace') if isinstance(v, bytes) else (v or '')
            return dict(filename=target.name, target_type='exe', status='timeout', return_code=None,
                        stdout=dec(exc.stdout), stderr=dec(exc.stderr) + '\n程序在等待退出时超时。',
                        duration_seconds=round(time.monotonic() - t0, 3), started_at_utc=started,
                        timeout_seconds=timeout, note='CLI 模式超时；不一定代表软件存在缺陷。')
    else:
        # GUI programs generally remain running; that is normal, not a timeout failure.
        # Do not pipe stdout/stderr: child processes can inherit handles and hang on cleanup.
        proc = None
        try:
            proc = subprocess.Popen(command, cwd=str(target.parent), stdin=subprocess.DEVNULL,
                                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            try:
                code = proc.wait(timeout=timeout)
                status = 'exited' if code == 0 else 'failed'
                detail = f'程序在观察窗口内退出，退出码 {code}。'
            except subprocess.TimeoutExpired:
                code = None
                status = 'launched'
                detail = f'程序持续运行超过 {timeout} 秒，检测到成功启动；不代表功能测试通过。'
            return dict(filename=target.name, target_type='exe', status=status,
                        return_code=code, stdout='', stderr='',
                        duration_seconds=round(time.monotonic() - t0, 3), started_at_utc=started,
                        timeout_seconds=timeout, note=detail + ' GUI 模式无法直接读取窗口日志。')
        except OSError as exc:
            return dict(filename=target.name, target_type='exe', status='error', return_code=None,
                        stdout='', stderr=f'{type(exc).__name__}: {exc}',
                        duration_seconds=round(time.monotonic() - t0, 3), started_at_utc=started,
                        timeout_seconds=timeout, note='程序启动失败。')
        finally:
            # If still alive, stop only the launched root process. Child processes may remain.
            if proc is not None and proc.poll() is None:
                proc.terminate()
                try:
                    proc.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    proc.wait()


def test_website(url: str, timeout: int = 15) -> dict[str, Any]:
    """Run website smoke test in a separate Python process.

    Separates Playwright's Windows Proactor event loop from Streamlit's loop.
    """
    from urllib.parse import urlparse
    import json

    parsed = urlparse(url)
    if parsed.scheme not in ('http', 'https') or not parsed.hostname:
        raise ValueError('请输入完整的 http:// 或 https:// 地址')
    if not 3 <= timeout <= 60:
        raise ValueError('网页超时范围为 3–60 秒')

    #worker = Path(__file__).with_name('web_worker.py')
    worker = Path(__file__).resolve().with_name('web_worker.py')
    print(f"[DEBUG] multi_engine.py: {Path(__file__).resolve()}")
    print(f"[DEBUG] web_worker.py: {worker.resolve()}")
    print(f"[DEBUG] Python interpreter: {sys.executable}")
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUTF8"] = "1"
    if not worker.is_file():
        raise RuntimeError(f'缺少网页测试工作进程脚本：{worker}')
    started = datetime.now(timezone.utc).isoformat()
    t0 = time.monotonic()
    command = [sys.executable, str(worker), url, str(timeout)]
    kwargs = {}
    if os.name == 'nt':
        kwargs['creationflags'] = subprocess.CREATE_NO_WINDOW
    try:
            proc = subprocess.run(
            command,
            cwd=str(worker.parent),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="strict",
            env=env,
            stdin=subprocess.DEVNULL,
            timeout=timeout + 12,
            check=False,
            **kwargs
        )
    except subprocess.TimeoutExpired as exc:
        return dict(filename=url, target_type='website', status='timeout', return_code=None,
                    stdout='', stderr=f'独立网页测试进程超过 {timeout + 12} 秒，被终止。',
                    duration_seconds=round(time.monotonic()-t0, 3),
                    started_at_utc=started, timeout_seconds=timeout,
                    console_errors=[], note='网页测试进程超时；并不必然意味着网站有缺陷。')
    except OSError as exc:
        raise RuntimeError(f'无法启动网页测试子进程：{type(exc).__name__}: {exc}') from exc

    if proc.returncode != 0:
        detail = proc.stderr.strip() or proc.stdout.strip() or f'退出码 {proc.returncode}'
        raise RuntimeError(f'网页测试子进程异常退出：{detail[:2500]}')
    try:
        result = json.loads(proc.stdout)
    except (ValueError, TypeError) as exc:
        raise RuntimeError(f'网页测试子进程未返回有效 JSON。stderr: {proc.stderr[-1800:]} stdout: {proc.stdout[-500:]}') from exc
    if not isinstance(result, dict) or not {'status', 'target_type', 'stderr', 'stdout'} <= result.keys():
        raise RuntimeError('网页测试进程返回结果格式不正确')
    return result
