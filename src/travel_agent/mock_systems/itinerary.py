from typing import Any

from ._storage import find_record


def get_itinerary(trip_id: str) -> dict[str, Any] | None:
    return find_record("itineraries.json", "trip_id", trip_id)
