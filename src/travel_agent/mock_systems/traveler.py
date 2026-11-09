from typing import Any

from ._storage import find_record


def get_traveler_profile(traveler_id: str) -> dict[str, Any] | None:
    return find_record("travelers.json", "traveler_id", traveler_id)
