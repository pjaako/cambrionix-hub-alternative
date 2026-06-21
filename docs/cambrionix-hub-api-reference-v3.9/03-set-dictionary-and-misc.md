# Cambrionix Hub API — Set Dictionary and Miscellaneous Reference
> API v3.9+ (Manual version: 2025-06)

Covers the tail end of Section 14.2 "Get Dictionary" (Uptime_sec), Section 14.3 "Set Dictionary", Section 14.4 "Deprecated Dictionaries", Section 15 "Socket Connections", Section 16 "Controlling the LEDs", Section 17 "Battery Information", and Section 18 "API Error codes".

Source: [Cambrionix Hub API User Manual](../Cambrionix-Hub-API-User-Manual-v3.9.pdf), pages 237-310 (end of document).

---

## 14.2. Get Dictionary (continued)

### Uptime_sec

Time in seconds the hub has been running since the last reset.

**Syntax: see Call Structure**

```json
{
  "method": "cbrx_connection_get",
  "params": [
    connection-handle,
    "Uptime_sec"
  ]
}
```

`connection-handle` is the Connection Handles as an integer.

**Returns:**

```json
{
  "result": uptime
}
```

`uptime` is the amount of time in seconds of continuos running, diplayed as an integer.

**Example**

```json
{
  "jsonrpc": "2.0",
  "id": 0,
  "result": 151304
}
```

---

## 14.3. Set Dictionary

The following table lists all keys settable via the Set Dictionary, and the feature set each key requires.

| Key | Feature set |
|---|---|
| [Beep](#beep) | 5V |
| [ClearErrorFlags](#clearerrorflags) | base |
| [ClearLCD](#clearlcd) | 5V |
| [ClearRebootFlag](#clearrebootflag) | base |
| [FiveVoltRail.OverVoltage](#fivevoltrailovervoltage) | 5V |
| [FiveVoltRail.UnderVoltage](#fivevoltrailundervoltage) | 5V |
| [InputRail.OverVoltage](#inputrailovervoltage) | PD |
| [InputRail.UnderVoltage](#inputrailundervoltage) | PD |
| [LCDText.ROW.COL](#lcdtextrowcol) | 5V |
| [Mode](#mode) | base |
| [Port.N.gate](#portngate) | gate |
| [Port.N.led1](#portnled1) | base |
| [Port.N.led2](#portnled2) | base |
| [Port.N.led3](#portnled3) | base |
| [Port.N.leds](#portnleds) | base |
| [Port.N.mode](#portnmode) | base |
| [Port.N.profiles](#portnprofiles) | sync |
| [Port.N.RGB](#portnrgb) | gate |
| [ProfileEnable.n](#profileenablen) | 5V |
| [Reboot](#reboot) | base |
| [RemoteControl](#remotecontrol) | base |
| [RGBControl](#rgbcontrol) | gate |
| [SecurityArmed](#securityarmed) | 5V |
| [Settings](#settings) | base |
| [Temperature.OverTemperature](#temperatureovertemperature) | temperature |
| [TwelveVoltRail.OverVoltage](#twelvevoltrailovervoltage) | 12V |
| [TwelveVoltRail.UnderVoltage](#twelvevoltrailundervoltage) | 12V |

---

#### Beep

Beep for the number of milliseconds passed in.

**Syntax: see Call Structure**

```json
{
  "method": "cbrx_connection_set",
  "params": [
    connection-handle,
    "beep",
    Value
  ]
}
```

| Parameter | Description |
|---|---|
| *connection-handle* | The Connection Handles as an integer |
| *Value* | The value you wish to set for the key |

| Value | Description |
|---|---|
| time period | An integer for the amount of time required for the beep in ms |

**Returns:**

```json
{
  "result": true
}
```

**Errors**

If there is an error in the API method then a JSON-RPC Error Object will be returned.

**Example**

```json
{
  "jsonrpc": "2.0",
  "id": 0,
  "method": "cbrx_connection_set",
  "params": [
    7654,
    "beep",
    250
  ]
}
```

---

#### ClearErrorFlags

Clear all error flags.

**Syntax: see Call Structure**

```json
{
  "method": "cbrx_connection_set",
  "params": [
    connection-handle,
    "ClearErrorFlags",
    Value
  ]
}
```

| Parameter | Description |
|---|---|
| *connection-handle* | The Connection Handles as an integer |
| *Value* | The value you wish to set for the key |

| Value | Description |
|---|---|
| true | Clear the error flags |

**Returns:**

```json
{
  "result": true
}
```

**Errors**

If there is an error in the API method then a JSON-RPC Error Object will be returned.

**Example**

```json
{
  "jsonrpc": "2.0",
  "id": 0,
  "method": "cbrx_connection_set",
  "params": [
    7654,
    "ClearErrorFlags",
    true
  ]
}
```

---

#### ClearLCD

Clear the LCD.

**Syntax: see Call Structure**

```json
{
  "method": "cbrx_connection_set",
  "params": [
    connection-handle,
    "ClearLCD",
  ]
}
```

| Parameter | Description |
|---|---|
| *connection-handle* | The Connection Handles as an integer |

**Returns:**

```json
{
  "result": true
}
```

**Errors**

If there is an error in the API method then a JSON-RPC Error Object will be returned.

**Example**

```json
{
  "jsonrpc": "2.0",
  "id": 0,
  "method": "cbrx_connection_set",
  "params": [
    7654,
    "ClearLCD",
  ]
}
```

---

#### ClearRebootFlag

Clear the reboot flag.

**Syntax: see Call Structure**

```json
{
  "method": "cbrx_connection_set",
  "params": [
    connection-handle,
    "ClearRebootFlag",
    Value
  ]
}
```

| Parameter | Description |
|---|---|
| *connection-handle* | The Connection Handles as an integer |
| *Value* | The value you wish to set for the key |

| Value | Description |
|---|---|
| true | Clear the Rebooted flag |

**Returns:**

```json
{
  "result": true
}
```

**Errors**

If there is an error in the API method then a JSON-RPC Error Object will be returned.

**Example**

```json
{
  "jsonrpc": "2.0",
  "id": 0,
  "method": "cbrx_connection_set",
  "params": [
    7654,
    "ClearRebootFlag",
    true
  ]
}
```

---

#### FiveVoltRail.OverVoltage

Force the behaviour of a 5V over voltage condition.

**Syntax: see Call Structure**

```json
{
  "method": "cbrx_connection_set",
  "params": [
    connection-handle,
    "FiveVoltRail.OverVoltage",
    Value
  ]
}
```

| Parameter | Description |
|---|---|
| *connection-handle* | The Connection Handles as an integer |
| *Value* | The value you wish to set for the key |

| Value | Description |
|---|---|
| true | Set 5V over voltage flag |

**Returns:**

```json
{
  "result": true
}
```

**Errors**

If there is an error in the API method then a JSON-RPC Error Object will be returned.

**Example**

```json
{
  "jsonrpc": "2.0",
  "id": 0,
  "method": "cbrx_connection_set",
  "params": [
    7654,
    "FiveVoltRail.OverVoltage",
    true
  ]
}
```

---

#### FiveVoltRail.UnderVoltage

Force the behaviour of a 5V under voltage condition.

**Syntax: see Call Structure**

```json
{
  "method": "cbrx_connection_set",
  "params": [
    connection-handle,
    "FiveVoltRail.UnderVoltage",
    Value
  ]
}
```

| Parameter | Description |
|---|---|
| *connection-handle* | The Connection Handles as an integer |
| *Value* | The value you wish to set for the key |

| Value | Description |
|---|---|
| true | Set 5V under voltage flag |

**Returns:**

```json
{
  "result": true
}
```

**Errors**

If there is an error in the API method then a JSON-RPC Error Object will be returned.

**Example**

```json
{
  "jsonrpc": "2.0",
  "id": 0,
  "method": "cbrx_connection_set",
  "params": [
    7654,
    "FiveVoltRail.UnderVoltage",
    true
  ]
}
```

---

#### InputRail.OverVoltage

Force the behaviour of an input rail over voltage condition.

**Syntax: see Call Structure**

```json
{
  "method": "cbrx_connection_set",
  "params": [
    connection-handle,
    "InputRail.OverVoltage",
    Value
  ]
}
```

| Parameter | Description |
|---|---|
| *connection-handle* | The Connection Handles as an integer |
| *Value* | The value you wish to set for the key |

| Value | Description |
|---|---|
| true | Set voltage input over voltage flag |

**Returns:**

```json
{
  "result": true
}
```

**Errors**

If there is an error in the API method then a JSON-RPC Error Object will be returned.

**Example**

```json
{
  "jsonrpc": "2.0",
  "id": 0,
  "method": "cbrx_connection_set",
  "params": [
    7654,
    "InputRail.OverVoltage",
    true
  ]
}
```

---

#### InputRail.UnderVoltage

Force the behaviour of an input rail under voltage condition.

**Syntax: see Call Structure**

```json
{
  "method": "cbrx_connection_set",
  "params": [
    connection-handle,
    "InputRail.UnderVoltage",
    Value
  ]
}
```

| Parameter | Description |
|---|---|
| *connection-handle* | The Connection Handles as an integer |
| *Value* | The value you wish to set for the key |

| Value | Description |
|---|---|
| true | Set voltage input under voltage flag |

**Returns:**

```json
{
  "result": true
}
```

**Errors**

If there is an error in the API method then a JSON-RPC Error Object will be returned.

**Example**

```json
{
  "jsonrpc": "2.0",
  "id": 0,
  "method": "cbrx_connection_set",
  "params": [
    7654,
    "InputRail.UnderVoltage",
    true
  ]
}
```

---

#### LCDText.ROW.COL

Write the string on the LCD at (row, column). Row and column are zero based.

**Syntax: see Call Structure**

```json
{
  "method": "cbrx_connection_set",
  "params": [
    connection-handle,
    "LCDText.ROW.COL",
    Value
  ]
}
```

| Parameter | Description |
|---|---|
| *connection-handle* | The Connection Handles as an integer |
| *ROW* | LCD Row you wish to start writing |
| *COL* | LCD Collum you wish to start writing |
| *Value* | The value you wish to set for the key |

| Value | Description |
|---|---|
| String | A Text string you wish to display on the LCD |

**Returns:**

```json
{
  "result": true
}
```

**Errors**

If there is an error in the API method then a JSON-RPC Error Object will be returned.

**Example**

```json
{
  "jsonrpc": "2.0",
  "id": 0,
  "method": "cbrx_connection_set",
  "params": [
    7654,
    "LCDText.4.5",
    "hello"
  ]
}
```

---

#### Mode

Set same mode to all USB Ports. Please see product user manuals for details on the modes supported by each hub.

**Syntax: see Call Structure**

```json
{
  "method": "cbrx_connection_set",
  "params": [
    connection-handle,
    "mode",
    "Value"
  ]
}
```

| Parameter | Description |
|---|---|
| *connection-handle* | The Connection Handles as an integer |
| *Value* | The value you wish to set for the key |

| Value | Description |
|---|---|
| c | Charge mode |
| s | Sync and Charge mode |
| b | biased mode |
| o | off |

**Returns:**

```json
{
  "result": true
}
```

**Errors**

If there is an error in the API method then a JSON-RPC Error Object will be returned.

**Example**

```json
{
  "id": 0,
  "jsonrpc": "2.0",
  "method": "cbrx_connection_set",
  "params": [
    7654,
    "Mode",
    "s"
  ]
}
```

---

#### Port.N.gate

Open or close specified gate. You should monitor the state of the required gate via cbrx_connection_get(handle, "Gates") to ensure it completes.

**Syntax: see Call Structure**

```json
{
  "method": "cbrx_connection_set",
  "params": [
    connection-handle,
    "Port.N.gate",
    Value
  ]
}
```

| Parameter | Description |
|---|---|
| *connection-handle* | The Connection Handles as an integer |
| *N* | Port number |
| *Value* | The value you wish to set for the key |

| Value | Description |
|---|---|
| open | Open gate |
| close | Close gate |
| stop | Stop current gate action |

**Returns:**

```json
{
  "result": true
}
```

**Errors**

If there is an error in the API method then a JSON-RPC Error Object will be returned.

**Example**

```json
{
  "id": 0,
  "jsonrpc": "2.0",
  "method": "cbrx_connection_set",
  "params": [
    7654,
    "Port.1.gate",
    "open"
  ]
}
```

---

#### Port.N.led1

Set the status of the first LED.

**Syntax: see Call Structure**

```json
{
  "method": "cbrx_connection_set",
  "params": [
    connection-handle,
    "Port.N.led1",
    Value
  ]
}
```

| Parameter | Description |
|---|---|
| *connection-handle* | The Connection Handles as an integer |
| *N* | Port number |
| *Value* | The value you wish to set for the key |

| Value | Description |
|---|---|
| Flash pattern | 0-255 with the LEDs flashing according to the bit pattern represented by the value. |

**Returns:**

```json
{
  "result": true
}
```

**Errors**

If there is an error in the API method then a JSON-RPC Error Object will be returned.

**Example**

```json
{
  "id": 0,
  "jsonrpc": "2.0",
  "method": "cbrx_connection_set",
  "params": [
    7654,
    "Port.1.led1",
    170
  ]
}
```

---

#### Port.N.led2

Set the status of the second LED.

**Syntax: see Call Structure**

```json
{
  "method": "cbrx_connection_set",
  "params": [
    connection-handle,
    "Port.N.led2",
    Value
  ]
}
```

| Parameter | Description |
|---|---|
| *connection-handle* | The Connection Handles as an integer |
| *N* | Port number |
| *Value* | The value you wish to set for the key |

| Value | Description |
|---|---|
| Flash pattern | 0-255 with the LEDs flashing according to the bit pattern represented by the value. |

**Returns:**

```json
{
  "result": true
}
```

**Errors**

If there is an error in the API method then a JSON-RPC Error Object will be returned.

**Example**

```json
{
  "id": 0,
  "jsonrpc": "2.0",
  "method": "cbrx_connection_set",
  "params": [
    7654,
    "Port.1.led2",
    170
  ]
}
```

---

#### Port.N.led3

Set the status of the third LED.

**Syntax: see Call Structure**

```json
{
  "method": "cbrx_connection_set",
  "params": [
    connection-handle,
    "Port.N.led3",
    Value
  ]
}
```

| Parameter | Description |
|---|---|
| *connection-handle* | The Connection Handles as an integer |
| *N* | Port number |
| *Value* | The value you wish to set for the key |

| Value | Description |
|---|---|
| Flash pattern | 0-255 with the LEDs flashing according to the bit pattern represented by the value. |

**Returns:**

```json
{
  "result": true
}
```

**Errors**

If there is an error in the API method then a JSON-RPC Error Object will be returned.

**Example**

```json
{
  "id": 0,
  "jsonrpc": "2.0",
  "method": "cbrx_connection_set",
  "params": [
    7654,
    "Port.1.led3",
    170
  ]
}
```

---

#### Port.N.leds

Set the status of all three LEDs.

**Syntax: see Call Structure**

```json
{
  "method": "cbrx_connection_set",
  "params": [
    connection-handle,
    "Port.N.leds",
    Value
  ]
}
```

| Parameter | Description |
|---|---|
| *connection-handle* | The Connection Handles as an integer |
| *N* | Port Number |
| *Value* | The value you wish to set for the key |

**Value**

A 24 bit numeric value consisting of the individual LED settings as 8 bit values shifted and OR'ed together. i.e. `led1 | (led2 << 8) | (led3 << 16)`, so with led1 and led2 as zero, and led3 being `0b10101010` (decimal 170), the result should be 11,141,120 decimal.

On a ThunderSync3, 255 is Green, 65,280 is red, 16,711,680 is Yellow.

On a ModIT, Blue is used instead of Yellow, but you can of course mix colours into any RGB mix.

**Returns:**

```json
{
  "result": true
}
```

**Errors**

If there is an error in the API method then a JSON-RPC Error Object will be returned.

**Example**

```json
{
  "id": 0,
  "jsonrpc": "2.0",
  "method": "cbrx_connection_set",
  "params": [
    7654,
    "Port.1.leds",
    11193404
  ]
}
```

---

#### Port.N.mode

Set mode of a single USB port. Sync mode can only be set on device that implement the sync feature set. Biased mode can only be set on devices that implement the 5V feature set.

**Syntax: see Call Structure**

```json
{
  "method": "cbrx_connection_set",
  "params": [
    connection-handle,
    "Port.N.mode",
    Value
  ]
}
```

| Parameter | Description |
|---|---|
| *connection-handle* | The Connection Handles as an integer |
| *N* | Port number |
| *Value* | The value you wish to set for the key |

| Value | Description |
|---|---|
| c | Charge mode |
| s | Sync and Charge mode |
| b | Biased mode |
| o | Off |

**Returns:**

```json
{
  "result": true
}
```

**Errors**

If there is an error in the API method then a JSON-RPC Error Object will be returned.

**Example**

```json
{
  "id": 0,
  "jsonrpc": "2.0",
  "method": "cbrx_connection_set",
  "params": [
    7654,
    "Port.1.Mode",
    "c"
  ]
}
```

---

#### Port.N.profiles

Set the list of enabled profiles.

**Syntax: see Call Structure**

```json
{
  "method": "cbrx_connection_set",
  "params": [
    connection-handle,
    "Port.N.profiles",
    Value
  ]
}
```

| Parameter | Description |
|---|---|
| *connection-handle* | The Connection Handles as an integer |
| *N* | Port number |
| *Value* | The value you wish to set for the key |

| Value | Description |
|---|---|
| profile | A comma separated list of profiles to enable, see product user manuals for details on profiles applicable to your hub. |

**Returns:**

```json
{
  "result": true
}
```

**Errors**

If there is an error in the API method then a JSON-RPC Error Object will be returned.

**Example**

```json
{
  "id": 0,
  "jsonrpc": "2.0",
  "method": "cbrx_connection_set",
  "params": [
    7654,
    "Port.1.profiles",
    "1,2,3"
  ]
}
```

---

#### Port.N.RGB

Set RGB colour of ModIT LEDs.

**Syntax: see Call Structure**

```json
{
  "method": "cbrx_connection_set",
  "params": [
    connection-handle,
    "Port.N.RGB",
    Value
  ]
}
```

| Parameter | Description |
|---|---|
| *connection-handle* | The Connection Handles as an integer |
| *N* | Port number |
| *Value* | The value you wish to set for the key |

**Value**

Colour value can either be an integer (where you must supply full RGBA), or a string. For a string, you can specify it as RGB, RGBA, RRGGBB or RRGGBBAA. Much like you can with an HTML colour. For example, use "FF0000" or "F00" for red, "FFFFFF" for white and so on. Optionally supply the alpha (intensity) digits, so "FFFFFF80" for half bright white.

**Returns:**

```json
{
  "result": true
}
```

**Errors**

If there is an error in the API method then a JSON-RPC Error Object will be returned.

**Example**

```json
{
  "id": 0,
  "jsonrpc": "2.0",
  "method": "cbrx_connection_set",
  "params": [
    7654,
    "Port.1.RGB",
    "ff08"
  ]
}
```

---

#### ProfileEnable.n

Enable or disable the global profile n.

**Syntax: see Call Structure**

```json
{
  "method": "cbrx_connection_set",
  "params": [
    connection-handle,
    "ProfileEnable.n"
  ]
}
```

| Parameter | Description |
|---|---|
| *connection-handle* | The Connection Handles as an integer |
| *n* | Profile number |

**Returns:**

```json
{
  "result": true
}
```

**Errors**

If there is an error in the API method then a JSON-RPC Error Object will be returned.

**Example**

```json
{
  "id": 0,
  "jsonrpc": "2.0",
  "method": "cbrx_connection_set",
  "params": [
    7654,
    "ProfileEnable.n"
  ]
}
```

---

#### Reboot

Reboot the hub now. The API will attempt to re-establish connection automatically, but you should not expected to receive updated results for several seconds.

**Syntax: see Call Structure**

```json
{
  "method": "cbrx_connection_set",
  "params": [
    connection-handle,
    "Reboot",
    Value
  ]
}
```

| Parameter | Description |
|---|---|
| *connection-handle* | The Connection Handles as an integer |
| *Value* | The value you wish to set for the key |

| Value | Description |
|---|---|
| true | Reboot the hub. |

**Returns:**

```json
{
  "result": true
}
```

**Errors**

If there is an error in the API method then a JSON-RPC Error Object will be returned.

**Example**

```json
{
  "id": 0,
  "jsonrpc": "2.0",
  "method": "cbrx_connection_set",
  "params": [
    7654,
    "Reboot",
    "true"
  ]
}
```

---

#### RemoteControl

Enable / disable controlling of the unit controls. This will allow the LEDs or LCD to be updated or panel button pushes to be detected.

**Syntax: see Call Structure**

```json
{
  "method": "cbrx_connection_set",
  "params": [
    connection-handle,
    "RemoteControl",
    Value
  ]
}
```

| Parameter | Description |
|---|---|
| *connection-handle* | The Connection Handles as an integer |
| *Value* | The value you wish to set for the key |

| Value | Description |
|---|---|
| true | Enable manual remote control mode |
| false | Disable manual remote control mode |
| "auto" | Enable auto control mode via the API |

**Returns:**

```json
{
  "result": true
}
```

**Errors**

If there is an error in the API method then a JSON-RPC Error Object will be returned.

**Example**

```json
{
  "id": 0,
  "jsonrpc": "2.0",
  "method": "cbrx_connection_set",
  "params": [
    7654,
    "RemoteControl",
    "true"
  ]
}
```

---

#### RGBControl

Enable / disable ModIT RGB LED control for ports. This does not require RemoteControl to be enabled.

**Syntax: see Call Structure**

```json
{
  "method": "cbrx_connection_set",
  "params": [
    connection-handle,
    "RGBControl",
    {
      "port": N,
      "enable": value
    }
  ]
}
```

| Parameter | Description |
|---|---|
| *connection-handle* | The Connection Handles as an integer |
| *N* | port number |
| *value* | The value you wish to set for the key |

| Value | Description |
|---|---|
| true | Enable control of the RGB LED's |
| false | Disbale control of the RGB LED's |

**Returns:**

```json
{
  "result": true
}
```

**Errors**

If there is an error in the API method then a JSON-RPC Error Object will be returned.

**Example**

```json
{
  "id": 0,
  "jsonrpc": "2.0",
  "method": "cbrx_connection_set",
  "params": [
    7654,
    "RGBControl",
    {
      "port": 8,
      "enable": true
    }
  ]
}
```

**Multiple ports**

If you wish to set control on a range of ports then the params would change. You would need to enter two values the 'start' value of the port to start with and the 'end' value of the port to finish with.

**Syntax: see Call Structure**

```json
{
  "method": "cbrx_connection_set",
  "params": [
    connection-handle,
    "RGBControl",
    {
      "start": N,
      "end": N,
      "enable": value
    }
  ]
}
```

| Parameter | Description |
|---|---|
| *connection-handle* | The Connection Handles as an integer |
| *N* | port number |
| *value* | The value you wish to set for the key |

| Value | Description |
|---|---|
| true | Enable control of the RGB LED's |
| false | Disbale control of the RGB LED's |

**Returns:**

```json
{
  "result": true
}
```

**Errors**

If there is an error in the API method then a JSON-RPC Error Object will be returned.

**Example**

```json
{
  "id": 0,
  "jsonrpc": "2.0",
  "method": "cbrx_connection_set",
  "params": [
    7654,
    "RGBControl",
    {
      "start": 1,
      "end": 8,
      "enable": true
    }
  ]
}
```

---

#### SecurityArmed

Enable / disable security feature. If the security is enabled, removal of a device from a port will sound an alarm (if installed) and flash lights (if installed).

**Syntax: see Call Structure**

```json
{
  "method": "cbrx_connection_set",
  "params": [
    connection-handle,
    "SecurityArmed",
    Value
  ]
}
```

| Parameter | Description |
|---|---|
| *connection-handle* | The Connection Handles as an integer |
| *Value* | The value you wish to set for the key |

| Value | Description |
|---|---|
| true | enable security |
| false | disable security |

**Returns:**

```json
{
  "result": true
}
```

**Errors**

If there is an error in the API method then a JSON-RPC Error Object will be returned.

**Example**

```json
{
  "id": 0,
  "jsonrpc": "2.0",
  "method": "cbrx_connection_set",
  "params": [
    7654,
    "SecurityArmed",
    "true"
  ]
}
```

---

#### Settings

Perform command line interface operation on the connected hub and return the complete result. This allows you to run commands directly on the hub's command line without stopping the API service. In order to update the settings the CLI setting will require a `settings_unlock\n` prefix to the command. For more information on using CLI commands please see the CLI documentation: https://www.cambrionix.com/cambrionix-cli.

**Syntax: see Call Structure**

```json
{
  "method": "cbrx_connection_set",
  "params": [
    connection-handle,
    "Settings",
    "settings_unlock\nCommand"
  ]
}
```

| Parameter | Description |
|---|---|
| *connection-handle* | The Connection Handles as an integer |
| *Command* | The Command you wish to send to the hub. For all CLI commands see the CLI Documentation: https://www.cambrionix.com/cambrionix-cli |

**Returns:**

```json
{
  "jsonrpc": "2.0",
  "id": 0,
  "result": "Unlocked \nSetting updated"
}
```

**Errors**

If there is an error in the API method then a JSON-RPC Error Object will be returned.

If you attempt to update a setting that is already set you will receive a message stating that the setting is already set such as the example of sending the ports on below:

```json
{
  "jsonrpc": "2.0",
  "id": 0,
  "result": "Unlocked \nForcing ports on has already been defined."
}
```

**Example**

```json
{
  "jsonrpc": "2.0",
  "id": 0,
  "method": "cbrx_hub_set",
  "params": [
    "DM01K2A8",
    "settings",
    "settings_unlock\nsettings_set ports_on 1 1 1 1 1 1 1 1 1 1 1 1"
  ]
}
```

---

#### Temperature.OverTemperature

Force the behaviour of an over temperature condition.

**Syntax: see Call Structure**

```json
{
  "method": "cbrx_connection_set",
  "params": [
    connection-handle,
    "Temperature.OverTemperature",
    Value
  ]
}
```

| Parameter | Description |
|---|---|
| *connection-handle* | The Connection Handles as an integer |
| *Value* | The value you wish to set for the key |

| Value | Description |
|---|---|
| true | Set the over temperature flag |

**Returns:**

```json
{
  "result": true
}
```

**Errors**

If there is an error in the API method then a JSON-RPC Error Object will be returned.

**Example**

```json
{
  "id": 0,
  "jsonrpc": "2.0",
  "method": "cbrx_connection_set",
  "params": [
    7654,
    "Temperature.OverTemperature",
    "true"
  ]
}
```

---

#### TwelveVoltRail.OverVoltage

Force the behaviour of a 12V over voltage condition. TwelveVoltRail is the same as InputRail.

**Syntax: see Call Structure**

```json
{
  "method": "cbrx_connection_set",
  "params": [
    connection-handle,
    "TwelveVoltRail.OverVoltage",
    Value
  ]
}
```

| Parameter | Description |
|---|---|
| *connection-handle* | The Connection Handles as an integer |
| *Value* | The value you wish to set for the key |

| Value | Description |
|---|---|
| true | Set the 12V over voltage flag |

**Returns:**

```json
{
  "result": true
}
```

**Errors**

If there is an error in the API method then a JSON-RPC Error Object will be returned.

**Example**

```json
{
  "id": 0,
  "jsonrpc": "2.0",
  "method": "cbrx_connection_set",
  "params": [
    7654,
    "TwelveVoltRail.OverVoltage",
    "true"
  ]
}
```

---

#### TwelveVoltRail.UnderVoltage

Force the behaviour of a 12V under voltage condition.

TwelveVoltRail is the same as InputRail.

**Syntax: see Call Structure**

```json
{
  "method": "cbrx_connection_set",
  "params": [
    connection-handle,
    "TwelveVoltRail.UnderVoltage",
    Value
  ]
}
```

| Parameter | Description |
|---|---|
| *connection-handle* | The Connection Handles as an integer |
| *Value* | The value you wish to set for the key |

| Value | Description |
|---|---|
| true | Set the 12V under voltage flag |

**Returns:**

```json
{
  "result": true
}
```

**Errors**

If there is an error in the API method then a JSON-RPC Error Object will be returned.

**Example**

```json
{
  "id": 0,
  "jsonrpc": "2.0",
  "method": "cbrx_connection_set",
  "params": [
    7654,
    "TwelveVoltRail.UnderVoltage",
    "true"
  ]
}
```

---

## 14.4. Deprecated Dictionaries

These dictionaries exist to support backwards compatibility only and should not be used. These key-values may be removed in future versions.

| API Call | Description |
|---|---|
| [Settings](#settings-deprecated) | Obtain current hub Internal hub settings. |

#### Settings (deprecated)

Obtain current hub Internal hub settings, returns as text.

**Syntax: see Call Structure**

```json
{
  "method": "cbrx_connection_get",
  "params": [
    connection-handle,
    "Settings",
  ]
}
```

`connection-handle` is the Connection Handles as an integer.

**Returns:**

```json
{
  "jsonrpc": "2.0",
  "id": 5,
  "result": [
    "Current memory Settings :",
    "",
    "settings_set company_name manufacturer-name",
    "settings_set product_name product-name",
    "settings_set local_name local-name",
    "settings_set attach_threshold attach-threshold",
    "settings_set default_profile default-profile",
    "settings_set remap_ports port-order",
    "settings_set ports_on ports-on",
    "settings_set sync_chrg sync-charge",
    "settings_set alt_sync_chrg alt-sync-charge",
    "settings_set misc_flags Internal hub-flags",
    "settings_set display_mode display-mode",
    "settings_set charged_threshold charged-threshold",
    "settings_set temperature_max shutdown-temperature",
    "settings_set stagger stagger"
  ]
}
```

| Variables | Description |
|---|---|
| *manufacturer-name* | Defined name of manufacturer, Default is 'Cambrionix' |
| *product-name* | Hardware name of product |
| *local-name* | Local name set by the user, "-" if not set |
| *attach-threshold* | Current drawn in mA that the hub detects a device is connected, "d" means factory default is set |
| *default-profile* | Default profile for each port |
| *port-order* | Order the ports are by port number |
| *ports-on* | Whether each port is default on, 0 is default off, 1 is default on |
| *sync-charge* | Whether CDP* on each port on, 0 is off, 1 is on, comma seperated list |
| *alt-sync-charge* | Whether alternative CDP* on each port on, 0 is off, 1 is on |
| *Internal hub-flags* | If any Internal hub Misc flags are active |
| *display-mode* | Change the display mode for logs, "d" means factory default is set |
| *charged-threshold* | Current drawn in mA that the hub detects a device is fully charged, "d" means factory default is set |
| *shutdown-temperature* | Temperature that will shutdown the hub if reached in Celsius, "d" means factory default is set |
| *stagger* | A delay between ports turning on in ms, "d" means factory default is set |

\*Charging Downstream Port (CDP) being enabled means that a port is capable of transferring data and charging the device at the same time with a higher current than just data syncing alone. With CDP enabled the hub can supply up to 1.5 A.

If you disable CDP you will receive the notification "This Hub has the Charge Downstream Port UCS mode disabled. This could limit the maximum current seen on some ports." This notification is there to ensure you haven't turned this off by accident and can still have the highest charge available.

**Example**

```json
{
  "jsonrpc": "2.0",
  "id": 5,
  "result": [
    "Current memory Settings :",
    "",
    "settings_set company_name cambrionix",
    "settings_set product_name SuperSync15",
    "settings_set local_name -",
    "settings_set attach_threshold d",
    "settings_set default_profile 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0",
    "settings_set remap_ports 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15",
    "settings_set ports_on 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0",
    "settings_set sync_chrg 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1",
    "settings_set alt_sync_chrg 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 ",
    "settings_set misc_flags 0000",
    "settings_set display_mode d",
    "settings_set charged_threshold d",
    "settings_set temperature_max d",
    "settings_set stagger d"
  ]
}
```

---

## 15. Socket Connections

When using the Python wrapper that provides the `cbrxapi` module, each time a call is made to the API, a socket is created. This socket is then used to send the command and receive the response before being closed.

If you are writing your own program, you may wish to consider creating a single socket at the start of your communication with the API and keeping this socket open until you wish to stop using the API. Keeping the socket open for the lifetime of your communication with the API will reduce the load on the system and lead to shorter communication cycles with the API.

If you do choose to manage your own socket connections to the API, it is important that you do not close the socket before receiving the response from the final command. Closing the socket without waiting to receive the response may lead to the requested operation not being completed, this is especially important on set and close operations.

---

## 16. Controlling the LEDs

The API can control product LEDs. By default these LEDs are controlled automatically by the product to indicate the state that a port is in.

In order for the LEDs to be controlled by the API this automatic control must be disabled and this is done by setting the "RemoteControl" key to be 'True'. If you wish to return control of the LEDs to the automatic control you set "RemoteControl" to be 'False'. See `cbrx_connection_set` for more information on using this Method.

Control of an LED is achieved by providing an 8 bit value which is interpreted in binary as a pattern that is continuously cycled through. So by setting the value `11110000b`, the LED will flash slowly. The LED will be lit where there is a '1' and unlit where there is a '0'. Alternatively setting the value `10101010b` will make the LED flash fast. The pattern need not be symmetrical so `10010000b` will produce two short flashes close together with a longer pause before the cycle repeats.

Any value set for an LED while RemoteControl is False will be overwritten and so have no effect.

A special argument of "auto" in place of True allows the hub to override the user set LED pattern when a device attached to that port is removed.

---

## 17. Battery Information

Battery information can be retrieved for connected devices. For Android™ devices using Android Debug Bridge (ADB), and for iOS devices an in-built build of libimobile.

ADB can be used to query the battery level on any Android™ devices providing a few conditions are met.

- The Android platform tools are installed, these can be downloaded from here.
- The ADB binary is in the path, or it's path is provided to the API via `cbrx_config_set`.
- The device has USB debugging enabled.
- You have trusted the computer from the phone if the phone requires it.

See this page for details on enabling debug mode on Android™ devices. The only options that are required are to enable developer mode and USB debugging.

```
# Install Android platform tools on Linux sudo apt install
        Android-platform-tools#   # Install Android platform tools on macOS
        brew cask install Android-platform-tools   # Install Android
        platform tools on Windows # Goto
        https://developer.Android.com/studio/releases/platform-tools # Download
        SDK Platform-Tools for Windows # Extract and add the folder to your
    path
        or use # cbrx_config_set("adb_path" <pathname>) to add to API
        settings.
```

### Finding adb without the path

Alternatively from setting the path, we can tell the API where to find these programs.

```json
{
  "jsonrpc": "2.0",
  "id": 0,
  "method": "cbrx_config_set",
  "params": {
    "adb_path": "/usr/local/bin"
  }
}
```

### Mobile-device battery trust-levels

To obtain the battery information on mobile devices (phones / tablets) the device must be paired with the host system. To pair a device you will need to trust the host system on the mobile device when first connecting. There are various trust levels which are documented below.

| Trust level | Description |
|---|---|
| "not-paired" | Device not paired |
| "paired" | Device paired |
| "pending" | Battery information pending |
| "failed" | Failed to obtain battery information |
| "prohibited" | Prohibited from obtaining battery information |
| "error" | Error on obtaining battery information |

---

## 18. API Error codes

| Code | Value | Description |
|---|---|---|
| CBRXAPI_ERRORCODE_IDNOTFOUND | -10001 | ID not found. The unit ID passed in does not represent a hub or it has been disconnected since discovery was last run. Note that there is an internal timeout that will close unused handles after a minute. |
| CBRXAPI_ERRORCODE_NOHANDLINGTHREAD | -10002 | Unable to start handling thread. This error is not applicable past 2.1. |
| CBRXAPI_ERRORCODE_KEYNOTFOUND | -10003 | Key not found. A key that is passed in cannot be found. It may be misspelled or not exist in the dictionary for this unit. |
| CBRXAPI_ERRORCODE_ERRORSETTINGVALUE | -10004 | Could not set value. The (key value) pair was not acceptable. This could mean the key does not exist or is misspelled the value is of the wrong type or the value passed is invalid or out of range. |
| CBRXAPI_ERRORCODE_INVALIDHANDLE | -10005 | Invalid handle. The handle passed in to a function is not valid or no longer valid. This could happen either by passing in an incorrect value or if the handle has already been closed (i.e. by cbrx_closeandlock being called) or the unit has been disconnected from the computer. |
| CBRXAPI_ERRORCODE_TIMEOUT | -10006 | Timeout on communication. An operation towards a hub took too long to complete. It may have been disconnected or just slow to respond. It is worth retrying the operation. |
| CBRXAPI_ERRORCODE_DROPPED | -10007 | Socket connection to remote has been dropped. |
| CBRXAPI_ERRORCODE_METHOD_REMOVED | -10008 | The method has been removed. |
| CBRXAPI_ERRORCODE_AGAIN | -10009 | System not ready. Try again. This is likely caused by a very prompt call to an API function and the system has not progressed through startup enough to service it. |
| CBRXAPI_ERRORCODE_FIRMWARE_UPDATE | -10010 | Error performing firmware update. |
| CBRXAPI_ERRORCODE_FIRMWARE_FILE | -10011 | Firmware file error. This would usually be due to file format errors. |
| CBRXAPI_ERRORCODE_DEVICE_NOT_FOUND | -10012 | Device not found. |
| CBRXAPI_ERRORCODE_HUB_NOT_FOUND | -10013 | Hub not found. |
| CBRXAPI_ERRORCODE_CONNECTION_ERROR | -10014 | Could not open the serial port connection to the hub. |

**Total error codes: 14 rows.**

Note: in the source manual's printed table, the last two rows appear in this order on the page: `CBRXAPI_ERRORCODE_CONNECTION_ERROR` (-10014) followed by `CBRXAPI_ERRORCODE_HUB_NOT_FOUND` (-10013) — i.e. not in strict ascending numeric order. Both codes and descriptions above were verified against the source page exactly as printed.

---

## Appendix (end-of-document material)

### Use of Trademarks, Registered Trademarks, and other Protected Names and Symbols

This manual may make reference to trademarks, registered trademarks, and other protected names and or symbols of third-party companies not related in any way to Cambrionix. Where they occur these references are for illustrative purposes only and do not represent an endorsement of a product or service by Cambrionix, or an endorsement of the product(s) to which this manual applies by the third-party company in question.

Cambrionix hereby acknowledges that all trademarks, registered trademarks, service marks, and other protected names and/or symbols contained in this manual and related documents are the property of their respective holders.

- "Mac" and "macOS" are trademarks of Apple Inc., registered in the U.S. and other countries and regions.
- "Intel" and the Intel logo are trademarks of Intel Corporation or its subsidiaries.
- "Thunderbolt" and the Thunderbolt logo are trademarks of Intel Corporation or its subsidiaries.
- "Android" is a trademark of Google LLC.
- "Chromebook" is a trademark of Google LLC.
- "iOS" is a trademark or registered trademark of Apple Inc, in the US and other countries and is used under license.
- "Linux" is the registered trademark of Linus Torvalds in the U.S. and other countries.
- "Microsoft" and "Microsoft Windows" are trademarks of the Microsoft group of companies.
- "Cambrionix" and the logo are trademarks of Cambrionix Limited.

All trademarks and registered trademarks mentioned are acknowledged and respected as the property of their respective holders.

#### Important Notice on Protected Information

Please note that certain components of Cambrionix technology are considered protected intellectual property (IP) of Cambrionix. Specifically:

- Source Code: The source code of our software is proprietary and cannot be provided.
- Proprietary Methods: Detailed descriptions and implementations of our proprietary methods are also protected.

As such, requests for access to the source code or other protected information will be respectfully declined. We appreciate your understanding and cooperation.

### Cambrionix Patents

| Title | Link | Application Number | Grant Number |
|---|---|---|---|
| Syncing and Charging Port | GB2489429 | 1105081.2 | 2489429 |
| CAMBRIONIX | UK00002646615 | 2646615 | 00002646615 |
| CAMBRIONIX INTELLIGENT... | UK00002646617 | 2646617 | 00002646617 |

### Licensing

The use of Cambrionix Hub API is subject to the Cambrionix Connect SaaS conditions, the document can be downloaded and viewed using the following link:

https://downloads.cambrionix.com/documentation/en/Cambrionix-Connect-SaaS-Conditions.pdf

The use of Cambrionix Hub API is subject to the Cambrionix Licence agreement, the document can be downloaded and viewed using the following link:

https://downloads.cambrionix.com/documentation/en/Cambrionix-Licence-Agreement.pdf

### Company Information (back cover)

```
Cambrionix Limited
The Maurice Wilkes Building
Cowley Road
Cambridge CB4 0DS
United Kingdom

+44 (0) 1223 755520
https://www.cambrionix.com

Cambrionix Ltd is a company registered in England and Wales
with the company number 06210854
```

This is the final page of the manual (page 310).
