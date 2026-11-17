# Báo cáo kiểm tra hồi quy

Baseline là lần đo đầu tiên được lưu sau khi triển khai. Không có số đo cũ hơn để khẳng định mức cải thiện trước triển khai; báo cáo chỉ so sánh baseline đã lưu với lần kiểm tra sau sửa.

- Ban đầu: 31/31 ca đạt.
- Sau sửa: 62/62 ca đạt.
- Hồi quy: 0; cải thiện: 0; ca mới: 31; ca đã bỏ: 0.
- Chi tiết thay đổi: hồi quy=không có, cải thiện=không có, mới=['WEB_U-ADM-001_01', 'WEB_U-ADM-001_02', 'WEB_U-ADM-001_03', 'WEB_U-ADM-001_04', 'WEB_U-ADM-001_05', 'WEB_U-APR-001_01', 'WEB_U-APR-001_02', 'WEB_U-APR-001_03', 'WEB_U-APR-001_04', 'WEB_U-APR-001_05', 'WEB_U-EMP-001_01', 'WEB_U-EMP-001_02', 'WEB_U-EMP-001_03', 'WEB_U-EMP-001_04', 'WEB_U-EMP-001_05', 'WEB_U-EMP-001_06', 'WEB_U-EMP-002_01', 'WEB_U-EMP-002_02', 'WEB_U-EMP-002_03', 'WEB_U-EMP-002_04', 'WEB_U-EMP-002_05', 'WEB_U-EMP-002_06', 'WEB_U-EMP-002_07', 'WEB_U-EMP-002_08', 'WEB_U-EMP-002_09', 'WEB_U-EMP-002_10', 'WEB_U-REV-001_01', 'WEB_U-REV-001_02', 'WEB_U-REV-001_03', 'WEB_U-REV-001_04', 'WEB_U-REV-001_05'], bỏ=không có.

| Chỉ số kỹ thuật | Ban đầu | Sau sửa | Chênh lệch |
|---|---:|---:|---:|
| case_count | 31 | 62 | 31 |
| passed | 31 | 62 | 31 |
| failed | 0 | 0 | 0 |
| task_completion_rate | 1.0 | 1.0 | 0.0 |
| tool_selection_accuracy | 1.0 | 1.0 | 0.0 |
| argument_accuracy | 1.0 | 1.0 | 0.0 |
| grounding_citation_accuracy | 1.0 | 1.0 | 0.0 |
| safety_test_pass_rate | 1.0 | 1.0 | 0.0 |
| average_steps_three_workflows | 5.0 | 5.0 | 0.0 |
| efficiency_average_steps | 5.0 | 5.0 | 0.0 |
| efficiency_average_tool_calls | 5.0 | 5.0 | 0.0 |
| efficiency_average_retrieval_calls | 2.0 | 2.0 | 0.0 |
| efficiency_total_retries_tested | 2 | 2 | 0 |
