# Host passthrough kit for the Cambrionix hub serial port

## Why
An LXC container cannot be given a USB port, only device nodes. The hub's serial port
(FTDI FT230X, USB `0403:6015`) is `/dev/ttyUSBn` on the Proxmox host, and `n` / the minor
change on replug or hub swap. A static Proxmox `devN: /dev/ttyUSB0` entry therefore breaks, and
a real `/dev/ttyUSB0` node in the container also shadows the symlink this kit creates.
The web app (pyserial) only globs `/dev/ttyUSB*`, so the node must keep the host's kernel name.

## Design
Host udev rule mirrors the node to `/dev/ct-serial/<kernel name>` (owner 100000:100020 =
container root:dialout, mode 0660). `/dev/ct-serial` is bind-mounted into the container, and
inside it tmpfiles creates `/dev/ttyUSBn -> ct-serial/ttyUSBn` (n = 0..7; dangling links are
harmless). Matching is by VID/PID only, so any hub works.

## Files
- `90-ct-serial.rules` - host udev rule (add/remove of the mirrored node).
- `ct-serial.conf` - the two lines added to `/etc/pve/lxc/<CTID>.conf` (cgroup allow `c 188:*`, bind mount).
- `install-ct-serial.sh` - host installer (idempotent); warns about static `devN: /dev/ttyUSB*`
  lines and prints `pct set <CTID> -delete devN`; `--remove-static-dev` does it for you.
- `container/cambrionix-tty.conf`, `container/install-container-side.sh` - container-side symlinks.

## Host steps (Proxmox host, as root)
```
scp -r root@<container-ip>:/opt/cambrionix-hub-alternative/host /root/ct-serial
cd /root/ct-serial && ./install-ct-serial.sh 101
pct set 101 -delete devN        # only if the script warned about a static dev line (or use --remove-static-dev)
pct reboot 101
```

## Container step (as root in the container; normally already done)
```
/opt/cambrionix-hub-alternative/host/container/install-container-side.sh
```

## Verify (inside the container)
```
ls -l /dev/ct-serial/ /dev/ttyUSB*
udevadm info --query=property /dev/ttyUSB0 | grep ID_SERIAL_SHORT
systemctl restart cambrionix-hub
curl -s localhost:1401/api/hubs | head -c 300
```
`/dev/ttyUSB0` must be a symlink to `ct-serial/ttyUSB0`, not a char node.
