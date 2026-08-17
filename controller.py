import threading
import time
import queue
import logging
from dataclasses import asdict

from hub_client import discover_hubs

logger = logging.getLogger(__name__)


def _close_all(hubs: list) -> None:
    for h in hubs:
        if hasattr(h, "close"):
            try:
                h.close()
            except Exception:
                pass


class HubController:
    """Background polling layer that owns the serial port.

    We use a producer-consumer model where the web application produces
    commands and a dedicated worker thread consumes them. This decouples
    HTTP requests from hardware I/O latency.

    Two locks are replaced by a command queue for writes, while a cache lock
    remains for thread-safe reads of the last known state.
    """

    def __init__(self, poll_interval: float = 2.0) -> None:
        self._cache_lock = threading.Lock()
        self._cache: list[dict] = []
        self._hubs: dict[str, any] = {}  # Hub ID -> HubClient registry
        self._command_queue = queue.Queue()
        self._poll_interval = poll_interval
        self._last_discovery = 0.0
        self._discovery_interval = 60.0

        self._worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
        self._worker_thread.start()

    def _worker_loop(self) -> None:
        logger.info("HubController worker loop started")
        while True:
            try:
                # 1. Process all pending commands (priority)
                while not self._command_queue.empty():
                    try:
                        cmd = self._command_queue.get_nowait()
                        self._process_command(cmd)
                        self._command_queue.task_done()
                    except queue.Empty:
                        break

                # 2. Periodic Discovery
                now = time.monotonic()
                if now - self._last_discovery > self._discovery_interval or not self._hubs:
                    self._discover()
                    self._last_discovery = now

                # 3. Poll all registered hubs
                self._poll()

                # 4. Wait interruptibly until next poll
                elapsed = time.monotonic() - now
                wait_time = max(0.1, self._poll_interval - elapsed)
                try:
                    cmd = self._command_queue.get(timeout=wait_time)
                    self._process_command(cmd)
                    self._command_queue.task_done()
                except queue.Empty:
                    pass
            except Exception as e:
                logger.error(f"Error in worker loop: {e}", exc_info=True)
                time.sleep(1)

    def _discover(self) -> None:
        logger.debug("Discovering hubs...")
        try:
            discovered = discover_hubs()
            new_hubs_dict = {h.hub_id: h for h in discovered}

            # Close and remove hubs no longer present
            current_ids = set(self._hubs.keys())
            found_ids = set(new_hubs_dict.keys())

            removed_ids = current_ids - found_ids
            for hid in removed_ids:
                logger.info(f"Hub {hid} removed")
                h = self._hubs.pop(hid)
                if hasattr(h, "close"):
                    h.close()

            # Add new hubs, close redundant new instances for existing hubs
            for hid, h in new_hubs_dict.items():
                if hid not in self._hubs:
                    logger.info(f"Hub {hid} discovered")
                    self._hubs[hid] = h
                else:
                    # Hub already known, close the fresh discovery instance
                    if hasattr(h, "close"):
                        h.close()
        except Exception as e:
            logger.error(f"Discovery failed: {e}")

    def _poll(self) -> None:
        state = []
        for hid, h in list(self._hubs.items()):
            try:
                state.append({
                    "hub_id": h.hub_id,
                    "modes": h.supported_modes(),
                    "ports": [asdict(p) for p in h.get_ports()],
                    "error": None,
                })
            except Exception as e:
                logger.error(f"Error polling hub {hid}: {e}")
                state.append({
                    "hub_id": hid,
                    "modes": [],
                    "ports": [],
                    "error": str(e),
                })
                # Force discovery on next iteration if a hub fails
                self._last_discovery = 0

        with self._cache_lock:
            self._cache = state

    def _apply_set_mode(self, hub_id: str, port_id: int | None, mode: str) -> None:
        h = self._hubs.get(hub_id)
        if not h:
            logger.warning(f"Command ignored: Hub {hub_id} not found")
            return
        try:
            if port_id is None:
                logger.info(f"Command: Setting hub {hub_id} ALL ports to {mode}")
            else:
                logger.info(f"Command: Setting hub {hub_id} port {port_id} to {mode}")
            h.set_mode(port_id, mode)
        except Exception as e:
            logger.error(f"Failed to set mode for hub {hub_id}: {e}")
            self._last_discovery = 0  # Force rediscovery on error

    def _process_command(self, cmd: tuple) -> None:
        op, *args = cmd
        if op == "set_mode":
            hub_id, port_id, mode = args
            self._apply_set_mode(hub_id, port_id, mode)
        elif op == "set_mode_all":
            hub_id, mode = args
            self._apply_set_mode(hub_id, None, mode)
        elif op == "discover":
            logger.info("Command: Manual hub discovery")
            self._discover()
            self._last_discovery = time.monotonic()

    def get_hubs(self) -> list[dict]:
        with self._cache_lock:
            return list(self._cache)

    def set_mode(self, hub_id: str, port_id: int, mode: str) -> None:
        """Pushes command to queue and returns immediately."""
        self._command_queue.put(("set_mode", hub_id, port_id, mode))

    def set_mode_all(self, hub_id: str, mode: str) -> None:
        """Pushes a hub-wide (every port) set-mode command to queue and returns immediately."""
        self._command_queue.put(("set_mode_all", hub_id, mode))

    def discover(self) -> None:
        """Pushes discovery command to queue."""
        self._command_queue.put(("discover",))
