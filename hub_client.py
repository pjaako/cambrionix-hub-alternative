from hub_backends import CliClient


def discover_hubs():
    return CliClient.discover_serial()


__all__ = ["discover_hubs"]
