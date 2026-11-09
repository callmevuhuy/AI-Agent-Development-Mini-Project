from typing import Any

from travel_agent.mock_systems.trip import get_trip_request as read_trip_request
from travel_agent.tools._result import record_result


def run(arguments: dict[str, Any]) -> dict[str, Any]:
    return record_result(read_trip_request(arguments["trip_id"]), "mock_travel_request_system")
