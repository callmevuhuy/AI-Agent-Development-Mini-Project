from typing import Any

from ._storage import find_record


def get_trip_request(trip_id: str) -> dict[str, Any] | None:
    return find_record("trips.json", "trip_id", trip_id)
