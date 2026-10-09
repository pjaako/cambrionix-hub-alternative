#!/bin/bash
# Run as root INSIDE the container (CT): creates /dev/ttyUSBn -> ct-serial/ttyUSBn symlinks.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
install -m 0644 "$HERE/cambrionix-tty.conf" /etc/tmpfiles.d/cambrionix-tty.conf
systemd-tmpfiles --create /etc/tmpfiles.d/cambrionix-tty.conf
echo "+ /dev/ttyUSB*:"
ls -l /dev/ttyUSB* 2>/dev/null || true
if [ -c /dev/ttyUSB0 ] && [ ! -L /dev/ttyUSB0 ]; then
  echo "WARNING: /dev/ttyUSB0 is a real char node, not a symlink: static Proxmox devN"
  echo "         passthrough is still active. Remove it on the host (pct set <CTID> -delete devN),"
  echo "         then 'pct reboot <CTID>'. See ../README.md."
fi
