"""
urllib SSL 兼容降级 — Termux/受限环境自动切换到 curl subprocess。

用法:
    from curl_fallback import curl_fetch_json, curl_fetch_text
    
    try:
        data = urllib_fetch(url)  # 原有逻辑
    except (URLError, OSError):
        data = curl_fetch_json(url)
"""

import json
import os
import subprocess
from typing import Any


# Termux CA 证书路径（Python subprocess 不会自动继承 shell 的 CURL_CA_BUNDLE）
_CERT_PATHS = [
    '/data/data/com.termux/files/usr/etc/tls/cert.pem',
    '/etc/ssl/certs/ca-certificates.crt',
    '/etc/ssl/cert.pem',
]
_CURL_ENV = os.environ.copy()
for _cp in _CERT_PATHS:
    if os.path.exists(_cp):
        _CURL_ENV['CURL_CA_BUNDLE'] = _cp
        break


def _curl_get(url: str, timeout: int = 20) -> subprocess.CompletedProcess:
    return subprocess.run(
        ['curl', '-s', '--connect-timeout', str(timeout), url],
        capture_output=True, text=True,
        timeout=timeout + 5,
        env=_CURL_ENV,
    )


def curl_fetch_json(url: str, timeout: int = 20) -> Any:
    """用 curl GET URL，返回解析后的 JSON。"""
    r = _curl_get(url, timeout)
    if r.returncode != 0 or not r.stdout.strip():
        raise OSError(f'curl failed (rc={r.returncode}): {r.stderr.strip() or "empty response"}')
    return json.loads(r.stdout)


def curl_fetch_text(url: str, timeout: int = 20) -> str:
    """用 curl GET URL，返回原始文本。"""
    r = _curl_get(url, timeout)
    if r.returncode != 0:
        raise OSError(f'curl failed (rc={r.returncode}): {r.stderr.strip()}')
    return r.stdout
