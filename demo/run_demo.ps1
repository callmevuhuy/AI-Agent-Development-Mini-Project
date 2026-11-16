$ErrorActionPreference = "Stop"

Write-Host "=== 1. Employee (U-EMP-002): Natural prompts without raw IDs ===" -ForegroundColor Cyan
python -m travel_agent.app message --user U-EMP-002 --text "I am traveling to Sydney on Dec 31 for a workshop, what do I need to prepare?"
python -m travel_agent.app message --user U-EMP-002 --text "My flight to Tokyo on Dec 8 is delayed, what should I do?"
python -m travel_agent.app message --user U-EMP-002 --text "Please review my Tokyo trip expenses"
python -m travel_agent.app message --user U-EMP-002 --text "Can you book a hotel in Tokyo for me?"

Write-Host "=== 2. Reviewer (U-REV-001): Cross-employee review ===" -ForegroundColor Cyan
python -m travel_agent.app message --user U-REV-001 --text "List all trips"
python -m travel_agent.app message --user U-REV-001 --text "Review expense report EXP-2026-003"

Write-Host "=== 3. Admin (U-ADM-001): Read-only governance & CSV handoff queue ===" -ForegroundColor Cyan
python -m travel_agent.app handoffs --status open
python -m travel_agent.app admin-trips --user U-ADM-001
python -m travel_agent.app admin-audit --user U-ADM-001 --trip TRIP-2026-004
