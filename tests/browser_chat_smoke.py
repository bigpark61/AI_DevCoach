"""Optional Chromium UI tests with an in-browser API fixture (no real credentials).
Run: python tests/browser_chat_smoke.py
Install optional dependency: pip install playwright; playwright install chromium
Backend persistence and account isolation are separately tested by unittest.
"""
import json
import os
import re
from pathlib import Path

from playwright.sync_api import sync_playwright, expect

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = r'''
window.fixture = {user: null, histories: {}, pending: null, calls: []};
window.fetch = async (url, options = {}) => {
  const path = String(url); const f = window.fixture;
  const body = options.body ? JSON.parse(options.body) : {};
  f.calls.push(path);
  const respond = (data, status=200) => new Response(status===204 ? null : JSON.stringify(data), {status, headers:{'Content-Type':'application/json'}});
  if (path === '/api/auth/login') {
    f.user = {id:body.email, email:body.email};
    return respond(f.user);
  }
  if (path === '/api/auth/logout') {f.user=null;return respond(null,204);}
  if (!f.user) return respond({detail:'로그인이 필요합니다.'},401);
  if (path === '/api/agent/history') return respond({messages:f.histories[f.user.id] || []});
  if (path === '/api/progress/dashboard') return respond({plan_id:'test'});
  if (path === '/api/coach/progress-feedback') return respond({completion_rate:0,blocked_tasks:0,summary:'테스트 코칭',actions:['다음 행동'],generated_at:new Date().toISOString()});
  if (path === '/api/agent/chat') {
    if (body.message === 'FAIL TEST') return respond({detail:'테스트 전송 실패'},502);
    const owner = f.user.id;
    const finish = () => {
      const reply = '테스트 답변: ' + body.message;
      (f.histories[owner] ||= []).push({role:'user', content:body.message}, {role:'assistant',content:reply,sources:[]});
      return respond({reply, sources:[]});
    };
    if (body.message === 'DELAYED TEST') return new Promise(resolve=>{f.pending=()=>{f.pending=null;resolve(finish());};});
    return finish();
  }
  throw new Error('Unexpected test request: '+path);
};
'''

def run():
    results = []
    html = re.sub(r'<script[^>]*src="[^"]*"[^>]*></script>', '', (ROOT/'frontend/index.html').read_text())
    html = re.sub(r'<link[^>]*>', '', html)
    with sync_playwright() as p:
        options = {'headless': True, 'args': ['--no-sandbox']}
        if os.getenv('PLAYWRIGHT_CHROMIUM_EXECUTABLE'):
            options['executable_path'] = os.environ['PLAYWRIGHT_CHROMIUM_EXECUTABLE']
        browser = p.chromium.launch(**options)
        page = browser.new_page(viewport={'width':1360,'height':950})
        errors=[]
        page.on('pageerror',lambda e:errors.append(str(e)))
        page.set_default_timeout(5000)
        print('Browser initialized', flush=True)
        page.set_content(html)
        print('DOM ready', flush=True)
        page.add_style_tag(content='.error{display:none}.error.show{display:block}')
        page.add_script_tag(content=FIXTURE)
        print('API fixture ready', flush=True)
        page.add_script_tag(content=(ROOT/'frontend/app.js').read_text())
        print('Application loaded', flush=True)
        # Isolate chat UI from profile/assessment onboarding; actual backend auth is
        # covered by test_chat_persistence.py and test_app.py.
        page.evaluate('() => { continueUser = async () => openProgressView("agent"); }')
        def login(email):
            page.locator('#email').fill(email)
            page.locator('#password').fill('correct-horse-42')
            page.locator('#auth-form button[type=submit]').click()
            page.locator('#agent-message').wait_for()
        def send(message):
            page.locator('#agent-message').fill(message)
            page.locator('#agent-chat-form button[type=submit]').click()
        login('alpha@example.com'); print('Login OK',flush=True); send('처음 질문입니다')
        expect(page.locator('.agent-message')).to_have_count(2)
        page.locator('#logout-action').click();login('alpha@example.com')
        expect(page.locator('.agent-message')).to_have_count(2)
        results.append('PASS: logout/login restores chat from history API fixture')
        if os.getenv('DEVCOACH_SCREENSHOT'):
            page.screenshot(path=os.environ['DEVCOACH_SCREENSHOT'],full_page=True)
        page.locator('[data-progress-view="coach"]').click()
        expect(page.locator('.coach-panel')).to_be_visible()
        assert page.locator('#revision-request-form').count()==0
        assert page.get_by_text('재계획 요청 제출',exact=True).count()==0
        results.append('PASS: replan form/button absent; coaching panel remains')
        page.locator('[data-progress-view="agent"]').click()
        send('FAIL TEST')
        expect(page.locator('#agent-chat-error')).to_be_visible()
        expect(page.locator('#agent-message')).to_have_value('FAIL TEST')
        expect(page.locator('.agent-message')).to_have_count(2)
        results.append('PASS: failed send preserves draft and adds no fake answer')
        send('DELAYED TEST');page.wait_for_function('!!fixture.pending')
        page.locator('#logout-action').click();login('beta@example.com')
        expect(page.locator('.agent-message')).to_have_count(0)
        page.evaluate('fixture.pending()')
        expect(page.locator('.agent-message')).to_have_count(0)
        assert page.evaluate('state.agentHistory.length')==0
        results.append('PASS: stale reply from prior login does not enter new account')
        page.locator('#logout-action').click();login('alpha@example.com')
        expect(page.locator('.agent-message')).to_have_count(4)
        results.append('PASS: completed in-flight turn reloads for original account')
        send('DELAYED TEST');page.wait_for_function('!!fixture.pending')
        page.locator('[data-progress-view="coach"]').click()
        expect(page.locator('.coach-panel')).to_be_visible()
        page.evaluate('fixture.pending()')
        expect(page.locator('.coach-panel')).to_be_visible()
        assert page.locator('#agent-chat-form').count()==0
        results.append('PASS: late chat response does not change current non-chat view')
        assert not errors,errors
        results.append('PASS: no browser JavaScript exceptions')
        browser.close()
    print('\n'.join(results))

if __name__ == '__main__':
    run()
