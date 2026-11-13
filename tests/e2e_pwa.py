"""ステップ3（ホーム画面追加・オフライン・フレーズ集）のブラウザ確認。使い方: python tests/e2e_pwa.py
※ Tailwind/FontAwesome の CDN は遮断して試すので、見た目（スタイル）は確認できません。"""
import json, os, sys, tempfile, threading
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT); sys.path.insert(0, os.path.join(ROOT, "tests"))
import conftest  # noqa: F401
from werkzeug.serving import make_server
from app import app, ASSET_V

srv = make_server("127.0.0.1", 5077, app, threaded=True)
threading.Thread(target=srv.serve_forever, daemon=True).start()
B = "http://127.0.0.1:5077"
fails, errs = [], []
def check(name, cond):
    print(("OK   " if cond else "FAIL ") + name)
    if not cond: fails.append(name)

SEED = """(() => { const now = Date.now();
  localStorage.setItem('tl_history_v1', JSON.stringify([
    {id:'h1', ts:now-1000, fav:true, mode:'text', src:'こんにちは', out:'Hello', srcLang:'Japanese', tgt:'English', tcode:'en-US'},
    {id:'h2', ts:now-2000, fav:false, mode:'text', src:'ありがとう', out:'Thanks', srcLang:'Japanese', tgt:'English', tcode:'en-US'}]));
  localStorage.setItem('tl_glossary_v1', JSON.stringify([{id:'g1', kind:'term', term:'草', meaning:'lol', to:'English', ts:now}]));
})()"""

from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    br = p.chromium.launch()
    ctx = br.new_context(viewport={"width": 390, "height": 800}, accept_downloads=True)
    ctx.route("**/*", lambda r: r.abort() if not r.request.url.startswith(B) else r.continue_())
    pg = ctx.new_page()
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.on("dialog", lambda d: d.accept())
    pg.add_init_script("SpeechSynthesis.prototype.speak=function(){window.__spoken=(window.__spoken||0)+1}")
    ctx.request.post(B + "/set-display-language", form={"ui_lang": "Japanese"})

    # --- manifest / SW 登録 ---
    pg.goto(B + "/"); pg.evaluate(SEED)
    man = ctx.request.get(B + "/manifest.webmanifest").json()
    check("manifest ok", man["short_name"] == "TOOKIE" and len(man["icons"]) == 3)
    check("manifest linked in page", pg.get_attribute("link[rel=manifest]", "href") == "/manifest.webmanifest")
    pg.wait_for_function("navigator.serviceWorker && navigator.serviceWorker.controller === null || true")
    pg.evaluate("navigator.serviceWorker.ready.then(() => 1)")
    pg.reload()
    pg.wait_for_function("navigator.serviceWorker.controller !== null", timeout=15000)
    check("service worker controls the page", True)
    keys = pg.evaluate("caches.keys()")
    check(f"cache created for this version ({keys})", ("tookie-" + ASSET_V) in keys)
    cached = pg.evaluate("(async()=>{const c=await caches.open('tookie-'+%s);return (await c.keys()).map(r=>new URL(r.url).pathname+new URL(r.url).search)})()" % json.dumps(ASSET_V))
    for must in ["/offline", f"/static/js/app.js?v={ASSET_V}", f"/static/js/history.js?v={ASSET_V}", "/static/phrasebook/ko-kr.json", "/static/phrasebook/index.json"]:
        check(f"precached {must}", must in cached)
    check("API is not cached", not any(u.startswith("/api") for u in cached))

    # --- オンラインモードでは、通信が切れても勝手にオフライン画面へ切り替えない ---
    ctx.set_offline(True)
    try:
        pg.goto(B + "/"); swapped = pg.locator("#offline-status").count() > 0
    except Exception:
        swapped = False
    check("online mode: no automatic swap to the offline page", not swapped)
    ctx.set_offline(False)

    # --- 完全オフライン（オフラインモードを選んだ状態） ---
    pg.goto(B + "/")
    pg.evaluate("setNetMode('offline')")
    ctx.set_offline(True)
    pg.goto(B + "/")
    check("offline: navigation shows offline page", "オフラインです" in pg.inner_text("#offline-status"))
    check("offline: title", "オフライン" in pg.title())
    # 履歴
    pg.click("#hf-all")
    txt = pg.inner_text("#history-list")
    check("offline: history readable", "Hello" in txt and "Thanks" in txt)
    pg.click("#hf-fav")
    check("offline: favorites filter", "Hello" in pg.inner_text("#history-list") and "Thanks" not in pg.inner_text("#history-list"))
    pg.click("#hf-gl")
    check("offline: glossary readable", "lol" in pg.inner_text("#glossary-list"))
    check("offline: no reuse button on offline page", pg.locator("#history-list [title=再利用]").count() == 0)
    # フレーズ集
    pg.click("#hf-phrases")
    pg.wait_for_selector("#phrase-list >> text=Hello") if False else pg.wait_for_function("document.querySelectorAll('#phrase-list > div.space-y-2 > div').length === 81")
    check("offline: phrasebook shows 81 phrases (Japanese UI -> default English)", pg.inner_text("#phrase-lang") != "" and pg.input_value("#phrase-lang") == "English")
    pg.select_option("#phrase-lang", "Korean")
    pg.wait_for_function("document.querySelector('#phrase-list').innerText.includes('안녕하세요')")
    check("offline: switch to Korean", "감사합니다" in pg.inner_text("#phrase-list") and "こんにちは" in pg.inner_text("#phrase-list"))
    pg.fill("#phrase-search", "駅")
    pg.wait_for_function("document.querySelectorAll('#phrase-list > div.space-y-2 > div').length === 1")
    check("offline: search by Japanese meaning", "역이 어디예요" in pg.inner_text("#phrase-list"))
    pg.fill("#phrase-search", "zzzz")
    pg.wait_for_function("!document.getElementById('phrase-empty').classList.contains('hidden')")
    check("offline: empty search message", True)
    pg.fill("#phrase-search", "")
    pg.wait_for_function("document.querySelectorAll('#phrase-list > div.space-y-2 > div').length === 81")
    pg.click("#phrase-list button[title=読み上げ]")
    check("offline: speak button calls TTS", pg.evaluate("window.__spoken") >= 1)
    pg.select_option("#phrase-lang", "Arabic")
    pg.wait_for_function("document.querySelector('#phrase-list').innerText.includes('مرحباً')")
    check("offline: RTL text rendered with dir=auto", pg.get_attribute("#phrase-list div.space-y-2 > div div[dir=auto]", "dir") == "auto")
    check("offline: language choice remembered", pg.evaluate("localStorage.getItem('tl_phrase_lang_v1')") == "Arabic")
    # バックアップ書き出しもオフラインで
    pg.click("#hf-settings")
    with pg.expect_download() as dl:
        pg.click("text=バックアップを書き出す")
    path = os.path.join(tempfile.mkdtemp(), "b.json"); dl.value.save_as(path)
    check("offline: backup export works", len(json.load(open(path, encoding="utf-8"))["data"]["history"]) == 2)
    check("install box hidden when not installable", pg.is_hidden("#install-box"))

    # --- オフラインで翻訳を送信 → オフライン画面 ---
    ctx.set_offline(False)
    pg.goto(B + "/")
    check("offline MODE + network available: '/' still shows the offline page", pg.locator("#offline-status").count() == 1)
    pg.click("text=翻訳画面に戻る")
    pg.wait_for_selector("textarea[name=direct_text]")
    check("'back to translator' switches to online mode", pg.evaluate("getNetMode()") == "online")
    pg.goto(B + "/")
    check("online mode again: main page loads", pg.is_visible("textarea[name=direct_text]"))

    # バナー: ブラウザが「オフライン」と言っても、サーバーに届くなら出さない
    pg.evaluate("Object.defineProperty(navigator,'onLine',{get:()=>false,configurable:true}); window.dispatchEvent(new Event('offline'))")
    pg.wait_for_timeout(600)
    check("banner stays hidden when browser says offline but server is reachable", pg.is_hidden("#offline-banner"))
    ctx.set_offline(True)
    pg.evaluate("window.dispatchEvent(new Event('offline'))")
    pg.wait_for_function("!document.getElementById('offline-banner').classList.contains('hidden')", timeout=8000)
    check("banner shown when the server is really unreachable", True)
    ctx.set_offline(False)
    pg.evaluate("Object.defineProperty(navigator,'onLine',{get:()=>true,configurable:true}); window.dispatchEvent(new Event('online'))")
    pg.wait_for_function("document.getElementById('offline-banner').classList.contains('hidden')")
    check("banner hidden again when back online", True)

    # --- スタート画面の選択式（Online / Offline） ---
    pg.evaluate("setNetMode('online')")
    pg.goto(B + "/start")
    check("start: online selected by default", pg.is_checked("input[name=network_mode][value=online]"))
    check("start: offline option is enabled", pg.is_enabled("input[name=network_mode][value=offline]"))
    pg.check("input[name=network_mode][value=offline]")
    pg.click("button.start-opt:has-text('日本語')")
    pg.wait_for_selector("#offline-status")
    check("start: choosing Offline opens the offline page", "オフライン" in pg.inner_text("#offline-status"))
    check("start: mode remembered (page + service worker)", pg.evaluate("getNetMode()") == "offline" and pg.evaluate("(async()=>{const r=await (await caches.open('tookie-mode')).match('/__net_mode');return await r.text()})()") == "offline")
    pg.goto(B + "/start")
    check("start: remembers the last choice", pg.is_checked("input[name=network_mode][value=offline]"))
    pg.check("input[name=network_mode][value=online]")
    pg.click("button.start-opt:has-text('日本語')")
    pg.wait_for_selector("textarea[name=direct_text]")
    check("start: choosing Online opens the translator", pg.evaluate("getNetMode()") == "online")

    # --- 英語UI・Cookieなし（初回オフライン画面） ---
    ctx2 = br.new_context(); ctx2.route("**/*", lambda r: r.abort() if not r.request.url.startswith(B) else r.continue_())
    q = ctx2.new_page(); q.on("pageerror", lambda e: errs.append(str(e)))
    q.goto(B + "/offline")
    check("fresh visitor can open /offline (English)", "You are offline" in q.inner_text("#offline-status"))
    q.click("#hf-phrases")
    q.wait_for_function("document.querySelectorAll('#phrase-list > div.space-y-2 > div').length === 81")
    check("English UI: phrase meaning line is English", "Hello" in q.inner_text("#phrase-list") or "Bonjour" in q.inner_text("#phrase-list"))
    br.close()
check(f"no JS page errors ({errs})", not errs)
print("FAILS:", fails); sys.exit(1 if fails else 0)
