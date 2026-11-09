from typing import Any

from travel_agent.mock_systems.draft_workspace import upsert_draft
from travel_agent.tools._result import success


def create(workflow: str, source_id: str, content: dict[str, Any]) -> dict[str, Any]:
    return success(upsert_draft(workflow, source_id, content), "mock_draft_workspace", read_only=False)
