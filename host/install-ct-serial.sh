#!/bin/bash
# Run as root ON THE PROXMOX HOST, from the directory holding these files:
#   ./install-ct-serial.sh [CTID] [--remove-static-dev]     (default CTID 101)
set -euo pipefail
CTID=101
REMOVE_STATIC=0
for arg in "$@"; do
  case "$arg" in
    --remove-static-dev) REMOVE_STATIC=1;;
    *) CTID="$arg";;
  esac
done
HERE="$(cd "$(dirname "$0")" && pwd)"
CONF="/etc/pve/lxc/${CTID}.conf"

[ -f "$CONF" ] || { echo "no container config $CONF"; exit 1; }

echo "+ installing udev rule"
install -m 0644 "$HERE/90-ct-serial.rules" /etc/udev/rules.d/90-ct-serial.rules
udevadm control --reload
udevadm trigger -s tty --action=add
sleep 1
echo "+ /dev/ct-serial now contains:"
ls -la /dev/ct-serial/ 2>/dev/null || echo "  (empty - is the hub plugged in? check: udevadm info /dev/ttyUSB0 | grep ID_)"

echo "+ updating $CONF"
NEED_REBOOT=0
while IFS= read -r line; do
  case "$line" in ''|'#'*) continue;; esac
  if grep -qxF "$line" "$CONF"; then
    echo "  already present: $line"
  else
    echo "$line" >> "$CONF"
    echo "  added: $line"
    NEED_REBOOT=1
  fi
done < "$HERE/ct-serial.conf"

echo "+ checking for static ttyUSB passthrough in $CONF"
STATIC="$(grep -E '^dev[0-9]+: /dev/ttyUSB' "$CONF" || true)"
if [ -n "$STATIC" ]; then
  while IFS= read -r sline; do
    key="${sline%%:*}"
    if [ "$REMOVE_STATIC" = 1 ]; then
      pct set "$CTID" -delete "$key"
      echo "  removed: $sline"
      NEED_REBOOT=1
    else
      echo "!!!!------------------------------------------------------------"
      echo "!!!! WARNING: static passthrough still configured: $sline"
      echo "!!!! It breaks on replug / hub swap and a real /dev/ttyUSB0 node"
      echo "!!!! shadows the container's tmpfiles symlink. Remove it with:"
      echo "!!!!     pct set $CTID -delete $key"
      echo "!!!! or re-run: $0 $CTID --remove-static-dev"
      echo "!!!!------------------------------------------------------------"
    fi
  done <<< "$STATIC"
else
  echo "  none"
fi

if [ "$NEED_REBOOT" = 1 ]; then
  echo "+ container config changed; restart it to pick up the bind mount:"
  echo "    pct reboot $CTID"
else
  echo "+ container config unchanged"
fi
