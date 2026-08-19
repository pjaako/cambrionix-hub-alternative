import threading
import time
import queue
import logging
import os
from dataclasses import asdict

from hub_backends import CommandRefused
from hub_client import discover_hubs
from models import CommandError

logger = logging.getLogger(__name__)

# How long a failed command stays visible. It only explains a click, so it does
# not need to live forever: the *reason* a command was refused (a port error
# flag, a health flag) is polled state that persists on its own for as long as
# it is true. Must stay above the client-side pending timeout in main.js so a
# tile cannot return to normal while the explanation is still on screen.
_COMMAND_ERROR_TTL = 30.0

_HEALTH_FLAG_TEXT = {
    "UV": "under-voltage recorded (UV)",
    "OV": "over-voltage recorded (OV)",
    "OT": "over-temperature recorded (OT)",
    "E": "error flag set (E)",
}
_LATCHED_HINT = ("The firmware refuses mode changes while this is set, and it "
                 "latches until the hub is power-cycled.")


def _hub_error_detail(poll_error, health_flags, command_error) -> str | None:
    """One human-readable line for the hub header."""
    if poll_error:
        return f"Poll failed: {poll_error} - showing last known state."
    if health_flags:
        named = ", ".join(_HEALTH_FLAG_TEXT.get(f, f) for f in health_flags)
        return f"Hub health: {named}. {_LATCHED_HINT}"
    if command_error:
        return command_error["message"]
    return None


def _port_error_detail(command_error, error_flag, hub_detail) -> str | None:
    """One human-readable line for a port tile."""
    if command_error:
        return command_error["message"]
    if error_flag:
        return "Firmware error flag (E) set - the hub refuses mode changes on this port."
    return hub_detail


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
        # Undecorated poll output. _cache is this plus error decoration, so a
        # refusal can be folded in without re-reading the hardware.
        self._raw_state: list[dict] = []
        # (hub_id, port_id | None) -> CommandError. port_id None means hub-wide.
        self._command_errors: dict[tuple, CommandError] = {}
        # Dev-only simulated faults, populated solely via inject_error().
        self._injected: dict[str, dict] = {}
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
                # Drop errors and simulated faults with the hub they described,
                # so a reconnect does not inherit them.
                self._injected.pop(hid, None)
                for key in [k for k in self._command_errors if k[0] == hid]:
                    del self._command_errors[key]

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
        previous = {h["hub_id"]: h for h in self._raw_state}
        state = []
        for hid, h in list(self._hubs.items()):
            try:
                ports = [asdict(p) for p in h.get_ports()]
                state.append({
                    "hub_id": h.hub_id,
                    "modes": h.supported_modes(),
                    "ports": ports,
                    # health() reads what get_ports() just fetched, so this
                    # costs no extra round trip.
                    "health": asdict(h.health()),
                    "error": None,
                })
            except Exception as e:
                logger.error(f"Error polling hub {hid}: {e}")
                # Keep the last known ports rather than blanking the grid: an
                # operator needs to see what the ports were doing when the hub
                # dropped. The stale flag is what tells the UI to dim them.
                old = previous.get(hid, {})
                state.append({
                    "hub_id": hid,
                    "modes": old.get("modes", []),
                    "ports": old.get("ports", []),
                    "health": old.get("health"),
                    "error": str(e),
                })
                # Force discovery on next iteration if a hub fails
                self._last_discovery = 0

        self._raw_state = state
        self._refresh_cache_view()

    def _refresh_cache_view(self) -> None:
        """Rebuild the public cache from raw poll output plus error decoration.

        The single place where errors are turned into what the UI renders. Both
        renderers (Jinja SSR and renderPort in main.js) consume the computed
        `blocked` and `error_detail` rather than re-deriving them, so they
        cannot drift apart.

        Called by the poll loop and by the command handlers, so a refused
        command shows up immediately instead of waiting for the next poll.
        """
        now = time.time()
        for key, err in list(self._command_errors.items()):
            if now - err.at > _COMMAND_ERROR_TTL:
                del self._command_errors[key]

        view = []
        for hub in self._raw_state:
            hub_id = hub["hub_id"]
            injected = self._injected.get(hub_id, {})

            health = dict(hub.get("health") or {})
            if injected.get("health_flags"):
                health["error_flags"] = sorted(
                    set(health.get("error_flags") or []) | set(injected["health_flags"])
                )
            health_flags = health.get("error_flags") or []

            poll_error = injected.get("poll_error") or hub.get("error")
            hub_command_error = self._command_errors.get((hub_id, None))
            hub_command_error = asdict(hub_command_error) if hub_command_error else None
            hub_blocked = bool(poll_error) or bool(health_flags)
            hub_detail = _hub_error_detail(poll_error, health_flags, hub_command_error)

            ports = []
            for raw_port in hub["ports"]:
                port = dict(raw_port)  # never mutate the raw poll output
                if port["id"] in injected.get("port_flags", ()):
                    port["error_flag"] = True
                port_error = self._command_errors.get((hub_id, port["id"]))
                port_error = asdict(port_error) if port_error else None
                port["command_error"] = port_error
                # One concept: a tile is red exactly when its controls are
                # dead. A refused command counts - whatever caused the refusal
                # will almost certainly refuse the retry too. The TTL re-enables
                # the button after 30s so a retry is never permanently barred.
                port["blocked"] = (
                    bool(port_error) or bool(port.get("error_flag")) or hub_blocked
                )
                port["error_detail"] = _port_error_detail(
                    port_error, port.get("error_flag"), hub_detail if hub_blocked else None
                )
                ports.append(port)

            view.append({
                **hub,
                "ports": ports,
                "health": health or None,
                "error": poll_error,
                # Ports are last-known rather than freshly read.
                "stale": bool(poll_error),
                "command_error": hub_command_error,
                "blocked": hub_blocked or hub_command_error is not None,
                "error_detail": hub_detail,
            })

        with self._cache_lock:
            self._cache = view

    def _record_command_error(self, hub_id, port_id, error: CommandError) -> None:
        self._command_errors[(hub_id, port_id)] = error

    def _clear_command_error(self, hub_id, port_id) -> None:
        self._command_errors.pop((hub_id, port_id), None)
        if port_id is None:
            # A hub-wide command that succeeded proves nothing is blocked.
            for key in [k for k in self._command_errors if k[0] == hub_id]:
                del self._command_errors[key]

    def _apply_set_mode(self, hub_id: str, port_id: int | None, mode: str) -> None:
        h = self._hubs.get(hub_id)
        if not h:
            logger.warning(f"Command ignored: Hub {hub_id} not found")
            self._record_command_error(hub_id, port_id, CommandError(
                kind="transport", code=None, message=f"Hub {hub_id} is not connected",
                command="", mode=mode, port_id=port_id, at=time.time()))
            self._refresh_cache_view()
            return
        try:
            if port_id is None:
                logger.info(f"Command: Setting hub {hub_id} ALL ports to {mode}")
            else:
                logger.info(f"Command: Setting hub {hub_id} port {port_id} to {mode}")
            h.set_mode(port_id, mode)
        except CommandRefused as e:
            logger.error(f"Hub {hub_id} refused mode {mode}: {e.message}")
            self._record_command_error(hub_id, port_id, CommandError(
                kind="refused", code=e.code, message=e.message,
                command=e.command, mode=mode, port_id=port_id, at=time.time()))
            # Deliberately no rediscovery here. A refusal is a considered answer
            # over a healthy link, not a dead hub - tearing down and rescanning
            # the serial port on every refused click would cost a lot and fix
            # nothing.
        except Exception as e:
            logger.error(f"Failed to set mode for hub {hub_id}: {e}")
            self._record_command_error(hub_id, port_id, CommandError(
                kind="transport", code=None, message=str(e),
                command="", mode=mode, port_id=port_id, at=time.time()))
            self._last_discovery = 0  # Force rediscovery on error
        else:
            self._clear_command_error(hub_id, port_id)
        self._refresh_cache_view()

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
        elif op == "inject_error":
            self._apply_injection(args[0])

    def _apply_injection(self, payload: dict) -> None:
        """Simulate a fault. Dev-only, reached through the gated debug route.

        Injected faults are decorated by the same _refresh_cache_view() pass as
        real ones, so what you see in the browser is what a genuine failure
        looks like - not a separate rendering path that could diverge.
        """
        targets = [payload["hub_id"]] if payload.get("hub_id") else [
            h["hub_id"] for h in self._raw_state
        ]
        for hub_id in targets:
            slot = self._injected.setdefault(
                hub_id, {"port_flags": set(), "health_flags": [], "poll_error": None}
            )
            if payload.get("clear"):
                self._injected.pop(hub_id, None)
                for key in [k for k in self._command_errors if k[0] == hub_id]:
                    del self._command_errors[key]
                continue

            kind = payload.get("kind", "command")
            if kind == "command":
                self._record_command_error(hub_id, payload.get("port_id"), CommandError(
                    kind="injected", code=payload.get("code"),
                    message=payload.get("message") or "injected error",
                    command="(injected)", mode=payload.get("mode", "on"),
                    port_id=payload.get("port_id"), at=time.time()))
            elif kind == "port_flag":
                if payload.get("port_id") is None:
                    slot["port_flags"] = {p["id"] for h in self._raw_state
                                          if h["hub_id"] == hub_id for p in h["ports"]}
                else:
                    slot["port_flags"].add(payload["port_id"])
            elif kind == "health":
                slot["health_flags"] = list(payload.get("flags") or ["UV"])
            elif kind == "poll":
                slot["poll_error"] = payload.get("message") or "injected poll failure"
            else:
                logger.warning("Unknown injection kind %r", kind)
        self._refresh_cache_view()

    def inject_error(self, payload: dict) -> None:
        """Queue a simulated fault. No-op unless CAMBRIONIX_DEV_TOOLS is set."""
        if not os.environ.get("CAMBRIONIX_DEV_TOOLS"):
            logger.warning("inject_error ignored: CAMBRIONIX_DEV_TOOLS is not set")
            return
        self._command_queue.put(("inject_error", payload))

    def get_hubs(self) -> list[dict]:
        """Snapshot of the last known state. Treat the dicts as read-only -
        they are rebuilt by _refresh_cache_view(), not copied per caller."""
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
