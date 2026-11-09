from typing import Any

from travel_agent.tools._draft import create


def run(arguments: dict[str, Any]) -> dict[str, Any]:
    return create("pretrip", arguments["trip_id"], arguments["checklist"])
