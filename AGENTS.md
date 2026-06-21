# Agent Instructions and Project Context

This file provides context and instructions for AI agents working on the Cambrionix Hub Alternative project.

## Project Goal
Create a Python-based web application (GUI) to control and log charging processes for devices connected to Cambrionix hubs.

## Key Resources
- **API Reference**: `docs/cambrionix-hub-api-reference-v3.9/` contains Markdown versions of the API documentation. This is the primary source of truth for API calls.
- **Official Manual**: `docs/Cambrionix-Hub-API-User-Manual-v3.9.pdf` contains diagrams and original text.

## Technical Stack
- **Language**: Python
- **Environment**: Python virtual environment (`venv/`).
- **GUI**: Web-based (specific framework to be decided, e.g., Flask, FastAPI with a frontend).
- **API**: Cambrionix Hub API (JSON-RPC).

## Development Guidelines
- **Always use venv**: Ensure all packages are installed and executed within the virtual environment.
- **Reference the docs**: Before implementing any API call, check the `docs/` folder to ensure correct JSON-RPC syntax and parameters.
- **Surgical Changes**: When modifying existing code, keep changes focused and minimal.
- **Logging**: Implement robust logging for both the application behavior and the charging process data.

## API Notes
- The API uses JSON-RPC over TCP/IP or Serial.
- See `docs/cambrionix-hub-api-reference-v3.9/01-overview-and-methods.md` for connection methods and basic request structure.
