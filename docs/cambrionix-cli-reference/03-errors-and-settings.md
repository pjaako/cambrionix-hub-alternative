# Cambrionix CLI Reference - Part 3

Community-maintained technical reference generated from the [Cambrionix CLI User Manual (PDF)](../Cambrionix-CLI-User-Manual.pdf), covering firmware version 2025-06.

## 6. Errors

Failed commands respond with an error code in the format: `*Ennn: Explanation`

### 6.1. Command Error Codes
| Code | Error Name | Description |
| :--- | :--- | :--- |
| **400** | ERR_COMMAND_NOT_RECOGNISED | Command is not valid |
| **401** | ERR_EXTRANEOUS_PARAMETER | Too many parameters |
| **402** | ERR_INVALID_PARAMETER | Parameter is not valid |
| **403** | ERR_WRONG_PASSWORD | Invalid password |
| **404** | ERR_MISSING_PARAMETER | Mandatory parameter missing |
| **407** | ERR_UNKNOWN_PROFILE_ID | Invalid profile ID |
| **410** | ERR_INVALID_PORT_NUMBER | Port number not valid for this product |
| **421** | ERR_INVALID_MODE_CHAR | Invalid mode character |
| **423** | ERR_CONSOLE_MODE_NOT_REMOTE | Remote mode required |
| **425** | ERR_BAD_LED_PATTERN | Invalid LED pattern |

### 6.2. Fatal Errors
Fatal errors are reported immediately: `*FATAL ERROR Ennn: Explanation`. 
When a fatal error occurs, the CLI will only respond to `<ETX>` and `<CR>`. If received, the system enters boot mode. Otherwise, it reboots after ~9 seconds.

## 7. Charging Profiles

When a device is in Charge Mode, the hub tries various profiles to find the one that draws the highest current.

| ID | Name / Type | Description |
| :--- | :--- | :--- |
| **0** | **Intelligent** | Automatic selection of profiles 1-6. |
| **1** | **Apple 2.1A** | Fast charge for Apple (short detection). |
| **2** | **BC1.2** | Standard for most Android and other devices. |
| **3** | **Samsung** | Specific profile for Samsung devices. |
| **4** | **Apple 2.1A (L)** | Fast charge for Apple (long detection). |
| **5** | **Apple 1.0A** | Standard charge for Apple. |
| **6** | **Apple 2.4A** | Ultra-fast charge for Apple. |

## 8. Port Modes

Port modes determine how VBUS and data lines are handled.

| Mode | Description |
| :--- | :--- |
| **Charge** | Disconnected from host. Scans for best charging profile. |
| **Sync** | Attached to host USB bus. Charging depends on device/host. |
| **Biased** | Device detected but no charging/syncing (Universal FW). |
| **Off** | Power (VBUS) removed. No detection possible. |

## 9. LED Control

LEDs can be controlled in `remote` mode using `ledb` and `leds` commands. The flash pattern is an 8-bit byte (MSB to LSB).

### 9.1. Pattern Characters
| Char | Description | Pattern (Binary) |
| :--- | :--- | :--- |
| **0** | Off | 00000000 |
| **1** | On | 11111111 |
| **f** | Flash fast | 10101010 |
| **m** | Flash medium | 11001100 |
| **s** | Flash slowly | 11110000 |
| **p** | Single pulse | 10000000 |
| **d** | Double pulse | 10100000 |
| **x** | Unchanged | - |

*Note: Capitalized versions (O, C, F, M, S, P, D) perform the same function without needing to be in remote mode.*

### 9.2. Default LED Indicators
- **Power (Green)**: Power on, no fault.
- **Power (Blue)**: Power on, host connected.
- **Power (Red Flashing)**: Major fault.
- **Port (Off)**: Disconnected/Disabled.
- **Port (Yellow)**: Resetting/Updating.
- **Port (Green Pulsing)**: Charging.
- **Port (Green)**: Charged.
- **Port (Blue)**: Sync mode.
- **Port (Red)**: Fault.

## 10. Internal Hub Settings

Internal settings persist across reboots. To change them, you must first unlock the settings.

### 10.1. Configuration Commands
- `settings_unlock`: Must be issued before `settings_set`.
- `settings_set <setting> <value>`: Applies the new value.

### 10.2. Key Settings
| Setting | Description |
| :--- | :--- |
| **local_name** | A name for the hub (up to 16 chars). |
| **attach_threshold** | Current (mA) above which a device is considered "Attached". |
| **charged_threshold** | Current (mA) below which a device is considered "Charged". |
| **default_profile** | Profile used by default when entering charge mode. |
| **temperature_max** | Max internal temperature (°C) before emergency shutdown. |
| **stagger** | Enable/Disable staggered port power-on (prevents inrush current). |
| **stagger_offset** | Delay (ms) between ports during staggered power-on. |
| **sync_chrg** | Allow charging in Sync mode (if supported). |
| **remap_ports** | Change logical port mapping to physical ports. |
