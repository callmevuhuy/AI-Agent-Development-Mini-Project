from typing import Any

from ._storage import find_record


def get_user(user_id: str) -> dict[str, Any] | None:
    return find_record("users.json", "user_id", user_id)
