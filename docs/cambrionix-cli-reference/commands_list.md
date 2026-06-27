# Cambrionix CLI Quick Reference

This document provides a simplified guide to the terminal commands for Cambrionix products.

## General Syntax
Commands are issued as text followed by arguments.
- **Example:** `mode c 1` (Set port 1 to charge mode)
- **Response:** Success is usually indicated by `>>`. Errors follow the format `*Ennn: Explanation`.

---

## Essential Commands

| Command | Syntax | Description |
| :--- | :--- | :--- |
| **bd** | `bd` | Show product architecture and port mapping. |
| **id** | `id` | Show product identity (Model, ID, etc.). |
| **system** | `system` | View system parameters (FW version, hardware, etc.). |
| **health** | `health` | Check supply voltages, temperature, and system flags. |
| **state** | `state [p]` | List state, current (mA), and flags for port `p` (or all). |
| **mode** | `mode <m> [p]` | Set port `p` (or all) to mode `<m>`. |
| **reboot** | `reboot` | Soft reset of the product firmware. |
| **beep** | `beep [ms]` | Make the product beep for `ms` milliseconds. |
| **cls** | `cls` | Clear the terminal screen. |

---

## Configuration & Advanced Commands

| Command | Syntax | Description |
| :--- | :--- | :--- |
| **list_profiles** | `list_profiles` | List all available charging profiles and their status. |
| **en_profile** | `en_profile <i> <e>` | Enable (`e=1`) or Disable (`e=0`) profile index `i`. |
| **get_profiles** | `get_profiles <p>` | Get profiles currently assigned to port `p`. |
| **remote** | `remote [exit]` | Enter/Exit remote control mode (needed for LED/LCD/Keys). |
| **leds** | `leds <string>` | Set LED pattern (requires `remote` mode). |
| **lcd** | `lcd <r> <c> <s>` | Write string `s` to LCD at row `r`, column `c`. |
| **cef** | `cef` | Clear system error flags. |
| **crf** | `crf` | Clear the rebooted flag. |

---

## Mode Reference (`mode <m> [p]`)

Use these characters for `<m>` to change port behavior:

| Mode | Key | Description |
| :--- | :--- | :--- |
| **Charge** | `c` | Disconnect from host and charge using best profile. |
| **Sync** | `s` | Connect to host USB bus. |
| **Off** | `o` | Remove power (VBUS) from the port. |
| **Biased** | `b` | Detect device but no charging/syncing (Universal FW). |

---

## State Flags (from `state` command)

The `state` command returns a string of flags. Common flags include:

| Flag | Meaning |
| :--- | :--- |
| **A / D** | **A**ttached / **D**etached (Device presence). |
| **C / I / F** | **C**harging / **I**dle / **F**inished charging. |
| **P** | **P**rofiling (Detecting best charge profile). |
| **S / O / B** | **S**ync / **O**ff / **B**iased mode. |
| **E / R** | **E**rror present / **R**ebooted recently. |
| **T** | **T**heft (Device was removed unexpectedly). |
| **r** | Vbus is being **r**eset during mode change. |

---

## Charging Profiles (for `mode c <p> [profile]`)

| ID | Name / Type | Description |
| :--- | :--- | :--- |
| **0** | **Intelligent** | Automatic selection of profiles 1-6. |
| **1** | **Apple 2.1A** | Fast charge for Apple (short detection). |
| **2** | **BC1.2** | Standard for most Android and other devices. |
| **3** | **Samsung** | Specific profile for Samsung devices. |
| **4** | **Apple 2.1A (L)** | Fast charge for Apple (long detection). |
| **5** | **Apple 1.0A** | Standard charge for Apple. |
| **6** | **Apple 2.4A** | Ultra-fast charge for Apple. |

---

## Quick Examples

- **Turn off all ports:**
  `mode o`
- **Charge port 5 only:**
  `mode c 5`
- **Check health of the hub:**
  `health`
- **See what is happening on port 2:**
  `state 2`

---

## Notes
- **Deprecated:** The `l` (Live View) command is deprecated and should not be used in scripts.
- **Errors:** All error codes start with `*E`. (e.g., `*E001`).
