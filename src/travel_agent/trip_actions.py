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
