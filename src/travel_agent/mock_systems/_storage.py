import json
import os
from pathlib import Path
from threading import Lock
from typing import Any


_DATA_DIR = Path(__file__).resolve().parents[3] / "data"
_DATASETS = {
    "users.json",
    "trips.json",
    "travelers.json",
    "itineraries.json",
    "approvals.json",
    "approval_requests.json",
    "expenses.json",
    "policy_chunks.json",
    "requirements.json",
    "audit_events.json",
}
_WRITE_LOCK = Lock()


def load_dataset(filename: str) -> Any:
    if filename not in _DATASETS:
        raise ValueError("Unknown mock dataset")
    with (_DATA_DIR / filename).open(encoding="utf-8") as source:
        return json.load(source)


def find_record(filename: str, key: str, value: str) -> dict[str, Any] | None:
    return next((row for row in load_dataset(filename) if row.get(key) == value), None)


def write_dataset(filename: str, data: Any) -> None:
    if filename not in _DATASETS:
        raise ValueError("Unknown mock dataset")
    path = _DATA_DIR / filename
    with _WRITE_LOCK:
        temporary = path.with_suffix(path.suffix + ".tmp")
        with temporary.open("w", encoding="utf-8", newline="\n") as target:
            json.dump(data, target, ensure_ascii=False, indent=2)
            target.write("\n")
        os.replace(temporary, path)
