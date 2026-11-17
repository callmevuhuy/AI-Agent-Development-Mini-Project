const vm=require('vm'), fs=require('fs'), assert=require('assert/strict');
const script=fs.readFileSync(process.argv[2],'utf8');
class Element {
  constructor(){this.children=[];this.events={};this.textContent='';this.value='U-REV-001';}
  appendChild(child){this.children.push(child);}
  querySelector(){return this.bubble ||= new Element();}
  setAttribute(){}
  addEventListener(name,fn){this.events[name]=fn;}
}
const stream=new Element(), user=new Element();
const calls=[];
const ctx=vm.createContext({document:{getElementById:id=>id==='user'?user:stream,createElement:()=>new Element(),createTextNode:s=>({textContent:s})},
  esc:String,uiLabel:String,formatMarkdown:String,userGeneration:0,URLSearchParams,
  fetch:async url=>{calls.push(url);return {ok:true,json:async()=>({trip_id:'TRIP-2026-006',fields:{destination:'Sydney',purpose:'<script>test</script>'},source:'mock'})};}});
vm.runInContext(script.slice(script.indexOf('function appendBotMsg'),script.indexOf('// Xử lý gửi tin nhắn')),ctx);
ctx.data={responses:[{request:'Read',bot_response:'Allowed',trip_references:[{trip_id:'TRIP-2026-006'}]}, {request:'Request approval',bot_response:'Denied',route:'REJECT_SAFETY'}]};
vm.runInContext('appendBotMsg(data)',ctx);
assert.equal(stream.children.length,2);
const button=stream.children[0].bubble.children[0].children[0];
assert.equal(stream.children[1].bubble.children[0].children.length,0);
assert(button.events.mouseenter && button.events.focus);
(async()=>{
  await button.events.mouseenter();
  assert(calls[0].includes('/api/trip/reference?'));
  assert(button.children[1].textContent.includes('Sydney'));
  assert(button.children[1].textContent.includes('<script>test</script>')); // Chỉ gán textContent, không nội suy HTML.
  await button.events.focus();
  assert.equal(calls.length,2); // Mỗi lần mở đều kiểm tra lại quyền/nguồn.
  ctx.fetch=async()=>({ok:false,json:async()=>({error:'Không có quyền'})});
  await button.events.mouseenter();
  assert.equal(button.children[1].textContent,'Không có quyền');
  console.log('PASS: multiple bubbles, accessible Trip reference, safe text and permission reload');
})().catch(error=>{console.error(error);process.exitCode=1;});
