from typing import Any

from travel_agent.mock_systems.itinerary import get_itinerary as read_itinerary
from travel_agent.tools._result import record_result


def run(arguments: dict[str, Any]) -> dict[str, Any]:
    return record_result(read_itinerary(arguments["trip_id"]), "mock_itinerary_system")
