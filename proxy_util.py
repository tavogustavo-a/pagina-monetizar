"""Parseo y prueba de proxies HTTP, HTTPS, SOCKS4 y SOCKS5."""
from __future__ import annotations

import json
import re
import socket
import urllib.error
import urllib.request
from contextlib import contextmanager
from contextvars import ContextVar
from urllib.parse import quote, unquote

SUPPORTED_PROTOCOLS = ("http", "https", "socks5", "socks4")
IP_API_HOST = "ip-api.com"
IP_API_PATH = "/json/?fields=status,message,country,countryCode,query"
IP_API_URL = f"http://{IP_API_HOST}{IP_API_PATH}"

_PROTO_PREFIX = re.compile(
    r"^(?P<proto>https?|socks5h?|socks4a?|socks)\s*(://|:)?\s*",
    re.I,
)


def normalize_protocol(value: str) -> str:
    p = (value or "http").strip().lower()
    if p in ("socks", "socks5h"):
        return "socks5"
    if p == "socks4a":
        return "socks4"
    if p in SUPPORTED_PROTOCOLS:
        return p
    return "http"


def _looks_port(value: str) -> bool:
    try:
        port = int((value or "").strip())
    except (TypeError, ValueError):
        return False
    return 1 <= port <= 65535


def _looks_host(value: str) -> bool:
    host = (value or "").strip().strip("[]")
    if not host:
        return False
    if host.count(".") >= 1:
        return True
    if ":" in host:
        return True
    return bool(re.fullmatch(r"[A-Za-z0-9._-]+", host))


def _split_host_port(rest: str) -> tuple[str, int]:
    text = (rest or "").strip()
    if text.startswith("["):
        end = text.find("]")
        if end < 0:
            raise ValueError("invalid_format")
        host = text[1:end]
        tail = text[end + 1 :].lstrip(":")
        if not _looks_port(tail):
            raise ValueError("invalid_format")
        return host, int(tail)
    if text.count(":") == 1:
        host, port_s = text.rsplit(":", 1)
        if not _looks_port(port_s):
            raise ValueError("invalid_format")
        return host.strip(), int(port_s)
    raise ValueError("invalid_format")


def parse_proxy_line(raw: str) -> dict[str, str | int]:
    text = (raw or "").strip().strip("'\"")
    if not text:
        raise ValueError("empty")
    lines = [ln.strip() for ln in text.splitlines() if ln.strip() and not ln.strip().startswith("#")]
    if not lines:
        raise ValueError("empty")
    text = re.sub(r"\s+", " ", lines[0]).strip()

    protocol = "http"
    proto_match = _PROTO_PREFIX.match(text)
    if proto_match:
        protocol = normalize_protocol(proto_match.group("proto"))
        text = text[proto_match.end() :].lstrip()

    username = ""
    password = ""
    host = ""
    port = 0

    if "@" in text:
        auth, rest = text.rsplit("@", 1)
        host, port = _split_host_port(rest)
        if ":" in auth:
            username, password = auth.split(":", 1)
        else:
            username = auth
    else:
        if text.startswith("["):
            host, port = _split_host_port(text)
        else:
            parts = [p.strip() for p in text.split(":")]
            if len(parts) == 2 and _looks_port(parts[1]):
                host, port = parts[0], int(parts[1])
            elif len(parts) == 3 and _looks_port(parts[1]):
                host, port = parts[0], int(parts[1])
                username = parts[2]
            elif len(parts) >= 4 and _looks_port(parts[1]) and _looks_host(parts[0]):
                host = parts[0]
                port = int(parts[1])
                username = parts[2]
                password = ":".join(parts[3:])
            elif len(parts) >= 4 and _looks_port(parts[-1]) and _looks_host(parts[-2]):
                host = parts[-2]
                port = int(parts[-1])
                username = parts[0]
                password = ":".join(parts[1:-2])
            else:
                raise ValueError("invalid_format")

    host = (host or "").strip().strip("[]")
    username = unquote((username or "").strip())
    password = unquote(password or "")
    if not host or int(port) <= 0 or int(port) > 65535:
        raise ValueError("invalid_format")

    return {
        "protocol": protocol,
        "host": host,
        "port": int(port),
        "username": username,
        "password": password,
    }


def build_proxy_url(data: dict) -> str:
    protocol = normalize_protocol(str(data.get("protocol") or "http"))
    host = str(data.get("host") or "").strip()
    port = int(data.get("port") or 0)
    username = str(data.get("username") or "")
    password = str(data.get("password") or "")
    host_fmt = f"[{host}]" if ":" in host and not host.startswith("[") else host
    if username:
        auth = f"{quote(username, safe='')}:{quote(password, safe='')}"
        return f"{protocol}://{auth}@{host_fmt}:{port}"
    return f"{protocol}://{host_fmt}:{port}"


def proxy_display(data: dict, *, mask_password: bool = True) -> str:
    protocol = normalize_protocol(str(data.get("protocol") or "http"))
    host = str(data.get("host") or "")
    port = int(data.get("port") or 0)
    username = str(data.get("username") or "")
    password = str(data.get("password") or "")
    host_fmt = f"[{host}]" if ":" in host and not host.startswith("[") else host
    if username:
        pw = "****" if mask_password and password else password
        return f"{protocol}://{username}:{pw}@{host_fmt}:{port}"
    return f"{protocol}://{host_fmt}:{port}"


def _proxy_handler_url(data: dict) -> str:
    protocol = normalize_protocol(str(data.get("protocol") or "http"))
    url = build_proxy_url(data)
    if protocol == "https":
        return url.replace("https://", "http://", 1)
    return url


_active_proxy_url: ContextVar[str] = ContextVar("active_proxy_url", default="")
_orig_urlopen = urllib.request.urlopen
_urlopen_patched = False


def active_proxy_url() -> str:
    """URL del proxy activo en el contexto de publicación actual ('' si no hay)."""
    return (_active_proxy_url.get() or "").strip()


def proxy_handler_for(proxy_url: str):
    """Devuelve un handler urllib para enrutar por el proxy dado."""
    data = parse_proxy_line(proxy_url)
    protocol = normalize_protocol(str(data.get("protocol") or "http"))
    if protocol.startswith("socks"):
        try:
            import socks
            from sockshandler import SocksiPyHandler
        except ImportError as exc:
            raise OSError("socks_fail") from exc
        kind = socks.SOCKS5 if protocol == "socks5" else socks.SOCKS4
        user = str(data.get("username") or "") or None
        password = str(data.get("password") or "") or None
        return SocksiPyHandler(
            kind,
            str(data["host"]),
            int(data["port"]),
            rdns=True,
            username=user,
            password=password,
        )
    handler_url = _proxy_handler_url(data)
    return urllib.request.ProxyHandler({"http": handler_url, "https": handler_url})


def _make_proxy_opener(proxy_url: str):
    return urllib.request.build_opener(proxy_handler_for(proxy_url))


def _proxied_urlopen(url, data=None, timeout=socket._GLOBAL_DEFAULT_TIMEOUT, **kwargs):
    proxy_url = (_active_proxy_url.get() or "").strip()
    if not proxy_url:
        return _orig_urlopen(url, data, timeout, **kwargs)
    opener = _make_proxy_opener(proxy_url)
    return opener.open(url, data, timeout)


def install_urlopen_proxy_hook() -> None:
    global _urlopen_patched
    if _urlopen_patched:
        return
    urllib.request.urlopen = _proxied_urlopen
    _urlopen_patched = True


@contextmanager
def using_proxy(proxy_url: str | None):
    """Enruta urllib.request.urlopen por el proxy durante la publicación."""
    install_urlopen_proxy_hook()
    url = (proxy_url or "").strip()
    token = _active_proxy_url.set(url)
    try:
        yield url
    finally:
        _active_proxy_url.reset(token)


install_urlopen_proxy_hook()


def classify_proxy_error(exc: BaseException | str) -> str:
    text = str(exc or "").lower()
    reason = getattr(exc, "reason", None)
    if reason is not None:
        text = f"{text} {reason}".lower()
    errno = getattr(exc, "errno", None)
    if errno is None and reason is not None:
        errno = getattr(reason, "errno", None)
    code = getattr(exc, "code", None)

    if code == 407 or "407" in text or "authentication" in text or "proxy_auth" in text:
        return "auth"
    if code in (401, 403) or "403" in text:
        return "denied"
    if code and 400 <= int(code) < 600:
        return "http_status"
    if errno in (11001, 11002, 8, -2, -3) or "getaddrinfo" in text or "name or service not known" in text:
        return "host_unresolved"
    if errno in (10060, 110, 60) or "timed out" in text or "timeout" in text:
        return "timeout"
    if errno in (10061, 111) or "connection refused" in text or "actively refused" in text:
        return "refused"
    if errno in (10051, 10065, 101, 113) or "unreachable" in text or "no route" in text:
        return "unreachable"
    if errno in (10054, 104) or "reset" in text:
        return "reset"
    if "ssl" in text or "certificate" in text:
        return "ssl"
    if "socks" in text:
        return "socks_fail"
    return "test_failed"


def _recv_exact(sock: socket.socket, n: int) -> bytes:
    buf = b""
    while len(buf) < n:
        chunk = sock.recv(n - len(buf))
        if not chunk:
            raise OSError("connection closed")
        buf += chunk
    return buf


def _socks5_http_get(data: dict, timeout: float) -> bytes:
    sock = socket.create_connection((str(data["host"]), int(data["port"])), timeout=timeout)
    sock.settimeout(timeout)
    try:
        user = str(data.get("username") or "")
        password = str(data.get("password") or "")
        if user:
            sock.sendall(b"\x05\x02\x00\x02")
        else:
            sock.sendall(b"\x05\x01\x00")
        ver, method = _recv_exact(sock, 2)
        if ver != 5:
            raise OSError("socks_handshake")
        if method == 2:
            u_b = user.encode("utf-8")[:255]
            p_b = password.encode("utf-8")[:255]
            sock.sendall(bytes([1, len(u_b)]) + u_b + bytes([len(p_b)]) + p_b)
            _, status = _recv_exact(sock, 2)
            if status != 0:
                raise OSError("proxy_auth")
        elif method != 0:
            raise OSError("socks_handshake")
        host_b = IP_API_HOST.encode("idna")
        sock.sendall(b"\x05\x01\x00\x03" + bytes([len(host_b)]) + host_b + (80).to_bytes(2, "big"))
        resp = _recv_exact(sock, 4)
        if resp[0] != 5 or resp[1] != 0:
            raise OSError("socks_connect")
        atyp = resp[3]
        if atyp == 1:
            _recv_exact(sock, 6)
        elif atyp == 3:
            ln = _recv_exact(sock, 1)[0]
            _recv_exact(sock, ln + 2)
        elif atyp == 4:
            _recv_exact(sock, 18)
        else:
            raise OSError("socks_connect")
        req = (
            f"GET {IP_API_PATH} HTTP/1.0\r\n"
            f"Host: {IP_API_HOST}\r\n"
            "User-Agent: TuyahoProxyCheck/1.0\r\n"
            "Connection: close\r\n\r\n"
        ).encode("ascii")
        sock.sendall(req)
        chunks: list[bytes] = []
        while True:
            piece = sock.recv(4096)
            if not piece:
                break
            chunks.append(piece)
        raw = b"".join(chunks)
        _, _, body = raw.partition(b"\r\n\r\n")
        return body or raw
    finally:
        sock.close()


def _socks4_http_get(data: dict, timeout: float) -> bytes:
    dest_ip = socket.gethostbyname(IP_API_HOST)
    parts = [int(x) for x in dest_ip.split(".")]
    user = str(data.get("username") or "").encode("utf-8")[:255]
    payload = bytes([4, 1]) + (80).to_bytes(2, "big") + bytes(parts) + user + b"\x00"
    sock = socket.create_connection((str(data["host"]), int(data["port"])), timeout=timeout)
    sock.settimeout(timeout)
    try:
        sock.sendall(payload)
        resp = _recv_exact(sock, 8)
        if resp[1] != 0x5A:
            raise OSError("socks_connect")
        req = (
            f"GET {IP_API_PATH} HTTP/1.0\r\n"
            f"Host: {IP_API_HOST}\r\n"
            "User-Agent: TuyahoProxyCheck/1.0\r\n"
            "Connection: close\r\n\r\n"
        ).encode("ascii")
        sock.sendall(req)
        chunks: list[bytes] = []
        while True:
            piece = sock.recv(4096)
            if not piece:
                break
            chunks.append(piece)
        raw = b"".join(chunks)
        _, _, body = raw.partition(b"\r\n\r\n")
        return body or raw
    finally:
        sock.close()


def _geo_from_payload(payload: dict) -> dict:
    if payload.get("status") != "success":
        return {
            "ok": False,
            "error": "geo_failed",
            "country_code": "",
            "country_name": "",
            "ip": "",
        }
    return {
        "ok": True,
        "error": "",
        "ip": str(payload.get("query") or ""),
        "country_code": str(payload.get("countryCode") or "").upper(),
        "country_name": str(payload.get("country") or ""),
    }


def _fail(code: str) -> dict:
    return {
        "ok": False,
        "error": code,
        "country_code": "",
        "country_name": "",
        "ip": "",
    }


def test_proxy(data: dict, *, timeout: float = 14.0) -> dict:
    protocol = normalize_protocol(str(data.get("protocol") or "http"))
    if protocol.startswith("socks"):
        try:
            raw = (
                _socks5_http_get(data, timeout)
                if protocol == "socks5"
                else _socks4_http_get(data, timeout)
            )
            payload = json.loads(raw.decode("utf-8", errors="replace"))
        except json.JSONDecodeError:
            return _fail("test_failed")
        except Exception as exc:
            return _fail(classify_proxy_error(exc))
        return _geo_from_payload(payload)

    proxy_url = _proxy_handler_url(data)
    handler = urllib.request.ProxyHandler({"http": proxy_url, "https": proxy_url})
    opener = urllib.request.build_opener(handler)
    req = urllib.request.Request(
        IP_API_URL,
        headers={"User-Agent": "TuyahoProxyCheck/1.0"},
    )
    try:
        with opener.open(req, timeout=timeout) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return _fail(classify_proxy_error(e))
    except (urllib.error.URLError, OSError, TimeoutError, json.JSONDecodeError, ValueError) as e:
        return _fail(classify_proxy_error(e))
    return _geo_from_payload(payload)
