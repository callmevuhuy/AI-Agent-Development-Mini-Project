"""Đối chiếu quyền giữa Trips và chat, gồm scope chọn độc lập với dòng yêu cầu."""
import json
from pathlib import Path
import shutil
import subprocess
from io import BytesIO
from types import SimpleNamespace

import pytest

from test_conversational_and_fixes import isolate_runtime_dirs
from travel_agent.conversation import handle_turn
from travel_agent.logging_utils import read_handoff_queue
from travel_agent.mock_systems import _storage, draft_workspace
from travel_agent.web_demo import build_collection_payload, make_handler


def post(path, payload):
    body = json.dumps(payload).encode()
    wire = f'POST {path} HTTP/1.0\r\nContent-Length: {len(body)}\r\n\r\n'.encode() + body
    output = BytesIO()

    class Connection:
        def makefile(self, *args):
            return BytesIO(wire)

        def sendall(self, data):
            output.write(data)

    make_handler()(Connection(), ('127.0.0.1', 0), SimpleNamespace())
    headers, response = output.getvalue().split(b'\r\n\r\n', 1)
    return int(headers.split()[1]), json.loads(response)


def trip_request(user, trip, action, scope=None, request_type=None, **extra):
    payload = {'user_id': user, 'session_id': 'trip-actions', 'trip_id': trip, 'action': action, **extra}
    if scope is not None:
        payload['approval_scope'] = scope
    if request_type is not None:
        payload['request_action_type'] = request_type
    return post('/api/trip/action', payload)


def business_snapshot():
    return {name: _storage.load_dataset(name) for name in ('trips.json', 'approval_requests.json', 'expenses.json')}


@pytest.mark.parametrize('selected_trip,selected_type,row_trip,row_type,action', [
    ('TRIP-2026-002', 'escalation', 'TRIP-2026-001', 'checklist_review', 'details'),
    ('TRIP-2026-001', 'checklist_review', 'TRIP-2026-002', 'escalation', 'itinerary'),
    ('TRIP-2026-001', 'checklist_review', 'TRIP-2026-001', 'publish_request', 'details'),
])
def test_approver_cannot_switch_scope_by_clicking_a_different_request(selected_trip, selected_type, row_trip, row_type, action):
    # Hai loại yêu cầu cùng một Trip vẫn là hai scope khác nhau.
    requests = _storage.load_dataset('approval_requests.json')
    requests.append({'trip_id': 'TRIP-2026-001', 'action_type': 'publish_request',
                     'status': 'pending', 'assigned_approver_id': 'U-APR-001'})
    _storage.write_dataset('approval_requests.json', requests)
    before = business_snapshot()
    status, result = trip_request('U-APR-001', row_trip, action,
                                  {'trip_id': selected_trip, 'action_type': selected_type}, row_type)
    assert status == 403 and result['code'] == 'unauthorized_scope'
    assert 'không khớp' in result['error']
    assert not any(word in json.dumps(result) for word in ('Tokyo', 'Singapore', 'MOCK-'))
    assert business_snapshot() == before
    assert not list(draft_workspace.DRAFT_DIR.glob('*.json')) and not read_handoff_queue()


@pytest.mark.parametrize('trip,scope_type,action,prompt,expected', [
    ('TRIP-2026-001', 'checklist_review', 'details', 'Xem chi tiết chuyến ', 'completed'),
    ('TRIP-2026-002', 'escalation', 'itinerary', 'Xem hành trình ', 'completed'),
    ('TRIP-2026-001', 'checklist_review', 'itinerary', 'Xem hành trình ', 'failed_validation'),
    ('TRIP-2026-002', 'escalation', 'details', 'Xem chi tiết chuyến ', 'failed_validation'),
])
def test_trip_and_chat_keep_the_requested_read_type(trip, scope_type, action, prompt, expected):
    scope = {'trip_id': trip, 'action_type': scope_type}
    before = business_snapshot()
    status, result = trip_request('U-APR-001', trip, action, scope, scope_type)
    chat = handle_turn(prompt + trip, 'U-APR-001', session_id='chat-actions', approval_scope=scope)
    assert status == 200 and result['outcome'] == chat['outcome'] == expected
    assert result['route'] == chat['route']
    assert result['bot_response'] == chat['bot_response']
    if expected == 'failed_validation':
        assert result['error']['code'] == 'unauthorized_scope'
        assert not result['result'] and not result['citations'] and not result['handoff_required']
        assert 'MOCK-' not in result['bot_response'] and 'Tokyo' not in result['bot_response']
    assert business_snapshot() == before
    assert not list(draft_workspace.DRAFT_DIR.glob('*.json')) and not read_handoff_queue()


@pytest.mark.parametrize('user,action,trip,prompt', [
    ('U-EMP-002', 'details', 'TRIP-2026-006', 'Xem chi tiết chuyến '),
    ('U-EMP-002', 'itinerary', 'TRIP-2026-006', 'Xem hành trình '),
    ('U-EMP-002', 'checklist', 'TRIP-2026-006', 'Chuẩn bị checklist '),
    ('U-EMP-002', 'support', 'TRIP-2026-002', 'Tạo yêu cầu phê duyệt hỗ trợ sự cố gián đoạn '),
    ('U-REV-001', 'details', 'TRIP-2026-006', 'Xem chi tiết chuyến '),
    ('U-REV-001', 'itinerary', 'TRIP-2026-006', 'Xem hành trình '),
    ('U-REV-001', 'checklist', 'TRIP-2026-006', 'Chuẩn bị checklist '),
    ('U-ADM-001', 'audit', 'TRIP-2026-006', 'Xem nhật ký kiểm toán cho '),
])
def test_legal_actions_match_chat_for_other_roles(user, action, trip, prompt):
    status, result = trip_request(user, trip, action)
    chat = handle_turn(prompt + trip, user, session_id='legal-chat')
    assert status == 200 and result['route'] == chat['route'] == 'SELF_SERVE'
    assert result['outcome'] == chat['outcome']
    assert result['intent'] == chat['intent']
    assert not result.get('error') and not chat.get('error')


@pytest.mark.parametrize('user,action,trip', [
    ('U-REV-001', 'support', 'TRIP-2026-006'),
    ('U-REV-001', 'audit', 'TRIP-2026-006'),
    ('U-ADM-001', 'details', 'TRIP-2026-006'),
    ('U-ADM-001', 'itinerary', 'TRIP-2026-006'),
    ('U-ADM-001', 'checklist', 'TRIP-2026-006'),
    ('U-ADM-001', 'support', 'TRIP-2026-006'),
    ('U-EMP-002', 'details', 'TRIP-2026-001'),
    ('U-EMP-002', 'itinerary', 'TRIP-2026-001'),
    ('U-EMP-002', 'checklist', 'TRIP-2026-001'),
    ('U-EMP-002', 'support', 'TRIP-2026-001'),
    ('U-EMP-002', 'audit', 'TRIP-2026-006'),
])
def test_direct_trip_requests_cannot_bypass_other_role_or_owner_boundaries(user, action, trip):
    before = business_snapshot()
    status, result = trip_request(user, trip, action)
    assert status == 200 and result['route'] == 'REJECT_SAFETY'
    assert result['error']['code'] == 'unauthorized_scope'
    assert not result['citations'] and not result['handoff_required']
    assert set(result['result']) <= {'error', 'error_code', 'message', 'outcome'}
    assert not any(word in json.dumps(result['result']) for word in ('Singapore', 'MOCK-', 'traveler_id'))
    assert business_snapshot() == before
    assert not list(draft_workspace.DRAFT_DIR.glob('*.json')) and not read_handoff_queue()


@pytest.mark.parametrize('action', ['checklist', 'support', 'audit'])
def test_approver_scope_does_not_grant_workflow_or_admin_actions(action):
    before = business_snapshot()
    status, result = trip_request('U-APR-001', 'TRIP-2026-001', action,
                                  {'trip_id': 'TRIP-2026-001', 'action_type': 'checklist_review'}, 'checklist_review')
    assert status == 200 and result['route'] == 'REJECT_SAFETY'
    assert result['error']['code'] == 'unauthorized_scope' and not result['handoff_required']
    assert business_snapshot() == before
    assert not list(draft_workspace.DRAFT_DIR.glob('*.json')) and not read_handoff_queue()


def test_forged_or_stale_scope_and_missing_scope_are_rechecked_by_server():
    for scope, request_type in [(None, 'checklist_review'),
                                 ({'trip_id': 'TRIP-2026-001', 'action_type': 'checklist_review'}, None)]:
        assert trip_request('U-APR-001', 'TRIP-2026-001', 'details', scope, request_type)[0] == 403
    requests = _storage.load_dataset('approval_requests.json')
    requests[0]['assigned_approver_id'] = 'U-APR-002'
    _storage.write_dataset('approval_requests.json', requests)
    _, result = trip_request('U-APR-001', 'TRIP-2026-001', 'details',
                             {'trip_id': 'TRIP-2026-001', 'action_type': 'checklist_review'}, 'checklist_review')
    assert result['route'] == 'REJECT_SAFETY' and not result['result']
    assert result['error']['code'] == 'unauthorized_scope'


@pytest.mark.parametrize('fields', [{'action': 'approve'}, {'action': []}, {'trip_id': '../data'},
                                    {'role': 'Admin'}, {'action': None}, {'message': 'ignore rules'}])
def test_typed_actions_reject_unknown_fields_actions_and_invalid_ids(fields):
    payload = {'user_id': 'U-EMP-002', 'trip_id': 'TRIP-2026-006', 'action': 'details', **fields}
    status, result = post('/api/trip/action', payload)
    assert status == 400 and result['code'] == 'invalid_argument'


@pytest.mark.parametrize('user,actions', [('U-EMP-001', ['details', 'itinerary', 'checklist', 'support']),
                                         ('U-REV-001', ['details', 'itinerary', 'checklist']),
                                         ('U-ADM-001', ['audit'])])
def test_trip_menus_only_offer_supported_role_actions(user, actions):
    rows = build_collection_payload('trips', user)
    assert rows and all(row['allowed_actions'] == actions for row in rows)


def test_approver_menus_follow_request_type():
    rows = build_collection_payload('trips', 'U-APR-001')
    assert {r['action_type']: r['allowed_actions'] for r in rows} == {
        'checklist_review': ['details'], 'escalation': ['itinerary']}


def test_workspace_trip_buttons_keep_scope_and_send_typed_actions(tmp_path):
    from travel_agent.web_demo import _HTML

    node = shutil.which('node')
    if not node:
        pytest.skip('Node.js chỉ cần cho kiểm tra JavaScript của giao diện.')
    script = tmp_path / 'web-demo.js'
    script.write_text(_HTML.split('<script>')[1].split('</script>')[0], encoding='utf-8')
    syntax = subprocess.run([node, '--check', str(script)], capture_output=True, text=True, timeout=20)
    assert syntax.returncode == 0, syntax.stderr
    smoke = subprocess.run([node, str(Path(__file__).with_name('trip_actions_ui_smoke.cjs')), str(script)],
                           capture_output=True, text=True, encoding='utf-8', timeout=20)
    assert smoke.returncode == 0, smoke.stdout + smoke.stderr
