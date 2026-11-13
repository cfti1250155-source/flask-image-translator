import base64
import binascii
import json
import re

from flask import jsonify, render_template, request, session
from languages import (
    AUTO, LANGUAGES, get_lang_code, get_native_name, is_rtl,
    is_supported,
)
from limits import limiter, stats
from phrasebook import available_languages
from translator import PDF_MAX_PAGES, TranslationError
from ui_i18n import get_ui_labels

MAX_TEXT_LEN = 5000
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp", "image/heic", "image/heif"}
VALID_MODES = {"text", "image", "voice", "camera"}

# エラーラベル → HTTPステータス
ERROR_STATUS = {
    "err_empty": 400, "err_too_long": 400, "err_image": 400, "err_no_text": 422,
    "err_blocked": 422, "err_pdf": 400, "err_pdf_big": 413, "err_rate": 429, "err_daily": 429,
    "err_quota": 503, "err_overloaded": 503, "err_no_key": 503, "err_api_key": 503,
    "err_timeout": 504, "err_connection": 502, "err_failed": 502,
}


def client_ip():
    fwd = request.headers.get("X-Forwarded-For", "")
    return (fwd.split(",")[0].strip() if fwd else request.remote_addr) or "unknown"


def guard():
    """翻訳APIを呼ぶ前の利用制限チェック。問題なければ何もせず、超過なら TranslationError"""
    key = limiter.check(client_ip())
    if key:
        raise TranslationError(key)


def track(kind, key="ok"):
    stats.record(kind, key)


def api_error(ui, key, status=None):
    return jsonify(error=ui.get(key, key), key=key), status or ERROR_STATUS.get(key, 502)


def get_langs():
    src = session.get("source_lang", AUTO)
    tgt = session.get("target_lang", "English")
    if src == "Chinese":
        src = "Chinese (Simplified)"
    if tgt == "Chinese":
        tgt = "Chinese (Simplified)"
    if not is_supported(src, allow_auto=True):
        src = AUTO
    if not is_supported(tgt):
        tgt = "English"
    session["source_lang"], session["target_lang"] = src, tgt
    return src, tgt


def get_ui_lang():
    """スタート画面で選んだ表示言語（未選択なら None）"""
    lang = session.get("ui_lang")
    return lang if is_supported(lang) else None


def get_ui():
    return get_ui_labels(get_ui_lang() or "English")


def clean_context(raw):
    out = []
    if isinstance(raw, list):
        for c in raw[-8:]:
            if isinstance(c, dict):
                text = str(c.get("text") or "").strip()[:300]
                if text:
                    out.append({"speaker": "B" if c.get("speaker") == "B" else "A", "text": text})
    return out


def clean_glossary(raw):
    out = []
    if isinstance(raw, list):
        for g in raw[:20]:
            if isinstance(g, dict):
                term = str(g.get("term") or "").strip()[:100]
                meaning = str(g.get("meaning") or "").strip()[:200]
                if term and meaning:
                    out.append({"term": term, "meaning": meaning,
                                "kind": "example" if g.get("kind") == "example" else "term"})
    return out


def remember_recent(name):
    """最近使った言語（最大6件）をセッションに保存"""
    if not is_supported(name):
        return
    recent = [n for n in session.get("recent", []) if n != name and is_supported(n)]
    session["recent"] = ([name] + recent)[:6]


def render_main(status=200, **ctx):
    source_lang, target_lang = get_langs()
    ui = get_ui()
    ui_lang = get_ui_lang() or "English"
    base = dict(
        ui_lang=ui_lang,
        ui_code=get_lang_code(ui_lang),
        ui_rtl=is_rtl(ui_lang),
        ui_native=get_native_name(ui_lang),
        source_lang=source_lang,
        source_display=ui["auto_detect"] if source_lang == AUTO else get_native_name(source_lang),
        target_lang=target_lang,
        target_display=get_native_name(target_lang),
        source_code=get_lang_code(source_lang),
        target_code=get_lang_code(target_lang),
        target_rtl=is_rtl(target_lang),
        ui=ui,
        active_mode="text",
        translated_text=None,
        original_text=None,
        detected_lang=None,
        input_text="",
        error=None,
        result_entry=None,
        pronunciation=None,
        overlay_blocks=None,
        pdf_max_pages=PDF_MAX_PAGES,
        same_detected=False,
        same_lang=(source_lang == target_lang),
        phrase_langs=available_languages(),
        lang_list=[{"name": l["name"], "code": l["code"], "native": l["native"]} for l in LANGUAGES],
    )
    base.update(ctx)
    return render_template("index.html", **base), status


def read_camera_data(data_url):
    m = re.match(r"^data:(image/[a-zA-Z0-9.+-]+);base64,(.+)$", data_url or "", re.S)
    if not m or m.group(1) not in ALLOWED_IMAGE_TYPES:
        raise TranslationError("err_image")
    try:
        return base64.b64decode(m.group(2), validate=True), m.group(1)
    except (binascii.Error, ValueError):
        raise TranslationError("err_image")


def read_upload():
    f = request.files.get("image")
    if not f or not f.filename:
        raise TranslationError("err_image")
    if f.mimetype not in ALLOWED_IMAGE_TYPES:
        raise TranslationError("err_image")
    data = f.read()
    if not data:
        raise TranslationError("err_image")
    return data, f.mimetype


def read_pdf_upload(field="file"):
    """アップロードされたPDFを読む。問題があれば TranslationError"""
    from translator import PDF_MAX_BYTES
    f = request.files.get(field)
    if not f or not f.filename:
        raise TranslationError("err_pdf")
    data = f.read(PDF_MAX_BYTES + 1)
    if len(data) > PDF_MAX_BYTES:
        raise TranslationError("err_pdf_big")
    if not data.startswith(b"%PDF"):
        raise TranslationError("err_pdf")
    return data
