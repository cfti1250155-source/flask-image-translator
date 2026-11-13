"""V11のブラウザ確認（結果カードの「…」メニュー・ゴミ箱・元に戻す・空港フレーズ）。
CDN(Tailwind等)は遮断するため、見た目は style.css の部品だけを検証する。使い方: python tests/e2e_v11.py [スクショの保存先]"""
import json, os, sys, threading
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT); sys.path.insert(0, os.path.join(ROOT, "tests"))
import conftest  # noqa: F401
import translator
from werkzeug.serving import make_server
from app import app

SHOTS = sys.argv[1] if len(sys.argv) > 1 else None
def fake(parts, system=None):
    if system and "explanation" in system: return '{"explanation":"slang!"}'
    return '{"detected_language":"English","source_text":"Hello, mr Brown.","translation":"こんにちは、ブラウンさん。","pronunciation":"Konnichiwa, Buraun-san."}'
translator._generate = fake
srv = make_server("127.0.0.1", 5082, app, threaded=True)
threading.Thread(target=srv.serve_forever, daemon=True).start()
B = "http://127.0.0.1:5082"
errs, fails = [], []
def check(name, cond):
    print(("OK   " if cond else "FAIL ") + name)
    if not cond: fails.append(name)
def shot(pg, name):
    if SHOTS: pg.screenshot(path=os.path.join(SHOTS, name + ".png"), full_page=False)

from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    br = p.chromium.launch()
    ctx = br.new_context(viewport={"width": 390, "height": 844}, device_scale_factor=2)
    ctx.route("**/*", lambda r: r.abort() if not r.request.url.startswith(B) else r.continue_())
    pg = ctx.new_page()
    pg.add_init_script("Object.defineProperty(window,'speechSynthesis',{configurable:true,value:{speak(u){if(u.text.trim())window.__spoke=(window.__spoke||0)+1},cancel(){},getVoices(){return[]}}});window.SpeechSynthesisUtterance=function(t){this.text=t}")
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.on("dialog", lambda d: d.accept())
    ctx.request.post(B + "/set-display-language", form={"ui_lang": "Japanese"})
    pg.goto(B + "/", wait_until="domcontentloaded")
    pg.wait_for_function("typeof toggleResultMenu==='function' && typeof trashAdd==='function' && typeof undoToast==='function'")
    pg.fill("textarea[name=direct_text]", "Hello, mr Brown.")
    pg.click("#tab-text button[type=submit]")
    pg.wait_for_selector(".rc-actions")
    pg.wait_for_function("JSON.parse(localStorage.getItem('tl_history_v1')||'[]').length>0")

    # ---- 結果カードのレイアウト ----
    r = pg.evaluate("""(() => { const q = s => document.querySelector(s).getBoundingClientRect();
        const sp = document.querySelector('.rc-actions .rc-btn').getBoundingClientRect();
        const bs = [...document.querySelectorAll('.rc-actions > .rc-right > .rc-btn, .rc-actions > .rc-right .rc-wrap > .rc-btn')].map(b => b.getBoundingClientRect());
        const out = q('#resultText-text'), act = q('.rc-actions');
        return { sp: [sp.left, sp.top, sp.width, sp.height], bs: bs.map(b => [b.left, b.top, b.width, b.height]), outBottom: out.bottom, actTop: act.top,
                 cardRight: q('.rc-actions').right, vw: innerWidth, sw: document.documentElement.scrollWidth }; })()""")
    check(f"speak button at the left, big enough {r['sp']}", r["sp"][2] >= 44 and r["sp"][3] >= 44 and r["sp"][0] < 100)
    check(f"copy and … at the right, same row as speak, big enough {r['bs']}",
          len(r["bs"]) == 2 and all(b[2] >= 44 and b[3] >= 44 and abs(b[1] - r["sp"][1]) < 2 for b in r["bs"]) and r["bs"][1][0] > r["vw"] / 2)
    check("buttons are under the translated text", r["actTop"] >= r["outBottom"])
    check("no horizontal scroll", r["sw"] <= r["vw"])
    check("pron is smaller than the translation", pg.evaluate("parseFloat(getComputedStyle(document.querySelector('.rc-pron')).fontSize) < parseFloat(getComputedStyle(document.querySelector('.rc-out')).fontSize)"))
    check("menu is closed at first", not pg.is_visible(".rc-menu"))
    pg.evaluate("document.querySelector('.rc-actions').scrollIntoView({block:'center'})")
    shot(pg, "1_result_card")

    # ---- 「…」メニュー ----
    pg.click(".rc-more")
    check("menu opens with 6 items", pg.is_visible(".rc-menu") and pg.locator(".rc-menu .rc-item").count() == 6)
    check("aria-expanded true", pg.get_attribute(".rc-more", "aria-expanded") == "true")
    labels = pg.locator(".rc-menu .rc-label").all_inner_texts()
    check(f"menu labels {labels}", labels == ["訳を修正", "大きく表示", "別の言い方", "スラング・意味を解説", "単語帳に保存", "お気に入り"])
    box = pg.evaluate("(() => { const r = document.querySelector('.rc-menu').getBoundingClientRect(); return [r.left, r.top, r.right, r.bottom, innerWidth, innerHeight]; })()")
    check(f"menu fits in the screen {['%.0f' % v for v in box]}", box[0] >= 0 and box[2] <= box[4] and box[1] >= 0 and box[3] <= box[5])
    check("every item is at least 44px tall", pg.evaluate("[...document.querySelectorAll('.rc-item')].every(e => e.getBoundingClientRect().height >= 43)"))
    shot(pg, "2_menu_open")
    pg.keyboard.press("Escape")
    check("Esc closes the menu", not pg.is_visible(".rc-menu") and pg.get_attribute(".rc-more", "aria-expanded") == "false")
    pg.click(".rc-more"); pg.click("h1, header, body", position={"x": 5, "y": 5}, force=True)
    check("tapping outside closes the menu", not pg.is_visible(".rc-menu"))

    # 各メニュー項目
    pg.click(".rc-more"); pg.click(".rc-item:has-text('大きく表示')")
    pg.wait_for_selector(".big-overlay")
    check("big display opened from the menu and menu closed", pg.is_visible(".big-overlay") and not pg.is_visible(".rc-menu"))
    pg.click(".big-close"); 
    pg.click(".rc-more"); pg.click(".rc-item:has-text('スラング')")
    pg.wait_for_function("document.getElementById('explain-text').textContent.includes('slang!')")
    check("explain from the menu", True)
    pg.click(".rc-more"); pg.click(".rc-item.fav-btn")
    check("menu closes after favorite", not pg.is_visible(".rc-menu"))
    check("favorite from the menu turns the star solid", "fa-solid" in pg.get_attribute(".rc-item.fav-btn i", "class"))
    check("favorite saved in history", pg.evaluate("JSON.parse(localStorage.getItem('tl_history_v1'))[0].fav === true"))
    pg.click(".rc-more"); pg.click(".rc-item:has-text('単語帳に保存')")
    check("saved to the word list and menu closed", pg.evaluate("JSON.parse(localStorage.getItem('tl_vocab_v1')).length") == 1 and not pg.is_visible(".rc-menu"))
    pg.click(".rc-more")
    check("saved label shows in the menu afterwards", "保存しました" in pg.inner_text(".rc-menu"))
    pg.keyboard.press("Escape")
    # 読み上げ・コピー（メニューの外）
    pg.click(".rc-actions > .rc-btn")
    check("speak button works", pg.evaluate("window.__spoke || 0") >= 1)

    # ---- 履歴 → ゴミ箱 ----
    pg.click("#nav-history")
    pg.click("#hf-all")
    check("history has the entry", pg.locator("#history-list > div").count() == 1)
    pg.locator("#history-list button[title=削除]").first.click()
    pg.wait_for_selector("#undo-toast")
    check("toast: moved to trash + restore button", "ゴミ箱に移しました" in pg.inner_text("#undo-toast") and "元に戻す" in pg.inner_text("#undo-toast"))
    check("history is now empty and entry is in trash", pg.locator("#history-list > div").count() == 0
          and pg.evaluate("JSON.parse(localStorage.getItem('tl_trash_v1')).length") == 1)
    shot(pg, "3_toast")
    pg.click("#undo-toast button")
    check("undo from the toast restores it (favorite kept)", pg.locator("#history-list > div").count() == 1
          and pg.evaluate("JSON.parse(localStorage.getItem('tl_history_v1'))[0].fav === true")
          and pg.evaluate("JSON.parse(localStorage.getItem('tl_trash_v1')).length") == 0 and not pg.is_visible("#undo-toast"))
    # 一括消去（お気に入りは残る）
    pg.evaluate("addHistory({mode:'text',src:'a',out:'A',srcLang:'English',tgt:'Japanese',tcode:'ja-JP'}); addHistory({mode:'text',src:'b',out:'B',srcLang:'English',tgt:'Japanese',tcode:'ja-JP'}); renderHistory()")
    check("3 entries before clearing", pg.locator("#history-list > div").count() == 3)
    pg.click("#history-clear-btn")
    n = pg.evaluate("[loadHistory().length, loadTrash().length, loadTrash()[0].items.length]")
    check(f"clear history keeps favorites and sends the rest to trash as one batch {n}", n == [1, 1, 2])
    pg.wait_for_selector("#undo-toast")
    # ゴミ箱の画面
    pg.click("#hf-trash")
    check("trash screen shows 1 batch (2 items) with days left", pg.locator("#trash-list > div").count() == 1
          and "2件" in pg.inner_text("#trash-list") and "残り30日" in pg.inner_text("#trash-list"))
    check("trash note mentions 30 days", "30日間" in pg.inner_text("#trash-note"))
    check("history-clear button hidden on the trash screen", not pg.is_visible("#history-clear-btn"))
    shot(pg, "4_trash")
    pg.click("#trash-list button[title=元に戻す]")
    check("restore from the trash screen", pg.evaluate("loadHistory().length") == 3 and pg.evaluate("loadTrash().length") == 0
          and pg.is_visible("#trash-empty") and not pg.is_visible("#trash-empty-btn"))
    # 完全に削除・ゴミ箱を空にする
    pg.evaluate("trashAdd('history', [loadHistory()[1]]); trashAdd('history', [loadHistory()[2]]); renderTrash()")
    check("2 items in trash", pg.locator("#trash-list > div").count() == 2 and pg.is_visible("#trash-empty-btn"))
    pg.locator("#trash-list button[title=完全に削除]").first.click()
    check("delete forever removes one", pg.locator("#trash-list > div").count() == 1)
    pg.click("#trash-empty-btn")
    check("empty trash removes everything", pg.evaluate("loadTrash().length") == 0 and pg.is_visible("#trash-empty"))
    # 期限切れの自動削除
    pg.evaluate("localStorage.setItem('tl_trash_v1', JSON.stringify([{tid:'old',kind:'history',at:Date.now()-31*86400000,items:[{id:'x',ts:1,src:'s',out:'o'}]},{tid:'new',kind:'history',at:Date.now()-29*86400000,items:[{id:'y',ts:2,src:'s2',out:'o2'}]}])); renderTrash()")
    check("items older than 30 days disappear, 29-day-old stays with 1 day left", pg.locator("#trash-list > div").count() == 1 and "残り1日" in pg.inner_text("#trash-list"))
    pg.evaluate("trashEmpty()")

    # ---- 用語集・単語帳・チャット ----
    pg.click("#hf-gl")
    pg.fill("#gl-term", "ガチ勢"); pg.fill("#gl-meaning", "hardcore player"); pg.click("#glossary-section button[type=submit]")
    check("glossary item added", pg.locator("#glossary-list > div").count() == 1)
    pg.locator("#glossary-list button[title=削除]").click()
    check("glossary delete goes to trash and can be undone", pg.evaluate("loadGlossary().length") == 0 and pg.evaluate("loadTrash()[0].kind") == "glossary")
    pg.click("#undo-toast button")
    check("glossary restored", pg.evaluate("loadGlossary().length") == 1 and pg.locator("#glossary-list > div").count() == 1)
    pg.click("#hf-study")
    check("vocab item listed", pg.locator("#study-list > div").count() == 1)
    pg.locator("#study-list button[title=削除]").click()
    check("vocab delete goes to trash", pg.evaluate("loadVocab().length") == 0 and pg.evaluate("loadTrash()[0].kind") == "vocab")
    pg.click("#undo-toast button")
    check("vocab restored with its study state", pg.evaluate("loadVocab().length") == 1 and pg.evaluate("loadVocab()[0].box") == 0)
    pg.click("#nav-conversation")
    pg.fill("#conv-input", "やっほー"); pg.press("#conv-input", "Enter")
    pg.wait_for_selector("#conv-log >> text=こんにちは、ブラウンさん。")
    pg.wait_for_function("loadChat().length === 1")
    pg.click("button[onclick='clearConversation()']")
    check("clearing the chat goes to trash", pg.evaluate("loadChat().length") == 0 and pg.evaluate("loadTrash()[0].kind") == "chat" and pg.locator("#conv-log > *").count() == 0)
    pg.click("#undo-toast button")
    check("chat restored and redrawn", pg.evaluate("loadChat().length") == 1 and pg.locator("#conv-log > *").count() == 1 and not pg.is_visible("#conv-empty"))

    # ---- 空港フレーズ ----
    pg.click("#nav-history"); pg.click("#hf-phrases")
    pg.select_option("#phrase-lang", "English")
    pg.wait_for_selector("#phrase-list >> text=I'd like a window seat, please")
    check("phrasebook shows 81 phrases", pg.locator("#phrase-list .flex.gap-2.items-start").count() == 81)
    heads = pg.locator("#phrase-list > div.text-\\[11px\\]").all_inner_texts()
    check(f"airport categories come right after the basics {heads[:3]}", heads[0] == "あいさつ・基本" and heads[1].startswith("空港") and len(heads) == 11)
    pg.fill("#phrase-search", "窓側")
    check("search finds the window-seat phrase (Japanese meaning)", pg.locator("#phrase-list .flex.gap-2.items-start").count() == 1)
    pg.fill("#phrase-search", "")
    check("phrase copy button has a real label", pg.locator("#phrase-list button[title=コピー]").count() >= 1)

    # ---- ライトテーマ ----
    pg.click("#nav-text")
    pg.evaluate("document.documentElement.setAttribute('data-theme','light')")
    pg.evaluate("document.querySelector('.rc-actions').scrollIntoView({block:'center'})")
    pg.click(".rc-more"); shot(pg, "5_light_menu")
    bg = pg.evaluate("getComputedStyle(document.querySelector('.rc-menu')).backgroundColor")
    check(f"light theme menu is light {bg}", bg == "rgb(255, 255, 255)")
    pg.keyboard.press("Escape")

    # ---- すべて削除はゴミ箱も消す ----
    pg.evaluate("trashAdd('history', [{id:'z',ts:1,src:'s',out:'o'}])")
    pg.evaluate("document.documentElement.removeAttribute('data-theme')")
    pg.evaluate("deleteAllData()")
    pg.wait_for_url("**/start")
    check("delete-all also erases the trash", pg.evaluate("localStorage.getItem('tl_trash_v1')") is None)
    ctx.close(); br.close()

print("page errors:", errs)
if errs: fails.append("page errors")
print("\nFAILED:" if fails else "\nALL OK", fails or "")
sys.exit(1 if fails else 0)
