from hub_backends import CliClient


def discover_hubs(known: dict | None = None):
    """`known`: hub_id -> registered client; those are reported present without reopening their ports."""
    return CliClient.discover_serial(known)


__all__ = ["discover_hubs"]
