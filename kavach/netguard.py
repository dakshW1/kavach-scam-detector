"""Network guard: blocks every outgoing internet connection from this program.

Called once when the app starts. It replaces Python's low-level socket functions so that any
attempt to reach a non-local address raises NetworkBlocked, whether it comes from our code or from
a library. Connections to this computer itself (localhost) are still allowed, because the app's own
web page talks to it that way.

The only exception is the optional "Online Scam Intel" feature: when the user clicks "Send this
search", it opens a short window with `allow(hosts)` that permits exactly those search hosts.
"""
from __future__ import annotations

import contextlib
import ipaddress
import socket
import threading

_real_connect = socket.socket.connect
_real_connect_ex = socket.socket.connect_ex
_real_getaddrinfo = socket.getaddrinfo
_real_create_connection = socket.create_connection

_state = threading.local()
_enabled = False
blocked_attempts: list[str] = []      # what was blocked this session (shown in the privacy panel)
allowed_log: list[str] = []           # what was allowed through allow() (Online Scam Intel only)


class NetworkBlocked(ConnectionError):
    pass


def _allowed_hosts() -> set[str]:
    return getattr(_state, "hosts", set())


def _is_local(host) -> bool:
    if host is None:
        return True
    h = str(host).strip("[]").lower()
    if h in ("localhost", "", "0.0.0.0") or h.endswith(".localhost"):
        return True
    try:
        ip = ipaddress.ip_address(h.split("%")[0])
        return ip.is_loopback or ip.is_unspecified
    except ValueError:
        return False


def _check(host, what: str):
    if not _enabled or _is_local(host):
        return
    allowed = _allowed_hosts()
    if allowed and (str(host) in allowed or str(host) in getattr(_state, "ips", set())):
        return
    blocked_attempts.append(f"{what} {host}")
    raise NetworkBlocked(f"Kavach blocked a network connection to {host}: this app works offline.")


def _guarded_getaddrinfo(host, *args, **kwargs):
    _check(host, "lookup")
    res = _real_getaddrinfo(host, *args, **kwargs)
    if _allowed_hosts() and host in _allowed_hosts():
        _state.ips = getattr(_state, "ips", set()) | {r[4][0] for r in res}
    return res


def _guarded_connect(self, address):
    host = address[0] if isinstance(address, tuple) else address
    if self.family in (socket.AF_INET, socket.AF_INET6):
        _check(host, "connect")
    return _real_connect(self, address)


def _guarded_connect_ex(self, address):
    host = address[0] if isinstance(address, tuple) else address
    if self.family in (socket.AF_INET, socket.AF_INET6):
        _check(host, "connect")
    return _real_connect_ex(self, address)


def _guarded_create_connection(address, *args, **kwargs):
    _check(address[0], "connect")
    return _real_create_connection(address, *args, **kwargs)


def enable() -> None:
    """Block all outgoing connections (idempotent)."""
    global _enabled
    socket.socket.connect = _guarded_connect
    socket.socket.connect_ex = _guarded_connect_ex
    socket.getaddrinfo = _guarded_getaddrinfo
    socket.create_connection = _guarded_create_connection
    _enabled = True


def disable() -> None:
    """Restore normal networking (used only by tests)."""
    global _enabled
    socket.socket.connect = _real_connect
    socket.socket.connect_ex = _real_connect_ex
    socket.getaddrinfo = _real_getaddrinfo
    socket.create_connection = _real_create_connection
    _enabled = False


def is_enabled() -> bool:
    return _enabled


@contextlib.contextmanager
def allow(hosts: set[str]):
    """Temporarily allow connections to exactly these hosts, in this thread only."""
    prev_h, prev_i = _allowed_hosts(), getattr(_state, "ips", set())
    _state.hosts, _state.ips = set(hosts), set()
    allowed_log.extend(sorted(hosts))
    try:
        yield
    finally:
        _state.hosts, _state.ips = prev_h, prev_i


def self_test() -> bool:
    """True if an outgoing connection is really refused right now (used by the privacy panel)."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(0.5)
        try:
            s.connect(("1.1.1.1", 443))
        finally:
            s.close()
        return False
    except NetworkBlocked:
        blocked_attempts.pop() if blocked_attempts and blocked_attempts[-1].endswith("1.1.1.1") else None
        return True
    except OSError:
        return False
