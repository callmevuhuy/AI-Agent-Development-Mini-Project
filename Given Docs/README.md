# Project quick start

Run commands from the repository root. See the root `README.md` for full setup, roles, environment variables, and limitations.

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m travel_agent.app message --user U-EMP-002 --text "My flight to Tokyo on Dec 8 is delayed, what should I do?"
python -m travel_agent.app web --port 8080
python -m pytest -v
python eval/run_eval.py --label after
```

The offline NLU router and BM25 retriever are deterministic; no LLM or API key is configured. All systems and records are mock data.
