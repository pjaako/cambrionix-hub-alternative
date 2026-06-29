import threading
import time
from dataclasses import asdict

from hub_client import discover_hubs


def _close_all(hubs: list) -> None:
    for h in hubs:
        if hasattr(h, "close"):
            h.close()


class HubController:
    """Background polling layer that owns the serial port.

    A daemon thread polls all hubs on a fixed schedule and stores results in
    an in-memory cache.  Web routes read from the cache (no serial I/O per
    request).  Mode changes go write-through: they acquire the serial lock,
    open a fresh connection, send the command, and close.

    Two locks deliberately separate serial I/O from cache access so that web
    reads are never blocked by ongoing serial communication.
    """

    def __init__(self, poll_interval: float = 2.0) -> None:
        self._serial_lock = threading.Lock()
        self._cache_lock = threading.Lock()
        self._cache: list[dict] = []
        self._poll_interval = poll_interval
        t = threading.Thread(target=self._loop, daemon=True)
        t.start()

    def _loop(self) -> None:
        while True:
            self._refresh()
            time.sleep(self._poll_interval)

    def _refresh(self) -> None:
        with self._serial_lock:
            hubs = discover_hubs()
            state = []
            for h in hubs:
                try:
                    state.append({
                        "hub_id": h.hub_id,
                        "modes": h.supported_modes(),
                        "ports": [asdict(p) for p in h.get_ports()],
                        "error": None,
                    })
                except Exception as e:
                    state.append({
                        "hub_id": h.hub_id,
                        "modes": [],
                        "ports": [],
                        "error": str(e),
                    })
                finally:
                    if hasattr(h, "close"):
                        h.close()
        with self._cache_lock:
            self._cache = state

    def get_hubs(self) -> list[dict]:
        with self._cache_lock:
            return list(self._cache)

    def set_mode(self, hub_id: str, port_id: int, mode: str) -> None:
        with self._serial_lock:
            hubs = discover_hubs()
            try:
                hub = next((h for h in hubs if h.hub_id == hub_id), None)
                if hub is None:
                    raise KeyError(f"hub {hub_id!r} not found")
                hub.set_mode(port_id, mode)
            finally:
                _close_all(hubs)
