$ErrorActionPreference = "Stop"

python -m travel_agent.app message --user U-EMP-002 --text "Prepare checklist for TRIP-2026-006"
python -m travel_agent.app message --user U-EMP-002 --text "Flight delay on TRIP-2026-002"
python -m travel_agent.app message --user U-EMP-002 --text "Review expense report EXP-2026-001"
python -m travel_agent.app admin-trips --user U-ADM-001
python -m travel_agent.app admin-audit --user U-ADM-001 --trip TRIP-2026-004
