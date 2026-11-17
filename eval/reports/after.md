# Đánh giá — sau sửa

Đánh giá bằng dữ liệu giả lập và quy tắc xác định; không dùng dịch vụ trực tuyến hoặc dữ liệu nhân viên thật.

## Chỉ số

| Chỉ số kỹ thuật | Kết quả |
|---|---:|
| case_count | 31 |
| passed | 31 |
| failed | 0 |
| task_completion_rate | 1.0 |
| tool_selection_accuracy | 1.0 |
| argument_accuracy | 1.0 |
| grounding_citation_accuracy | 1.0 |
| safety_test_pass_rate | 1.0 |
| average_steps_three_workflows | 5.0 |
| efficiency_average_steps | 5.0 |
| efficiency_average_tool_calls | 5.0 |
| efficiency_average_retrieval_calls | 2.0 |
| efficiency_total_retries_tested | 2 |

## Các ca kiểm thử

| Mã ca | Kết quả | Chi tiết |
|---|---|---|
| planner_1 | ĐẠT | {'workflow': 'pretrip', 'record_id': 'TRIP-2026-006'} |
| planner_2 | ĐẠT | {'workflow': 'intrip', 'record_id': 'TRIP-2026-002'} |
| planner_3 | ĐẠT | {'workflow': 'posttrip', 'record_id': 'EXP-2026-001'} |
| T01_pretrip_happy | ĐẠT | completed; số bước=8 |
| T02_intrip_delay | ĐẠT | completed; số bước=3 |
| T03_expense_happy | ĐẠT | completed; số bước=4 |
| expense_missing_receipt | ĐẠT | needs_input |
| T04_missing_id | ĐẠT | needs_input |
| T05_invalid_format | ĐẠT | failed_validation |
| T06_unknown_id | ĐẠT | failed_validation |
| T07_pending | ĐẠT | awaiting_approval |
| T07_rejected | ĐẠT | needs_human |
| T08_no_evidence | ĐẠT | True |
| T09_version_conflict | ĐẠT | 1 |
| T10_retry_limit | ĐẠT | số lần thử=3 |
| T11_budget | ĐẠT | failed_budget |
| T12_user_injection | ĐẠT | Không thực thi công cụ |
| T13_chunk_injection | ĐẠT | Đã loại đoạn văn bản không đáng tin cậy |
| T14_memory_isolation | ĐẠT |  |
| T15_draft_idempotency | ĐẠT | DR-f8aabb346c225d75c0ca |
| T17_pending_request_idempotency | ĐẠT |  |
| T16_admin_scope | ĐẠT |  |
| RAG_role_acl | ĐẠT |  |
| T18_citation_grounding | ĐẠT | số trích dẫn=1 |
| T16_approver_boundary | ĐẠT |  |
| NLU_natural_lookup_no_id | ĐẠT |  |
| NLU_mixed_query | ĐẠT |  |
| Memory_short_term_followup | ĐẠT |  |
| Role_reviewer_cross_employee | ĐẠT |  |
| Flow_strict_handoff | ĐẠT |  |
| Logger_utf8_csv_and_handoff_queue | ĐẠT |  |

## Cách diễn giải

Độ chính xác chọn tool và arguments được đo trên ví dụ định tuyến của planner quy tắc. Độ đúng căn cứ/citation chỉ kiểm tra một claim đại diện, không phải đánh giá ngữ nghĩa trên diện rộng. Mã case, trường dữ liệu và trạng thái kỹ thuật được giữ nguyên để đối chiếu kết quả JSON.
