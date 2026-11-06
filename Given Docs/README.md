# Global Business Travel Operations Agent (training prototype)

Agent học tập làm việc với mock systems qua function calling. Không có booking/payment/email thật.

## Setup
```
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```
## Run
```
python -m travel_agent.cli --user U-EMP-001 --message "Tôi chuẩn bị công tác Singapore với mã TRIP-2026-001. Cần chuẩn bị gì?"
pytest -q
python eval/run_eval.py
```
LLM thật là tùy chọn (biến môi trường); mặc định dùng planner rule-based.

## Tài liệu
AGENTS.md · docs/ARCHITECTURE.md (sơ đồ kiến trúc + 3 workflow) · docs/PLAN.md · docs/WORKFLOWS.md · docs/TOOL_CARDS.md · docs/DATA_SPEC.md · docs/MEMORY_AND_SAFETY.md · docs/TEST_MATRIX.md

## Giới hạn
Xem docs/MEMORY_AND_SAFETY.md mục 4.
