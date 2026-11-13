"""ステップ2（バックアップ書き出し／読み込み／全削除）のブラウザ確認。使い方: python tests/e2e_backup.py"""
import json, os, sys, tempfile, threading
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT); sys.path.insert(0, os.path.join(ROOT, "tests"))
import conftest  # noqa: F401
from werkzeug.serving import make_server
from app import app

srv = make_server("127.0.0.1", 5078, app, threaded=True)
threading.Thread(target=srv.serve_forever, daemon=True).start()
B = "http://127.0.0.1:5078"
fails, errs = [], []
def check(name, cond):
    print(("OK   " if cond else "FAIL ") + name)
    if not cond: fails.append(name)

SEED = """(() => {
  const now = Date.now();
  localStorage.setItem('tl_history_v1', JSON.stringify([
    {id:'h1', ts:now-1000, fav:true,  mode:'text', src:'こんにちは', out:'Hello', srcLang:'Japanese', tgt:'English', tcode:'en-US'},
    {id:'h2', ts:now-2000, fav:false, mode:'text', src:'ありがとう', out:'Thanks', srcLang:'Japanese', tgt:'English', tcode:'en-US'}]));
  localStorage.setItem('tl_glossary_v1', JSON.stringify([{id:'g1', kind:'term', term:'草', meaning:'lol', to:'English', ts:now}]));
  localStorage.setItem('tl_chat_v1', JSON.stringify([{id:'c1', side:'A', src:'やあ', srcLang:'Japanese', tgt:'English', tcode:'en-US', out:'Hi', ts:now}]));
})()"""
LS = lambda k: "JSON.parse(localStorage.getItem('%s')||'[]').length" % k

from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    br = p.chromium.launch()
    ctx = br.new_context(viewport={"width": 390, "height": 800}, accept_downloads=True)
    ctx.route("**/*", lambda r: r.abort() if not r.request.url.startswith(B) else r.continue_())
    pg = ctx.new_page()
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.on("dialog", lambda d: d.accept())
    ctx.request.post(B + "/set-display-language", form={"ui_lang": "Japanese"})
    pg.goto(B + "/"); pg.evaluate(SEED); pg.reload()

    pg.click("#open-settings")
    check("data tab shows counts", "履歴 2件" in pg.inner_text("#data-counts") and "用語集 1件" in pg.inner_text("#data-counts"))
    check("never-backed-up message", "まだバックアップしていません" in pg.inner_text("#data-last"))

    with pg.expect_download() as dl:
        pg.click("text=バックアップを書き出す")
    path = os.path.join(tempfile.mkdtemp(), "b.json"); dl.value.download(path) if False else dl.value.save_as(path)
    b = json.load(open(path, encoding="utf-8"))
    check("export file content", b["app"] == "tookie" and len(b["data"]["history"]) == 2 and len(b["data"]["glossary"]) == 1 and len(b["data"]["chat"]) == 1)
    check("export filename", dl.value.suggested_filename.startswith("tookie-backup-"))
    check("last backup recorded", "最後のバックアップ" in pg.inner_text("#data-last"))

    # --- 全削除 → スタート画面 ---
    pg.click("text=この端末のデータをすべて削除")
    pg.wait_for_url("**/start")
    check("delete -> start screen", True)
    pg.goto(B + "/start")
    left = pg.evaluate("Object.keys(localStorage).filter(k=>k.startsWith('tl_')).length")
    check("localStorage emptied", left == 0)
    ctx.request.post(B + "/set-display-language", form={"ui_lang": "Japanese"})
    pg.goto(B + "/"); pg.click("#nav-history")
    check("history empty after delete", pg.is_visible("#history-empty"))

    # --- 読み込み（復元） ---
    pg.click("#open-settings")
    pg.set_input_files("#data-section input[type=file]", path)
    pg.wait_for_function("document.getElementById('data-status').textContent.includes('読み込みました')")
    check("restored counts", pg.evaluate(LS('tl_history_v1')) == 2 and pg.evaluate(LS('tl_glossary_v1')) == 1 and pg.evaluate(LS('tl_chat_v1')) == 1)
    pg.click("#hf-all")
    check("restored history visible", "Hello" in pg.inner_text("#history-list") and "Thanks" in pg.inner_text("#history-list"))
    pg.click("#nav-conversation")
    check("restored chat bubble visible", "Hi" in pg.inner_text("#conv-log"))
    # 2回読み込んでも重複しない（統合）
    pg.click("#open-settings")
    pg.set_input_files("#data-section input[type=file]", path)
    pg.wait_for_function("document.getElementById('data-status').textContent.includes('読み込みました')")
    check("no duplicates on re-import", pg.evaluate(LS('tl_history_v1')) == 2 and pg.evaluate(LS('tl_chat_v1')) == 1)
    check("favorite preserved", pg.evaluate("JSON.parse(localStorage.getItem('tl_history_v1')).find(x=>x.id==='h1').fav") is True)

    # --- 不正なファイル ---
    def bad(content, name="x.json"):
        f = os.path.join(tempfile.mkdtemp(), name); open(f, "w", encoding="utf-8").write(content); return f
    for label, content in [("not json", "{{{"), ("wrong app", json.dumps({"app": "other", "version": 1, "data": {}})),
                           ("future version", json.dumps({"app": "tookie", "version": 99, "data": {"history": []}})),
                           ("empty data", json.dumps({"app": "tookie", "version": 1, "data": {"history": "x"}}))]:
        pg.set_input_files("#data-section input[type=file]", bad(content))
        pg.wait_for_function("document.getElementById('data-status').textContent.includes('読み込めません')")
        check(f"rejects {label}", pg.evaluate(LS('tl_history_v1')) == 2)
        pg.evaluate("document.getElementById('data-status').textContent=''")
    # 悪意のある中身: HTML・巨大文字列・型違い → 無害化され、スクリプトは動かない
    evil = {"app": "tookie", "version": 1, "data": {
        "history": [{"id": "e1", "ts": 1, "out": "<img src=x onerror=window.__pwned=1>", "src": "<script>window.__pwned=1</script>", "tgt": "English"},
                    {"id": 5, "out": "A" * 99999, "fav": "yes"}, None, "str", {"out": ""}],
        "glossary": [{"term": "x", "meaning": "y", "to": "NoSuchLang"}, {"term": "<b>t</b>", "meaning": "m", "to": "English"}],
        "chat": [{"side": "Z", "src": "s", "out": "o"}]}}
    pg.set_input_files("#data-section input[type=file]", bad(json.dumps(evil)))
    pg.wait_for_function("document.getElementById('data-status').textContent.includes('読み込みました')")
    pg.click("#hf-all"); pg.click("#hf-gl")
    hist = pg.evaluate("JSON.parse(localStorage.getItem('tl_history_v1'))")
    check("html kept as text, not executed", pg.evaluate("window.__pwned") is None)
    check("oversized string truncated", max(len(h["out"]) for h in hist) <= 5000)
    check("bad types coerced", all(isinstance(h["id"], str) and isinstance(h["fav"], bool) for h in hist))
    check("unknown language glossary dropped", pg.evaluate(LS('tl_glossary_v1')) == 2)
    check("bad chat side coerced to A", pg.evaluate("JSON.parse(localStorage.getItem('tl_chat_v1')).every(m=>m.side==='A'||m.side==='B')"))
    # 大きすぎるファイル
    pg.click("#open-settings")
    pg.set_input_files("#data-section input[type=file]", bad("x" * (5 * 1024 * 1024 + 10)))
    pg.wait_for_function("document.getElementById('data-status').textContent.includes('大きすぎ')")
    check("rejects >5MB", True)
    br.close()
check(f"no JS page errors ({errs})", not errs)
print("FAILS:", fails); sys.exit(1 if fails else 0)
