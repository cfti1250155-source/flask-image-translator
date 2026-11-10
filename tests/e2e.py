"""ブラウザ(Playwright/Chromium)での動作確認。CDN(Tailwind等)は遮断するため見た目の崩れは検証できない。
使い方: python tests/e2e.py"""
import os, sys, threading, types
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT); sys.path.insert(0, os.path.join(ROOT, "tests"))
import conftest  # noqa: F401  (ダミーgenaiを入れる)
import translator
from werkzeug.serving import make_server
from app import app

def fake(parts, system=None):
    if system and "explanation" in system: return '{"explanation":"slang!"}'
    return '{"detected_language":"Japanese","source_text":"こんにちは","translation":"Hello"}'
translator._generate = fake
srv = make_server("127.0.0.1", 5077, app, threaded=True)
threading.Thread(target=srv.serve_forever, daemon=True).start()
B = "http://127.0.0.1:5077"
errs, fails = [], []
def check(name, cond):
    print(("OK   " if cond else "FAIL ") + name)
    if not cond: fails.append(name)

from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    br = p.chromium.launch()
    for run in range(5):   # switchTab 未定義のフレーク検出のため複数回
        ctx = br.new_context(viewport={"width": 390, "height": 800})
        ctx.route("**/*", lambda r: r.abort() if not r.request.url.startswith(B) else r.continue_())
        pg = ctx.new_page()
        pg.add_init_script("window.speechSynthesis={speak(){},cancel(){},getVoices(){return[]}};window.SpeechSynthesisUtterance=function(t){this.text=t}")
        pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.goto(B + "/start")
        pg.evaluate("document.querySelector('#start-form').requestSubmit ? 0:0")
        pg.request.post(B + "/set-display-language", form={"ui_lang": "Japanese"})
        r = pg.context.request.post(B + "/set-display-language", form={"ui_lang": "Japanese"})
        pg.goto(B + "/", wait_until="domcontentloaded")
        # 読み込み直後の素早いタップでも落ちないこと
        pg.click("#nav-conversation")
        pg.wait_for_function("typeof setSpeaker==='function' && document.getElementById('tab-conversation') && !document.getElementById('tab-conversation').classList.contains('hidden')")
        check(f"run{run}: chat tab opens right after load", True)
        pg.click("#nav-text")
        src = pg.inner_text("#source-lang-container"); tgt = pg.inner_text("#target-lang-container")
        check(f"run{run}: From=自動判定 / To=English ({src!r},{tgt!r})", "自動判定" in src and "English" in tgt)
        # 空送信はブラウザ側で止まる
        pg.click("#tab-text button[type=submit]")
        check(f"run{run}: empty text blocked", pg.url.rstrip("/") == B)
        pg.fill("textarea[name=direct_text]", "こんにちは")
        pg.click("#tab-text button[type=submit]")
        pg.wait_for_selector("text=Hello")
        check(f"run{run}: translation shown", True)
        pg.wait_for_function("JSON.parse(localStorage.getItem('tl_history_v1')||'[]').length>0")
        hist = pg.evaluate("JSON.parse(localStorage.getItem('tl_history_v1')||'[]').length")
        check(f"run{run}: history saved", hist == 1)
        ctx.close()
    # チャット
    ctx = br.new_context(viewport={"width": 390, "height": 800})
    ctx.route("**/*", lambda r: r.abort() if not r.request.url.startswith(B) else r.continue_())
    pg = ctx.new_page(); pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.add_init_script("window.speechSynthesis={speak(){},cancel(){},getVoices(){return[]}};window.SpeechSynthesisUtterance=function(t){this.text=t}")
    pg.context.request.post(B + "/set-display-language", form={"ui_lang": "Japanese"})
    pg.goto(B + "/"); pg.click("#nav-conversation")
    pg.fill("#conv-input", "やっほー"); pg.press("#conv-input", "Enter")
    pg.wait_for_selector("#conv-log >> text=Hello")
    check("chat bubble translated, speaker switched", "border-emerald-500" in pg.get_attribute("#chat-card-B", "class"))
    # エラー表示 (翻訳失敗)
    def boom(parts, system=None): raise type("ReadTimeout", (Exception,), {})("t")
    translator._generate = boom
    pg.fill("#conv-input", "えらー"); pg.press("#conv-input", "Enter")
    pg.wait_for_selector("#conv-log >> text=時間がかかり")
    check("timeout message shown in chat", True)
    br.close()
bad = [e for e in errs if "switchTab" in e or "is not defined" in e]
check(f"no JS page errors ({errs})", not errs)
print("FAILS:", fails); sys.exit(1 if fails else 0)
