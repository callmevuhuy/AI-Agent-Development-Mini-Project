import json
from io import BytesIO
from types import SimpleNamespace
import pytest
from test_conversational_and_fixes import isolate_runtime_dirs
from travel_agent.mock_systems import _storage
from travel_agent.mock_systems.approval import record_external_decision
from travel_agent.web_demo import build_collection_payload, make_handler
from travel_agent.conversation import handle_turn
from travel_agent.dispatcher import dispatch


def read(uid='U-APR-001', trip='TRIP-2026-001', action='checklist_review'):
    return handle_turn('Xem chi tiết chuyến ' + trip, uid, session_id='assignment',
                       approval_scope={'trip_id': trip, 'action_type': action})


def add_other_approver():
    users = _storage.load_dataset('users.json')
    users.append({'user_id': 'U-APR-002', 'role': 'Approver', 'traveler_id': None})
    _storage.write_dataset('users.json', users)
    rows = _storage.load_dataset('approval_requests.json')
    rows.append({'trip_id': 'TRIP-2026-006', 'action_type': 'checklist_review', 'status': 'pending', 'assigned_approver_id': 'U-APR-002', 'action_summary': 'Private summary'})
    _storage.write_dataset('approval_requests.json', rows)


def test_assignment_listing_is_minimal_and_isolated_by_approver():
    add_other_approver()
    first = build_collection_payload('trips', 'U-APR-001')
    second = build_collection_payload('trips', 'U-APR-002')
    assert {r['trip_id'] for r in first} == {'TRIP-2026-001', 'TRIP-2026-002'}
    assert {r['trip_id'] for r in second} == {'TRIP-2026-006'}
    assert all(set(r) == {'trip_id', 'action_type', 'action_label', 'status', 'assigned_approver_id', 'allowed_actions'} for r in first + second)
    assert all(r['status'] == 'pending' for r in first + second)
    assert read()['outcome'] == 'completed'
    assert read('U-APR-002', 'TRIP-2026-006')['outcome'] == 'completed'


@pytest.mark.parametrize('uid,trip', [('U-APR-001','TRIP-2026-006'), ('U-APR-002','TRIP-2026-001')])
def test_forged_scope_for_other_approver_does_not_return_facts(uid, trip):
    add_other_approver()
    r = read(uid, trip)
    assert r['route'] == 'REJECT_SAFETY' and r['error']['code'] == 'unauthorized_scope'
    assert 'không có quyền' in r['bot_response']
    assert not r['result'] and not r['citations'] and not r['handoff_required']
    policy = dispatch('search_travel_policy', {'query':'approval policy','category':'approval'}, 'pretrip',
                      {'user_id':uid, 'role':'Approver', 'session_id':'policy', 'approval_scope':{'trip_id':trip,'action_type':'checklist_review'}})
    assert not policy['ok']


def test_missing_assignment_is_fail_closed_and_missing_scope_is_not_a_ticket():
    rows = _storage.load_dataset('approval_requests.json')
    for row in rows: row.pop('assigned_approver_id')
    _storage.write_dataset('approval_requests.json', rows)
    assert build_collection_payload('trips', 'U-APR-001') == []
    assert read()['route'] == 'REJECT_SAFETY'
    r = handle_turn('Xem chi tiết chuyến TRIP-2026-001', 'U-APR-001', session_id='none')
    assert r['error']['code'] == 'unauthorized_scope' and not r['handoff_required']


def test_reassignment_or_resolution_invalidates_old_scope_immediately():
    add_other_approver()
    assert read()['outcome'] == 'completed'
    rows = _storage.load_dataset('approval_requests.json')
    rows[0]['assigned_approver_id'] = 'U-APR-002'
    _storage.write_dataset('approval_requests.json', rows)
    assert read()['route'] == 'REJECT_SAFETY'
    with pytest.raises(ValueError):
        record_external_decision('TRIP-2026-001','checklist_review','approved','reviewed','Reviewed.',actor_id='U-APR-001')
    record_external_decision('TRIP-2026-001','checklist_review','approved','reviewed','Reviewed.',actor_id='U-APR-002')
    assert read('U-APR-002')['route'] == 'REJECT_SAFETY'
    assert not any(r['trip_id'] == 'TRIP-2026-001' for r in build_collection_payload('trips','U-APR-002'))
    for row in rows: row['status'] = 'approved'
    _storage.write_dataset('approval_requests.json', rows)
    assert build_collection_payload('trips','U-APR-001') == []


def test_http_assignment_list_and_chat_recheck_same_permission_boundary():
    add_other_approver()
    def request(path, payload=None):
        body = json.dumps(payload).encode() if payload is not None else b''
        method = 'POST' if payload is not None else 'GET'
        wire = f'{method} {path} HTTP/1.0\r\nContent-Length: {len(body)}\r\n\r\n'.encode() + body
        output = BytesIO()
        class Connection:
            def makefile(self,*args): return BytesIO(wire)
            def sendall(self,data): output.write(data)
        make_handler()(Connection(),('127.0.0.1',0),SimpleNamespace())
        headers, response = output.getvalue().split(b'\r\n\r\n',1)
        return int(headers.split()[1]), json.loads(response)
    status, rows = request('/api/trips?user_id=U-APR-001')
    assert status == 200 and len(rows) == 2
    status, result = request('/api/chat', {'user_id':'U-APR-001','session_id':'http', 'message':'Xem chi tiết chuyến TRIP-2026-006', 'approval_scope':{'trip_id':'TRIP-2026-006','action_type':'checklist_review'}})
    assert status == 200 and result['error']['code'] == 'unauthorized_scope'
    assert 'Sydney' not in result['bot_response']
