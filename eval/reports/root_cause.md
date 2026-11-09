# Root-cause analysis

## Evaluation findings and fixes

1. **Irrelevant expense-policy conflict blocked unrelated reports.** The summary builder previously considered every active policy rule even when a report contained no expense in that category, and the workflow queried meals/lodging generically. It now checks rules only for categories present and searches only those categories. Fixtures now separate a clean expense report, a receipt-missing report, and a meals/version-conflict report. Tests confirm completed, needs-input, and needs-human outcomes respectively.
2. **RAG authorization needed to precede retrieval.** Role checks only at response shaping would leak document existence through conflicts/citations. The dispatcher now validates role and (for Approver) pending action scope, then the policy KB filters `allowed_roles` before BM25, version review, and citation. A targeted fixture test proves a role-restricted chunk is absent from Employee results and available to Reviewer.
3. **Approval history needed a trusted decision boundary.** The agent tool only creates pending requests. The external mock helper verifies an Approver and pending request, updates source fixtures, and appends a reasoned decision event. Admin gets read-only access to that event stream.

## Limits

There was no archived pre-change metric baseline. The first official baseline is the completed deterministic build; therefore the regression report compares two verification runs of the same acceptance set and does not claim historical improvement. Planner accuracy uses three supported routing examples, and grounding/citation metric uses one representative claim; these are prototype checks, not broad model-quality estimates.
