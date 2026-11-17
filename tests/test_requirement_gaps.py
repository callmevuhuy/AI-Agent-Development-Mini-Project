"""Kiểm tra điều kiện nghiệm thu sâu hơn terminal outcome của workflow."""
from dataclasses import replace
import pytest
from test_conversational_and_fixes import isolate_runtime_dirs
from travel_agent.app import run_workflow
from travel_agent.conversation import handle_turn
from travel_agent.dispatcher import dispatch
from travel_agent.registry import TOOL_REGISTRY
from travel_agent.mock_systems import _storage, draft_workspace
from travel_agent.orchestrator import run_tool
from travel_agent.state import RunState
from travel_agent.tools._result import failure


def ctx():
    return {'user_id':'U-EMP-002','role':'Employee','session_id':'requirements'}


@pytest.mark.parametrize('trip,outcome', [('TRIP-2026-001','awaiting_approval'), ('TRIP-2026-004','needs_human')])
def test_blocked_approval_never_saves_checklist(trip, outcome):
    before = _storage.load_dataset('approvals.json')
    result, state = run_workflow('pretrip','U-EMP-001',trip)
    assert result['outcome'] == outcome and 'draft' not in result
    assert not list(draft_workspace.DRAFT_DIR.glob('*.json'))
    assert not any(e.get('tool') == 'create_travel_checklist_draft' for e in state.trace)
    assert _storage.load_dataset('approvals.json') == before


@pytest.mark.parametrize('output', [None, {}, {'ok':True,'data':{}}, {'ok':False}, {'ok':'yes'}])
def test_dispatcher_rejects_malformed_observations(monkeypatch, output):
    spec = TOOL_REGISTRY['get_trip_request']
    monkeypatch.setitem(TOOL_REGISTRY,'get_trip_request',replace(spec,handler=lambda arguments: output))
    result = dispatch('get_trip_request',{'trip_id':'TRIP-2026-006'},'pretrip',ctx())
    assert not result['ok'] and result['error']['code'] == 'unavailable'
    assert not result['error']['retryable'] and 'data' not in result


@pytest.mark.parametrize('tool,args,workflow,code', [
    ('unknown_tool',{},'pretrip','not_allowed'),
    ('get_expense_report',{'report_id':'EXP-2026-001'},'pretrip','not_allowed'),
    ('get_trip_request',{'trip_id':'TRIP-2026-006','role':'Admin'},'pretrip','invalid_argument'),
    ('search_travel_policy',{'query':'x'*201,'category':'travel'},'pretrip','invalid_argument'),
    ('search_travel_policy',{'query':'travel policy','category':'travel','max_results':100},'pretrip','invalid_argument'),
])
def test_invalid_calls_stop_before_handler(monkeypatch, tool, args, workflow, code):
    calls = []
    for name, spec in list(TOOL_REGISTRY.items()):
        monkeypatch.setitem(TOOL_REGISTRY,name,replace(spec,handler=lambda arguments: calls.append(arguments)))
    result = dispatch(tool,args,workflow,ctx())
    assert result['error']['code'] == code and not calls


@pytest.mark.parametrize('workflow,record,tool', [
    ('pretrip','TRIP-2026-006','create_travel_checklist_draft'),
    ('intrip','TRIP-2026-002','create_escalation_or_support_draft'),
    ('posttrip','EXP-2026-001','create_expense_review_draft'),
])
def test_failed_save_is_partial_then_retry_keeps_single_artifact(monkeypatch, workflow, record, tool):
    original = TOOL_REGISTRY[tool]
    monkeypatch.setitem(TOOL_REGISTRY,tool,replace(original,handler=lambda arguments: failure('unavailable','Save failed.',retryable=False)))
    result, state = run_workflow(workflow,'U-EMP-002',record)
    assert result['outcome'] == 'partial' and 'draft' not in result
    assert not list(draft_workspace.DRAFT_DIR.glob('*.json'))
    assert sum(e.get('tool') == tool and e.get('action') == 'tool_call' for e in state.trace) == 1
    monkeypatch.setitem(TOOL_REGISTRY,tool,original)
    first, _ = run_workflow(workflow,'U-EMP-002',record)
    second, _ = run_workflow(workflow,'U-EMP-002',record)
    assert first['draft']['draft_id'] == second['draft']['draft_id']
    assert len(list(draft_workspace.DRAFT_DIR.glob('*.json'))) == 1
    assert first['draft']['delivery_status'] in {'not_sent','not_published'}


def test_missing_policy_stops_end_to_end_without_fake_citations():
    _storage.write_dataset('policy_chunks.json',[])
    result = handle_turn('Chuẩn bị checklist TRIP-2026-006','U-EMP-002',session_id='empty-policy')
    assert result['outcome'] == 'needs_human'
    assert not result['citations']
    assert not result['result'].get('checklist',{}).get('evidence')


def test_followup_reloads_facts_after_mock_changes():
    first = handle_turn('Xem hành trình TRIP-2026-002','U-EMP-002',session_id='fresh')
    rows = _storage.load_dataset('itineraries.json')
    row = next(r for r in rows if r['trip_id'] == 'TRIP-2026-002')
    row['flight']['flight_id'] = 'MOCK-UPDATED'
    _storage.write_dataset('itineraries.json', rows)
    second = handle_turn('Xem hành trình TRIP-2026-002','U-EMP-002',session_id='fresh')
    assert 'MOCK-UPDATED' not in first['bot_response']
    assert 'MOCK-UPDATED' in second['bot_response']
    assert any(e.get('tool') == 'get_itinerary' for e in second['trace'])


def test_non_retryable_errors_are_not_retried(monkeypatch):
    import travel_agent.orchestrator as orchestrator
    calls=[]
    monkeypatch.setattr(orchestrator,'dispatch',lambda *a,**kw: (calls.append(1) or failure('invalid_argument','Invalid.',retryable=False)))
    state=RunState('pretrip',ctx())
    run_tool(state,'get_trip_request',{'trip_id':'TRIP-2026-006'})
    assert len(calls) == state.step_count == 1


def test_training_dataset_minimum_and_lineage():
    trips=_storage.load_dataset('trips.json')
    travelers=_storage.load_dataset('travelers.json')
    itineraries=_storage.load_dataset('itineraries.json')
    expenses=_storage.load_dataset('expenses.json')
    chunks=_storage.load_dataset('policy_chunks.json')
    assert len(trips)>=6 and len(travelers)>=4 and len(itineraries)>=4 and len(expenses)>=3 and len(chunks)>=8
    assert len({t['department'] for t in travelers})>=2
    assert all({'chunk_id','doc_id','source','section','version','category','text'} <= c.keys() for c in chunks)
    assert {'travel','expense','visa','insurance','approval'} <= {c['category'] for c in chunks}
    ids={t['trip_id'] for t in trips}
    assert all(r['trip_id'] in ids for r in itineraries+expenses)
