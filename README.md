# Cambrionix Hub Alternative

A Python-based application with a web GUI to control and log the charging process of devices connected to a Cambrionix Hub via the Cambrionix Hub API.

## Features

- **Web GUI**: User-friendly interface to monitor and control the hub.
- **Charging Control**: Ability to set charging modes and limits for connected devices.
- **Logging**: Detailed logs of charging processes for analysis and auditing.
- **Cambrionix API Integration**: Built on top of the official Cambrionix Hub API (v3.9+).

## Prerequisites

- Python 3.8+
- Cambrionix Hub (with network or USB access for API calls)

## Getting Started

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd cambrionix-hub-alternative
   ```

2. **Set up the virtual environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**:
   *(Dependencies will be added as development progresses)*
   ```bash
   pip install -r requirements.txt
   ```

## Documentation

The API reference and user manuals can be found in the `docs/` directory.

- [Cambrionix Hub API Reference](./docs/cambrionix-hub-api-reference-v3.9/01-overview-and-methods.md)
- [Cambrionix Hub API User Manual (PDF)](./docs/Cambrionix-Hub-API-User-Manual-v3.9.pdf)

## License

This project is licensed under the MIT License - see the LICENSE file for details.
*(Note: Cambrionix API documentation content is property of Cambrionix Ltd.)*
