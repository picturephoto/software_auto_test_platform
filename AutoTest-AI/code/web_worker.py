"""Isolated Playwright worker. Communicates via one JSON object on stdout."""
from __future__ import annotations
import asyncio
import json
import sys
import time
from datetime import datetime, timezone


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(
        encoding="utf-8",
        errors="strict"
    )

if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(
        encoding="utf-8",
        errors="backslashreplace"
    )
# On Windows Playwright needs subprocess-capable Proactor policy.
# Set this in the isolated worker, not the Streamlit process.
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())


def main(url: str, timeout: int) -> dict:
    start = time.monotonic()
    started = datetime.now(timezone.utc).isoformat()
    errors = []
    status = 'error'
    http_status = None
    title = ''
    try:
        from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout
        with sync_playwright() as pw:
            browser = None
            try:
                browser = pw.chromium.launch(headless=True)
                page = browser.new_page()
                page.on('pageerror', lambda error: errors.append(f'JavaScript: {error}'))
                page.on('console', lambda msg: errors.append(f'Console: {msg.text}') if msg.type == 'error' else None)
                page.on('requestfailed', lambda req: errors.append(f'Request failed: {req.method} {req.url}'))
                response = page.goto(url, wait_until='domcontentloaded', timeout=timeout * 1000)
                page.wait_for_timeout(1000)
                http_status = response.status if response else None
                title = page.title()
                if http_status is None:
                    errors.append('网页未返回主文档 HTTP 状态码')
                elif http_status >= 400:
                    errors.append(f'HTTP {http_status}: 主页面请求失败')
                status = 'failed' if errors else 'passed'
            except PWTimeout as exc:
                status = 'timeout'
                errors.append(f'导航超时: {exc}')
            except Exception as exc:
                status = 'error'
                errors.append(f'{type(exc).__name__}: {exc}')
            finally:
                if browser:
                    browser.close()
    except Exception as exc:
        errors.append(f'{type(exc).__name__}: {exc}')
    return dict(filename=url, target_type='website', status=status, return_code=None,
                stdout=f'URL: {url}\nTitle: {title}\nHTTP status: {http_status}',
                stderr='\n'.join(errors), duration_seconds=round(time.monotonic()-start, 3),
                started_at_utc=started, timeout_seconds=timeout, http_status=http_status,
                console_errors=errors,
                note='网页冒烟测试：仅检测加载、JS/控制台和网络请求错误，不等同于完整功能测试。')


if __name__ == '__main__':
    try:
        data = main(sys.argv[1], int(sys.argv[2]))
    except Exception as exc:
        data = dict(filename=sys.argv[1] if len(sys.argv)>1 else '', target_type='website',
                    status='error', return_code=None, stdout='',
                    stderr=f'{type(exc).__name__}: {exc}', duration_seconds=0,
                    started_at_utc=datetime.now(timezone.utc).isoformat(),
                    timeout_seconds=0, console_errors=[f'{type(exc).__name__}: {exc}'])
    print(json.dumps(data, ensure_ascii=False),flush=True)
