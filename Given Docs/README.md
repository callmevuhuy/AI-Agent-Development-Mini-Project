# Project quick start

Run commands from the repository root. See the root `README.md` for setup, CLI examples, roles, and limitations.

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
python -m travel_agent.app message --user U-EMP-002 --text "Prepare checklist for TRIP-2026-006"
python -m pytest -q
python eval/run_eval.py --label after
```

The offline planner is deterministic; no LLM or API key is configured. All systems and records are mock data.
