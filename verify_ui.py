"""End-to-end check of the error UI against a real hub.

Port tiles are built twice - server-side by Jinja on first load, and
client-side by renderPort() on every 2s poll - so both renderers are checked:
the SSR markup over plain HTTP, and the polled DOM in a real browser (which
also catches console errors). Injected faults travel the same decoration path
as real ones, so what this asserts is what a genuine failure looks like.

Requires a connected hub with CambrionixApiService stopped, plus
`python -m playwright install chromium`. Named verify_* rather than test_* so
pytest does not collect it - it starts a server at import time.
"""
import re
import os
import threading
import time

os.environ["CAMBRIONIX_DEV_TOOLS"] = "1"

import httpx
import uvicorn
from playwright.sync_api import sync_playwright

import app as appmod

BASE = "http://127.0.0.1:8013"

threading.Thread(
    target=lambda: uvicorn.run(appmod.app, host="127.0.0.1", port=8013, log_level="error"),
    daemon=True,
).start()
time.sleep(8)

hub_id = list(appmod.hub._hubs)[0]
print("hub:", hub_id)

console_errors = []
failures = []


def inject(**kw):
    kw.setdefault("hub_id", hub_id)
    httpx.post(f"{BASE}/api/debug/inject-error", json=kw)


def check_ssr(label, want_hub_error, want_blocked_tiles):
    """Assert the server-rendered markup, which a browser replaces within ~100ms."""
    h = httpx.get(BASE).text
    hub_err = 'class="hub-section has-error' in h
    tiles = len(re.findall(r'<div class="port-tile[^"]*has-error"', h))
    badges = len(re.findall(r'class="tile-error"', h))
    disabled = len(re.findall(r'pwr-btn[^"]*" disabled', h))
    ok = (hub_err == want_hub_error and tiles == want_blocked_tiles
          and badges == want_blocked_tiles and disabled == want_blocked_tiles)
    print("  SSR  %-27s hub_err=%-5s tiles=%-3d badges=%-3d btns_off=%-3d %s"
          % (label, hub_err, tiles, badges, disabled, "OK" if ok else "MISMATCH"))
    if not ok:
        failures.append("SSR " + label)


def check(label, page, want_hub_error, want_blocked_tiles):
    # Wait out at least one 2s poll so the JS renderer, not the SSR pass,
    # produced what we are looking at.
    time.sleep(3.0)
    hub_error = page.locator(".hub-section.has-error").count()
    tiles = page.locator(".port-tile.has-error").count()
    badges = page.locator(".tile-error").count()
    detail = page.locator(".hub-error-detail").first.inner_text()
    disabled = page.locator(".pwr-btn[disabled]").count()
    lock_disabled = page.locator(".hub-lock-toggle[disabled]").count()
    ok = (bool(hub_error) == want_hub_error and tiles == want_blocked_tiles
          and disabled == want_blocked_tiles and badges == want_blocked_tiles)
    print("  %-32s hub_err=%-5s tiles=%-3d badges=%-3d btns_off=%-3d lock_off=%d %s"
          % (label, bool(hub_error), tiles, badges, disabled, lock_disabled,
             "OK" if ok else "MISMATCH"))
    if detail:
        print("       detail: %s" % detail[:70])
    if not ok:
        failures.append(label)
    check_ssr(label, want_hub_error, want_blocked_tiles)


with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    page.on("console", lambda m: console_errors.append(m.text) if m.type == "error" else None)
    page.on("pageerror", lambda e: console_errors.append("pageerror: %s" % e))

    page.goto(BASE, wait_until="networkidle")
    check("baseline", page, False, 0)

    inject(kind="command", port_id=1, code="422")
    check("(a) refused command, port 1", page, False, 1)
    print("       badge text: %r" % page.locator(".tile-error").first.inner_text())
    inject(clear=True)

    inject(kind="port_flag", port_id=2)
    check("(b) firmware E flag, port 2", page, False, 1)
    inject(clear=True)

    inject(kind="health", flags=["UV"])
    check("(c) hub health UV", page, True, 16)
    inject(clear=True)

    inject(kind="poll", message="serial port disappeared")
    check("(d) hub poll failure", page, True, 16)
    stale = page.locator(".hub-section.is-stale").count()
    print("       stale dimming applied: %s" % bool(stale))
    inject(clear=True)

    check("recovered", page, False, 0)

    # A refused command must release the tile from its pending state; before
    # this change it stayed disabled forever because it never reached target.
    inject(kind="port_flag", port_id=4)
    time.sleep(3)
    stuck = page.locator(".port-tile.pending").count()
    print("  %-32s pending tiles=%d %s"
          % ("no stuck pending tiles", stuck, "OK" if stuck == 0 else "MISMATCH"))
    if stuck:
        failures.append("stuck pending")
    inject(clear=True)

    browser.close()

print("\nconsole errors: %s" % (console_errors or "none"))
print("mismatches    : %s" % (failures or "none"))
print("RESULT: %s" % ("PASS" if not console_errors and not failures else "FAIL"))
