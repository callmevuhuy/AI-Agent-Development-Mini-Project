from typing import Any

from ._storage import find_record, load_dataset


def get_trip_request(trip_id: str) -> dict[str, Any] | None:
    return find_record("trips.json", "trip_id", trip_id)


def list_trip_requests(traveler_id: str | None = None) -> list[dict[str, Any]]:
    rows = load_dataset("trips.json")
    if traveler_id is not None:
        return [row for row in rows if row.get("traveler_id") == traveler_id]
    return rows
