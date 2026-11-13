"""ステップ5のブラウザ確認（重ね翻訳・PDF翻訳・単語帳）。使い方: python tests/e2e_step5.py"""
import io, json, os, re, sys, threading, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT); sys.path.insert(0, os.path.join(ROOT, "tests"))
import conftest  # noqa: F401
import translator
from werkzeug.serving import make_server
from app import app
from PIL import Image, ImageDraw
from pypdf import PdfWriter

def fake(parts, system=None):
    prompt = parts[-1] if parts else ""
    if system and "box_2d" in system:
        return json.dumps({"detected_language": "Japanese", "blocks": [
            {"text": "ラーメン", "translation": "Ramen noodles", "box_2d": [100, 100, 250, 600]},
            {"text": "餃子", "translation": "Gyoza", "box_2d": [500, 200, 650, 500]}]})
    if system and "pages" in system:
        m = re.search(r"pages (\d+) to (\d+)", prompt)
        a, b = int(m.group(1)), int(m.group(2))
        return json.dumps({"pages": [{"page": n, "translation": f"Translated page {n}"} for n in range(a, b + 1)]})
    return '{"detected_language":"Japanese","source_text":"こんにちは","translation":"Hello","pronunciation":""}'
translator._generate = fake
srv = make_server("127.0.0.1", 5081, app, threaded=True)
threading.Thread(target=srv.serve_forever, daemon=True).start()
B = "http://127.0.0.1:5081"
errs, fails = [], []
def check(name, cond):
    print(("OK   " if cond else "FAIL ") + name)
    if not cond: fails.append(name)

tmp = tempfile.mkdtemp()
img = Image.new("RGB", (1200, 800), "white"); d = ImageDraw.Draw(img)
d.rectangle([100, 80, 600, 200], outline="black"); d.text((120, 120), "RAMEN", fill="black")
imgpath = os.path.join(tmp, "menu.png"); img.save(imgpath)
w = PdfWriter()
for _ in range(7): w.add_blank_page(width=200, height=200)
pdfpath = os.path.join(tmp, "doc.pdf"); w.write(open(pdfpath, "wb"))

from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    br = p.chromium.launch()
    ctx = br.new_context(viewport={"width": 390, "height": 900})
    ctx.route("**/*", lambda r: r.abort() if not r.request.url.startswith(B) else r.continue_())
    pg = ctx.new_page()
    pg.add_init_script("window.speechSynthesis={speak(){},cancel(){},getVoices(){return[]}};window.SpeechSynthesisUtterance=function(t){this.text=t}")
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.context.request.post(B + "/set-display-language", form={"ui_lang": "Japanese"})
    pg.goto(B + "/", wait_until="domcontentloaded")
    pg.wait_for_function("typeof renderOverlay==='function' && typeof runPdf==='function' && typeof startStudy==='function'")

    # ---- 画像の重ね翻訳 ----
    pg.click("#nav-image")
    check("overlay hidden before translating", not pg.is_visible("#overlay-box"))
    pg.set_input_files("#tab-image input[type=file]", imgpath)
    pg.click("#tab-image button[type=submit]")
    pg.wait_for_selector("#overlay-box:not(.hidden)")
    pg.wait_for_function("document.getElementById('overlay-img').complete && document.getElementById('overlay-img').naturalWidth>0")
    check("overlay image is the (downscaled) upload", pg.evaluate("document.getElementById('overlay-img').src.startsWith('data:image/jpeg')"))
    n = pg.evaluate("document.querySelectorAll('#overlay-layer .ov-block').length")
    check(f"2 blocks drawn ({n})", n == 2)
    check("overlay sits below the picker", pg.evaluate("""(() => { const a = document.getElementById('img-file-name').getBoundingClientRect();
        const b = document.getElementById('overlay-box').getBoundingClientRect(); return b.top >= a.bottom - 1; })()"""))
    pos = pg.evaluate("""(() => { const s = document.getElementById('overlay-stage').getBoundingClientRect();
        const e = document.querySelector('.ov-block').getBoundingClientRect();
        return [(e.left - s.left) / s.width, (e.top - s.top) / s.height, e.width / s.width, e.height / s.height]; })()""")
    check(f"block position/size match box_2d {['%.2f' % v for v in pos]}",
          abs(pos[0] - .1) < .02 and abs(pos[1] - .1) < .02 and abs(pos[2] - .5) < .02 and abs(pos[3] - .15) < .02)
    fits = pg.evaluate("[...document.querySelectorAll('.ov-block')].every(e => e.scrollHeight <= e.clientHeight + 1 && e.scrollWidth <= e.clientWidth + 1)")
    check("text fits inside each block", fits)
    check("result box also shows text", "Ramen noodles" in pg.inner_text("#resultText-image"))
    pg.click(".ov-block >> nth=0")
    check("tap shows original", pg.inner_text(".ov-block >> nth=0") == "ラーメン")
    pg.click(".ov-block >> nth=0")
    check("tap again shows translation", pg.inner_text(".ov-block >> nth=0") == "Ramen noodles")
    pg.click("#overlay-toggle")
    check("toggle hides overlay", not pg.is_visible("#overlay-layer"))
    pg.click("#overlay-toggle")
    check("toggle shows overlay", pg.is_visible("#overlay-layer"))

    # ---- 画像を保持できない形式(ブラウザが読めないHEICなど)は訳文の一覧になる ----
    heic = os.path.join(tmp, "x.heic"); open(heic, "wb").write(b"\x00\x00\x00\x18ftypheic" + b"0" * 64)
    pg.goto(B + "/", wait_until="domcontentloaded"); pg.click("#nav-image")
    pg.set_input_files("#tab-image input[type=file]", heic)
    pg.click("#tab-image button[type=submit]")
    pg.wait_for_selector("#overlay-list:not(.hidden)")
    check("fallback list when image cannot be kept", not pg.is_visible("#overlay-stage") and "Gyoza" in pg.inner_text("#overlay-list"))

    # ---- PDF 翻訳 ----
    pg.goto(B + "/", wait_until="domcontentloaded"); pg.click("#nav-image")
    pg.set_input_files("#tab-image input[type=file]", pdfpath)
    pg.click("#tab-image button[type=submit]")
    pg.wait_for_function("document.querySelectorAll('#pdf-result .p-3').length === 7")
    texts = pg.eval_on_selector_all("#pdf-result .p-3 > div:nth-child(2)", "els => els.map(e => e.textContent)")
    check(f"7 pages translated in order {texts[:2]}...", texts == [f"Translated page {i}" for i in range(1, 8)])
    check("done message", "7" in pg.inner_text("#pdf-result [role=status]"))
    check("stayed on the page (no form post)", pg.url.rstrip("/") == B)
    check("PDF flow left no overlay", not pg.is_visible("#overlay-box"))

    # ---- 単語帳 ----
    pg.click("#nav-text")
    pg.fill("textarea[name=direct_text]", "こんにちは")
    pg.click("#tab-text button[type=submit]")
    pg.wait_for_selector("#resultText-text")
    pg.click("#tab-text button[onclick*=saveVocabCurrent]")
    v = pg.evaluate("JSON.parse(localStorage.getItem('tl_vocab_v1'))")
    check(f"saved to vocab {v and v[0]['out']}", len(v) == 1 and v[0]["out"] == "Hello" and v[0]["box"] == 0)
    pg.click("#tab-text button[onclick*=saveVocabCurrent]")
    check("saving twice does not duplicate", pg.evaluate("JSON.parse(localStorage.getItem('tl_vocab_v1')).length") == 1)
    pg.click("#nav-history"); pg.click("#hf-study")
    check("study stats", "1" in pg.inner_text("#study-stats"))
    pg.click("#study-start")
    check("card front shown", pg.inner_text("#study-front") == "こんにちは" and not pg.is_visible("#study-back"))
    pg.click("#study-reveal")
    check("answer revealed", pg.inner_text("#study-answer") == "Hello" and pg.is_visible("#study-grade"))
    pg.click("#study-grade button >> nth=0")       # もう一度 → 同じカードがもう一度出る
    check("again re-queues the card", pg.is_visible("#study-card") and pg.inner_text("#study-front") == "こんにちは")
    pg.click("#study-reveal"); pg.click("#study-grade button >> nth=1")   # 覚えた
    v = pg.evaluate("JSON.parse(localStorage.getItem('tl_vocab_v1'))[0]")
    check(f"got it → box 1, due tomorrow ({v['box']})", v["box"] == 1 and v["due"] > 0)
    check("session ends, no more due", not pg.is_visible("#study-card") and "今日の復習は終わり" in pg.inner_text("#study-msg"))
    # バックアップに入り、全削除で消える
    check("backup includes vocab", pg.evaluate("collectBackup().data.vocab.length") == 1)
    pg.evaluate("""() => { const b = parseBackup(JSON.stringify(collectBackup())); localStorage.removeItem('tl_vocab_v1'); applyBackup(b); }""")
    check("restore from backup", pg.evaluate("loadVocab().length") == 1)
    check("no JS errors", not errs)
    if errs: print(errs)
    br.close()
srv.shutdown()
print("FAILED:", fails) if fails else print("ALL OK")
sys.exit(1 if fails else 0)
