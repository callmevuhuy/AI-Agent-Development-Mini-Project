const fs = require('fs');
const vm = require('vm');
const assert = require('assert/strict');
const script = fs.readFileSync(process.argv[2], 'utf8');
class Element {
  constructor() { this.value = ''; this.children = []; this.button = {}; this.textContent = ''; }
  set innerHTML(html) {
    this.html = html;
    this.children = [];
    const match = html.match(/<button\b([^>]*)>/);
    if (match) this.button = {disabled: /\bdisabled\b/.test(match[1])};
  }
  get innerHTML() { return this.html; }
  appendChild(child) { this.children.push(child); }
  querySelector() { return this.button; }
}
const elements = new Map();
const element = id => {
  if (!elements.has(id)) elements.set(id, new Element());
  return elements.get(id);
};
let role = 'Approver';
let sent = [];
let fetched = [];
const context = vm.createContext({
  document: {getElementById: element, createElement: () => new Element(), querySelector: element},
  esc: v => String(v), currentRole: () => role, uiLabel: v => v,
  switchView: () => {}, sendTurn: payload => sent.push(payload),
  appendUserMsg: () => {}, showTypingIndicator: () => () => {}, appendSystemMsg: () => {},
  isAgentThinking: false, userGeneration: 0, Math,
  setTimeout: fn => { fn(); return 0; },
  fetch: async (url, options) => { fetched.push({url, payload: JSON.parse(options.body)}); return {ok:false, json:async()=>({code:'unauthorized_scope', error:'Denied'})}; },
});
vm.runInContext(script.slice(script.indexOf('function updateApprovalOptions'), script.indexOf('// Quản lý Drafts')), context);
const rows = [
  {trip_id:'TRIP-2026-001',action_type:'checklist_review',action_label:'Xem xét checklist',assigned_approver_id:'U-APR-001',allowed_actions:['details']},
  {trip_id:'TRIP-2026-002',action_type:'escalation',action_label:'Xem xét hỗ trợ',assigned_approver_id:'U-APR-001',allowed_actions:['itinerary']},
];
context.rows = rows;
const scope = element('approval-scope');
function render() { vm.runInContext('renderAssignedRequests(rows)', context); return element('trips-table-body').children; }
let rendered = render();
assert(rendered.every(row => row.button.disabled));
for (const [index, action] of [[0,'details'],[1,'itinerary']]) {
  scope.value = rows[index].trip_id + '|' + rows[index].action_type;
  rendered = render();
  assert.equal(rendered[index].button.disabled, false);
  assert.equal(rendered[1-index].button.disabled, true);
  const previous = scope.value;
  rendered[1-index].button.onclick(); // Ngay cả khi gọi handler của nút khóa.
  assert.equal(scope.value, previous);
  assert.equal(sent.length, index);
  rendered[index].button.onclick();
  assert.equal(scope.value, previous);
  assert.deepEqual(JSON.parse(JSON.stringify(sent[index])), {trip_id:rows[index].trip_id,action,request_action_type:rows[index].action_type});
}
vm.runInContext('updateApprovalOptions(rows)', context);
assert.equal(scope.value, 'TRIP-2026-002|escalation');
vm.runInContext('updateApprovalOptions([])', context);
assert.equal(scope.value, '');
context.rows = [{...rows[0],action_type:'publish_request'}, rows[0]];
scope.value = 'TRIP-2026-001|checklist_review';
rendered = render();
assert.equal(rendered[0].button.disabled, true);
assert.equal(rendered[1].button.disabled, false);
for (const [nextRole, actions] of [['Employee',['details','itinerary','checklist','support']],['Reviewer',['details','itinerary','checklist']],['Admin',['audit']]]) {
  role = nextRole;
  context.trips = [{trip_id:'TRIP-2026-006',allowed_actions:actions,travel_status:'submitted'}];
  vm.runInContext('renderTripsTable(trips)', context);
  const html = element('trips-table-body').children[0].innerHTML;
  const options = [...html.matchAll(/<option value="([^"]+)"/g)].map(m => m[1]);
  assert.deepEqual(options, actions);
}
// Thực thi sendTurn thật để xác minh payload không thay scope và không gửi prompt tự do cho Trips.
vm.runInContext(script.slice(script.indexOf('async function sendTurn('), script.indexOf('// Quản lý Chuyến đi & Lịch trình')), context);
role = 'Approver';
scope.value = 'TRIP-2026-001|checklist_review';
element('user').value = 'U-APR-001';
element('session').value = 'ui-smoke';
element('chat-input').value = 'Xem hồ sơ';
(async () => {
  await vm.runInContext("sendTurn({trip_id:'TRIP-2026-001',action:'details',request_action_type:'checklist_review'})", context);
  assert.equal(fetched[0].url, '/api/trip/action');
  assert.equal(fetched[0].payload.approval_scope.action_type, 'checklist_review');
  assert.equal(fetched[0].payload.request_action_type, 'checklist_review');
  assert.equal(fetched[0].payload.action, 'details');
  assert.equal(scope.value, 'TRIP-2026-001|checklist_review');
  element('chat-input').value = 'Hỏi trợ lý';
  await vm.runInContext('sendTurn()', context);
  assert.equal(fetched[1].url, '/api/chat');
  assert.equal(fetched[1].payload.message, 'Hỏi trợ lý');
  console.log('PASS: scope độc lập, hai chiều lệch scope, cùng Trip khác loại yêu cầu, menu mọi role, payload Trips/chat.');
})().catch(error => { console.error(error); process.exitCode = 1; });
