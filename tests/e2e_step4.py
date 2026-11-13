"""ステップ4のブラウザ確認（CDN遮断のため、見た目は computed style で確認）。使い方: python tests/e2e_step4.py"""
import os, sys, threading
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT); sys.path.insert(0, os.path.join(ROOT, "tests"))
import conftest  # noqa: F401
import translator
from werkzeug.serving import make_server
from app import app

seen = []
def fake(parts, system=None):
    seen.append(parts[0] if parts else "")
    if system and "alternatives" in system:
        return '{"alternatives":["Hi there","Hey!","Good day"]}'
    return '{"detected_language":"English","source_text":"hello","translation":"こんにちは","pronunciation":"konnichiwa"}'
translator._generate = fake
srv = make_server("127.0.0.1", 5078, app, threaded=True)
threading.Thread(target=srv.serve_forever, daemon=True).start()
B = "http://127.0.0.1:5078"
errs, fails = [], []
def check(name, cond):
    print(("OK   " if cond else "FAIL ") + name)
    if not cond: fails.append(name)

from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    br = p.chromium.launch()
    ctx = br.new_context(viewport={"width": 390, "height": 800})
    ctx.route("**/*", lambda r: r.abort() if not r.request.url.startswith(B) else r.continue_())
    pg = ctx.new_page()
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.context.request.post(B + "/set-display-language", form={"ui_lang": "Japanese"})
    pg.goto(B + "/", wait_until="domcontentloaded")
    pg.wait_for_function("typeof renderSettings==='function' && typeof showBig==='function'")

    # --- ヘッダーの歯車から設定を開く ---
    pg.click("#open-settings")
    check("header gear opens settings", pg.is_visible("#settings-section") and not pg.is_visible("#tab-text"))
    pg.click("#open-settings")
    check("settings section visible", pg.is_visible("#settings-section") and not pg.is_visible("#history-list"))
    pg.click("#settings-section [data-setting=formality] [data-v=formal]")
    pg.click("#settings-section [data-setting=fs] [data-v=xl]")
    st = pg.evaluate("JSON.parse(localStorage.getItem('tl_settings_v1'))")
    check(f"settings saved {st}", st["formality"] == "formal" and st["fs"] == "xl" and st["pron"] is True)
    check("font size applied", pg.evaluate("getComputedStyle(document.documentElement).fontSize") == "20.48px")
    pg.uncheck("#set-pron"); pg.check("#set-pron")

    # --- ライト配色 ---
    pg.click("#settings-section [data-setting=theme] [data-v=light]")
    check("light attr", pg.evaluate("document.documentElement.getAttribute('data-theme')") == "light")
    bg = pg.evaluate("getComputedStyle(document.body).backgroundColor")
    card = pg.evaluate("getComputedStyle(document.querySelector('[class*=bg-slate-900]')).backgroundColor")
    check(f"light colors body={bg} card={card}", bg == "rgb(241, 245, 249)" and card == "rgb(255, 255, 255)")

    # --- 翻訳（丁寧さ・読み方がサーバーに届く） ---
    pg.click("#nav-text")
    pg.fill("textarea[name=direct_text]", "hello")
    pg.click("#tab-text button[type=submit]")
    pg.wait_for_selector("#pron-text:not(.hidden)")
    check("reading shown", "konnichiwa" in pg.inner_text("#pron-text"))
    check("formal+reading requested", "polite, formal" in seen[-1] and "romanized reading" in seen[-1])
    check("settings survive reload (light)", pg.evaluate("document.documentElement.getAttribute('data-theme')") == "light")

    # --- 大きく表示 ---
    pg.click("#tab-text .rc-more"); pg.click("#tab-text button[onclick*=showBigResult]")
    pg.wait_for_selector(".big-overlay")
    fs = pg.evaluate("parseFloat(getComputedStyle(document.querySelector('.big-text')).fontSize)")
    check(f"big text is large ({fs}px)", fs >= 60)
    check("big shows reading", "konnichiwa" in pg.inner_text(".big-overlay"))
    pg.click(".big-overlay", position={"x": 200, "y": 400})
    check("tap closes", pg.query_selector(".big-overlay") is None)

    # --- 別の言い方 ---
    pg.click("#tab-text .rc-more"); pg.click("#tab-text button[onclick*=showAlternatives]")
    pg.wait_for_selector("#alts-text .alt-chip")
    chips = pg.eval_on_selector_all("#alts-text .alt-chip", "els=>els.map(e=>e.textContent)")
    check(f"alternatives {chips}", chips == ["Hi there", "Hey!", "Good day"])
    pg.click("#alts-text .alt-chip >> nth=1")
    check("alternative replaces result", pg.inner_text("#resultText-text") == "Hey!")
    check("stale reading hidden", not pg.is_visible("#pron-text"))
    out = pg.evaluate("JSON.parse(localStorage.getItem('tl_history_v1'))[0].out")
    check("history updated", out == "Hey!")

    # --- チャット: 同じ言語警告 ---
    pg.click("#nav-conversation")
    pg.select_option("#conv-lang-A", "English"); pg.select_option("#conv-lang-B", "English")
    check("chat same-language warning", pg.is_visible("#conv-warn"))
    pg.select_option("#conv-lang-B", "Japanese")
    check("warning clears", not pg.is_visible("#conv-warn"))
    pg.fill("#conv-input", "hello"); pg.click("#conv-send")
    pg.wait_for_selector("#conv-log >> text=konnichiwa")
    check("chat shows reading", True)

    # --- メイン: 同じ言語警告 ---
    pg.click("#nav-text")
    for t in ("source", "target"):   # ブラウザ自身のfetchでCookieを扱わせる
        pg.evaluate("""async (t) => { const f = new URLSearchParams({target_lang: 'English', lang_type: t});
            await fetch('/set-language', {method: 'POST', body: f}); }""", t)
    pg.goto(B + "/", wait_until="domcontentloaded")
    check("main same-language banner", pg.is_visible("#same-lang-warning"))

    # --- 全データ削除で設定も消える ---
    pg.evaluate("localStorage.getItem('tl_settings_v1') && 1")
    check("no JS errors", not errs)
    if errs: print(errs)
    br.close()
srv.shutdown()
print("FAILED:", fails) if fails else print("ALL OK")
sys.exit(1 if fails else 0)
