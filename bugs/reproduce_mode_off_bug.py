"""
Standalone reproduction of the REST API "mode off is unrecoverable" bug.
See bug_report_rest_api_mode_off_unrecoverable.md (this directory) for the full writeup.

Three parts, run in order against a real attached device:
  1. Toggle the port off/on via the hub's raw firmware CLI (ad-hoc /command) -- works.
  2. Toggle the port off/on via the REST API mode endpoint -- "on" silently fails.
  3. Revive the stuck port using the firmware CLI again, leaving the hub in a working state.

Run from the project root:
  python bugs/reproduce_mode_off_bug.py [hubId] [portId]

If hubId is omitted, the first hub reported by GET /api/v1/hubs is used.
If portId is omitted, it defaults to 2.
"""

import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from test_api import check_api, firmware_command, rest_get_port, rest_list_hubs, rest_set_mode

PAUSE = 5


def banner(title):
    print("\n" + "=" * 70)
    print(title)
    print("=" * 70)


def show_rest_state(hub_id, port_id, label):
    state = rest_get_port(hub_id, port_id)
    mode = state["state"]["mode"]
    sensors = {s["type"]: s["value"] for s in state.get("sensors", [])}
    mA = sensors.get("milliamps")
    V = sensors.get("volts")
    print(f"[REST]      {label}: mode={mode!r}  current={mA} mA  voltage={V} V")
    return state


def show_firmware_state(hub_id, port_id, label):
    out = firmware_command(hub_id, f"state {port_id}\n")
    line = [l for l in out.splitlines() if l.strip().startswith(str(port_id))]
    print(f"[firmware]  {label}: {line[0].strip() if line else out.strip()}")


def wait(seconds=PAUSE):
    print(f"... waiting {seconds}s ...")
    time.sleep(seconds)


def part1_firmware_cli_works(hub_id, port_id):
    banner("PART 1: toggling the port via the raw firmware CLI (ad-hoc /command)")
    print(
        "This sends 'mode o' / 'mode c' directly to the hub's own command shell over\n"
        "serial, bypassing both the REST and JSON-RPC layers of CambrionixApiService.\n"
        "Expectation: the port goes off, then comes back on, with no extra recovery step."
    )

    show_firmware_state(hub_id, port_id, "before")

    print(f"\n>> sending firmware command: mode o {port_id}")
    firmware_command(hub_id, f"mode o {port_id}\n")
    show_firmware_state(hub_id, port_id, "after 'mode o' (off)")
    wait()

    print(f"\n>> sending firmware command: mode c {port_id}")
    firmware_command(hub_id, f"mode c {port_id}\n")
    wait()
    show_firmware_state(hub_id, port_id, "after 'mode c' (on)")

    print("\nResult: firmware-level off -> on round trip works correctly.")


def part2_rest_api_breaks(hub_id, port_id):
    banner("PART 2: toggling the same port via the REST API mode endpoint")
    print(
        "Now using POST /api/v1/hubs/{hubId}/ports/{portId}/mode, the documented,\n"
        "supported way for an application to control the port.\n"
        "Expectation if the API worked like the firmware CLI: off, then on again."
    )

    show_rest_state(hub_id, port_id, "before")

    print("\n>> POST .../mode  {\"mode\": \"off\"}")
    result = rest_set_mode(hub_id, port_id, "off")
    print(f"   API response: {result}")
    wait()
    show_rest_state(hub_id, port_id, "after mode=off")

    print("\n>> POST .../mode  {\"mode\": \"on\"}")
    result = rest_set_mode(hub_id, port_id, "on")
    print(f"   API response: {result}  <-- reports success")
    wait()
    state = show_rest_state(hub_id, port_id, "after mode=on")

    if state["state"]["mode"] == "off":
        print(
            "\nBUG REPRODUCED: the API call returned success, but the port's mode is\n"
            "still 'off' and it is not charging. Repeating the 'on' call (try it\n"
            "yourself) does not help -- the port is stuck until something below the\n"
            "REST layer intervenes."
        )
    else:
        print(
            "\nPort actually turned back on this run -- the bug did not reproduce.\n"
            "(If you see this, the underlying service state may have changed; try again.)"
        )


def part3_revive_with_firmware_cli(hub_id, port_id):
    banner("PART 3: reviving the stuck port with the firmware CLI")
    print(
        "Since Part 1 showed the firmware itself has no problem switching the port\n"
        "back on, we use the same ad-hoc command to recover the port without\n"
        "rebooting the whole hub (which would also drop every other attached device)."
    )

    print(f"\n>> sending firmware command: mode c {port_id}")
    firmware_command(hub_id, f"mode c {port_id}\n")
    wait()
    state = show_rest_state(hub_id, port_id, "after revival")

    if state["state"]["mode"] == "on":
        print("\nPort successfully revived -- back to 'on' and (re)charging.")
    else:
        print("\nPort still not 'on' -- give it a few more seconds and check again.")


if __name__ == "__main__":
    ok, info = check_api()
    if not ok:
        print(f"CambrionixApiService not reachable -- {info}")
        sys.exit(1)

    if len(sys.argv) > 1:
        hub_id = sys.argv[1]
    else:
        hubs = rest_list_hubs()
        if not hubs:
            print("No hubs found via GET /api/v1/hubs.")
            sys.exit(1)
        hub_id = hubs[0]
        print(f"No hubId given, using discovered hub: {hub_id}")

    port_id = int(sys.argv[2]) if len(sys.argv) > 2 else 2

    part1_firmware_cli_works(hub_id, port_id)
    part2_rest_api_breaks(hub_id, port_id)
    part3_revive_with_firmware_cli(hub_id, port_id)
