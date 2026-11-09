import hashlib
import json
import os
import re
import tempfile
from pathlib import Path
from typing import Any


DRAFT_DIR = Path(__file__).resolve().parents[3] / "data" / "drafts"
_SOURCE_IDS = re.compile(r"^(?:TRIP-\d{4}-\d{3}|EXP-\d{4}-\d{3})$")


def upsert_draft(workflow: str, source_id: str, content: dict[str, Any]) -> dict[str, Any]:
    if workflow not in {"pretrip", "intrip", "posttrip"} or not _SOURCE_IDS.fullmatch(source_id):
        raise ValueError("Invalid draft identity")
    if not isinstance(content, dict):
        raise ValueError("Draft content must be an object")
    draft_id = "DR-" + hashlib.sha256(f"{workflow}:{source_id}".encode()).hexdigest()[:20]
    draft = {
        "draft_id": draft_id,
        "workflow": workflow,
        "source_id": source_id,
        "draft_status": "draft_created",
        "delivery_status": "not_sent" if workflow == "intrip" else "not_published",
        "content": content,
    }
    serialized = json.dumps(draft, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
    if len(serialized.encode("utf-8")) > 32768:
        raise ValueError("Draft exceeds the storage limit")

    DRAFT_DIR.mkdir(parents=True, exist_ok=True)
    target = DRAFT_DIR / f"{draft_id}.json"
    reused = target.exists()
    temporary_path = None
    try:
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=DRAFT_DIR, delete=False) as temporary:
            temporary.write(serialized)
            temporary_path = Path(temporary.name)
        os.replace(temporary_path, target)
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)
    return {**draft, "reused": reused}
