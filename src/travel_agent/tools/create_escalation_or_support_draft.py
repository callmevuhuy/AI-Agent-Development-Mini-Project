from typing import Any

from travel_agent.tools._draft import create


def run(arguments: dict[str, Any]) -> dict[str, Any]:
    return create("intrip", arguments["trip_id"], arguments["support_draft"])
