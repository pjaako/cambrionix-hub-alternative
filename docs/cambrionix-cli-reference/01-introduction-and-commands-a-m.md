# Cambrionix CLI Reference

Community-maintained technical reference generated from the [Cambrionix CLI User Manual (PDF)](../Cambrionix-CLI-User-Manual.pdf), covering firmware version 2025-06.

Manual version: 2025-06, Cambrionix Ltd.

## 2. Introduction

This manual describes how to control products via their control interface. The Command Line Interface (CLI) enables the hub or hubs to be integrated into a larger system that is controlled by a host computer. A Serial terminal emulator must be installed to be able to use the CLI, and the emulator requires access to the COM port, so no other software, such as Cambrionix connect, can access the port at the same time. An example emulator that can be used is puTTY which can be downloaded from the following link: www.putty.org

Commands that are issued via the COM port are referred to as commands. Some settings modified by commands in this document are volatile – that is, the settings are lost when the hub is rebooted or powered off, please see individual commands for detail.

Throughout this manual optional parameters are shown in square brackets: `[ ]`. ASCII control characters are shown within `< >` brackets.

This document and commands are subject to change. Data should be parsed such to be tolerant of both upper and lower case, white space, additional new line characters ...etc.

### 2.1. Device location

The system appears as a virtual serial port (also called a VCP). On Microsoft Windows™, the system will appear as a numbered communication (COM) port. The COM port number can be found by accessing device manager.

On macOS®, a device file is created in the `/dev` directory. This is of the form `/dev/tty.usbserial S` where `S` is an alpha-numeric serial string unique to each device in the Universal Series.

### 2.2. USB Drivers

Communication to our products is enabled through a virtual COM port, this communication requires USB drivers.

On Windows 7 or later, a driver may automatically be installed (if Windows is configured to download drivers from the internet automatically). If this is not the case, the driver can be downloaded from www.ftdichip.com. The VCP drivers are required. For Linux® or Mac® computers, the default OS drivers should be used.

### 2.3. Communication Settings

The default communications settings are as below.

| Communication setting | Value |
| :--- | :--- |
| Number of bits per second (baud) | 115200 |
| Number of data bits | 8 |
| Parity | None |
| Number of stop bits | 1 |
| Flow control | None |

ANSI terminal emulation should be selected. Command sent must be terminated with `<CR><LF>`. Lines received by the hub are terminated with `<CR><LF>`.

The hub will accept back-to-back commands, however, the host computer should wait for a response before issuing a new command.

> **CAUTION: The hub may become unresponsive**
> For serial communications you must wait for a response from any commands before issuing a new command. Failure to do so can cause the hub to become unresponsive and require a full power reset.

### 2.4. Boot text and command prompt

At boot, the hub will issue a string of ANSI escape sequences to reset an attached terminal emulator. The title block follows this, then a command prompt.

The command prompt received is:
`>>`

Except in boot mode where it is:
`boot>>`

To reach a new boot prompt, send `<ETX>`. This cancels any partial command string.

### 2.5. Products and their Firmware

Below is a list of products, their part numbers and the Firmware type it uses.

| Firmware | Part Number | Product Name |
| :--- | :--- | :--- |
| Universal | PP15S | PowerPad15S |
| Universal | PP15C | PowerPad15C |
| Universal | PP8S | PowerPad8S |
| Universal | SS15 | SuperSync15 |
| Universal | TS3-16 | ThunderSync3-16 |
| SMART | TS3-C10 | ThunderSync3-C10 |
| Universal | U16S Spade | U16S Spade |
| Universal | U8S | U8S |
| PDSync | PDSync-C4 | PDSync-C4 |
| Universal | ModIT-Max | ModIT-Max |
| Motor Control | Motor control board | ModIT-Max |

### 2.6. Command structure

Each command follows the below format:
`Command mandatory-parameters [optional-parameters]<CR><LF>`

The command will need to be entered first, if no parameters exist for the command then this will need to be followed immediately by `<CR>` and `<LF>` to send the command.

Not every command has mandatory parameters but if they are applicable then these will need to be entered for the command to work, once the command and mandatory parameters are entered then `<CR><LF>` will be required to signify the end of a command.

Optional parameters are shown inside square brackets e.g. `[port]`. These do not need to be entered for the command to be sent, but if they are included they will need to be followed by `<CR><LF>` to signify the end of a command. Only one `<CR><LF>` is required at the end of each command even if there are multiple parameters such as the format shown above.

Throughout the user manual we signify optional parameters with square brackets, these are not part of the command but just to show the parameters are optional, so if you see `[p]` in the command syntax then all that would need to be input is `p`.

### 2.7. Response structure

Each command will receive its specific response followed by `<CR><LF>`, a command prompt and then a space. The response is terminated as shown below:
`>>`

Some command responses are "live" meaning there will be a continuous response from the product until the command is cancelled by sending an `<ETX>` command. In these instances you will not receive the standard response as above until `<ETX>` command has been sent. If you disconnect the product it will not stop the data stream and reconnecting will result in the continuation of the data stream.

## 3. Commands

Below is a list of commands that are supported by all products:

| Command | Description |
| :--- | :--- |
| **bd** | Product description |
| **cef** | Clear error flags |
| **cls** | Clear terminal screen |
| **crf** | Clear rebooted flag |
| **health** | Show voltages, temperature, errors and boot flag |
| **host** | Show if USB host is present, and set mode change |
| **id** | Show id string |
| **l** | Live view (Periodically sends responses on the current state of the product) |
| **ledb** | Sets the LED pattern using a bit format |
| **leds** | Sets the LED pattern using a string format |
| **limits** | Show voltage and temperature limits |
| **loge** | Log state and events |
| **mode** | Sets the mode for one or more ports |
| **reboot** | Reboots the product |
| **remote** | Enter or exit mode where LEDs are controlled manually or automatically |
| **sef** | Set error flags |
| **state** | Show state for one or more ports |
| **system** | Show system hardware and firmware information |

Below is a table of commands specific to the Universal Firmware:

| Command | Description |
| :--- | :--- |
| **beep** | Makes the product beep |
| **clcd** | Clear LCD |
| **en_profile** | Enables or disables profile |
| **get_profiles** | Get list of profiles associated with a port |
| **keys** | Read key click event flags |
| **lcd** | Write a string to the LCD display |
| **list_profiles** | List all profiles on system |
| **logc** | Log current |
| **sec** | Set or get security mode |
| **serial_speed** | Change serial interface speed |

### 3.2. bd

The `bd` command provides a description of the architecture of the product. This includes all upstream and downstream ports, providing external software with the architecture of the USB connection tree.

**Syntax**
`bd`

**Response**
Name-value pairs indicating the presence of features, followed by a description of each USB hub listing what is attached to each port.

**Features**
| Parameter | Description |
| :--- | :--- |
| **Ports** | The number of USB ports |
| **Sync** | '1' if the product provides sync capability |
| **Temp** | '1' if the product can measure temperature |
| **EXTPSU** | '1' if the product is supplied with an external PSU (> 5V) |

**Attachment Section (1-based indices)**
| Parameter | Description |
| :--- | :--- |
| **Nodes** | Number of nodes (USB hubs or controllers) |
| **Node i Type** | Type of node `i` (see Node Table) |
| **Node i Ports** | Number of ports on node `i` |
| **Hub <i> Port <p>** | What is connected to port `<p>` of hub `i` (Hub `<j>`, Control Port, Expansion Port `<e>`, Port `<c>`, Unused Port, etc.) |

**Node Types**
| Node Type | Description |
| :--- | :--- |
| **Hub j** | USB 2.0 hub index `j` |
| **Optional Hub j** | A USB hub that may be fitted, index `j` |
| **Root r** | A USB controller with a root hub |
| **Turbo Hub j** | A USB hub capable of operating in Turbo mode, index `j` |
| **USB3 Hub j** | A USB 3.x hub, index `j` |

**Example**
```
>> bd
Ports: 15
Sync: 1
Temp: 1
EXTPSU: 1
Console: none
Nodes : 5
Node 1 Type : USB3 Hub 1
Node 1 Ports : 5
Hub 1 Port 1 : Turbo Hub 2
Hub 1 Port 2 : Turbo Hub 5
Hub 1 Port 3 : Turbo Hub 3
Hub 1 Port 4 : Turbo Hub 4
Hub 1 Port 5 : Control Port
...
```

### 3.3. cef

The `cef` command clears the system error flags.

**Syntax**
`cef`

**Response**
`>>`

### 3.4. cls

The `cls` command clears the terminal screen.

**Syntax**
`cls`

**Response**
The screen is cleared and the cursor is moved to the top left.
`>>`

### 3.5. crf

The `crf` command clears the rebooted flag. The rebooted flag is set when the hub is first powered on or rebooted.

**Syntax**
`crf`

**Response**
`>>`

### 3.6. health

The `health` command displays voltages, temperature, and system flags.

**Syntax**
`health`

**Response**
| Entry | Description |
| :--- | :--- |
| **5V_V1** | Supply voltage 1 (mV) |
| **5V_V2** | Supply voltage 2 (mV) - if applicable |
| **12V** | 12V supply voltage (mV) - if applicable |
| **Temp** | Internal temperature (milli-degrees Celsius) |
| **Flags** | System status flags (e.g., `R` for Rebooted, `E` for Error) |

**Example**
```
>> health
5V_V1: 5042
5V_V2: 5038
12V: 12050
Temp: 35400
Flags: R
>>
```

### 3.7. host

The `host` command shows if a USB host is present and sets how the hub responds to host detection.

**Syntax**
`host [mode]`

**Parameters**
| Mode | Description |
| :--- | :--- |
| **auto** | Ports enable sync connectivity as the host comes and goes. Charging is always enabled unless the port is turned off. |
| **off** | If the host is no longer detected, all charging ports will be turned off. |

**Response**
If parameter is supplied:
`>>`

If no parameter is supplied:
`Present: <value> Mode change: <value>`
(`Present` is '1' if host is detected, '0' otherwise).

### 3.8. id

The `id` command provides product identity information.

**Syntax**
`id`

**Response**
A string containing the product name, ID, and other identifying information.

**Example**
```
>> id
Model: PP15S
ID: 0123456789
>>
```

### 3.9. ledb

The `ledb` command assigns a flash bit pattern to an individual LED.

**Syntax**
`ledb port row ptn [control]`

**Parameters**
| Parameter | Description |
| :--- | :--- |
| **port** | Port number (starting at 1) |
| **row** | LED row number (1: Charged, 2: Charging, 3: Sync mode) |
| **ptn** | Flash pattern: decimal (0..255), hex (00h..ffh), or binary (00000000b..11111111b) |
| **[control]** | Optional: `H` (take over control), `R` (release control to normal) |

**Response**
`>>`

**Example**
```
# Flash port 8 charging LED at 50/50 duty cycle
ledb 8 2 11110000b >>

# Turn on port 1 charged LED continuously
ledb 1 1 ffh >>
```

### 3.10. leds

The `leds` command assigns a string of flash patterns to one row of LEDs. This is faster than `ledb` for controlling multiple ports.

**Syntax**
`leds row [ptnstr]`

**Parameters**
| Parameter | Description |
| :--- | :--- |
| **row** | LED row number (as in `ledb`) |
| **[ptnstr]** | A string of characters, one per port. See [LED Control](./03-errors-profiles-and-settings.md#9-led-control) for valid characters. |

**Example**
```
# Skip port 1 (x), set port 2 on (1), port 3 flash fast (f), port 4 pulse (p), port 5 off (0), etc.
leds 1 x1fp011 >>
```

### 3.11. limits

Displays the thresholds for under-voltage, over-voltage, and over-temperature errors.

**Syntax**
`limits`

**Response**
List of fixed thresholds (firmware-dependent).

**Example**
```
>> limits
5V Min:   4.50
5V Max:   5.58
Input Min:  9.59
Input Max: 20.00
Temperature (C): 75.0
```

### 3.12. logc

Displays the current for all ports at a pre-set interval (Universal firmware). Also includes temperature and fan speed.

**Syntax**
`logc seconds`

**Parameters**
| Parameter | Description |
| :--- | :--- |
| **seconds** | Interval between responses (1..32767) |

**Response**
CSV output. Stop by sending `q` or `<ETX>`.

**Example**
```
>> logc 2
Logging seconds, mA, degrees C, PWM%% with period (mins:secs): 00:02
000000, 0000, 0000, ..., 37.4,  0.0
000002, 0000, 0000, ..., 37.4,  0.0
```

### 3.13. logp

Displays current and voltage for all ports at a pre-set interval (PDSync and TS3-C10 firmware).

**Syntax**
`logp [seconds]`

**Response**
CSV output. Stop by sending `q` or `<CTRL-C>`.

### 3.14. loge

Reports port status change events and periodically reports the state of all ports.

**Syntax**
`loge [seconds]`

**Parameters**
| Parameter | Description |
| :--- | :--- |
| **seconds** | Interval for periodic report (default: 60s). Use `0` to disable periodic reports and only show events. |

**Response**
CSV output. Stop by sending `<ETX>`.

**Example**
```
>> loge
Logging events
System up for 70632
1, 0000, R D I, 0, 0, x, 0.00
...
```

### 3.15. mode

Sets the operating mode for one or more ports.

**Syntax**
`mode m [p] [cp]`

**Parameters**
| Parameter | Description |
| :--- | :--- |
| **m** | Mode character: `c` (Charge), `s` (Sync), `b` (Biased), `o` (Off) |
| **p** | Port number (Optional; affects all ports if omitted) |
| **cp** | Charging profile ID (Optional; only for single port in Charge mode) |

**Mode Characters**
| Character | Name | Description |
| :--- | :--- | :--- |
| **c** | **Charge** | Disconnects from host USB. Detects device and selects the best profile for fastest charging. |
| **s** | **Sync** | Attaches port to host USB bus via internal hub. Charging depends on device capabilities. |
| **b** | **Biased** | Device detected but no charging or syncing (Universal FW). |
| **o** | **Off** | Power (VBUS) removed from port. No detection possible. |

**Charging Profile IDs (`cp`)**
| ID | Description |
| :--- | :--- |
| **0** | Intelligent (automatic selection of 1-6) |
| **1** | 2.1A (Apple, short detection) |
| **2** | BC1.2 Standard (Majority of Android/others) |
| **3** | Samsung |
| **4** | 2.1A (Apple, long detection) |
| **5** | 1.0A (Typically Apple) |
| **6** | 2.4A (Typically Apple) |

**Example**
```
# Turn off all ports
mode o >>

# Put port 2 in charge mode
mode c 2 >>

# Put port 4 in charge mode using profile 1 (Apple 2.1A)
mode c 4 1 >>
```
