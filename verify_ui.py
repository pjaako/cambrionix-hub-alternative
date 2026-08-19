"""End-to-end check of the error UI against a real hub.

Port tiles are built twice - server-side by Jinja on first load, and
client-side by renderPort() on every 2s poll - so both renderers are checked:
the SSR markup over plain HTTP, and the polled DOM in a real browser (which
also catches console errors). Injected faults travel the same decoration path
as real ones, so what this asserts is what a genuine failure looks like.

The central invariant under test: a port fault reddens its own tile, while a
hub-wide fault reddens the hub header and disables the controls WITHOUT
reddening every tile - otherwise one genuinely broken port would be hidden
among fifteen healthy ones.

Requires a connected hub with CambrionixApiService stopped, plus
`python -m playwright install chromium`. Named verify_* rather than test_* so
pytest does not collect it - it starts a server at import time.
"""
import os
import re
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
n_ports = len(appmod.hub.get_hubs()[0]["ports"])
print("hub: %s (%d ports)" % (hub_id, n_ports))

console_errors = []
failures = []


def inject(**kw):
    kw.setdefault("hub_id", hub_id)
    httpx.post(f"{BASE}/api/debug/inject-error", json=kw)


def check_ssr(label, want_hub_error, want_red, want_disabled):
    """Assert the server-rendered markup, which a browser replaces within ~100ms."""
    h = httpx.get(BASE).text
    hub_err = 'class="hub-section has-error' in h
    red = len(re.findall(r'<div class="port-tile[^"]*has-error"', h))
    badges = len(re.findall(r'class="tile-error"', h))
    disabled = len(re.findall(r'pwr-btn[^"]*" disabled', h))
    ok = (hub_err == want_hub_error and red == want_red
          and badges == want_red and disabled == want_disabled)
    print("  SSR  %-28s hub_err=%-5s red=%-3d badges=%-3d btns_off=%-3d %s"
          % (label, hub_err, red, badges, disabled, "OK" if ok else "MISMATCH"))
    if not ok:
        failures.append("SSR " + label)


def check(label, page, want_hub_error, want_red, want_disabled):
    # Wait out at least one 2s poll so the JS renderer, not the SSR pass,
    # produced what we are looking at.
    time.sleep(3.0)
    hub_error = bool(page.locator(".hub-section.has-error").count())
    red = page.locator(".port-tile.has-error").count()
    badges = page.locator(".tile-error").count()
    disabled = page.locator(".pwr-btn[disabled]").count()
    lock_disabled = page.locator(".hub-lock-toggle[disabled]").count()
    detail = page.locator(".hub-error-detail").first.inner_text()
    ok = (hub_error == want_hub_error and red == want_red
          and badges == want_red and disabled == want_disabled)
    print("  DOM  %-28s hub_err=%-5s red=%-3d badges=%-3d btns_off=%-3d lock_off=%d %s"
          % (label, hub_error, red, badges, disabled, lock_disabled,
             "OK" if ok else "MISMATCH"))
    if detail:
        print("       detail: %s" % detail[:66])
    if not ok:
        failures.append(label)
    check_ssr(label, want_hub_error, want_red, want_disabled)


with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    page.on("console", lambda m: console_errors.append(m.text) if m.type == "error" else None)
    page.on("pageerror", lambda e: console_errors.append("pageerror: %s" % e))

    page.goto(BASE, wait_until="networkidle")

    # Whatever the hub reports on its own, before anything is injected.
    real_faults = sum(1 for x in appmod.hub.get_hubs()[0]["ports"] if x["port_error"])
    real_hub_err = appmod.hub.get_hubs()[0]["blocked"]
    print("baseline: %d real port fault(s), hub blocked=%s\n" % (real_faults, real_hub_err))
    base_red = real_faults
    base_off = n_ports if real_hub_err else real_faults
    # Inject onto a port that is not already faulted, or the count cannot move.
    clean = [x["id"] for x in appmod.hub.get_hubs()[0]["ports"] if not x["port_error"]]
    p1, p2 = clean[0], clean[1]
    print("clean ports used for injection: %d, %d" % (p1, p2))
    print()

    check("baseline", page, real_hub_err, base_red, base_off)

    inject(kind="command", port_id=p1, code="422")
    check("(a) refused command", page, real_hub_err, base_red + 1, base_off + 1)
    print("       badge: %r" % page.locator(".tile-error").first.inner_text())
    inject(clear=True)

    inject(kind="port_fault", port_id=p2)
    check("(b) injected port fault e", page, real_hub_err, base_red + 1, base_off + 1)
    inject(clear=True)

    # The invariant: hub-wide faults disable everything but redden nothing.
    inject(kind="health", flags=["UV"])
    check("(c) hub health UV", page, True, base_red, n_ports)
    inject(clear=True)

    inject(kind="health", flags=["E"])
    check("(d) hub-wide E flag", page, True, base_red, n_ports)
    inject(clear=True)

    inject(kind="poll", message="serial port disappeared")
    check("(e) hub poll failure", page, True, base_red, n_ports)
    print("       stale dimming: %s" % bool(page.locator(".hub-section.is-stale").count()))
    inject(clear=True)

    # A port fault must stay distinguishable underneath a hub-wide fault.
    inject(kind="port_fault", port_id=p2)
    inject(kind="health", flags=["UV"])
    check("(f) port fault under hub error", page, True, base_red + 1, n_ports)
    inject(clear=True)

    check("recovered", page, real_hub_err, base_red, base_off)

    # A refused command must release the tile from its pending state; before
    # this change it stayed disabled forever because it never reached target.
    inject(kind="port_fault", port_id=p2)
    time.sleep(3)
    stuck = page.locator(".port-tile.pending").count()
    print("  %-33s pending tiles=%d %s"
          % ("no stuck pending tiles", stuck, "OK" if stuck == 0 else "MISMATCH"))
    if stuck:
        failures.append("stuck pending")
    inject(clear=True)

    browser.close()

print("\nconsole errors: %s" % (console_errors or "none"))
print("mismatches    : %s" % (failures or "none"))
print("RESULT: %s" % ("PASS" if not console_errors and not failures else "FAIL"))
