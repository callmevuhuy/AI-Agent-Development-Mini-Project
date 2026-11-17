"""Tác vụ Trips dùng chung; menu không thay thế việc kiểm tra quyền tại server."""
import re

from travel_agent.nlu import RouteDecision

LABELS = {'details': 'Xem chi tiết', 'itinerary': 'Xem hành trình',
          'checklist': 'Kiểm tra checklist', 'support': 'Tạo yêu cầu phê duyệt hỗ trợ',
          'audit': 'Xem audit liên quan'}
ROLE_ACTIONS = {'Employee': ['details', 'itinerary', 'checklist', 'support'],
                'Reviewer': ['details', 'itinerary', 'checklist'], 'Admin': ['audit']}


def available_actions(role: str, scope_action: str | None = None) -> list[str]:
    if role == 'Approver':
        if scope_action == 'escalation':
            return ['itinerary']
        if scope_action in {'checklist_review', 'publish_request'}:
            return ['details']
        return []
    return list(ROLE_ACTIONS.get(role, []))


def action_decision(action: str, trip_id: str) -> RouteDecision:
    if action not in LABELS or not isinstance(trip_id, str) or not re.fullmatch(r'TRIP-\d{4}-\d{3}', trip_id):
        raise ValueError('Thao tác hoặc mã chuyến không hợp lệ.')
    intents = {'details': 'trip_details', 'itinerary': 'itinerary_read', 'checklist': 'pretrip',
               'support': 'request_approval', 'audit': 'admin_overview'}
    return RouteDecision('SELF_SERVE', intents[action], trip_id=trip_id,
                         draft_requested=action == 'checklist',
                         approval_action='escalation' if action == 'support' else None,
                         admin_action='audit' if action == 'audit' else None)


def trip_reference(user_id, trip_id, action_type=None):
    """Đọc lại nguồn và quyền hiện tại khi mở thẻ tham chiếu, không dùng cache chat."""
    from travel_agent.mock_systems.user import get_user
    from travel_agent.dispatcher import dispatch
    user = get_user(user_id)
    if not user:
        raise ValueError('Không tìm thấy tài khoản demo.')
    action_decision('details', trip_id)
    context = {'user_id':user_id, 'role':user['role'], 'session_id':'trip-reference'}
    itinerary = user['role'] == 'Approver' and action_type == 'escalation'
    if user['role'] == 'Approver':
        context['approval_scope'] = {'trip_id':trip_id, 'action_type':action_type}
    res = dispatch('get_itinerary' if itinerary else 'get_trip_request', {'trip_id':trip_id},
                   'intrip' if itinerary else 'pretrip', context)
    if not res['ok']:
        raise PermissionError(res['error']['message'])
    data = res['data']
    if itinerary:
        flight = data.get('flight',{})
        fields = {k:flight.get(k) for k in ('flight_id','origin','destination','departure','arrival','status')}
        fields['disruption'] = data.get('disruption')
    else:
        fields = {k:data.get(k) for k in ('destination','start_date','end_date','purpose','travel_status')}
    return {'trip_id':trip_id, 'kind':'itinerary' if itinerary else 'trip', 'fields':fields,
            'source':res['meta']['source']}
