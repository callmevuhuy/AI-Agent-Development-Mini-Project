from typing import Any

from travel_agent.tools._draft import create


def run(arguments: dict[str, Any]) -> dict[str, Any]:
    return create("posttrip", arguments["report_id"], arguments["review_preview"])
