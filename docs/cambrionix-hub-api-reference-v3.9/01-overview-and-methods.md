# Cambrionix Hub API Reference

Community-maintained technical reference generated from the [Cambrionix Hub API User Manual (PDF)](../Cambrionix-Hub-API-User-Manual-v3.9.pdf), covering API v3.9+ (Manual version: 2025-06). Covers pages 1-134: introduction, installation, quick start, API call structure, and API methods 5.1-5.34 (cbrx_apidetails through cbrx_pair_device), plus the start of section 6 (API Notifications), section 7 (Deprecated Methods), section 8 (Device string), section 9 (API Management), section 10 (Additional information), section 11 (Logging), and section 12 (Docks).

Manual version: 2025-06, Cambrionix Ltd.

## 2. Introduction

The Cambrionix Hub API controls Cambrionix products through a locally installed service called `CambrionixApiService`, which sits between the client application and the Cambrionix units and maps unit properties to API commands.

A Python wrapper is provided on top of a public-domain JSON-RPC library, so scripts can be written without needing detailed JSON knowledge. Alternatively, any language can connect directly to the daemon over a standard TCP/IP socket and exchange JSON. When communicating with a remote network-attached hub, this is done over an SSH tunnel.

The API supports multiple simultaneous client connections and concurrent access to numerous hubs.

Latest manual: https://www.cambrionix.com/cambrionix-api

### JSON-RPC library

The API uses JSON-RPC over TCP. JSON-RPC ("JavaScript Object Notation Remote Procedure Call") uses JSON as the data interchange format. Any language with a JSON-RPC library can be used.

## 2.1. Installation

### macOS Installation

An installer sets up `CambrionixApiService` to run as a daemon process, loaded on-demand via `launchd`, with the listening port attached. The installer requires UAC interaction and cannot be run silently. It can also configure installed Python 2 and 3 and point you to example scripts.

### Windows Installation

A self-extracting installer sets up `CambrionixApiService` to run as a Windows service. It requires UAC interaction and cannot be run silently. It can also install/configure Python 2 and 3 and point you to example scripts.

### Linux Installation

The Linux package is a Debian package, installable via GUI or from the command line with apt:

```
sudo dpkg -i /Downloads/cambrionix-api-setup-?????????.deb
```

To run persistently (i.e. on reboot):

```
sudo /usr/bin/CambrionixApiService --install --persistent
```

An armhf version has been tested on oDroid and Raspberry Pi. rpm is not supported directly; see https://fedingo.com/how-to-convert-deb-to-rpm-files-in-linux/ for help converting.

### USB Drivers

Most OSes include the required USB drivers by default. The installer can install them as an optional component (hidden if already present). Driver installation does not complete until a Cambrionix charger is attached for the first time; if the API and USB drivers are installed before ever connecting a charger, the API will not start, and the host machine must be rebooted after first connecting a hub to complete USB driver installation and start the API service correctly.

## 2.2. Prerequisites

### Direct access to USB hardware

The API needs direct access to USB hardware, so it does not work inside VMs (Parallels, VirtualBox, Microsoft Hyper-V), since virtualization prevents determining which USB device is connected to which physical port and may block access to the serial devices needed to query the hub.

### Thunderbolt with Windows

May require updated Thunderbolt Bus Drivers and possibly a BIOS update on Windows. After the Thunderbolt device is accepted, you may need to disconnect/reconnect it for Windows to connect physically.

### Sync capable charger for USB information

Returning USB device information (VID, PID, Manufacturer, Description, Serial Number) requires a USB connection from host to the connected device — present only on sync-capable products. Charge-only products have a USB connection to the charger but not to connected devices; the API still functions with charge-only chargers but cannot return USB device information for downstream devices.

### Version for universal firmware products

Products using the universal firmware must run firmware version 1.52 or later to be used with this API. Use the latest version from the Cambrionix website or Cambrionix Connect.

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

### USB drivers

The API daemon must communicate with the local hub. The hub appears as a USB device accompanied by a virtual communications port (VCP), which behaves like a standard serial/COM port. The OS must have the appropriate VCP driver installed.

| Linux | macOS | Windows |
|---|---|---|
| Default kernel support is sufficient. Do not install D2XX drivers — conflicts with required VCP drivers. | Default OS support is sufficient. Do not install D2XX drivers — conflicts with required VCP drivers. | D2XX support can coexist with VCP support; automatically installed on newer Windows 10 versions. |

### Operating System

Tested and confirmed operating systems (others may work but are untested):

- Windows 10
- Windows 11
- macOS 11 (Big Sur)
- macOS 12 (Monterey)
- macOS 13 (Ventura)
- macOS 14 (Sonoma)
- macOS 15 (Sequoia)
- Linux Ubuntu
- Linux Debian

For Linux, testing is performed only on the OSes listed above. An ARM hard float (armhf) version has also been tested on oDroid and Raspberry Pi.

## 3. Quick start

Example scripts in Node.JS, C#, VB.Net, and Python are included with the installed files. For Python, the newer asyncio example is recommended over the older synchronous examples.

- Windows: `%ProgramFiles%\Cambrionix\CambrionixAPI/examples`
- Linux: `/usr/local/share/cambrionix/apiservice/examples`
- macOS: `/Library/Cambrionix/ApiService/examples`

Per-language prerequisites:

- Python: Python 3.4, plus the `jsonrpc-websocket` module.
- Node.JS: Node.js plus NPM or Yarn.
- C# / VB.Net: Visual Studio.

To install the Python async API package, from `examples/python/asyncio` run:

```
pip install .
```

### 3.1. Python Example

The `jsonrpc-websocket` module automatically converts a Python script call into a JSON-RPC request.

Python:

```python
cbrxapi.cbrx_connection_open("DJ000102")
```

JSON-RPC Translation:

```json
{
  "id": 0,
  "jsonrpc": "2.0",
  "method": "cbrx_connection_open",
  "params": [
    "DJ000102"
  ]
}
```

Replies are automatically converted back from JSON into a Python dictionary, list, or value as appropriate.

Full example (Python 3.6; no error handling — add robust error handling in real code):

```python
# Import the cbrxapi library.
import sys
from cbrxapi import cbrxapi

print("Querying API Version...")
try:
    result = cbrxapi.cbrx_apiversion()
except Exception as e:
    print(f"Could not communicate with API : {e}")
    result = None

if result:
    print(f"API Version {result[0]}.{result[1]}")


# Call cbrx_discover with "local" to find any locally attached Cambrionix
# units.
# This will return a list of local Cambrionix units.
print("Discovering local devices..")
result = cbrxapi.cbrx_discover("local")
if not result or len(result) == 0:
    print("No Cambrionix unit found.")
    sys.exit(0)

print(f"Discovered {len(result)} units")

for unit_id in result:
    serial_port = cbrxapi.cbrx_discover_id_to_os_reference(unit_id)

    try:
        # Open a connection to the Cambrionix unit, which will return a handle
        # for the connection.
        handle = cbrxapi.cbrx_connection_open(unit_id)
    except Exception as e:
        print(f"Could not open connection to {unit_id} : {e}")
        handle = None

    if handle:
        # Using the handle, get the "Hardware" and "nrOfPorts" properties
        hardware = cbrxapi.cbrx_connection_get(handle, "Hardware")
        n_ports = cbrxapi.cbrx_connection_get(handle, "nrOfPorts")

        # Done using the Cambrionix unit, close the handle.
        cbrxapi.cbrx_connection_close(handle)

        # Finally, print out the information retrieved from the Cambrionix
        # unit.
        print(f"* {hardware} on {serial_port} has {n_ports} ports")
```

### 3.2. TypeScript Example

Simple example using TypeScript to obtain information on hubs and devices over a WebSocket.

```typescript
import React from 'react';
import Websocket from 'react-websocket';

class MyApiInterface extends React.Component {
  lastId = 0;

  render() {
    return (
      <Websocket ref={r => this.websocket = r} reconnect
                 url="ws://localhost:43424" protocol="jsonrpc"
                 onMessage={this.onDataReceived.bind(this)}
                 onOpen={this.onApiConnection.bind(this)}
                 onClose={this.onApiDisconnection.bind(this)} />
    );
  }

  requests = {};

  onDataReceived(json) {
    const data = JSON.parse(json);
    const id = data.id;
    if (id) {
      const request = this.requests[id];
      if (request && request.callback) {
        request.callback(data);
      }
      delete this.requests[id];
    }
    else
    {
      //Could get a notification here if you enable them on active connection
      //Notifications have no id and can arrive at any time
    }
  }

  makeRequest(method, params, callback) {
    var packet = {
      jsonrpc: "2.0",
      id:      ++this.lastId,
      method:  method,
      params:  params,
    };

    this.requests[packet.id] = {packet: packet, callback: callback};

    this.websocket.sendMessage(JSON.stringify(packet));
  }

  onApiConnection() {
    console.log("Connected");
    this.makeRequest("cbrx_discover", ["local"], console.log);
  }

  onApiDisconnection() {
    console.log("Disconnected");
    this.requests = {}
  }
}
```

### 3.3. HTTP GET Example

Connections can be made directly to an http-prefixed URI; JSON is extracted from either the address itself or the body content of the GET request. Try in a browser or via curl:

```
curl -get http://localhost:43424/?{\"id\":0,\"json-rpc\":\"2.0\",\"method\":\"cbrx_discover\",\"params\":[\"all\"]}
```

Socket connections can be simple binary data, HTTP GET requests, or WebSockets (such as from Node.js). Pasting the following into a browser address bar should give quick results:

```
http://localhost:43424/?{"jsonrpc":"2.0","id":1,"method":"cbrx_discover","params":["all"]}
```

On some Terminal/Command Prompt environments the URL may need encoding to avoid errors. Once encoded, the URL should look like:

```
http://localhost:43424/%7B%22jsonrpc%22:%222.0%22,%22id%22:0,%22method%22:%22cbrx_apidetails%22%7D
```

### 3.4. Error Handling

A JSON-RPC error response contains an `error` member with the following members:

- `code` (mandatory) - an integer indicating either a pre-defined JSON-RPC error code (range -32768 to -32000) or a CBRXAPI error code (documented in the CBRXAPI specific errors section).
- `message` (optional) - a message string explaining the error code.
- `data` (optional) - extra information about the error, such as debug messages or handles.

The Python JSON-RPC library used raises an exception for an error response, with this mapping:

- member `code` → `e.error_code`
- member `message` → `e.error_message`
- member `data` → `e.error_data`

Catching an error response:

```python
try:
    handle = cbrxapi.cbrx_connection_open(id)
except jsonrpc.RPCFault as e:
    gotException = True
    errorCode = e.error_code
    errorMessage = e.error_message
    errorData = e.error_data
```

Example error request and response:

```json
{
  "jsonrpc": "2.0",
  "id": 0,
  "method": "cbrx_connection_open",
  "params": [
    "0"
  ]
}
```

Response:

```json
{
  "jsonrpc": "2.0",
  "id": 0,
  "error": {
    "code": -10001,
    "message": "ID not found"
  }
}
```

## 4. API Call Structure

The descriptions of API calls in this reference contain JSON-RPC requests/responses as seen on the wire.

### 4.1. JSON-RPC request object

JSON-RPC is a stateless, light-weight RPC protocol. A Request object has the following members:

| Member | Description |
|---|---|
| `jsonrpc` | String specifying the JSON-RPC protocol version. MUST be exactly `"2.0"`. |
| `id` | An identifier established by the client; MUST be a String, Number, or NULL if included. If omitted, the request is assumed to be a notification. |
| `method` | A String containing the name of the method to invoke. |
| `params` | A structured value holding the parameters for the method invocation. Not required for every method. |

Complete JSON-RPC request:

```json
{
    "jsonrpc": "version",
    "id": 0,
    "method": "method-name",
    "params": [
        "structured-params"
    ]
}
```

### 4.2. JSON-RPC response object

A Response is returned for every RPC call except Notifications, expressed as a single JSON object with:

| Member | Description |
|---|---|
| `jsonrpc` | String specifying the JSON-RPC protocol version. MUST be exactly `"2.0"`. |
| `id` | Same value as the `id` member in the Request object. |
| `result` | Value determined by the method in the Request object. |
| `error` | Returned only on error. |

Complete JSON-RPC response:

```json
{
    "jsonrpc": "version",
    "id": 0,
    "result": "method-result"
}
```

### 4.3. JSON-RPC Error Object

When a call encounters an error, the Response Object's `error` member is an Object with:

| Member | Description |
|---|---|
| `code` | A Number (integer) indicating the error type that occurred. |
| `message` | A String providing a short description of the error. |
| `data` | A Primitive or Structured value with additional information about the error. |

Complete JSON-RPC error response:

```json
{ "jsonrpc": "version", "id": 0, "error": { "code": "error-code",
        "message": "error-message" } }
```

### 4.4. Call Structure

Note: the version/id pair has been removed from the Syntax and Return sections throughout this manual to simplify documentation. Two further key-value pairs must still be included in the actual JSON request: the JSON-RPC version (`"2.0"`) and an `id` identifying the request.

The `id` is mandatory but only relevant if multiple requests can be outstanding simultaneously over the same connection; it helps match responses to (asynchronous) requests. `CambrionixApiService` returns the matching `id` in the response.

```json
{
    "jsonrpc": "2.0",
    "id": 0
}
```

## 5. API Methods

There are 3 groups of calls in the API:

- **Version** - Obtain details about the API
- **Discovery** - Obtain details about what is connected to the API
- **Connection** - Manage connections and devices connected

### Version

| API Call | Description |
|---|---|
| `cbrx_apiversion` | Obtain the version of the API |
| `cbrx_apidetails` | Obtain an enhanced version of the details of the API |

### Discovery

| API Call | Description |
|---|---|
| `cbrx_discover` | Discover Cambrionix units |
| `cbrx_discover_id_to_os_reference` | Map a unit ID from unit to device as used by the OS |
| `cbrx_find` | Search for devices attached to local Cambrionix units |
| `cbrx_get_usb (tree)` | Return the entire USB tree that has been discovered |
| `cbrx_get_usb (descriptors)` | Request entire dump of a USB device's descriptor information |
| `cbrx_config_set` | Set configuration options |

### Connection

| API Call | Description |
|---|---|
| `cbrx_certificate` | Manage certificates and private keys to the API |
| `cbrx_connection_open` | Open a connection to a hub |
| `cbrx_connection_close` | Close an open connection to a hub |
| `cbrx_connection_getdictionary` | Get all keys on a hub specified by the connectionHandle. |
| `cbrx_connection_get` | Get a key from a hub specified by connectionHandle |
| `cbrx_hub_get` | Get a key from a hub specified by hubs serial number |
| `cbrx_device_get` | Get a key from a hub specified by USB device's serial number |
| `cbrx_connection_setdictionary` | List all writeable and command keys for the hub specified by connectionHandle |
| `cbrx_connection_set` | Set a key to the value specified on a hub specified by connectionHandle |
| `cbrx_hub_set` | Set a key to the value specified on a hub specified by hubs serial number |
| `cbrx_notifications` | Send notifications |
| `cbrx_firmware` | Add or remove firmware files |
| `cbrx_connection_closeandlock` | Close all connections to a hub and lock it |
| `cbrx_connection_unlock` | Unlock a hub that was previously locked. |
| `cbrx_connection_cli` | Perform command line interface operation |
| `cbrx_pair_device` | Initiate pairing of an iOS device |
| `cbrx_exit` | Restart the API |

### 5.1. cbrx_apidetails

Returns an enhanced version of the details of the API. This information can also be gained by passing an optional `true` parameter to `cbrx_apiversion`.

Syntax:

```json
{
  "method": "cbrx_apidetails"
}
```

Returns:

```json
{
  "result": {
    "version": [version-number],
    "semver": "semver-variant",
    "commitid": commitid-number,
    "branch": "branch-name",
    "capability": [API-capability],
    "notifications": [possible-notification],
    "install": "install-location",
    "logging": "logs-location",
    "settings": "settings-location",
    "documentation": "documentation-location",
    "cpu": {
      "brand": "brand-information",
      "arch": "CPU-architecture",
      "features": [CPU-features],
      "cores": cores-value
    },
    "os": "OS-information"
  }
}
```

| Output | Description |
|---|---|
| version-number | Version number of API as an integer (Major,Minor,Revision,Build) |
| semver-variant | The full name of the API version |
| commitid-number | The number value of the Commit ID |
| branch-name | The branch of API installed |
| API-capability | available with version of API |
| possible-notification | Array of strings to show possible notification. see API Notifications |
| install-location | The location of install files |
| logs-location | The location of where logs are stored |
| settings-location | The location of API settings |
| documentation-location | The web address of API documentation |
| brand-information | The brand of the CPU |
| CPU-architecture | The architecture of the CPU |
| CPU-features | Features available on CPU |
| cores-value | How many cores the CPU has |
| OS-information | Operating system running on local machine |

Example JSON-RPC request:

```json
{
  "jsonrpc": "2.0",
  "id": 0,
  "method": "cbrx_apidetails"
}
```

Example successful response:

```json
{
  "jsonrpc": "2.0",
  "id": 0,
  "result": {
    "version": [
      3,
      7,
      0,
      34
    ],
    "semver": "3.7.0+34",
    "guid": {
      "id": "d0dc3cac-e165-4e38-88bb-39064431bdc9",
      "computerId": "35aea4bc-44d3-4e9e-9b3c-c33b965c5639"
    },
    "host": [
      {
        "ip": "10.167.111.81",
        "port": 0,
        "nameServer": "10.167.111.241",
        "domainName": "CBRX.LOCAL",
        "hostName": "CBRXPC-011",
        "adapterName": "Intel(R) Ethernet Controller (3) I225-V",
        "adapterType": "Ethernet"
      }
    ],
    "commitid": 4287981321,
    "branch": "release",
    "capability": [
      "protobuf",
      "crash-report",
      "notification"
    ],
    "notifications": [
      "usb-changed",
      "usb-device-attached",
      "usb-device-detached",
      "discover-changed",
      "dead-hub-changed",
      "firmware-progress",
      "rfid-received",
      "rfid-removed",
      "over-temperature",
      "over-voltage",
      "under-voltage",
      "certificate-changed"
    ],
    "install": "C:\\Program Files\\Cambrionix\\API",
    "logging": "C:\\ProgramData\\Cambrionix\\Log",
    "settings": "C:\\ProgramData\\Cambrionix",
    "documentation": "C:\\Program Files\\Cambrionix\\API\\Cambrionix Hub API Reference.html",
    "cpu": {
      "brand": "12th Gen Intel(R) Core(TM) i9-12900K",
      "arch": "x64",
      "features": [
        "aes", "avx", "avx2", "bmi1", "bmi2", "clflushopt", "clfsh", "clwb",
        "cx16", "cx8", "erms", "f16c", "fma3", "fpu", "mmx", "movbe",
        "pclmulqdq", "popcnt", "rdrnd", "rdseed", "sha", "smx", "ss", "sse",
        "sse2", "sse3", "sse4_1", "sse4_2", "ssse3", "tsc", "vaes",
        "vpclmulqdq"
      ],
      "cores": 24
    },
    "os": "Windows 10 Pro 21H2 Build 19044.1889 64-bit"
  }
}
```

### 5.2. cbrx_apiversion

Return the version of the API running. There is another method which can be used, see `cbrx_apidetails` for more information.

Syntax:

```json
{
  "method": "cbrx_apiversion"
}
```

Returns:

```json
{
  "result": [Version-number]
}
```

`Version-number` consists of two numbers separated by commas. The leftmost number is called the major, the rightmost number is called the minor.

Errors: If there is an error in the API method then a JSON-RPC Error Object will be returned.

Example JSON-RPC request:

```json
{
  "jsonrpc": "2.0",
  "id": 0,
  "method": "cbrx_apiversion"
}
```

Example successful response:

```json
{
  "jsonrpc": "2.0",
  "id": 0,
  "result": [
    3,
    7
  ]
}
```

### 5.3. cbrx_certificate

Supply (or remove) a certificate and private key to the API to allow SSL connections from outside of localhost (the machine the API is running on). Without this certificate, the API will only listen for connections on `localhost:43424`. Once a valid certificate and private key are provided, this changes to `0.0.0.0:43424`. External connections (not from localhost) will only be allowed if they are SSL connections (HTTPS or Secure WebSockets).

The API does not make a copy of the certificate or private key, as this could violate security if they are in limited access folders — the API will need access to the files to be able to use them. This is tested when the "set" command is issued and should provide sufficient error information if it does not work.

It is up to the user to supply a certificate suitable for their usage. If not signed by a certificate authority, you will need to deal with this in the usual way, such as signing your own certificate authority and adding that to your application/browser.

Only a single certificate configuration is supported. If a password is supplied, it is obfuscated for security.

### 5.4. cbrx_certificate (set)

Supply a certificate and private key to the API.

Syntax:

```json
{
  "method": "cbrx_certificate",
  "params": [
    "set",{
      "private-key": key-filename,
      "certificate": certificate-filename,
      "password": password
    }
  ]
}
```

| Parameter | Description |
|---|---|
| key-filename | The filename including the path of the private key |
| certificate-filename | The filename including the path of the certificate |
| password | optional password if required by private key |

Returns:

```json
{
  "result": true
}
```

Errors: If there is an error in the API method then a JSON-RPC Error Object will be returned.

Notes: The files will need to be stored in a location that is accessible by the system and API.

Example JSON-RPC request:

```json
{
  "jsonrpc": "2.0",
  "id": 0,
  "method": "cbrx_certificate",
  "params": [
    "set",
    {
      "private-key": "C:\\git\\capi\\cbrxjson\\certificate\\key.pem",
      "certificate": "C:\\git\\capi\\cbrxjson\\certificate\\cert.pem"
    }
  ]
}
```

Example successful response:

```json
{
  "jsonrpc": "2.0",
  "id": 0,
  "result": true
}
```

### 5.5. cbrx_certificate (remove)

Remove the certificate and private key from the API:

Syntax:

```json
{
  "method": "cbrx_certificate",
  "params": ["remove"]
}
```

Returns:

```json
{
  "result": true
}
```

Errors: If there is an error in the API method then a JSON-RPC Error Object will be returned.

Example JSON-RPC request:

```json
{
  "jsonrpc": "2.0",
  "id": 0,
  "method": "cbrx_certificate",
  "params": [
    "remove"
  ]
}
```

Example successful response:

```json
{
  "jsonrpc": "2.0",
  "id": 0,
  "result": true
}
```

### 5.6. cbrx_certificate (get)

Get the supplied certificate and private key information from the API.

Syntax:

```json
{
  "method": "cbrx_certificate",
  "params": "get"
}
```

Returns:

```json
"result": {
  "certificate": "Certificate",
  "subject": {
    "C": "Country",
    "L": "Location",
    "O": "Organisation",
    "CN": "Common name"
  },
  "issuer": {
    "C": "Country",
    "O": "Organisation",
    "CN": "Common name"
  },
  "serial_number": "Serial number",
  "algorithm": "Algorithm",
  "extensions": {
    "subjectAltName": [Alternative names]
  },
  "validity": {
    "not_after": Vaild until,
    "not_before": Valid from
  }
}
```

| Variable | Description |
|---|---|
| Certificate | The public certificate in its entirety |
| Country | Country code |
| Location | Specific Location company is registered |
| Organisation | The organisations name |
| Common name | The name the organisation is referred to in the certificate |
| Serial number | Used to uniquely identify the certificate within a CA's systems |
| Algorithm | This contains a hashing algorithm and a digital signature algorithm. For example "sha256RSA" where sha256 is the hashing algorithm and RSA is the signature algorithm |
| Alternative names | All names associated with the certificate |
| Valid until | The time and date past which the certificate is no longer valid |
| Valid from | The earliest time and date on which the certificate is valid |

Errors: If there is an error in the API method then a JSON-RPC Error Object will be returned.

Example JSON-RPC request:

```json
{
  "jsonrpc": "2.0",
  "id": 0,
  "method": "cbrx_certificate",
  "params": "get"
}
```

Example successful response:

```json
{
  "jsonrpc": "2.0",
  "id": 0,
  "result": {
    "certificate": "-----BEGIN CERTIFICATE-----\r\D....CF7ig==\r\n-----END CERTIFICATE-----\r\n",
    "subject": {
      "C": "GB",
      "L": "Cambridge",
      "O": "Cambrionix Limited",
      "CN": "*.api.cambrionix.com"
    },
    "issuer": {
      "C": "US",
      "O": "DigiCert Inc",
      "CN": "DigiCert TLS RSA SHA256 2020 CA1"
    },
    "serial_number": "096...9BFBE",
    "algorithm": "sha256WithRSAEncryption",
    "extensions": {
      "subjectAltName": [
        "*.api.cambrionix.com",
        "api.cambrionix.com"
      ]
    },
    "validity": {
      "not_after": 169...99,
      "not_before": 16...400
    }
  }
}
```

### 5.7. cbrx_config_set

Allows setting persistent configuration options. Multiple configuration keys can be set at once.

Syntax:

```json
{
  "method": "cbrx_config_set",
  "params": {
    "configuration-key": configuration-value
  }
}
```

| Parameter | Description |
|---|---|
| configuration-key | The configuration key you wish to change, as per table below. |
| configuration-value | The value you wish to change the configuration to. |

| Configuration-key | Description |
|---|---|
| adb_path | The full pathname to the ADB executable from Android Developer Tools. |
| battery-update-enabled | Will the battery update be performed at all. |
| battery-updated-concurrency | How many concurrent battery updates will be run simultaneously. |
| battery-update-frequence-seconds | How many seconds between battery updates. |

Returns:

```json
{
  "result": true
}
```

Errors: If there is an error in the API method then a JSON-RPC Error Object will be returned.

Example JSON-RPC request:

```json
{
  "jsonrpc": "2.0",
  "id": 0,
  "method": "cbrx_config_set",
  "params": {
    "battery-update-enabled": true,
    "battery-update-concurrency": 2,
    "battery-update-frequency-seconds": 60
  }
}
```

Example successful response:

```json
{
  "jsonrpc": "2.0",
  "id": 0,
  "result": true
}
```

### 5.8. cbrx_connection_cli

Perform command line interface operation on the connected hub and return the complete result. This allows you to run commands directly on the hub's command line without stopping the API service. This method is only for using the CLI commands to obtain information and not update settings; if you wish to change the internal hub settings use the Settings command.

Syntax:

```json
{
  "method": "cbrx_connection_cli",
  "params": [
    connection-handle,
    cli-command
  ]
}
```

| Parameter | Description |
|---|---|
| connection-handle | The Connection Handles as an integer |
| cli-command | The CLI command you wish to send. For all CLI commands see the CLI Documentation www.cambrionix.com/cambrionix-cli |

Returns:

```json
{
  "result": [cli-response]
}
```

`cli-response` is an array of strings containing all the lines of output returned from the command. For more information see www.cambrionix.com/cli

Example JSON-RPC request:

```json
{
  "jsonrpc": "2.0",
  "id": 0,
  "method": "cbrx_connection_cli",
  "params": [
    7654,
    "id"
  ]
}
```

Example successful response:

```json
{
  "jsonrpc": "2.0",
  "id": 0,
  "result": ["mfr:cambrionix,mode:main,hw:PP15S,hwid:0x13,fw:1.83,bl: 0.12,s-n:000000,group:-,fc:un"]
}
```

### 5.9. cbrx_connection_close

Close a connection to a hub previously opened, as specified by the connection handle.

Syntax:

```json
{
  "method": "cbrx_connection_close",
  "params": [connection-handle]
}
```

`connection-handle` is the Connection Handles as an integer.

Returns:

```json
{
  "result": true
}
```

Errors: If there is an error in the API method then a JSON-RPC Error Object will be returned.

Example JSON-RPC request:

```json
{
  "jsonrpc": "2.0",
  "id": 0,
  "method": "cbrx_connection_close",
  "params": [
    7654
  ]
}
```

Example successful response:

```json
{
  "jsonrpc": "2.0",
  "id": 0,
  "result": true
}
```
### 5.10. cbrx_connection_closeandlock

Close all connections to a hub and lock it against further use until released by `cbrx_connection_unlock`. Other processes that were using these connections will get errors returned if trying to access this hub.

Syntax:

```json
{
  "method": "cbrx_connection_closeandlock",
  "params": [hub-serial]
}
```

`hub-serial` is a string which is the serial number of the hub.

Returns:

```json
{
  "result": true
}
```

Errors: If there is an error in the API method then a JSON-RPC Error Object will be returned.

Example JSON-RPC request:

```json
{
  "jsonrpc": "2.0",
  "id": 0,
  "method": "cbrx_connection_closeandlock",
  "params": [
    "DB0074F5"
  ]
}
```

Example successful response:

```json
{
  "jsonrpc": "2.0",
  "id": 0,
  "result": true
}
```

### 5.11. cbrx_connection_get

From the hub specified by the connection handle, get the key value.

Syntax:

```json
{
  "method": "cbrx_connection_get",
  "params": [
    connection-handle,
    "dictionary-key"
  ]
}
```

| Parameter | Description |
|---|---|
| `connection-handle` | The Connection Handles as an integer |
| `dictionary-key` | As returned by a call to `cbrx_connection_getdictionary`. See Get Dictionary for more information |

Returns:

```json
{
  "result": dictionary-value
}
```

`dictionary-value` is the value of the dictionary key, see Get Dictionary for more information.

Example JSON-RPC request:

```json
{
  "jsonrpc": "2.0",
  "id": 0,
  "method": "cbrx_connection_get",
  "params": [
    569,
    "nrOfPorts"
  ]
}
```

Example successful response:

```json
{
  "jsonrpc": "2.0",
  "id": 0,
  "result": 10
}
```

### 5.12. cbrx_connection_getdictionary

Get all keys that can return information on the hub specified.

Syntax:

```json
{
  "method": "cbrx_connection_getdictionary",
  "params": [connection-handle]
}
```

`connection-handle` is the Connection Handles as an integer.

Returns:

```json
{
  "result": [dictionary]
}
```

`dictionary` is an array of strings containing the names of the keys and values for the device. Please see Get Dictionary section.

Example JSON-RPC request:

```json
{
  "jsonrpc": "2.0",
  "id": 0,
  "method": "cbrx_connection_getdictionary",
  "params": [
    7654
  ]
}
```

Example successful response:

```json
{
  "jsonrpc": "2.0",
  "id": 0,
  "result": ["nrOfPorts", "SerialNumber"]
}
```

### 5.13. cbrx_connection_open

Open a connection to the hub specified. A successful open results in a connection handle that can be used for further calls.

Syntax:

```json
{
  "method": "cbrx_connection_open",
  "params": [
    hub-serial,
    location
  ]
}
```

| Parameter | Description |
|---|---|
| `hub-serial` | This is the serial number of the hub returned from `cbrx_discover` |
| `location` | `local` (default) or `docks`. See below. |

| Location | Description |
|---|---|
| `local` | connect to the local hub |
| `docks` | connect to a hub in a Docks (ID found from `cbrx_discover`) |

Returns:

```json
{
  "result": connection-handle
}
```

`connection-handle` is the Connection Handles as an integer.

Example JSON-RPC request:

```json
{
  "jsonrpc": "2.0",
  "id": 0,
  "method": "cbrx_connection_open",
  "params": [
    "DB0074F5"
  ]
}
```

Example successful response:

```json
{
  "jsonrpc": "2.0",
  "id": 0,
  "result": 579
}
```

### 5.14. cbrx_connection_set

On the hub specified by the connection handle, set the key value. Calls to a dock will result in the relevant key being set on both the chargers except for the port specific keys which will be directed to the appropriate charger only.

Syntax:

```json
{
  "method": "cbrx_connection_set",
  "params": [
    connection-handle,
    "dictionary-key",
    Value
  ]
}
```

| Parameter | Description |
|---|---|
| `connection-handle` | The Connection Handles as an integer |
| `dictionary-key` | As returned by a call to `cbrx_connection_setdictionary`. See Set Dictionary for more information |
| `Value` | The value you wish to set the key to |

Returns:

```json
{
  "result": true
}
```

Example JSON-RPC request:

```json
{
  "jsonrpc": "2.0",
  "id": 0,
  "method": "cbrx_connection_set",
  "params": [
    5313,
    "TwelveVoltRail.OverVoltage",
    true
  ]
}
```

Example successful response:

```json
{
  "jsonrpc": "2.0",
  "id": 0,
  "result": true
}
```

### 5.15. cbrx_connection_setdictionary

List all writeable value keys and command keys for the hub specified by Connection Handles.

Syntax:

```json
{
  "method": "cbrx_connection_setdictionary",
  "params": [connection-handle]
}
```

`connection-handle` is the Connection Handles as an integer.

Returns:

```json
{
  "result": [dictionary]
}
```

`dictionary` is an array of strings containing the names of the writeable keys and command keys for the device. Please see Set Dictionary section.

Example JSON-RPC request:

```json
{
  "jsonrpc": "2.0",
  "id": 0,
  "method": "cbrx_connection_setdictionary",
  "params": [
    7654
  ]
}
```

Example successful response:

```json
{
  "jsonrpc": "2.0",
  "id": 0,
  "result": ["Port.1.mode", "Reboot"]
}
```

### 5.16. cbrx_connection_unlock

Unlock a hub that was previously locked.

Syntax:

```json
{
  "method": "cbrx_connection_unlock",
  "params": [hub-serial]
}
```

`hub-serial` is a string which is the serial number of the hub.

Returns:

```json
{
  "result": true
}
```

Example JSON-RPC request:

```json
{
  "jsonrpc": "2.0",
  "id": 0,
  "method": "cbrx_connection_unlock",
  "params": [
    "DB0074F5"
  ]
}
```

Example successful response:

```json
{
  "jsonrpc": "2.0",
  "id": 0,
  "result": true
}
```

### 5.17. cbrx_device_get

From the hub specified by the serial number, get the key value. Similar to `cbrx_connection_get`. Only keys that are relevant to ports are accepted. Note that this is slower than other methods if you need to do multiple operations on the same device.

Syntax:

```json
{
  "method": "cbrx_device_get",
  "params": [
    usb-serial,
    dictionary-key
  ]
}
```

| Parameter | Description |
|---|---|
| `usb-serial` | USB serial number |
| `dictionary-key` | As returned by a call to `cbrx_connection_getdictionary`. See Get Dictionary for more information |

Returns:

```json
{
  "result": dictionary-value
}
```

Example JSON-RPC request:

```json
{
  "jsonrpc": "2.0",
  "id": 0,
  "method": "cbrx_device_get",
  "params": [
    "0000802000184C390CD2002E",
    "USBSpeed"
  ]
}
```

Example successful response:

```json
{
  "jsonrpc": "2.0",
  "id": 0,
  "result": "High"
}
```

### 5.18. cbrx_discover

Discover Cambrionix units, obtain hub serial number.

Syntax:

```json
{
  "method": "cbrx_discover",
  "params": [unit]
}
```

| Unit parameter | Description |
|---|---|
| `local` | Unit ID for hub attached |
| `docks` | Unit IDs for multiple hubs connected together and attached |

Returns:

```json
{
  "result": [hub-serial]
}
```

Example JSON-RPC request:

```json
{
  "jsonrpc": "2.0",
  "id": 0,
  "method": "cbrx_discover",
  "params": [
    "local"
  ]
}
```

Example successful response:

```json
{
  "jsonrpc": "2.0",
  "id": 0,
  "result": [
    "000000897FD0505A"
  ]
}
```

### 5.19. cbrx_discover ("all")

Discover all units and return detailed information about the hubs and their connected devices. Note that only devices that show up in a USB scan will be included. Unlike the other discovery methods, instead of an array of serial numbers, it will be an object of serial numbers with contents.

Syntax:

```json
{
  "method": "cbrx_discover",
  "params": ["all"]
}
```

Returns:

```json
{
  "result": {
    "hub-serial": {
      "Status": "status",
      "Manufacturer": "manufacturer-name",
      "Firmware": "firmware-version",
      "Bootloader": "bootloader-version",
      "SerialNumber": "hub-serial",
      "Group": "group-order",
      "FormFactor": "firmware-type",
      "PanelID": hardware-id,
      "Hardware": "product-name",
      "HostSerialPort": "serial-port",
      "USBVersion": usb-version,
      "LocationID": location-ID,
      "nrOfPorts": port-quantity,
      "ExtPSU": external-PSU,
      "Uptime_sec": runtime,
      "Rebooted": reboot-flag,
      "SyncSupported": sync-possible,
      "FiveVolt": 5V-present,
      "TwelveVolt": 12V-present,
      "TemperatureMonitoring": temp-possible,
      "HardwareFlags": "hardware-flags",
      "Devices": {device-string}
    }
  }
}
```

| Output | Description |
|---|---|
| `hub-serial` | Serial number of the hub |
| `status` | Whether there is a serial port open, see Status |
| `manufacturer-name` | Defined name of manufacturer, Default is 'Cambrionix' |
| `firmware-version` | Version number of the firmware. Format 'N.nn' |
| `bootloader-version` | Version number of the bootloader. Format 'N.nn' |
| `group-order` | Used to order hubs for updates |
| `firmware-type` | Denotes which firmware the product accepts |
| `hardware-id` | Hardware ID number of front panel product |
| `product-name` | Hardware name of product |
| `serial-port` | The Serial port the product is connected to |
| `usb-version` | The USB version number. Format 'N.nn' |
| `location-ID` | The Location IDs as an Integer |
| `port-quantity` | How many ports the product has |
| `external-psu` | Whether the product has an external power supply unit |
| `runtime` | How long the product has been powered (in ms) |
| `reboot-flag` | Whether the reboot flag is true or false |
| `sync-possible` | Whether the product is capable of sync |
| `5V-present` | Whether the product has 5V supplied |
| `12V-present` | Whether the product has 12V supplied |
| `temp-possible` | Whether the product can monitor temperature |
| `hardware-flags` | Hardware flags as detailed in Get Dictionary |
| `device-string` | Information from connected devices, see Device string |

Example JSON-RPC request:

```json
{
  "jsonrpc": "2.0",
  "id": 0,
  "method": "cbrx_discover",
  "params": [
    "all"
  ]
}
```

Example successful response:

```json
{
  "jsonrpc": "2.0",
  "id": 0,
  "result": {
    "000000897FD0505A": {
      "Status": "active",
      "Manufacturer": "cambrionix",
      "Firmware": "1.88.0",
      "Bootloader": "0.21",
      "SerialNumber": "000000897FD0505A",
      "Group": "-",
      "FormFactor": "un",
      "PanelID": 48,
      "Hardware": "SuperSync15",
      "HostSerialPort": "COM3",
      "USBVersion": 2.1,
      "LocationID": 574750720,
      "USB3CompanionLocationID": 2723151872,
      "HostPortLocationID": 574771200,
      "nrOfPorts": 15,
      "ExtPSU": true,
      "Uptime_sec": 167551,
      "Rebooted": true,
      "SyncSupported": true,
      "FiveVolt": true,
      "TwelveVolt": true,
      "TemperatureMonitoring": true,
      "HardwareFlags": "SLET",
      "Devices": {}
    }
  }
}
```

### 5.20. cbrx_discover_id_to_os_reference

Map a unit ID for a discovered hub to a device name as used by the OS. This can only be used for locally attached Cambrionix products.

Syntax:

```json
{
  "method": "cbrx_discover_id_to_os_reference",
  "params": ["hub-serial"]
}
```

`hub-serial` is a string which is the serial number of the hub.

Returns:

```json
{
  "result": "device-name"
}
```

`device-name` is what the OS uses for the connection. For more information please see Serial port.

Example JSON-RPC request:

```json
{
  "jsonrpc": "2.0",
  "id": 0,
  "method": "cbrx_discover_id_to_os_reference",
  "params": [
    "DB0074F5"
  ]
}
```

Example successful response:

```json
{
  "jsonrpc": "2.0",
  "id": 0,
  "result": "COM9"
}
### 5.21. cbrx_exit

Restart the API.

Syntax:

```json
{
  "method": "cbrx_exit"
}
```

Returns:

```json
{
  "result": true
}
```

Example JSON-RPC request:

```json
{
  "jsonrpc": "2.0",
  "id": 0,
  "method": "cbrx_exit"
}
```

Example successful response:

```json
{
  "jsonrpc": "2.0",
  "id": 0,
  "result": true
}
```

### 5.22. cbrx_find

Search for devices attached to local Cambrionix units.

Syntax:

```json
{
  "method": "cbrx_find",
  "params": [ID]
}
```

`ID` can be any of the following forms:

| ID Parameter | Description |
|---|---|
| `VID` | Search for any devices matching the vendor ID. (Integer) |
| `VID & PID` | Search for devices exactly matching the vendor and product IDs. (Integer) |
| `NAME` | Search for anything that matches the provided regex. The regex is run against a string made up of the manufacturer, product name, and USB serial number: `"<manufacturer-name>\x1D<product-name>\x1D<serial-number>"`. Matches substrings by default. |

Returns:

```json
{
  "result": {
    "usb-serial": {
      "HostDevice": "hub-serial",
      "HostPort": device-port,
      "HostDescription": "product-name",
      "HostSerial": "serial-port",
      "Device": { ... }
    }
  }
}
```

| Output | Description |
|---|---|
| `usb-serial` | The serial number of the device |
| `hub-serial` | The serial number of the hub returned from `cbrx_discover` |
| `device-port` | Port number of the hub the device is attached to |
| `product-name` | Hardware name of product |
| `serial-port` | The Serial port the product is connected to |
| `Device` | Information from connected devices, see Device string |

The entire USB tree is searched. If found beneath a Cambrionix hub, the connection details are returned. Useful for devices behind intermediate hubs. Results without a USB serial are grouped under an additional entry `NoSerial` (an array).

Example JSON-RPC request:

```json
{
  "jsonrpc": "2.0",
  "id": 0,
  "method": "cbrx_find",
  "params": [
    "i(Phone|Pad)"
  ]
}
```

Example successful response:

```json
{
  "jsonrpc": "2.0",
  "id": 0,
  "result": {
    "974a9d1e6848316264a8a9d8b094b7d5e63a7ae5": {
      "HostDevice": "60003",
      "HostPort": 2,
      "HostDescription": "TS3-C10",
      "Device": {
        "VID": 1452,
        "PID": 4779,
        "Manufacturer": "Apple Inc.",
        "Description": "iPad",
        "SerialNumber": "974a9d1e6848316264a8a9d8b094b7d5e63a7ae5",
        "DeviceType": "Apple",
        "LocationID": 856686592,
        "USBVersion": 2,
        "Battery": {
          "TrustLevel": "paired",
          "CurrentLevel": 100,
          "ChargingStatus": "full",
          "HealthPercent": 98
        }
      }
    }
  }
}
```

### 5.23. cbrx_firmware

Control all aspects of updating firmware on Cambrionix hubs. Sub-commands allow adding/removing files, listing available files, updating, and checking status.

Firmware types:
- `un`: Universal
- `pd`: PDSync
- `st`: TS3-C10
- `mc`: Motor control board

Syntax:

```json
{
  "method": "cbrx_firmware",
  "params": [firmware-call]
}
```

| firmware-call | Description |
|---|---|
| `add` | Provide firmware to the API as a source. See `cbrx_firmware (add)` |
| `remove` | Remove firmware from being available. See `cbrx_firmware (remove)` |
| `list` | List all available firmware. See `cbrx_firmware (list)` |
| `update` | Start the firmware update. See `cbrx_firmware (update)` |
| `status` | Get the status of the update. See `cbrx_firmware (status)` |

### 5.24. cbrx_firmware (add)

Adds a firmware file to the API local storage. Requires a Base64 encoded zip of the file.

Syntax:

```json
{
  "method": "cbrx_firmware",
  "params": [
    "add",
    "filename",
    "encoded-Bytes"
  ]
}
```

| Parameter | Description |
|---|---|
| `filename` | The name of the firmware file |
| `encoded-Bytes` | The encoded zip of the file in Base64 |

Returns:

```json
{
  "result": true
}
```

Example JSON-RPC request:

```json
{
  "jsonrpc": "2.0",
  "id": 0,
  "method": "cbrx_firmware",
  "params": [
    "add",
    "CambrionixFirmware-v1.87-un.enfir",
    "eJwsnduOLTFSbd9Lqn/8f8BywVzYg=="
  ]
}
```

### 5.25. cbrx_firmware (list)

Obtain a list of all available firmware versions.

Syntax:

```json
{
  "method": "cbrx_firmware",
  "params": ["list"]
}
```

Returns:

```json
{
  "result": [
    {
      "filename": "filename",
      "version": "firmware-version"
    }
  ]
}
```

Example successful response:

```json
{
  "jsonrpc": "2.0",
  "id": 0,
  "result": [
    {
      "filename": "CambrionixFirmware-v1.87-un.enfir",
      "version": "1.87"
    }
  ]
}
```

### 5.26. cbrx_firmware (remove)

Remove a firmware file from API local storage.

Syntax:

```json
{
  "method": "cbrx_firmware",
  "params": [
    "remove",
    "filename"
  ]
}
```

Returns:

```json
{
  "result": true
}
```

### 5.27. cbrx_firmware (status)

Obtain the status of a firmware update.

Syntax:

```json
{
  "method": "cbrx_firmware",
  "params": [
    "status",
    "connection-handle"
  ]
}
```

Returns:

```json
{
  "result": {
    "Version": "firmware-version",
    "Type": "firmware-type",
    "Progress": progress-percentage,
    "Stage": "stage-value"
  }
}
```

| Stage value | Description |
|---|---|
| `none` | Firmware is not being updated |
| `connecting` | Connecting to the hub |
| `init` | Update is initialising |
| `erasing` | Erasing current firmware |
| `updating` | New firmware is being installed |
| `verifying` | Checking installation |
| `complete` | Check completed |
| `rebooting` | Rebooting the hub |
| `rebooted` | Hub ready for use |
| `skipped` | Already updated |

Possible errors in `Stage`: `crypt-init-failed`, `init-failed`, `erase-failed`, `flash-failed`, `check-failed`, `reboot-failed`.

### 5.28. cbrx_firmware (update)

Start firmware updates. Can update multiple firmwares (e.g., main and motor control) at once.

Syntax:

```json
{
  "method": "cbrx_firmware",
  "params": [
    "update",
    "connection-handle",
    { "type": "filename", ... }
  ]
}
```

From version 3.9 onwards, you can use the hub's serial number instead of the connection handle.

Example JSON-RPC request:

```json
{
  "jsonrpc": "2.0",
  "id": "0",
  "method": "cbrx_firmware",
  "params": [
    "update",
    "7654",
    {
      "un": "CambrionixFirmware-v1.86-un.enfir",
      "mc": "CambrionixFirmware-v1.0.0-mc.enfir"
    }
  ]
}
```

### 5.29. cbrx_get_usb (tree)

Return the entire USB tree that has been discovered.

Syntax:

```json
{
  "method": "cbrx_get_usb",
  "params": ["tree"]
}
```

Returns a nested structure of USB devices including `VID`, `PID`, `Description`, `LocationID`, `USBVersion`, `USBPower`, `USBSpeed`, and `Endpoints` information.

Example successful response snippet:

```json
{
  "jsonrpc": "2.0",
  "id": 0,
  "result": [
    {
      "VID": 32902,
      "PID": 40429,
      "Description": "Intel(R) USB 3.1 Host Controller",
      "children": [
        {
          "VID": 3141,
          "PID": 26403,
          "LocationID": 558891008,
          "USBSpeed": { "Description": "High" }
        }
      ]
    }
  ]
}
```

### 5.30. cbrx_get_usb (descriptors)

Request entire dump of a USB device’s descriptor information.

Syntax:

```json
{
  "method": "cbrx_get_usb",
  "params": ["descriptors", "locationID | hub-serial"]
}
```

Returns Chapter 9 USB 3.2 specification compliant descriptors including `RawBytes`, `bLength`, `bDescriptorType`, `idVendor`, `idProduct`, and detailed `Configurations` / `Strings` / `BOS` structures.

### 5.31. cbrx_hub_get

Get a key value from a hub using its serial number (no need to open a connection first). Slower for multiple operations.

Syntax:

```json
{
  "method": "cbrx_hub_get",
  "params": [
    "hub-serial",
    "dictionary-key"
  ]
}
```

### 5.32. cbrx_hub_set

Set a key value on a hub using its serial number. Slower for multiple operations.

Syntax:

```json
{
  "method": "cbrx_hub_set",
  "params": [
    "hub-serial",
    "dictionary-key",
    Value
  ]
}
```

### 5.33. cbrx_notifications

Enable/disable notifications for certain events. Packets are JSON-RPC without an `id` field. Sent only to the requesting socket.

Syntax:

```json
{
  "method": "cbrx_notifications",
  "params": ["notification"]
}
```

Example notifications: `usb-device-attached`, `usb-changed`.

### 5.34. cbrx_pair_device

Initiate pairing of an iOS device. Usually automatic when querying battery.

Syntax:

```json
{
  "method": "cbrx_pair_device",
  "params": ["UDID"]
}
```
## 6. API Notifications

API notification packets are the same as other JSON-RPC packets, except that they do not have an `id` field. Most of these notifications do not supply anything in the `params` field. These notifications will only be sent if they are enabled using the `cbrx_notifications` method.

| Notification | Description |
|---|---|
| `all` | Request all notifications |
| `discover-changed` | API detected a change in available hubs. Re-run `cbrx_discover`. |
| `dead-hub-changed` | API detected a hub has become unresponsive or cannot be connected to. |
| `firmware-progress` | Updates on firmware update progress. |
| `over-temperature` | Hub is over temperature. |
| `over-voltage` | Hub is over voltage. |
| `rfid-received` | RFID card presented to a sensor. |
| `rfid-removed` | RFID card removed from a sensor. |
| `usb-device-attached` | Detailed info about specific devices that have attached. |
| `usb-device-detached` | Detailed info about specific devices that have detached. |
| `under-voltage` | Hub is under voltage. |
| `usb-changed` | API detected a change in the USB Tree. |

### Example notification packets

**discover-changed**
```json
{
  "jsonrpc": "2.0",
  "method": "discover-changed"
}
```

**dead-hub-changed**
```json
{
  "jsonrpc": "2.0",
  "method": "dead-hub-changed",
  "params": {
    "IsDead": true
  }
}
```

**firmware-progress**
```json
{
  "jsonrpc": "2.0",
  "method": "firmware-progress",
  "params": {
    "Progress": 60,
    "Stage": "flashing",
    "Type": "charger",
    "HostDevice": "1212343456567878",
    "HostSerial": "/dev/tty.usbmodem1421502",
    "HostDescription": "PS15-USB3"
  }
}
```

## 7. Deprecated Methods

These methods exist to support backwards compatibility only and should not be used.

| API Call | Description |
|---|---|
| `cbrx_apiversion (true)` | Obtain a detailed version of the API. Deprecated in 3.0, use `cbrx_apidetails`. |
| `cbrx_get_usbtree` | Return entire USB tree. Deprecated in 3.5, use `cbrx_get_usb (tree)`. |

## 8. Device string

When the API queries a device, it returns a detailed object under the `Device` key.

| Output | Description |
|---|---|
| `VID` / `PID` | Vendor and Product ID (Integer) |
| `Manufacturer` | Device manufacturer name |
| `Description` | Name of the hardware |
| `SerialNumber` | USB serial number |
| `LocationID` | 32-bit location identifier |
| `DevicePath` | Platform-specific path for the device |
| `USBVersion` | USB version number |
| `USBSpeed` | Current speed and Capability speed |
| `Endpoints` | Active and Maximum endpoints, plus memory usage |
| `Battery` | Data source, Trust level, level, health, temperature, etc. |
| `Phone...` | Mobile specific: Serial, Identity, Model, IMEI, Mac, OS version, ECID, Colour. |

## 9. API Management

### 9.1. Stopping the API service

- **Windows**: Use Task Manager -> Services tab -> Right-click `CambrionixApiService` -> Stop.
- **Linux**: `sudo systemctl stop CambrionixApiService`
- **macOS**: `sudo /usr/bin/CambrionixApiService --remove`

### 9.2. Starting the API Service

- **Windows**: Use Task Manager -> Services tab -> Right-click `CambrionixApiService` -> Start.
- **Linux**: `sudo systemctl start CambrionixApiService`
- **macOS**: `sudo /usr/bin/CambrionixApiService --install`

## 10. Additional information

### Cambrionix Connect Recorder Service
The Recorder service is an optional component that records device health, charging history, and connection events.

### Limitations
The API supports Universal, PDSync, TS3-C10, and Motor Control firmware products.

### Registry Tweak (Windows)
To prevent Windows from assigning new COM ports to identical USB devices, you can set `IgnoreHWSerNum` for specific VIDs/PIDs in `HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Control\usbflags`.

### Connection Handles
Handles become invalid after 30s of inactivity unless notifications are registered.

### Location IDs
A 32-bit unsigned integer representing the device's location in the USB tree (e.g., `0x00000abc` for path `a&b&c`).

### Endpoints
xHCI host controllers have limited endpoint memory (typically 64-128). Mobile devices often use 5+ endpoints each.

### Power States
- `D0`: Fully on
- `D1`, `D2`, `D3`: Low-power states (higher number = lower power).

### Status
- `idle`: Connected but not talking.
- `active`: Connected and in use.
- `missing`: No longer on USB tree.
- `unresponsive`: No longer responding.
- `locked`: Connection is locked.

## 11. Logging

Enable logging by creating a config file ending in `.log.cfg`.
- **Linux**: `echo "*=DEBUG" > /etc/opt/cambrionix/cambrionix.log.cfg`
- **Locations**:
    - Windows: `C:\ProgramData\Cambrionix`
    - macOS: `Library/Logs/Cambrionix`
    - Linux: `/var/log/cambrionix`

## 12. Docks

A Dock is a series of chargers connected via expansion ports. They can be treated as a single unit by calling `cbrx_discover` with the `docks` parameter. This combines `nrOfPorts` and `TotalCurrent_mA`. Ports are referenced sequentially starting from the parent charger.
