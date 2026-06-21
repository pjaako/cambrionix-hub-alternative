# Cambrionix Hub API — Dictionaries (Section 14)
> API v3.9+ (Manual version: 2025-06)

> Source: [Cambrionix Hub API User Manual](../Cambrionix-Hub-API-User-Manual-v3.9.pdf), PDF pages 135-236 (Section 13 "Dynamic Hubs" tail, Section 14 "Dictionaries": 14.1 Feature Sets, and most of 14.2 "Get Dictionary"). Section 14.2 continues past page 236 into the next reference chunk; some seam overlap/duplication with that continuation is expected.

## 13. Dynamic Hubs

It is possible to open a dynamic hub that is a combination of various other hubs. This behaves in the same way that Docks do. To open a dynamic hub, simply combine the serial numbers of all the hubs you wish to open into a special "Dynamic:" prefixed name as shown in this example.

```python
# Given three Cambrionix hubs with serial numbers of 'AAAAAAAA',
        'BBBBBBBB' and 'CCCCCCCC'   handleA =
        cbrxapi.cbrx_connection_open("AAAAAAAA") handleB =
        cbrxapi.cbrx_connection_open("BBBBBBBB") handleC =
        cbrxapi.cbrx_connection_open("CCCCCCCC") handleABC =
        cbrxapi.cbrx_connection_open("Dynamic:AAAAAAAA:BBBBBBBB:CCCCCCCC")
        print(cbrxapi.cbrx_connection_get(handleA, "nrOfPorts")) # 15
        print(cbrxapi.cbrx_connection_get(handleB, "nrOfPorts")) # 8
        print(cbrxapi.cbrx_connection_get(handleC, "nrOfPorts")) # 8
        print(cbrxapi.cbrx_connection_get(handleABC, "nrOfPorts")) # 31
```

This dynamic hub is treated as a single entity with it's ports being numbered from 1 to N, where N is the total number of ports across all hubs included.

## 14. Dictionaries

For each hub, the API can return two dictionaries:

- The Get dictionary, containing keys that can be read.
- The Set dictionary, containing keys which can be set.

The key-value pairs returned depend on the feature set(s) supported by the unit.

### 14.1. Feature Sets

The following feature sets are available:

| Feature set | Description |
|---|---|
| base | Base level functionality supported by all Cambrionix units |
| sync | Syncing capability |
| 5V | The unit has a fixed 5V power supply |
| 12V | The unit has a 12v power supply |
| temperature | The unit has a temperature sensor |
| PD | The unit implements the USB Power Delivery Specification |
| gate | The unit has a motor control product to control locking gates to secure devices connected to ports. |

All products support the base feature set.

The range of possible values for a key in the base feature set can be extended if an additional feature set is also available.

The Hardware key returns a value for the type of hub.

These are the extra feature sets CambrionixApiService supports for the various types of hub:

| hub type returned by "Hardware" | sync | 5V | 12V | Temperature | PD | gate |
|---|---|---|---|---|---|---|
| PP8C | | yes | yes | yes | | |
| PP8S | yes | yes | yes | yes | | |
| PP15C | | yes | yes | yes | | |
| PP15S | yes | yes | yes | yes | | |
| SS15 | yes | yes | yes | yes | | |
| Series8 | | yes | | | | |
| U8C-EXT | | yes | yes | yes | | |
| U8C | | yes | | | | |
| U8RA | yes | yes | | | | |
| U8S-EXT | yes | yes | yes | yes | | |
| U8S | yes | yes | | | | |
| U10C | | yes | | | | |
| U10S | yes | yes | | | | |
| U12S | yes | yes | | | | |
| U16S Spade-NL | yes | yes | | | | |
| PD-Sync 4 | yes*1 | | | yes | yes | |
| ThunderSync2-16 | yes | yes | | yes | | |
| ThunderSync3-16 | yes | yes | | yes | | |
| ModIT Max*2 | yes | yes | | yes | | yes |

\*1 It is to be noted that while the PDSync-C4 does not implement the "sync" feature set as such, nevertheless it does have sync capabilities and these are always available. This means that there is no need to switch between charge mode and sync mode.

\*2 The ModIT Max will identify itself as a ThunderSync3-16, but it has additional hardware for gate control.

### 14.2. Get Dictionary

The following table lists every dictionary key documented in this chunk, along with the feature set required for it to be present.

| Key | Feature set |
|---|---|
| Attached | 5V |
| Compiled | base |
| EnabledProfiles | 5V |
| Firmware | base |
| FirmwareRequirements | base |
| FiveVoltRail_flags | 5V |
| FiveVoltRail_Limit_Max_V | 5V |
| FiveVoltRail_Limit_Min_V | 5V |
| FiveVoltRail_V | 5V |
| FiveVoltRailMax_V | 5V |
| FiveVoltRailMin_V | 5V |
| Gates | gate |
| Group | base |
| Hardware | base |
| HardwareFlags | base |
| HardwareInformation | base |
| Health | base |
| HostPresent | PD |
| InputRail_flags | PD |
| InputRail_Limit_Max_V | PD |
| InputRail_Limit_Min_V | PD |
| InputRail_V | PD |
| InputRailMax_V | PD |
| InputRailMin_V | PD |
| Key.N | 5V |
| ModeChangeAuto | sync |
| nrOfPorts | base |
| PanelID | base |
| Port.N.Battery | sync |
| Port.N.Current_mA | base |
| Port.N.Description | PD |
| Port.N.Energy_Wh | base |
| Port.N.Flags | base |
| Port.N.FlashDrive | sync |
| Port.N.LocationID | sync |
| Port.N.Manufacturer | PD |
| Port.N.Mode | base |
| Port.N.PID | PD |
| Port.N.ProfileID | 5V |
| Port.N.Profiles | 5V |
| Port.N.SerialNumber | PD |
| Port.N.TimeCharged_sec | base |
| Port.N.TimeCharging_sec | base |
| Port.N.USBStrings | PD |
| Port.N.VID | PD |
| Port.N.Voltage_10mV | PD |
| PortInfo.N | base |
| PortsInfo | base |
| Profile.N.enabled | 5V |
| pwm_percent | temperature |
| Rebooted | base |
| SecurityArmed | 5V |
| Settings | base |
| SystemTitle | base |
| Temperature_C | temperature |
| Temperature_flags | temperature |
| Temperature_Limit_Max_C | temperature |
| TemperatureMax_C | temperature |
| TotalCurrent_mA | 5V |
| TotalPower_W | 5V |
| TwelveVoltRail_flags | 12V |
| TwelveVoltRail_Limit_Max_V | 12v |
| TwelveVoltRail_Limit_Min_V | 12v |
| TwelveVoltRail_V | 12V |
| TwelveVoltRailMax_V | 12V |
| TwelveVoltRailMin_V | 12V |
| Uptime_sec | base |

> Note: `nrOfPorts`/`PanelID`/etc. table reproduced above is the navigation index from the manual (page 138-141). Individual field reference entries follow below, each documented in the order they appear in the manual.

---

#### Attached

A bit-field with one bit set for each port with a device attached, port 1 in bit 0, port 2 in bit 1 and so on.

**Feature set:** 5V

**Syntax:** see Call Structure

```json
{
  "method": "cbrx_connection_get",
  "params": [
    connection-handle,
    "Attached"
  ]
}
```

*connection-handle* is the Connection Handles as an integer.

**Returns:**

```json
{
  "result": attached-bit
}
```

*attached-bit* is an integer value.

Example, of three devices connected to ports 1,2,3

```json
{
    "jsonrpc": "2.0",
    "id": 0,
    "result": 7
}
```

---

#### Compiled

Timestamp of firmware version.

**Feature set:** base

**Syntax:** see Call Structure

```json
{
  "method": "cbrx_connection_get",
  "params": [
    connection-handle,
    "Compiled"
  ]
}
```

*connection-handle* is the Connection Handles as an integer.

**Returns:**

```json
{
  "result": "compiled-date"
}
```

*compiled-date* is the timestamp of when the Firmware was compiled format "MMM DD YYYY HH mm SS"

| Timestamp | Description |
|---|---|
| MMM | Month first 3 letters in english |
| DD | Date of the month as integer |
| YYYY | Year as an integer |
| HH | Hour of build, 0-23 |
| mm | Minute of build, 0-59 |
| SS | Second of build, 0-59 |

**Example**

```json
{
    "jsonrpc": "2.0",
    "id": 0,
    "result": "Jul 08 2015 10:43:20"
}
```

---

#### EnabledProfiles

List of global profiles currently enabled

**Feature set:** 5V

**Syntax:** see Call Structure

```json
{
  "method": "cbrx_connection_get",
  "params": [
    connection-handle,
    "EnabledProfiles"
  ]
}
```

*connection-handle* is the Connection Handles as an integer.

**Returns:**

```json
{
  "result": "profiles"
}
```

*profiles* is list of all the charging profiles which are applied to the hub, profiles are displayed as a single number with a space between each profile.

**Example**

Return value where charging profiles 1,2,3 and 4 are enabled.

```json
{
    "jsonrpc": "2.0",
    "id": 0,
    "result": "1 2 3 4"
}
```

---

#### Firmware

Firmware version string.

**Feature set:** base

**Syntax:** see Call Structure

```json
{
  "method": "cbrx_connection_get",
  "params": [
    connection-handle,
    "Firmware"
  ]
}
```

*connection-handle* is the Connection Handles as an integer.

**Returns:**

```json
{
  "result": "firmware-version"
}
```

*firmware-version* is the version number of the firmware. Format 'N.nn'

**Example**

```json
{
    "jsonrpc": "2.0",
    "id": 0,
    "result": "1.55"
}
```

---

#### FirmwareRequirements

Get the types of firmware applicable to this hub, returned as an array containing information for all types of firmware that the hub accepts. For each entry, the form factor field indicates the firmware type for that part, which can be one of "un" for Universal, "pd" for PDSync, "st" for the TS3-C10 or "mc" for motor control board.

**Feature set:** base

| Firmware | Part Number | Product Name |
|---|---|---|
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

**Syntax:** see Call Structure

```json
{
  "method": "cbrx_connection_get",
  "params": [
    connection-handle,
    "FirmwareRequirements"
  ]
}
```

*connection-handle* is the Connection Handles as an integer.

**Returns:**

Returns an array of information about each type of firmware currently installed, with details of the firmware types required to update them.

```json
{
  "result": [
    {
      "Manufacturer": "manufacturer-name",
      "Hardware": "product-name",
      "Firmware": "firmware-version",
      "Bootloader": "bootloader-version",
      "Group": "group-order",
      "FormFactor": "firmware-type",
      "HardwareID":hardware-id,
      "Group": "group-order"
      "SerialNumber": "hub-serial",
    }
  ]
}
```

| Output | Description |
|---|---|
| hub-serial | This is the serial number of the hub returned from cbrx_discover |
| manufacturer-name | Defined name of manufacturer, Default is 'Cambrionix' |
| firmware-version | Version number of the firmware. Format 'N.nn' |
| bootloader-version | Version number of the bootloader. Format 'N.nn' |
| group-order | Used to order hubs which is useful when updating connected products so that down-stream products are updated and rebooted first. |
| firmware-type | Used to denote which firmware the product accepts |
| hardware-id | hardware ID number of front panel product |
| product-name | Hardware name of product |

**Example**

```json
{
    "jsonrpc": "2.0",
    "id": 0,
    "result": [
        {
            "Manufacturer": "cambrionix",
            "Hardware": "ThunderSync3-16",
            "Firmware": "1.87",
            "Bootloader": "0.21",
            "FormFactor": "un",
            "HardwareID": 50,
            "Group": "-",
            "SerialNumber": "DJ00ASBK"
        },
        {
            "Manufacturer": "cambrionix",
            "Hardware": "Motor Board",
            "Firmware": "0.08",
            "Bootloader": "0.05",
            "FormFactor": "mc",
            "HardwareID": 1,
            "Group": "+",
            "SerialNumber": "DJ00ASBK"
        }
    ]
}
```

---

#### FiveVoltRail_flags

Returns list of 5V supply rail error flags that have been detected, if any.

**Feature set:** 5V

**Syntax:** see Call Structure

```json
{
  "method": "cbrx_connection_get",
  "params": [
    connection-handle,
    "FiveVoltRail_flags"
  ]
}
```

*connection-handle* is the Connection Handles as an integer.

**Returns:**

```json
{
  "result": "flag"
}
```

| Flag | Description |
|---|---|
| UV | Under voltage occurred |
| OV | Over voltage occurred |
| UV OV | Both under and over voltage occurred. |

**Example**

```json
{
    "jsonrpc": "2.0",
    "id": 0,
    "result": "UV OV"
}
```

---

#### FiveVoltRail_Limit_Max_V

Upper limit of the 5V rail that will trigger the error flag.

**Feature set:** 5V

**Syntax:** see Call Structure

```json
{
  "method": "cbrx_connection_get",
  "params": [
    connection-handle,
    "FiveVoltRail_Limit_Max_V"
  ]
}
```

*connection-handle* is the Connection Handles as an integer.

**Returns:**

```json
{
  "result": FiveVoltRail-Limit-Max
}
```

*FiveVoltRail-Limit-Max* is a decimal number in Volts, format n.nn

**Example**

```json
{
    "jsonrpc": "2.0",
    "id": 0,
    "result": 5.58
}
```

---

#### FiveVoltRail_Limit_Min_V

Lower limit of the 5V rail that will trigger the error flag

**Feature set:** 5V

**Syntax:** see Call Structure

```json
{
  "method": "cbrx_connection_get",
  "params": [
    connection-handle,
    "FiveVoltRail_Limit_Min_V"
  ]
}
```

*connection-handle* is the Connection Handles as an integer.

**Returns:**

```json
{
  "result": FiveVoltRail-Limit-Min
}
```

*FiveVoltRail-Limit-Min* is a decimal number in Volts, format n.nn

**Example**

```json
{
    "jsonrpc": "2.0",
    "id": 0,
    "result": 3.50
}
```

---

#### FiveVoltRail_V

Current 5V supply voltage in Volt (V)

**Feature set:** 5V

**Syntax:** see Call Structure

```json
{
  "method": "cbrx_connection_get",
  "params": [
    connection-handle,
    "FiveVoltRail_V"
  ]
}
```

*connection-handle* is the Connection Handles as an integer.

**Returns:**

```json
{
  "result": FiveVoltRail_V
}
```

*FiveVoltRail_V* is a decimal number in Volts, format n.nn

**Example**

```json
{
    "jsonrpc": "2.0",
    "id": 0,
    "result": 5.25
}
```

---

#### FiveVoltRailMax_V

Highest 5V supply voltage measured in Volt (V)

**Feature set:** 5V

**Syntax:** see Call Structure

```json
{
  "method": "cbrx_connection_get",
  "params": [
    connection-handle,
    "FiveVoltRailMax_V"
  ]
}
```

*connection-handle* is the Connection Handles as an integer.

**Returns:**

```json
{
  "result": FiveVoltRailMax_V
}
```

*FiveVoltRailMax_V* is a decimal number in Volts, format n.nn

**Example**

```json
{
    "jsonrpc": "2.0",
    "id": 0,
    "result": 5.25
}
```

---

#### FiveVoltRailMin_V

Lowest 5V supply voltage measured in Volt (V)

**Feature set:** 5V

**Syntax:** see Call Structure

```json
{
  "method": "cbrx_connection_get",
  "params": [
    connection-handle,
    "FiveVoltRailMin_V"
  ]
}
```

*connection-handle* is the Connection Handles as an integer.

**Returns:**

```json
{
  "result": FiveVoltRailMin_V
}
```

*FiveVoltRailMin_V* is a decimal number in Volts, format n.nn

**Example**

```json
{
    "jsonrpc": "2.0",
    "id": 0,
    "result": 5.20
}
```

---

#### Gates

Returns an object describing the states of all gates on the expansion product if present. Currently, this is only available on the ModIT range.

**Feature set:** gate

**Syntax:** see Call Structure

```json
{
  "method": "cbrx_connection_get",
  "params": [
    connection-handle,
    "Gates"
  ]
}
```

*connection-handle* is the Connection Handles as an integer.

**Returns:**

```json
{
  "result":
  {
    "N":"state"
  }
}
```

*N* is the port number

| state | Description |
|---|---|
| open | The gate is open |
| closed | The gate is closed |
| opening | The gate is opening |
| closing | The gate is closing |
| stalled | The gate has stopped moving |
| timeout | The gate has taken too long to respond |
| unknown | Neither the top nor bottom end switches are engaged |
| open-stalled | The gate has stalled in the open position |
| closed-stalled | The gate has stalled in the closed position |
| opening-stalled | The gate has stalled whilst opening |
| closing-stalled | The gate has stalled whilst closing |
| disabled | Disabled flag has been set which prevents the gate from opening/ closing |

**Example**

```json
{
    "jsonrpc": "2.0",
    "id": 0,
    "result": {
        "1": "open",
        "2": "closed",
        "3": "closed",
        "4": "opening"
    }
}
```

---

#### Group

Group letter read from PCB jumpers.

**Feature set:** base

**Syntax:** see Call Structure

```json
{
  "method": "cbrx_connection_get",
  "params": [
    connection-handle,
    "Group"
  ]
}
```

*connection-handle* is the Connection Handles as an integer.

**Returns:**

```json
{
  "result": "group-order"
}
```

*group-order* Is used to order hubs which is useful when updating connected products so that down-stream products are updated and rebooted first., or "-" if no group jumper was fitted.

**Example**

```json
{
    "jsonrpc": "2.0",
    "id": 0,
    "result": "-"
}
```

---

#### Hardware

Part number of the hub.

**Feature set:** base

**Syntax:** see Call Structure

```json
{
  "method": "cbrx_connection_get",
  "params": [
    connection-handle,
    "Hardware"
  ]
}
```

*connection-handle* is the Connection Handles as an integer.

**Returns:**

```json
{
  "result": "product-name"
}
```

*product-name* is the hardware name of product

**Example**

```json
{
  "result": "ThunderSync3-16"
}
```

---

#### HardwareFlags

Flags indicating whether features are present

**Feature set:** base

**Syntax:** see Call Structure

```json
{
  "method": "cbrx_connection_get",
  "params": [
    connection-handle,
    "HardwareFlags"
  ]
}
```

*connection-handle* is the Connection Handles as an integer.

**Returns:**

```json
{
  "result": "flag"
}
```

| Flag | Description |
|---|---|
| S | Sync feature set |
| L | 5V feature set |
| E | 12V feature set |
| T | Temperature feature set |
| P | PD feature set |

**Example**

```json
{
    "jsonrpc": "2.0",
    "id": 0,
    "result": "SLET"
}
```

---

#### HardwareInformation

Information on the hub

**Feature set:** base

**Syntax:** see Call Structure

```json
{
  "method": "cbrx_connection_get",
  "params": [
    connection-handle,
    "HardwareInformation"
  ]
}
```

*connection-handle* is the Connection Handles as an integer.

**Returns:**

```json
{
  "result": {
    "ProductName": "product-name",
    "ProductWebPage": "product-webpage",
    "TemperatureRangeC": {
      "Min": min-temperature,
      "Max": max-temperature
    },
    "HumidityRange": {
      "Min": min-humidity,
      "Max": max-humidity
    },
    "DimensionsMillimetres": {
      "Width": product-width,
      "Length": product-length,
      "Height": product-height
    },
    "HostPortType": "host-port",
    "HostPortBandwidth": "host-port-bandwidth",
    "HubMaxPowerOutputWatts": hub-max-power-output,
    "Ports": {
      "1": {
        "HardwareInformation": {
          "Type": "port-type",
          "Bandwidth": "port-bandwidth",
          "VoltageMax": port-max-volts,
          "MilliampsMax": port-max-current
        }
      },
      // etc all ports.
    }
  }
}
```

| Variable | Description |
|---|---|
| product-name | Product name of the hub |
| product-webpage | The webpage for the hub |
| min-temperature | The minimum recommended temperature for the hubs enviroment (°C) |
| max-temperature | The maximum recommended temperature for the hubs enviroment |
| min-humidity | The minimum ambient humidty % for the hubs enviroment |
| max-humidity | The maximum ambient humidity % for the hubs enviroment |
| product-width | The width of the hub (mm) |
| product-length | The length of the hub (mm) |
| product-height | The height of the hub (mm) |
| host-port | The USB type of the host port |
| host-port-bandwidth | The maximum bandwidth for the host port (Gbps) |
| hub-max-power-output | The maximum power output for the whole hub |
| port-type | The USB type of the downstream ports |
| port-bandwidth | The maximum bandwidth for the downstream ports (Gbps) |
| port-max-volts | The maximum Voltage output for the downstream ports (V) |
| port-max-current | The maximum Current output fo the downstream ports (mA) |

**Example**

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "ProductName": "ThunderSync3-C10",
    "ProductWebPage": "https://www.cambrionix.com/products/thundersync3-c10",
    "TemperatureRangeC": {
      "Min": 10,
      "Max": 35
    },
    "HumidityRange": {
      "Min": 5,
      "Max": 95
    },
    "DimensionsMillimetres": {
      "Width": 193,
      "Length": 136,
      "Height": 34
    },
    "HostPortType": "Thunderbolt 3",
    "HostPortBandwidth": "40Gbps",
    "HubMaxPowerOutputWatts": 150,
    "Ports": {
      "1": {
        "HardwareInformation": {
          "Type": "USB Type-C",
          "Bandwidth": "5Gbps",
          "VoltageMax": 5.2,
          "MilliampsMax": 3000
        }
      },
      // etc all ports.
    }
  }
}
```

---

#### Health

All available keys that are not port specific and change dynamically, as a dictionary.

**Feature set:** base

**Syntax:** see Call Structure

```json
{
  "method": "cbrx_connection_get",
  "params": [
    connection-handle,
    "Health"
  ]
}
```

*connection-handle* is the Connection Handles as an integer.

**Returns:**

```json
{
  "result": {
    "Uptime_sec": Uptime_sec,
    "FiveVoltRail_V": FiveVoltRail_V,
    "FiveVoltRailMin_V":FiveVoltRailMin_V,
    "FiveVoltRailMax_V":FiveVoltRailMax_V,
    "FiveVoltRail_flags": "FiveVoltRail_flags",
    "TwelveVoltRail_V":TwelveVoltRail_V,
    "TwelveVoltRailMin_V":TwelveVoltRailMin_V,
    "TwelveVoltRailMax_V":TwelveVoltRailMax_V,
    "InputRail_V":InputRail_V
    "InputRailMin_V":InputRailMin_V,
    "InputRailMax_V":InputRailMax_V,
    "TwelveVoltRail_flags": "TwelveVoltRail_flags",
    "InputRail_flags": "InputRail_flags",
    "Temperature_C":Temperature_C,
    "TemperatureMax_C":TemperatureMax_C,
    "Temperature_flags": "Temperature_flags",
    "Rebooted":Rebooted
  }
}
```

| Output | Description |
|---|---|
| Uptime_sec | see Uptime_sec |
| FiveVoltRail_V | see FiveVoltRail_V |
| FiveVoltRailMin_V | see FiveVoltRailMin_V |
| FiveVoltRailMax_V | see FiveVoltRailMax_V |
| FiveVoltRail_flags | see FiveVoltRail_flags |
| TwelveVoltRail_V | see TwelveVoltRail_V |
| TwelveVoltRailMin_V | see TwelveVoltRailMin_V |
| TwelveVoltRailMax_V | see TwelveVoltRailMax_V |
| InputRail_V | see InputRail_V |
| InputRailMin_V | see InputRail_Limit_Min_V |
| InputRailMax_V | see InputRailMax_V |
| TwelveVoltRail_flags | see TwelveVoltRail_flags |
| InputRail_flags | see InputRail_flags |
| Temperature_C | see Temperature_C |
| TemperatureMax_C | see TemperatureMax_C |
| Temperature_flags | see Temperature_flags |
| Rebooted | see Rebooted |

**Example**

```json
{
    "jsonrpc": "2.0",
    "id": 0,
    "result": {
        "Uptime_sec": 528422,
        "FiveVoltRail_V": 5.23,
        "FiveVoltRailMin_V": 5.14,
        "FiveVoltRailMax_V": 5.25,
        "FiveVoltRail_flags": "",
        "TwelveVoltRail_V": 12.12,
        "TwelveVoltRailMin_V": 11.99,
        "TwelveVoltRailMax_V": 12.2,
        "InputRail_V": 12.12,
        "InputRailMin_V": 11.99,
        "InputRailMax_V": 12.2,
        "TwelveVoltRail_flags": "",
        "InputRail_flags": "",
        "Temperature_C": 37.3,
        "TemperatureMax_C": 41.1,
        "Temperature_flags": "",
        "Rebooted": true
    }
}
```

---

#### HostPresent

The hub monitors the host USB socket for an attached host computer.

**Feature set:** PD

**Syntax:** see Call Structure

```json
{
  "method": "cbrx_connection_get",
  "params": [
    connection-handle,
    "HostPresent"
  ]
}
```

*connection-handle* is the Connection Handles as an integer.

**Returns:**

```json
{
  "result":host
}
```

| host | description |
|---|---|
| true | Host is detected |
| false | No host is detected |

**Example**

```json
{
    "jsonrpc": "2.0",
    "id": 0,
    "result": true
}
```

---

#### InputRail_flags

List of input rail error flags if any are set.

**Feature set:** PD

**Syntax:** see Call Structure

```json
{
  "method": "cbrx_connection_get",
  "params": [
    connection-handle,
    "InputRail_flags"
  ]
}
```

*connection-handle* is the Connection Handles as an integer.

**Returns:**

```json
{
  "result":flag
}
```

| Flag | Description |
|---|---|
| UV | under voltage occurred |
| OV | over voltage occurred |
| no flags | voltage is acceptable |

**Example**

```json
{
    "jsonrpc": "2.0",
    "id": 0,
    "result": "OV UV"
}
```

---

#### InputRail_Limit_Max_V

Upper limit of the input rail that will trigger the error flag

**Feature set:** PD

**Syntax:** see Call Structure

```json
{
  "method": "cbrx_connection_get",
  "params": [
    connection-handle,
    "InputRail_Limit_Max_V"
  ]
}
```

*connection-handle* is the Connection Handles as an integer.

**Returns:**

```json
{
  "result": InputRail-Limit-Max
}
```

*InputRail-Limit-Max* is a decimal number in Volts, format n.nn

**Example**

```json
{
    "jsonrpc": "2.0",
    "id": 0,
    "result": 24.7
}
```

---

#### InputRail_Limit_Min_V

Lower limit of the input rail that will trigger the error flag.

**Feature set:** PD

**Syntax:** see Call Structure

```json
{
  "method": "cbrx_connection_get",
  "params": [
    connection-handle,
    "InputRail_Limit_Min_V"
  ]
}
```

*connection-handle* is the Connection Handles as an integer.

**Returns:**

```json
{
  "result": InputRail-Limit-Min
}
```

*InputRail-Limit-Min* is a decimal number in Volts, format n.nn

**Example**

```json
{
    "jsonrpc": "2.0",
    "id": 0,
    "result": 9.59
}
```

---

#### InputRail_V

Current input rail supply in Volts (V).

**Feature set:** PD

**Syntax:** see Call Structure

```json
{
  "method": "cbrx_connection_get",
  "params": [
    connection-handle,
    "InputRail_V"
  ]
}
```

*connection-handle* is the Connection Handles as an integer.

**Returns:**

```json
{
  "result":InputRail_V
}
```

*InputRail_V* is a decimal number in Volts, format n.nn

**Example**

```json
{
    "jsonrpc": "2.0",
    "id": 0,
    "result": 24.03
}
```

---

#### InputRailMax_V

Highest input voltage measured in Volts (V).

**Feature set:** PD

**Syntax:** see Call Structure

```json
{
  "method": "cbrx_connection_get",
  "params": [
    connection-handle,
    "InputRailMax_V"
  ]
}
```

*connection-handle* is the Connection Handles as an integer.

**Returns:**

```json
{
  "result":InputRailMax_V
}
```

*InputRailMax_V* is a decimal number in Volts, format n.nn

**Example**

```json
{
    "jsonrpc": "2.0",
    "id": 0,
    "result": 24.14
}
```

---

#### InputRailMin_V

Lowest input voltage measured in Volts (V).

**Feature set:** PD

**Syntax:** see Call Structure

```json
{
  "method": "cbrx_connection_get",
  "params": [
    connection-handle,
    "InputRailMin_V"
  ]
}
```

*connection-handle* is the Connection Handles as an integer.

**Returns:**

```json
{
  "result":InputRailMin_V
}
```

InputRailMin_V is a decimal number in Volts, format n.nn

**Example**

```json
{
    "jsonrpc": "2.0",
    "id": 0,
    "result": 23.82
}
```

---

#### Key.N

Get information if a button has been pressed, double-clicks cannot be detected.

**Feature set:** 5V

**Syntax:** see Call Structure

```json
{
  "method": "cbrx_connection_get",
  "params": [
    connection-handle,
    "Key.N"
  ]
}
```

*connection-handle* is the Connection Handles as an integer.

**Returns:**

```json
{
  "result": button
}
```

| button | Description |
|---|---|
| 0 | button n has not been pressed since the last time this entry was read |
| 1 | button n has been pressed since the last time this entry was read |

**Example**

```json
{
    "jsonrpc": "2.0",
    "id": 0,
    "result": 0
}
```

---

#### ModeChangeAuto

Mode change from Charge to Sync is automatic.

**Feature set:** sync

**Syntax:** see Call Structure

```json
{
  "method": "cbrx_connection_get",
  "params": [
    connection-handle,
    "ModeChangeAuto"
  ]
}
```

*connection-handle* is the Connection Handles as an integer.

**Returns:**

```json
{
  "result":auto-change
}
```

| auto-change | Description |
|---|---|
| true | Mode change from Charge to Sync is automatic. |
| false | Mode change from Charge to Sync is manual. |

**Example**

```json
{
    "jsonrpc": "2.0",
    "id": 0,
    "result": true
}
```

---

#### nrOfPorts

Number of USB ports on the hub.

**Feature set:** base

**Syntax:** see Call Structure

```json
{
  "method": "cbrx_connection_get",
  "params": [
    connection-handle,
    "nrOfPorts"
  ]
}
```

*connection-handle* is the Connection Handles as an integer.

**Returns:**

```json
{
  "result":portsnumber
}
```

*portsnumber* is an integer of the amount of ports available

**Example**

```json
{
    "jsonrpc": "2.0",
    "id": 0,
    "result": 8
}
```

**Note**

- On the PDSync-C4 you will have an additional port 0, which is the information on the host port.

---

#### PanelID

PanelID number of front panel board, if fitted.

**Feature set:** base

**Syntax:** see Call Structure

```json
{
  "method": "cbrx_connection_get",
  "params": [
    connection-handle,
    "PanelID"
  ]
}
```

*connection-handle* is the Connection Handles as an integer.

**Returns:**

```json
{
  "result": "Panel-ID"
}
```

*Panel-ID* is the ID number of front panel product, if not fitted will return Absent/None

**Example**

```json
{
    "jsonrpc": "2.0",
    "id": 0,
    "result": "Absent"
}
```

---

#### Port.N.Battery

If possible, retrieve the current battery level of the connected device. See notes about battery information collection. Depending on the device type (Android™, iOS etc.) and the host OS, different data may be returned.

For Apple, "Apple Mobile Device Support" must be installed (included with iTunes)

For Android, adb must be installed and running.

**Feature set:** sync

**Syntax:** see Call Structure

```json
{
  "method": "cbrx_connection_get",
  "params": [
   connection-handle
   "Port.N.Battery"
  ]
}
```

*connection-handle* is the Connection Handles as an integer.

**Returns:**

```json
{
  "result": {
    "CurrentLevel":battery-current-level,
    "CurrentTime":current-hub-time,
    "StartingLevel":charge-start-level,
    "StartingTime":charge-start-time,
  }
}
```

| Output | Description |
|---|---|
| battery-current-level | Current battery level of device displayed as a percentage |
| current-hub-time | The hub time, shown as an integer in ms |
| charge-start-level | Battery percentage level when device connected |
| charge-start-time | The hub time charging started, shown as an integer in ms |

**Example**

```json
{
    "jsonrpc": "2.0",
    "id": 0,
    "result": {
    "CurrentLevel": 78,
    "CurrentTime": 15234254346,
    "StartLevel": 23,
    "StartTime": 15124151512,
    }
}
```

---

#### Port.N.Current_mA

Current being delivered to the USB device connected to this USB port in milli-Amperes (mA).

**Feature set:** base

**Syntax:** see Call Structure

```json
{
  "method": "cbrx_connection_get",
  "params": [
    connection-handle,
    "Port.N.Current_mA"
  ]
}
```

*connection-handle* is the Connection Handles as an integer.

**Returns:**

```json
{
  "result": Current_mA
}
```

*Current_mA* is the current being delivered to the device, in mA (milliamperes)

**Example**

```json
{
    "jsonrpc": "2.0",
    "id": 0,
    "result": 0
}
```

---

#### Port.N.Description

Description as reported by the USB device attached to this USB port if it could be detected. Empty string is returned if it could not be detected.

**Feature set:** PD

**Syntax:** see Call Structure

```json
{
  "method": "cbrx_connection_get",
  "params": [
    connection-handle,
    "Port.N.Description"
  ]
}
```

*connection-handle* is the Connection Handles as an integer.

**Returns:**

```json
{
  "result": "Description"
}
```

*Description* is the name of the hardware.

**Example**

```json
{
    "jsonrpc": "2.0",
    "id": 0,
    "result": "SuperPhone6"
}
```

---

#### Port.N.Energy_Wh

Energy the USB device on this USB port has consumed.

**Feature set:** base

**Syntax:** see Call Structure

```json
{
  "method": "cbrx_connection_get",
  "params": [
    connection-handle,
    "Port.N.Energy_Wh"
  ]
}
```

*connection-handle* is the Connection Handles as an integer.

**Returns:**

```json
{
  "result":energy-Wh
}
```

*energy-Wh* is the power in Watt-hours (calculated every second), format of n.n

**Example**

```json
{
    "jsonrpc": "2.0",
    "id": 0,
    "result": 0.0
}
```

---

#### Port.N.Flags

Get a list of all flags on a specific port

**Feature set:** base

**Syntax:** see Call Structure

```json
{
  "method": "cbrx_connection_get",
  "params": [
    connection-handle,
    "Port.N.Flags"
  ]
}
```

*connection-handle* is the Connection Handles as an integer.

**Returns:**

```json
{
  "result": "flag"
}
```

List of case-sensitive flag characters, separated by spaces. O, S, B, I, P, C, F are mutually exclusive. A, D are mutually exclusive.

| Flag | Description |
|---|---|
| O | Port is in OFF mode |
| S | Port is in SYNC mode |
| B | Port is in Biased mode |
| I | Port is in charge mode, and is IDLE |
| P | Port is in charge mode, and is PROFILING |
| C | Port is in charge mode, and is CHARGING |
| F | Port is in charge mode, and has FINISHED charging |
| A | Device is ATTACHED to this port |
| D | No device is attached to this port. Port is DETACHED |
| T | Device has been stolen from port: THEFT |
| E | ERRORs are present. See health command |
| R | System has REBOOTED. See crf command |
| r | Vbus is being reset during mode change |

**Example**

```json
{
    "jsonrpc": "2.0",
    "id": 0,
    "result": "R D S"
}
```

---

#### Port.N.FlashDrive

If detected, returns the mount point of a USB flash drive. For Windows this will be a drive letter, otherwise it will be a volume mount point.

**Feature set:** sync

**Syntax:** see Call Structure

```json
{
  "method": "cbrx_connection_get",
  "params": [
    connection-handle,
    "Port.N.FlashDrive"
  ]
}
```

*connection-handle* is the Connection Handles as an integer.

**Returns:**

```json
{
  "Path:": "location",
  "Capacity":total-memory,
  "Available":available-memory
}
```

| Output | Description |
|---|---|
| location | Location the disk is in the host system |
| total-memory | Total memory on disk |
| available-memory | Memory on disk not being used |

**Examples:**

Windows:

```json
{
    "json": "2.0",
    "id": 0,
    "Path:": "H:",
    "Capacity": 123123123,
    "Available": 123123
}
```

macOS®:

```json
{
    "json": "2.0,
    "id": 0,
    "Path:": "/Volumes/SanDisk1",
    "Capacity": 123123123,
    "Available": 123123
}
```

Linux:

```json
{
    "json": "2.0",
    "id": 0,
    "Path:": "/media/bob/SanDisk1",
    "Capacity": 123123123,
    "Available": 123123
}
```

If there is no flash drive, the return value will simply be false.

This same information will also be provided in PortsInfo, PortInfo.N or cbrx_discover('all') in a "FlashDrive" field where applicable and present. If not applicable or preset, this field will be absent.

---

#### Port.N.LocationID

Return the location ID for a specific port. This does not require a device to be attached and so may be used to uniquely identify a USB slot. Location IDs indicate the bus number that a USB host controller is on in the first byte, then the port numbers down the tree for child devices.

**Feature set:** sync

**Syntax:** see Call Structure

```json
{
  "method": "cbrx_connection_get",
  "params": [
    connection-handle,
    "Port.N.LocationID"
  ]
}
```

*connection-handle* is the Connection Handles as an integer.

**Returns:**

```json
{
  "result":location-id
}
```

*location-id* Is the Location IDs as an Integer

**Example**

```json
{
    "jsonrpc": "2.0",
    "id": 0,
    "result": 563154944
}
```

**Note**

- for USB3 hubs, this location ID will be different when a USB3 device is plugged in compared to a USB2 device

---

#### Port.N.Manufacturer

Manufacturer as reported by the USB device attached to this USB port, if it could be detected. Empty string is returned if it could not be detected.

**Feature set:** PD

**Syntax:** see Call Structure

```json
{
  "method": "cbrx_connection_get",
  "params": [
    connection-handle,
    "Port.N.Manufacturer"
  ]
}
```

*connection-handle* is the Connection Handles as an integer.

**Returns:**

```json
{
  "result": "device-manufacturer"
}
```

*device-manufacturer* is the name of the device manufacturer

**Example**

```json
{
    "jsonrpc": "2.0",
    "id": 0,
    "result": "SuperPhone Makers Inc."
}
```

---

#### Port.N.Mode

Current port mode.

**Feature set:** base

**Syntax:** see Call Structure

```json
{
  "method": "cbrx_connection_get",
  "params": [
    connection-handle
    "Port.N.Mode"
  ]
}
```

*connection-handle* is the Connection Handles as an integer.

**Returns:**

```json
{
  "result": "mode"
}
```

For Standard USB hubs, the mode can be any of:

| mode character | Description |
|---|---|
| s | Sync mode |
| c | Charge mode |
| b | Biased mode |
| o | Off |

For Type-C hubs, the mode can be:

| mode character | Description |
|---|---|
| c | On |
| o | Off |

**Example**

```json
{
    "jsonrpc": "2.0",
    "id": 0,
    "result": "s"
}
```

---

#### Port.N.PID

Product ID of the USB device attached to this USB port, if it could be detected.

**Feature set:** PD

**Syntax:** see Call Structure

```json
{
  "method": "cbrx_connection_get",
  "params": [
    connection-handle,
    "Port.N.PID"
  ]
}
```

*connection-handle* is the Connection Handles as an integer.

**Returns:**

```json
{
  "result":product-id
}
```

*product-id* is the product ID number or PID. Displayed as an Integer. 0 (zero) is returned if it could not be detected.

**Example**

```json
{
    "jsonrpc": "2.0",
    "id": 0,
    "result": 0
}
```

---

#### Port.N.ProfileID

Profile ID number.

**Feature set:** 5V

**Syntax:** see Call Structure

```json
{
  "method": "cbrx_connection_get",
  "params": [
    connection-handle,
    "Port.N.PID"
  ]
}
```

> Note: the manual's syntax example for this entry literally reuses `"Port.N.PID"` as the params value (likely a documentation typo carried over from the previous entry); the intended key per the section heading and key table is `Port.N.ProfileID`.

*connection-handle* is the Connection Handles as an integer.

**Returns:**

```json
{
  "result":profile-ID
}
```

*profile-ID* is the profile number, or 0 if not charging.

**Example**

```json
{
    "jsonrpc": "2.0",
    "id": 0,
    "result": 0
}
```

---

#### Port.N.Profiles

List of enabled profiles for this port.

**Feature set:** 5V

**Syntax:** see Call Structure

```json
{
  "method": "cbrx_connection_get",
  "params": [
    connection-handle,
    "Port.N.Profiles"
  ]
}
```

*connection-handle* is the Connection Handles as an integer.

**Returns:**

```json
{
  "result": "profiles"
}
```

*profiles* is list of all the charging profiles which are applied to the port, profiles are displayed as a single number with a space between each profile.

**Example**

charging profiles 1,2,3 and 4 are enabled.

```json
{
    "jsonrpc": "2.0",
    "id": 0,
    "result": "1 2 3 4"
}
```

---

#### Port.N.SerialNumber

Serial number as reported by the USB device attached to this USB port, if it could be detected. Empty string is returned if it could not be detected.

**Feature set:** PD

**Syntax:** see Call Structure

```json
{
  "method": "cbrx_connection_get",
  "params": [
    connection-handle,
    "Port.N.SerialNumber"
  ]
}
```

*connection-handle* is the Connection Handles as an integer.

**Returns:**

```json
{
  "result": "usb-serial"
}
```

*usb-serial* is the USB serial number

**Example**

```json
{
    "jsonrpc": "2.0",
    "id": 0,
    "result": "1127dfa9037s1a8cb1"
}
```

---

#### Port.N.TimeCharged_sec

Time in seconds since this USB port detected the device has completed charging.

**Feature set:** base

**Syntax:** see Call Structure

```json
{
  "method": "cbrx_connection_get",
  "params": [
    connection-handle,
    "Port.N.TimeCharged_sec"
  ]
}
```

*connection-handle* is the Connection Handles as an integer.

**Returns:**

```json
{
  "result":charge-complete
}
```

*charge-complete* is the time in seconds that has passed since the device completed charging, -1 will be returned if this port has not detected completed charging.

**Example**

```json
{
    "jsonrpc": "2.0",
    "id": 0,
    "result": 0
}
```

---

#### Port.N.TimeCharging_sec

Time in seconds since this USB port started charging an attached device. 0 will be returned if the USB port has not started charging an attached device.

**Feature set:** base

**Syntax:** see Call Structure

```json
{
  "method": "cbrx_connection_get",
  "params": [
    connection-handle,
    "Port.N.TimeCharging_sec"
  ]
}
```

*connection-handle* is the Connection Handles as an integer.

**Returns:**

```json
{
  "result":charging-time
}
```

*charging-time* is the time passed in seconds that a port has been charging a device.

**Example**

```json
{
    "jsonrpc": "2.0",
    "id": 0,
    "result": 0
}
```

---

#### Port.N.USBStrings

A dictionary containing the values for "Manufacturer", "Description" and "SerialNumber" for this USB port.

**Feature set:** PD

**Syntax:** see Call Structure

```json
{
  "method": "cbrx_connection_get",
  "params": [
    connection-handle,
    "Port.N.USBStrings"
  ]
}
```

*connection-handle* is the Connection Handles as an integer.

**Returns:**

```json
{
  "SerialNumber": "usb-serial",
  "Description": "description",
  "Manufacturer": "device-manufacturer"
}
```

| Output | Description |
|---|---|
| usb-serial | USB serial number |
| description | Name of the hardware |
| device-manufacturer | The name of the device manufacturer |

**Example**

```json
{
    "json": 2.0,
    "id": 0,
    "SerialNumber": "23213dfe12e2412",
    "Description": "SuperPhone6",
    "Manufacturer": "SuperPhone Makers Inc."
}
```

---

#### Port.N.VID

Vendor ID of the USB device attached to this USB port.

**Feature set:** PD

**Syntax:** see Call Structure

```json
{
  "method": "cbrx_connection_get",
  "params": [
    connection-handle,
    "Port.N.VID"
  ]
}
```

*connection-handle* is the Connection Handles as an integer.

**Returns:**

```json
{
  "result": Vendor-ID
}
```

*Vendor-ID* is the vendor ID, VID. Displayed as an Integer. 0 (zero) is returned if it could not be detected.

**Example**

```json
{
    "jsonrpc": "2.0",
    "id": 0,
    "result": 0
}
```

---

#### Port.N.Voltage_10mV

Voltage being supplied to the port in 10mV.

**Feature set:** PD

**Syntax:** see Call Structure

```json
{
  "method": "cbrx_connection_get",
  "params": [
    connection-handle,
    "Port.N.Voltage_10mV"
  ]
}
```

*connection-handle* is the Connection Handles as an integer.

**Returns:**

```json
{
  "result":voltage-10mV
}
```

*voltage-10mV* is the voltage supplied to the port as an integer in increments of 10mV.

**Example**

```json
{
    "jsonrpc": "2.0",
    "id": 0,
    "result": 520
}
```

---

#### PortInfo.N

Get all port information for specified port. All available keys and values for this port as a dictionary.

**Feature set:** base

**Syntax:** see Call Structure

```json
{
  "method": "cbrx_connection_get",
  "params": [
    connection-handle,
    "PortInfo.N"
  ]
}
```

*connection-handle* is the Connection Handles as an integer.

**Returns:**

```json
{
  "result":{
    "Port":port-number,
    "Current_mA": Current_mA,
    "LocationID":location-id,
    "Flags": flags,
    "USBVersion":usb-version,
    "VID":Vendor-ID,
    "PID":product-ID,
    "Manufacturer": "device-manufacturer",
    "Description": "description",
    "SerialNumber": "usb-serial",
    "USBTree": {
      "LocationID":location-id,
      "USBVersion":usb-version,
      "USBPower": {
        "State": "power-state",
        "Description": "power-description"
      },
      "USBSpeed": {
        "Speed": "USB-speed",
        "Description": "USB-description"
        "Capability": {
          "Speed": "capable-speed",
          "Description": "capable-description"
        }
      },
      "Endpoints": {
        "Active":active-endpoints,
        "Memory":endpoint-memory
      }
    }
  }
}
```

| Output | Description |
|---|---|
| port-number | The number of the port on the hub |
| Current_mA | Current being delivered to the device, in mA (milliamperes) |
| location-id | The Location IDs as an Integer |
| flags | Flags on the port, see Port.N.Flags |
| usb-version | The USB version number of the connection to the hub. Format 'N.nn' |
| Vendor-ID | Device Vedor ID number or VID. Displayed as an Integer |
| product-ID | Product ID number or PID. Displayed as an Integer |
| device-manufacturer | The name of the device manufacturer |
| description | Name of the hardware |
| usb-serial | USB serial number |
| power-state | USB Power States code |
| power-description | USB power turned on/off |
| USB-speed | Maximum speed USB connection capable of |
| USB-description | Name of USB connection i.e. SuperSpeed USB 5Gbps |
| capable-speed | Maximum data speed device capable of |
| capable-description | Name of maximum data speed device capable of |
| active-endpoints | How many endpoints the device is using |
| endpoint-memory | Amount of memory being used by endpoints |

**Example**

```json
{
    "jsonrpc": "2.0",
    "id": 0,
    "result": {
        "Port": 1,
        "Current_mA": 1084,
        "LocationID": 563154944,
        "Flags": "R A S",
        "USBVersion": 2.1,
        "VID": 1256,
        "PID": 26720,
        "Manufacturer": "SAMSUNG",
        "Description": "SAMSUNG_Android",
        "SerialNumber": "RFCN20Q8LJM",
        "USBTree": {
            "LocationID": 563154944,
            "USBVersion": 2.1,
            "USBPower": {
                "State": "D0",
                "Description": "On"
            },
            "USBSpeed": {
                "Speed": "480Mbps",
                "Description": "High",
                "Capability": {
                    "Speed": "10Gbps",
                    "Description": "SuperSpeed USB 10Gbps"
                }
            },
            "Endpoints": {
                "Active": 9,
                "Memory": 36864
            }
        }
    }
}
```

---

#### PortsInfo

Get all port information for all ports. All available information for all ports as a dictionary of dictionaries. Most of these values can be queried individually

**Feature set:** base

**Syntax:** see Call Structure

```json
{
  "method": "cbrx_connection_get",
  "params": [
    connection-handle,
    "PortsInfo"
  ]
}
```

*connection-handle* is the Connection Handles as an integer.

**Returns**

```json
{
  "Port.1": {
    "Port":port-number,
    "Current_mA": Current_mA,
    "Flags": flags,
    "ProfileID":profile-ID,
    "TimeCharging_sec":charging-time,
    "TimeCharged_sec":charge-complete,
    "Energy_Wh":energy-Wh,
    "VID":Vendor-ID,
    "PID":product-ID,
    "Manufacturer": "device-manufacturer",
    "Description": "description",
    "SerialNumber": "usb-serial",
    "PhoneSerialNumber": "phone-serial",
    "PhoneIdentity": "phone-name",
    "IMEI": "IMEI-number",
    "MacAddress": "MacAdress",
    "PhoneSoftwareVersion": "phone-OS-version"
    "USBTree": {
      "USB2": {
        "LocationID":location-id,
        "VID":Vendor-ID,
        "PID":product-ID,
        "Manufacturer": "device-manufacturer",
        "Description": "description",
        "SerialNumber": "usb-serial",
        "USBVersion":usb-version,
        "Battery": {
          "DataSource": "battery-data-source",
          "TrustLevel": "trust-level",
          "PairingSupported":support-pairing,
          "HealthPercent":battery-health,
          "CurrentLevel":battery-current-level,
          "CurrentTime":current-hub-time,
          "StartingLevel":charge-start-level,
          "StartingTime":charge-start-time,
          "CapacityNew":new-battery-capacity,
          "Capacity":current-battery-capacity,
          "ChargingStatus": "charge-status",
        },
        "PhoneSerialNumber": "phone-serial",
        "PhoneIdentity": "phone-name",
        "IMEI": "IMEI-number",
        "MacAddress": "MacAdress",
        "PhoneSoftwareVersion": "phone-OS-version"
      }
    },
    "Battery": {
      "DataSource": "battery-data-source",
      "TrustLevel": "trust-level",
      "PairingSupported":support-pairing,
      "CurrentLevel":battery-current-level,
      "CurrentTime":current-hub-time,
      "StartingLevel":charge-start-level,
      "StartingTime":charge-start-time,
      "CapacityNew":new-battery-capacity,
      "Capacity":current-battery-capacity,
      "ChargingStatus": "charge-status",
      "HealthPercent":battery-health
    }
  },
  "Port.2": {
    "Port": 2,
    "Current_mA": 0,
    "Flags": "R D S",
    "ProfileID": 0,
    "TimeCharging_sec": 0,
    "TimeCharged_sec": 0,
    "Energy_Wh": 0.0,
    "VID": 0,
    "PID": 0,
    "Manufacturer": "",
    "Description": "",
    "SerialNumber": ""
  },
  "Port.3": ...
}
```

| Output | Description |
|---|---|
| port-number | The number of the port on the hub |
| Current_mA | Current being delivered to the mobile device, in mA (milliamperes) |
| flags | Flags on the port, see Port.N.Flags |
| profile-ID | The profile number, or 0 if not charging. |
| charging-time | Time passed in seconds that a port has been charging a device. |
| charge-complete | Time in seconds since the device completed charging |
| energy-Wh | Power in Watt-hours (calculated every second), format of n.n |
| Vendor-ID | Device Vedor ID number or VID. Displayed as an Integer |
| product-ID | Product ID number or PID. Displayed as an Integer |
| device-manufacturer | The name of the device manufacturer |
| description | Name of the hardware |
| usb-serial | USB serial number |
| phone-serial | Phone serial number |
| phone-name | Name of the phone |
| IMEI-number | The IMEI number of the phone |
| MacAddress | A unique address assigned to the mobile device. It is a 48 bit value, consisting of twelve hexadecimal characters |
| phone-OS-version | Version number of the OS on the phone |
| location-id | The Location IDs as an Integer |
| usb-version | The USB version number of the connection to the hub. Format 'N.nn' |
| battery-data-source | The source of the device battery information |
| trust-level | Whether the device is trusted/ paired |
| support-pairing | Whather the device supports being trusted/ paired |
| battery-health | Battery health shown as a percentage |
| battery-current-level | Current battery level of device displayed as a percentage |
| current-hub-time | The hub time, shown as an integer in ms |
| charge-start-level | Battery percentage level when device connected |
| charge-start-time | The hub time charging started, shown as an integer in ms |
| new-battery-capacity | The battery capacity of device from new |
| current-battery-capacity | The battery capacity of the device now |
| charge-status | Charging status of the battery i.e. full |

**Example**

Trimmed example of information returned.

```json
{
    "jsonrpc": "2.0",
    "id": 0,
    "Port.1": {
        "Port": 1,
        "Current_mA": 126,
        "Flags": "R A S",
        "ProfileID": 0,
        "TimeCharging_sec": 0,
        "TimeCharged_sec": 0,
        "Energy_Wh": 0.0,
        "VID": 1452,
        "PID": 4776,
        "Manufacturer": "SuperPhone Makers Inc.",
        "Description": "SuperPhone",
        "SerialNumber": "012a37d1fa07617ad7ef0430ba49f479ab9fb6b8",
        "PhoneSerialNumber": "ZCZCZCZCZCZC",
        "PhoneIdentity": "My Old SuperPhone",
        "IMEI": "354430099009999",
        "MacAddress": "aa:bb:cc:ff:ee:ff",
        "PhoneSoftwareVersion": "12.4.8",
        "USBTree": {
            "USB2": {
                "LocationID": 589570048,
                "VID": 1452,
                "PID": 4776,
                "Manufacturer": "SuperPhone Makers Inc.",
                "Description": "SuperPhone",
                "SerialNumber": "012a37d1fa07617ad7ef0430ba49f479ab9fb6b8",
                "USBVersion": 2.0,
                "Battery": {
                    "DataSource": "imobiledevice",
                    "TrustLevel": "paired",
                    "PairingSupported": true,
                    "HealthPercent": 95,
                    "CurrentLevel": 100,
                    "CurrentTime": 1613056296,
                    "StartingLevel": 100,
                    "StartingTime": 1613056293,
                    "CapacityNew": 1751,
                    "Capacity": 1678,
                    "ChargingStatus": "full"
                },
                "PhoneSerialNumber": "ZCZCZCZCZCZC",
                "PhoneIdentity": "My Old SuperPhone",
                "IMEI": "354430099009999",
                "MacAddress": "aa:bb:cc:ff:ee:ff",
                "PhoneSoftwareVersion": "12.4.8"
            }
        },
        "Battery": {
            "DataSource": "imobiledevice",
            "TrustLevel": "paired",
            "PairingSupported": true,
            "HealthPercent": 95,
            "CurrentLevel": 100,
            "CurrentTime": 1613056296,
            "StartingLevel": 100,
            "StartingTime": 1613056293,
            "CapacityNew": 1751,
            "Capacity": 1678,
            "ChargingStatus": "full"
        }
    },
    "Port.2": {
        ... (see truncated continuation; document picks up Port.2 example fields on next pages, mirroring the Port.2 stub shown above in the Returns block: Port 2, Current_mA 0, Flags "R D S", ProfileID 0, TimeCharging_sec 0, TimeCharged_sec 0, Energy_Wh 0.0, VID 0, PID 0, Manufacturer "", Description "", SerialNumber "")
    },
    "Port.3": ...
}
```

---

#### Profile.N.enabled

Get information if a specific profile is enabled. See specific product user manuals on profiles available on your hub.

**Feature set:** 5V

**Syntax:** see Call Structure

```json
{
  "method": "cbrx_connection_get",
  "params": [
    connection-handle,
    "Profile.N.enabled"
  ]
}
```

*connection-handle* is the Connection Handles as an integer.

**Returns:**

```json
{
  "result":profile-enabled
}
```

| profile-enabled | Description |
|---|---|
| true | Specific profile is enabled |
| false | Specific profile is not enabled |

**Example**

```json
{
    "jsonrpc": "2.0",
    "id": 0,
    "result": false
}
```

---

#### pwm_percent

Fan speed.

**Feature set:** temperature

**Syntax:** see Call Structure

```json
{
  "method": "cbrx_connection_get",
  "params": [
    connection-handle,
    "pwm_percent"
  ]
}
```

*connection-handle* is the Connection Handles as an integer.

**Returns:**

```json
{
  "result":fan-percent
}
```

*fan-percent* is the fan speed as a percentage, displayed as a number 0-100

**Example**

```json
{
    "jsonrpc": "2.0",
    "id": 0,
    "result": 100
}
```

---

#### Rebooted

A flag indicating if the system has been rebooted since power up.

**Feature set:** base

**Syntax:** see Call Structure

```json
{
  "method": "cbrx_connection_get",
  "params": [
    connection-handle,
    "Rebooted"
  ]
}
```

*connection-handle* is the Connection Handles as an integer.

**Returns:**

```json
{
  "result":rebooted
}
```

| Rebooted | Description |
|---|---|
| true | system has been rebooted |
| false | no reboot has occurred. |

**Example**

```json
{
    "jsonrpc": "2.0",
    "id": 0,
    "result": true
}
```

---

#### SecurityArmed

Is security armed?

**Feature set:** 5V

**Syntax:** see Call Structure

```json
{
  "method": "cbrx_connection_get",
  "params": [
    connection-handle,
    "SecurityArmed"
  ]
}
```

*connection-handle* is the Connection Handles as an integer.

**Returns:**

```json
{
  "result":security-armed
}
```

| security-armed | Description |
|---|---|
| true | Security has been armed |
| false | Security has not been armed |

**Example**

```json
{
    "jsonrpc": "2.0",
    "id": 0,
    "result": false
}
```

---

#### Settings

Obtain current hub Internal hub settings.

**Feature set:** base

**Syntax:** see Call Structure

```json
{
  "method": "cbrx_connection_get",
  "params": [
    connection-handle,
    "Settings",
    true
  ]
}
```

*connection-handle* is the Connection Handles as an integer.

**Returns:**

```json
{
  "result": {
    "company_name": "manufacturer-name",
    "product_name": "product-name",
    "local_name": "local-name",
    "attach_threshold": "attach-threshold",
    "default_profile": [default-profile],
    "remap_ports": [port-order],
    "ports_on": [ports-on],
    "sync_chrg": [sync-charge],
    "alt_sync_chrg": [alt-sync-charge],
    "misc_flags":Internal hub-flags,
    "display_mode": "display-mode",
    "charged_threshold": "charged-threshold",
    "temperature_max": "shutdown-temperature",
    "stagger": "stagger"
  }
}
```

| Variables | Description |
|---|---|
| manufacturer-name | Defined name of manufacturer, Default is 'Cambrionix' |
| product-name | Hardware name of product |
| local-name | Local name set by the user, "-" if not set |
| attach-threshold | Current drawn in mA that the hub detects a device is connected, "d" means factory default is set |
| default-profile | Default profile for each port, comma seperated list |
| port-order | Order the ports are by port number, comma seperated list |
| ports-on | Whether each port is default on, 0 is default off 1 is default on, comma seperated list |
| sync-charge | Whether CDP* on each port, 0 is off, 1 is on, comma seperated list |
| alt-sync-charge | Whether alternative CDP* on each port on, 0 is off, 1 is on, comma seperated list |
| Internal hub-flags | If any Internal hub Misc flags are active |
| display-mode | Change the display mode for logs, "d" means factory default is set |
| charged-threshold | Current drawn in mA that the hub detects a device is fully charged, "d" means factory default is set |
| shutdown-temperature | Temperature that will shutdown the hub if reached in Celsius, "d" means factory default is set |
| stagger | A delay between ports turning on in ms, "d" means factory default is set |

\*Charging Downstream Port (CDP) Being enabled means that a port is capable of transferring data and charging the device at the same time with a higher current than just data syncing alone. With CDP enabled the hub can supply up to 1.5 A

If you disable CDP you will receive the notification "This Hub has the Charge Downstream Port UCS mode disabled. This could limit the maximum current seen on some ports." This notification is there to ensure you haven't turned this off by accident and can still have the highest charge available.

**Example**

```json
{
    "jsonrpc": "2.0",
    "id": 5,
    "result": {
        "company_name": "cambrionix",
        "product_name": "SuperSync15",
        "local_name": "-",
        "attach_threshold": "d",
        "default_profile": [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
        "remap_ports": [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15],
        "ports_on": [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
        "sync_chrg": [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
        "alt_sync_chrg": [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
        "misc_flags": 0,
        "display_mode": "d",
        "charged_threshold": "d",
        "temperature_max": "d",
        "stagger": "d"
    }
}
```

---

#### SystemTitle

The system identification text.

**Feature set:** base

**Syntax:** see Call Structure

```json
{
  "method": "cbrx_connection_get",
  "params": [
    connection-handle,
    "SystemTitle"
  ]
}
```

*connection-handle* is the Connection Handles as an integer.

**Returns:**

```json
{
  "result":system-title
}
```

*system-title* is the full descriptive name of the hub

**Example**

```json
{
    "jsonrpc": "2.0",
    "id": 0,
    "result": "cambrionix U8S-EXT 8 Port USB Charge+Sync"
}
```

---

#### Temperature_C

Present PCB temperature in degrees Celsius.

**Feature set:** temperature

**Syntax:** see Call Structure

```json
{
  "method": "cbrx_connection_get",
  "params": [
    connection-handle,
    "Temperature_C"
  ]
}
```

*connection-handle* is the Connection Handles as an integer.

**Returns:**

```json
{
  "result":temperature
}
```

*temperature* is a measured temperatures as a decimal. ≤ 0 °C will return 0. Measured temperatures ≥100 °C will return 100.

**Example**

```json
{
    "jsonrpc": "2.0",
    "id": 0,
    "result": 37.7
}
```

---

#### Temperature_flags

Temperature error flags:

**Feature set:** temperature

**Syntax:** see Call Structure

```json
{
  "method": "cbrx_connection_get",
  "params": [
    connection-handle,
    "Temperature_flags"
  ]
}
```

*connection-handle* is the Connection Handles as an integer.

**Returns:**

```json
{
  "result":temperature-flags
}
```

| temperature-flags | Description |
|---|---|
| OT | over temperature event has occurred. |
| empty | temperature is acceptable |

**Example**

```json
{
    "jsonrpc": "2.0",
    "id": 0,
    "result": "OT"
}
```

---

#### Temperature_Limit_Max_C

Upper limit of the acceptable temperature range that will trigger the error flag.

**Feature set:** temperature

**Syntax:** see Call Structure

```json
{
  "method": "cbrx_connection_get",
  "params": [
    connection-handle,
    "Temperature_Limit_Max_C"
  ]
}
```

*connection-handle* is the Connection Handles as an integer.

**Returns:**

```json
{
  "result":temperature-limit-max
}
```

*temperature-limit-max* the upper limit in Celsius displayed as a decimal.

**Example**

```json
{
    "jsonrpc": "2.0",
    "id": 0,
    "result": 65.0
}
```

---

#### TemperatureMax_C

Highest PCB temperature recorded in degrees Celsius.

**Feature set:** temperature

**Syntax:** see Call Structure

```json
{
  "method": "cbrx_connection_get",
  "params": [
    connection-handle,
    "TemperatureMax_C"
  ]
}
```

*connection-handle* is the Connection Handles as an integer.

**Returns:**

```json
{
  "result":temperature-max
}
```

*temperature* is a measured temperatures displayed as a decimal. ≤0 °C will return 0. Measured temperatures ≥100 °C will return 100.

**Example**

```json
{
    "jsonrpc": "2.0",
    "id": 0,
    "result": 39.9
}
```

---

#### TotalCurrent_mA

Total current in mA for all USB ports.

**Feature set:** 5V

**Syntax:** see Call Structure

```json
{
  "method": "cbrx_connection_get",
  "params": [
    connection-handle,
    "TotalCurrent_mA"
  ]
}
```

*connection-handle* is the Connection Handles as an integer.

**Returns:**

```json
{
  "result":total-current
}
```

*total-current* is the total current across all ports in mA displayed as a decimal

**Example**

```json
{
    "jsonrpc": "2.0",
    "id": 0,
    "result": 0
}
```

---

#### TotalPower_W

Total power being consumed on all USB ports in Watts (W).

**Feature set:** 5V

**Syntax:** see Call Structure

```json
{
  "method": "cbrx_connection_get",
  "params": [
    connection-handle,
    "TotalPower_W"
  ]
}
```

*connection-handle* is the Connection Handles as an integer.

**Returns**

```json
{
  "result": "total-power"
}
```

*total-power* is the total power across all ports in watts displayed as an decimal.

**Example**

```json
{
    "jsonrpc": "2.0",
    "id": 0,
    "result": 3.4
}
```

---

#### TwelveVoltRail_flags

List of 12V supply rail error flags.

**Feature set:** 12V

**Syntax:** see Call Structure

```json
{
  "method": "cbrx_connection_get",
  "params": [
    connection-handle,
    "TwelveVoltRail_flags"
  ]
}
```

*connection-handle* is the Connection Handles as an integer.

**Returns:**

```json
{
  "result":twelve-volt-flags
}
```

| twelve-volt-flags | Description |
|---|---|
| "UV" | under voltage occurred |
| "OV" | over voltage occurred |
| "OV UV" | both over and under voltage occurred |
| " " | voltage is acceptable |

**Example**

```json
{
    "jsonrpc": "2.0",
    "id": 0,
    "result": " "
}
```

---

#### TwelveVoltRail_Limit_Max_V

Upper limit of the 12V rail that will trigger the error flag.

**Feature set:** 12v

**Syntax:** see Call Structure

```json
{
  "method": "cbrx_connection_get",
  "params": [
    connection-handle,
    "TwelveVoltRail_Limit_Max_V"
  ]
}
```

*connection-handle* is the Connection Handles as an integer.

**Returns:**

```json
{
  "result":twelve-volt-limit-max
}
```

*twelve-volt-limit-max* is the maximum amount of volts before error is flagged in Volts displayed as a decimal.

**Example**

```json
{
    "jsonrpc": "2.0",
    "id": 0,
    "result": 14.5
}
```

---

#### TwelveVoltRail_Limit_Min_V

Lower limit of the 12V rail that will trigger the error flag.

**Feature set:** 12v

**Syntax:** see Call Structure

```json
{
  "method": "cbrx_connection_get",
  "params": [
    connection-handle,
    "TwelveVoltRail_Limit_Min_V"
  ]
}
```

*connection-handle* is the Connection Handles as an integer.

**Returns:**

```json
{
  "result":twelve-volt-limit-min
}
```

*twelve-volt-limit-min* is the minimum amount of volts before error is flagged in Volts displayed as a decimal.

**Example**

```json
{
    "jsonrpc": "2.0",
    "id": 0,
    "result": 9.59
}
```

---

#### TwelveVoltRail_V

Current 12V supply voltage in Volts (V).

**Feature set:** 12V

**Syntax:** see Call Structure

```json
{
  "method": "cbrx_connection_get",
  "params": [
    connection-handle,
    "TwelveVoltRail_V"
  ]
}
```

*connection-handle* is the Connection Handles as an integer.

**Returns:**

```json
{
  "result":twelve-volt
}
```

*twelve-volt* is the amount of volts being supplied in Volts displayed as a decimal.

**Example**

```json
{
    "jsonrpc": "2.0",
    "id": 0,
    "result": 12.43
}
```

---

#### TwelveVoltRailMax_V

Highest 12V supply voltage measured.

**Feature set:** 12V

**Syntax:** see Call Structure

```json
{
  "method": "cbrx_connection_get",
  "params": [
    connection-handle,
    "TwelveVoltRailMax_V"
  ]
}
```

*connection-handle* is the Connection Handles as an integer.

**Returns:**

```json
{
  "result":twelve-volt-max
}
```

*twelve-volt-max* is the highest amount of volts seen in Volts displayed as a decimal.

**Example**

```json
{
    "jsonrpc": "2.0",
    "id": 0,
    "result": 12.52
}
```

---

#### TwelveVoltRailMin_V

Lowest 12V supply voltage measured in Volts (V).

**Feature set:** 12V

**Syntax:** see Call Structure

```json
{
  "method": "cbrx_connection_get",
  "params": [
    connection-handle,
    "TwelveVoltRailMin_V"
  ]
}
```

*connection-handle* is the Connection Handles as an integer.

**Returns:**

```json
{
  "result":twelve-volt-min
}
```

*twelve-volt-min* is the smallest amount of volts seen in Volts displayed as a decimal.

**Example**

```json
{
    "jsonrpc": "2.0",
    "id": 0,
    "result": 12.31
}
```

---

> End of pages 135-236. Section 14.2 "Get Dictionary" continues into the next reference chunk, starting with the `Uptime_sec` entry (the next key after `TwelveVoltRailMin_V` in the dictionary key table above).
