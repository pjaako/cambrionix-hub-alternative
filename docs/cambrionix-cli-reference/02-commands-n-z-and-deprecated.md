# Cambrionix CLI Reference - Part 2

Community-maintained technical reference generated from the [Cambrionix CLI User Manual (PDF)](../Cambrionix-CLI-User-Manual.pdf), covering firmware version 2025-06.

## 3. Commands (Continued)

### 3.16. Reboot

Reboots the product firmware.

**Syntax**
`reboot [watchdog]`

**Parameters**
| Parameter | Description |
| :--- | :--- |
| **watchdog** | Optional. If included, the system enters an infinite unresponsive loop until the watchdog timer expires (several seconds), then reboots. |

**Response**
`>>`

### 3.17. remote

Enables or disables remote control mode. This mode is required for manual control of LEDs, LCD, and reading key states.

**Syntax**
`remote [exit]`

**Parameters**
| Parameter | Description |
| :--- | :--- |
| **exit** | Optional. Exits remote control mode. |

**Response**
`>>`

### 3.18. sef

Sets system error flags (primarily for testing).

**Syntax**
`sef flag`

**Response**
`>>`

### 3.19. state

Displays the current status of each port, including mode, current, flags, and charging info.

**Syntax**
`state [p]`

**Parameters**
| Parameter | Description |
| :--- | :--- |
| **p** | Port number (Optional; affects all ports if omitted). |

**Response Format (Universal Firmware)**
`p, current_mA, flags, profile_id, time_charging, time_charged, energy`

**Response Format (PDSync-C4)**
`p, voltage_10mV, current_mA, flags, time_charging, time_charged, energy`
*(Port 0 is the host port for PDSync-C4).*

**Flags (Universal Firmware)**
| Flag | Description | Mutually Exclusive With |
| :--- | :--- | :--- |
| **O** | Port is in OFF mode | S, B, I, P, C, F |
| **S** | Port is in SYNC mode | O, B, I, P, C, F |
| **B** | Port is in BIASED mode | O, S, I, P, C, F |
| **I** | Charge mode: IDLE | O, S, B, P, C, F |
| **P** | Charge mode: PROFILING | O, S, B, I, C, F |
| **C** | Charge mode: CHARGING | O, S, B, I, P, F |
| **F** | Charge mode: FINISHED charging | O, S, B, I, P, C |
| **A** | Device ATTACHED | D |
| **D** | Port DETACHED (No device) | A |
| **T** | THEFT (Device removed unexpectedly) | - |
| **E** | ERRORs present (Check `health`) | - |
| **R** | System REBOOTED recently | - |
| **r** | VBUS being reset during mode change | - |

**Flags (PDSync and TS3-C10)**
3 columns of flags are returned.

*Column 1 (Attachment):*
- **A**: Attached
- **D**: Detached
- **P**: PD contract established
- **C**: Type-C cable detected (but no device)

*Column 2 (Status):*
- **I**: Idle
- **S**: Host port connected
- **C**: Charging
- **F**: Finished
- **O**: Off
- **c**: Power enabled, no device detected

*Column 3 (Quick Charge):*
- **_**: QC disallowed
- **+**: QC allowed but not enabled
- **q**: QC enabled but not in use
- **Q**: QC in use

**Flags (Motor Control)**
- **o**: Opening / **O**: Open
- **c**: Closing / **C**: Closed
- **U**: Unknown position
- **S**: Stall detected
- **T**: Timeout detected

**Example**
```
>> state 5
5, 1044, A C, 1, 5, x, 0.01
>>
```

### 3.20. system

Displays system hardware and firmware information.

**Syntax**
`system`

**Response**
Name-value pairs including firmware version, hardware revision, etc.

### 3.21. beep

Makes the product beep (Universal Firmware).

**Syntax**
`beep [ms]`

**Parameters**
| Parameter | Description |
| :--- | :--- |
| **ms** | Duration in milliseconds. |

### 3.22. clcd

Clears the LCD display (Universal Firmware).

**Syntax**
`clcd`

### 3.23. get_profiles

Gets the list of profiles associated with a port.

**Syntax**
`get_profiles p`

### 3.24. set_profiles

Sets the profiles allowed for a port.

**Syntax**
`set_profiles p [profiles]`

### 3.25. list_profiles

Lists all charging profiles available on the system and their status.

**Syntax**
`list_profiles`

### 3.26. en_profile

Enables or disables a specific charging profile globally.

**Syntax**
`en_profile i e`
(`i`: profile index, `e`: 1 to enable, 0 to disable).

### 3.27. keys

Reads key click event flags.

**Syntax**
`keys`

### 3.28. lcd

Writes a string to the LCD display.

**Syntax**
`lcd r c string`
(`r`: row, `c`: column).

### 3.29. sec

Sets or gets the security mode.

**Syntax**
`sec [mode]`

### 3.30. serial_speed

Changes the serial interface speed.

**Syntax**
`serial_speed baud`

### 3.31. set_delays

Sets various system delays.

### 3.32. boot

Enters the boot-loader mode.

**Syntax**
`boot`

### 3.33. gate

Gate control command (Motor Control Firmware).

### 3.34. proxy

Proxy command.

### 3.35. keyswitch

Read keyswitch state.

### 3.36. rgb

Set RGB LED color.

### 3.37. rgb_led

Set individual RGB LED.

### 3.38. stall

Get/set stall sensitivity.

## 4. Deprecated Methods

The following methods are deprecated and should not be used in new designs or scripts.

- **l** (Live View) - Replaced by `loge`.

## 5.1. l (Live View)

Periodically sends responses on the current state of the product. Deprecated.

**Syntax**
`l`
