"""Application-owned draft editing; source facts and evidence remain immutable."""
import json
import re
from travel_agent.dispatcher import dispatch
from travel_agent.mock_systems import draft_workspace
from travel_agent.mock_systems.user import get_user


def draft_detail(user_id, draft_id, edits=None):
    user = get_user(user_id)
    if not user or user['role'] not in {'Employee', 'Reviewer'}:
        raise PermissionError('Chỉ Employee và Reviewer được xem hoặc sửa draft nghiệp vụ.')
    if not isinstance(draft_id, str) or not re.fullmatch(r'DR-[a-f0-9]{20}', draft_id):
        raise ValueError('Mã Draft không hợp lệ.')
    path = draft_workspace.DRAFT_DIR / f'{draft_id}.json'
    if not path.exists():
        raise ValueError('Không tìm thấy Draft.')
    draft = json.loads(path.read_text(encoding='utf-8'))
    ctx = {'user_id': user_id, 'role': user['role'], 'session_id': 'workspace'}
    expense = draft['workflow'] == 'posttrip'
    source = dispatch('get_expense_report' if expense else 'get_trip_request',
                      {'report_id' if expense else 'trip_id': draft['source_id']},
                      'posttrip' if expense else 'pretrip', ctx)
    if not source['ok']:
        raise PermissionError(source['error']['message'])
    facts = source['data']
    trip_id = facts.get('trip_id')
    trip = dispatch('get_trip_request', {'trip_id': trip_id}, 'pretrip', ctx)
    itinerary = dispatch('get_itinerary', {'trip_id': trip_id}, 'intrip', ctx)
    if edits is not None:
        if (not isinstance(edits, dict) or set(edits) - {'notes', 'proposed_purpose', 'checklist_items'}
                or any(not isinstance(v, str) or len(v) > 4000 for v in edits.values())):
            raise ValueError('Chỉ được sửa ghi chú, mục đích đề xuất và checklist; mỗi trường tối đa 4000 ký tự.')
        draft['content']['user_edits'] = edits
        draft = draft_workspace.upsert_draft(draft['workflow'], draft['source_id'], draft['content'])
    trip_facts = trip.get('data', {}) if trip['ok'] else {}
    required = ['trip_id', 'traveler_id', 'destination', 'start_date', 'end_date', 'purpose']
    return {**draft, 'source_facts': facts, 'trip_facts': trip_facts,
            'itinerary': itinerary.get('data', {}) if itinerary['ok'] else {},
            'missing_fields': [k for k in required if not trip_facts.get(k)],
            'notice': 'Nội dung đề xuất chỉ lưu trong Draft. Kiểm tra lại luôn dùng dữ liệu nguồn.'}
