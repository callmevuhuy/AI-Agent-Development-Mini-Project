"""Golden expectations for the exact demo cards, independent of router output."""
import re
from travel_agent.web_demo import _HTML
from travel_agent.conversation import handle_turn

S, C, H, R = 'SELF_SERVE', 'CLARIFY', 'HANDOFF_STAFF', 'REJECT_SAFETY'
EXPECTED_ROUTES = {
    'U-EMP-002': [S,S,S,S,S,S,C,S,R,R],
    'U-EMP-001': [S,C,H,H,S,S],
    'U-REV-001': [S,H,C,R,H],
    'U-APR-001': [S,S,H,R,R],
    'U-ADM-001': [S,S,S,R,R],
}
EXPECTED_TOOLS = {
    'U-EMP-002': ['get_itinerary','create_travel_checklist_draft','calculate_expense_summary','search_travel_policy','request_approval','set_preference',None,None,None,'get_trip_request'],
    'U-EMP-001': ['create_travel_checklist_draft',None,'get_trip_request','calculate_expense_summary',None,'search_travel_policy'],
    'U-REV-001': ['list_my_trips','calculate_expense_summary','get_trip_request',None,'search_travel_policy'],
    'U-APR-001': ['get_trip_request','get_itinerary','search_travel_policy','get_trip_request','search_travel_policy'],
    'U-ADM-001': ['admin_list_trips','admin_get_audit_history','admin_get_audit_history',None,None],
}


def evaluate_cards():
    cases = []
    for uid, group in re.findall(r"'(U-[A-Z]+-\d+)': \[(.*?)\n  \]", _HTML, re.S):
        prompts = re.findall(r"prompt: '([^']*)'", group)
        assert len(prompts) == len(EXPECTED_ROUTES[uid])
        for i, prompt in enumerate(prompts):
            scope = None
            if uid == 'U-APR-001':
                scope = {'trip_id': 'TRIP-2026-002' if i == 1 else 'TRIP-2026-001', 'action_type': 'escalation' if i == 1 else 'checklist_review'}
            r = handle_turn(prompt, uid, session_id=f'web-eval-{i}', approval_scope=scope)
            tool = EXPECTED_TOOLS[uid][i]
            events = [e for e in r['trace'] if e.get('action') == 'tool_call']
            tool_correct = any(e.get('tool') == tool for e in events) if tool else not events
            ids = re.findall(r'(?:TRIP|EXP)-\d{4}-\d{3}', prompt)
            argument_correct = all(any(value in e.get('safe_args', {}).values() for e in events) for value in ids) if tool else not events
            passed = r['route'] == EXPECTED_ROUTES[uid][i] and bool(r['bot_response'])
            if uid == 'U-EMP-002' and i == 3:
                passed = passed and '250' in r['bot_response'] and bool(r['citations'])
            if uid == 'U-EMP-002' and i == 8:
                passed = passed and r['step_count'] == 0 and not r['handoff_required']
            cases.append({'case_id': f'WEB_{uid}_{i+1:02}', 'passed': bool(passed), 'safety': EXPECTED_ROUTES[uid][i] == R,
                          'detail': f"{r['route']}; {r['outcome']}", 'steps': r['step_count'],
                          'tool_correct': tool_correct, 'argument_correct': argument_correct,
                          'retries': sum(e.get('transition') == 'retry_scheduled' for e in r['trace'])})
    return cases
