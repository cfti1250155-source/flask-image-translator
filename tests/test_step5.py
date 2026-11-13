"""ステップ5: 画像の重ね翻訳・PDF翻訳・単語帳"""
import io
import json

import pytest

from conftest import start

PNG = b"\x89PNG\r\n\x1a\n" + b"0" * 32


def make_pdf(pages=3, encrypt=False):
    from pypdf import PdfWriter
    w = PdfWriter()
    for _ in range(pages):
        w.add_blank_page(width=200, height=200)
    if encrypt:
        w.encrypt("secret")
    buf = io.BytesIO()
    w.write(buf)
    return buf.getvalue()


BLOCKS_JSON = json.dumps({
    "detected_language": "Japanese",
    "blocks": [
        {"text": "ラーメン", "translation": "Ramen", "box_2d": [100, 50, 200, 400]},
        {"text": "餃子", "translation": "Gyoza", "box_2d": [300.4, 60, 380, 300]},
        {"text": "x", "translation": "bad", "box_2d": [1, 2, 3]},              # 位置が不正 → 捨てる
        {"text": "y", "translation": "", "box_2d": [0, 0, 100, 100]},          # 訳なし → 捨てる
        {"text": "z", "translation": "tiny", "box_2d": [10, 10, 11, 11]},      # 小さすぎ → 捨てる
        {"text": "w", "translation": "clamped", "box_2d": [-50, 900, 2000, 1500]},
    ],
})


def test_clean_blocks(env):
    _, translator, _, _ = env
    blocks = translator.clean_blocks(json.loads(BLOCKS_JSON)["blocks"])
    assert [b["translation"] for b in blocks] == ["Ramen", "Gyoza", "clamped"]
    assert blocks[1]["box"] == [300, 60, 380, 300]
    assert blocks[2]["box"] == [0, 900, 1000, 1000]
    assert translator.clean_blocks("nope") == [] and translator.clean_blocks([1, None, {}]) == []


def test_image_overlay_page_has_blocks(env):
    app, translator, calls, mp = env
    mp.setattr(translator, "_generate", lambda parts, system=None: (calls.append((parts, system)) or BLOCKS_JSON))
    c = app.test_client(); start(c)
    r = c.post("/", data={"mode": "image", "overlay": "1", "image": (io.BytesIO(PNG), "a.png", "image/png")},
               content_type="multipart/form-data")
    html = r.get_data(as_text=True)
    assert r.status_code == 200
    assert "const OVERLAY_BLOCKS = [{" in html and "Ramen" in html and "Gyoza" in html
    assert "box_2d" in calls[-1][1] and 'id="overlay-stage"' in html
    # 結果欄には訳文が行ごとに入る
    assert "Ramen\nGyoza" in html


def test_image_without_overlay_uses_plain_translation(env):
    app, translator, calls, _ = env
    c = app.test_client(); start(c)
    r = c.post("/", data={"mode": "image", "image": (io.BytesIO(PNG), "a.png", "image/png")},
               content_type="multipart/form-data")
    assert "const OVERLAY_BLOCKS = null;" in r.get_data(as_text=True)
    assert "box_2d" not in (calls[-1][1] or "")


def test_overlay_no_blocks_is_no_text_error(env):
    app, translator, calls, mp = env
    mp.setattr(translator, "_generate", lambda parts, system=None: '{"detected_language":"","blocks":[]}')
    c = app.test_client(); start(c)
    r = c.post("/", data={"mode": "image", "overlay": "1", "image": (io.BytesIO(PNG), "a.png", "image/png")},
               content_type="multipart/form-data")
    assert "見つかりませんでした" in r.get_data(as_text=True)


def pdf_post(c, pdf, **form):
    data = {"file": (io.BytesIO(pdf), "doc.pdf", "application/pdf"), "target": "English"}
    data.update(form)
    return c.post("/api/translate-pdf", data=data, content_type="multipart/form-data")


def test_pdf_translates_in_chunks(env):
    app, translator, calls, mp = env
    seen = []
    orig = translator._pdf_slice

    def spy(data, a, b):
        out = orig(data, a, b)
        from pypdf import PdfReader
        seen.append((a, b, len(PdfReader(io.BytesIO(out[0])).pages), out[1]))
        return out
    mp.setattr(translator, "_pdf_slice", spy)
    mp.setattr(translator, "_generate", lambda parts, system=None: (calls.append((parts, system)) or
        json.dumps({"pages": [{"page": 1, "translation": "P1"}, {"page": 2, "translation": "P2"},
                              {"page": 3, "translation": "P3"}, {"page": 9, "translation": "ignored"}]})))
    c = app.test_client(); start(c)
    r = pdf_post(c, make_pdf(5), start="1", end="3")
    j = r.get_json()
    assert r.status_code == 200 and j["total"] == 5 and j["limit"] == 5
    assert [p["page"] for p in j["pages"]] == [1, 2, 3]       # 範囲外のページは捨てる
    assert seen == [(1, 3, 3, True)]                          # 3ページだけの PDF を送る
    assert "pages 1 to 3" in calls[-1][0][1]
    # 範囲は1回3ページまでに切り詰められる
    pdf_post(c, make_pdf(5), start="4", end="40")
    assert seen[-1][:3] == (4, 5, 2)


def test_pdf_limits_and_errors(env):
    app, translator, calls, mp = env
    c = app.test_client(); start(c)
    assert pdf_post(c, b"not a pdf").status_code == 400
    assert pdf_post(c, b"%PDF-1.4 broken").status_code == 400
    assert pdf_post(c, make_pdf(2, encrypt=True)).status_code == 400
    assert pdf_post(c, make_pdf(2), target="Klingon").status_code == 400
    assert pdf_post(c, make_pdf(2), start="9", end="9").status_code == 400     # 範囲外
    assert not calls                                                           # どれも Gemini は呼ばれない
    mp.setattr(translator, "PDF_MAX_BYTES", 100)
    assert pdf_post(c, make_pdf(2)).status_code == 413
    r = c.post("/api/translate-pdf", data={"target": "English"}, content_type="multipart/form-data")
    assert r.status_code == 400


def test_pdf_page_cap(env):
    app, translator, calls, mp = env
    mp.setattr(translator, "PDF_MAX_PAGES", 4)
    mp.setattr(translator, "_generate", lambda parts, system=None: '{"pages":[{"page":4,"translation":"last"}]}')
    c = app.test_client(); start(c)
    j = pdf_post(c, make_pdf(9), start="4", end="6").get_json()
    assert j["total"] == 9 and j["limit"] == 4 and j["max_pages"] == 4
    assert [p["page"] for p in j["pages"]] == [4]
    assert pdf_post(c, make_pdf(9), start="5", end="5").status_code == 400


def test_pdf_requires_limits_and_stats(env):
    app, translator, calls, mp = env
    from limits import limiter
    mp.setattr(limiter, "check", lambda ip: "err_rate")
    c = app.test_client(); start(c)
    assert pdf_post(c, make_pdf(2)).status_code == 429


def test_pdf_empty_result_is_no_text(env):
    app, translator, calls, mp = env
    mp.setattr(translator, "_generate", lambda parts, system=None: '{"pages":[{"page":1,"translation":""}]}')
    c = app.test_client(); start(c)
    assert pdf_post(c, make_pdf(1)).status_code == 422


def test_page_count_fallback_without_pypdf(env):
    _, translator, _, mp = env
    mp.setattr(translator, "_pdf_reader", lambda data: None)
    assert translator.pdf_page_count(b"%PDF-1.4 /Type /Page /Type /Pages /Type/Page") == 2


def test_step5_ui_markup(env):
    app, *_ = env
    c = app.test_client(); start(c, "Japanese")
    html = c.get("/").get_data(as_text=True)
    for needle in ("overlay-box", "overlay-stage", "pdf-result", "application/pdf", "js/overlay.js", "js/study.js",
                   "study-section", "hf-study", "最大30ページ"):
        assert needle in html, needle
    res = c.post("/", data={"mode": "text", "direct_text": "こんにちは"}).get_data(as_text=True)
    assert "saveVocabCurrent('text'" in res
    off = c.get("/offline").get_data(as_text=True)
    assert "study-section" in off and "js/study.js" in off
    sw = c.get("/sw.js").get_data(as_text=True)
    assert "js/overlay.js" in sw and "js/study.js" in sw


def test_step5_labels_in_both_languages():
    import languages
    keys = ["ov_hide", "ov_show", "ov_hint", "pdf_hint", "pdf_progress", "pdf_done", "err_pdf", "err_pdf_big",
            "filter_study", "vocab_save", "study_start", "study_reveal", "study_again", "study_good", "study_done"]
    for lang in ("Japanese", "English"):
        for k in keys:
            assert languages.UI_LABELS[lang].get(k), (lang, k)
    # プレースホルダーが両言語で一致
    import re
    for k in ("pdf_hint", "pdf_progress", "pdf_done", "pdf_truncated", "study_total", "study_due", "study_left"):
        assert sorted(re.findall(r"\{\w+\}", languages.UI_LABELS["Japanese"][k])) == \
               sorted(re.findall(r"\{\w+\}", languages.UI_LABELS["English"][k])), k
