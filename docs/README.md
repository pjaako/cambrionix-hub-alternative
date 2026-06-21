# Cambrionix Hub API Reference (Unofficial) — OBSOLETE

> **⚠ Do not use this documentation for new development.**
>
> This folder documents the **legacy JSON-RPC API (v3.9)**, which has been superseded by the **REST API (v4.0)**. The v3.9 reference contains known inaccuracies against the v4.0 service (flag field behaviour, response shapes) and will not be updated.
>
> **Use the live API documentation served by `CambrionixApiService` instead:**
> - Swagger UI: `http://localhost:43424/api/v1/swagger`
> - OpenAPI JSON: `http://localhost:43424/openapi.json`
>
> This folder is kept for historical reference only.

This directory contains a community-maintained Markdown conversion of the **Cambrionix Hub API User Manual** (Target API: v3.9+ / June 2025).

## Disclaimer

**This is NOT an official Cambrionix document.**

This documentation is an unofficial derivative work created for improved readability for AI coding agents and other machines. For the definitive technical specification, please refer to the official documentation at [cambrionix.com](https://www.cambrionix.com/cambrionix-api).

The authors of this conversion are not affiliated with, endorsed by, or sponsored by Cambrionix Ltd. Use this information at your own risk.

## Visual Aids and Diagrams

This Markdown reference contains all technical specifications, JSON-RPC syntax, and tables from the manual. However, it does **not** include the visual diagrams (such as USB tree illustrations or physical LED flash pattern diagrams).

Please refer to the original [Cambrionix-Hub-API-User-Manual-v3.9.pdf](./Cambrionix-Hub-API-User-Manual-v3.9.pdf) included in this repository for all visual references.

## Attribution and Copyright

- **Intellectual Property:** All content extracted from the manual remains the property of **Cambrionix Ltd.**
- **Trademarks:** All trademarks, service marks, and registered trademarks (including Cambrionix, macOS, Windows, Android, etc.) mentioned in this documentation are the property of their respective owners.
- **Licensing:** No software license (such as MIT or GPL) is applied to the content of this documentation, as the copyright for the source text is held by the original author.

## Reference Files

The documentation is split into the following sequential parts:

1. [01-overview-and-methods.md](./cambrionix-hub-api-reference-v3.9/01-overview-and-methods.md): Introduction, Installation, API Call Structure, and Methods 5.1-5.34.
2. [02-get-dictionary.md](./cambrionix-hub-api-reference-v3.9/02-get-dictionary.md): Dynamic Hubs, Feature Sets, and the Get Dictionary.
3. [03-set-dictionary-and-misc.md](./cambrionix-hub-api-reference-v3.9/03-set-dictionary-and-misc.md): Set Dictionary, LED Control, Battery Info, and Error Codes.
