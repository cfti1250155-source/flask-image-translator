import base64
import binascii
import os
import re
import secrets
import time
from collections import defaultdict, deque

from flask import Flask, redirect, render_template, request, session, url_for

from languages import SUPPORTED_LANGUAGES, LANGUAGES, get_lang_code, get_ui_labels, is_supported
import translator
from translator import TranslationError

app = Flask(__name__)

_secret = os.environ.get("SECRET_KEY")
if not _secret:
    # 未設定なら起動ごとにランダム生成（本番では必ず環境変数で固定すること）
    _secret = secrets.token_hex(32)
    print("[warn] SECRET_KEY が未設定です。再起動でセッションが無効になります。", flush=True)
app.secret_key = _secret
app.config.update(
    MAX_CONTENT_LENGTH=10 * 1024 * 1024,  # アップロード上限 10MB
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=not os.environ.get("FLASK_DEBUG"),
)

MAX_TEXT_LEN = 5000
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp", "image/heic", "image/heif"}
VALID_MODES = {"text", "image", "voice", "camera"}

# --- 簡易レート制限（IPごと 1分に20回まで。ワーカー1つ前提のメモリ内実装） ---
RATE_LIMIT, RATE_WINDOW = 20, 60
_hits = defaultdict(deque)


def _client_ip():
    fwd = request.headers.get("X-Forwarded-For", "")
    return (fwd.split(",")[0].strip() if fwd else request.remote_addr) or "unknown"


def _rate_ok():
    now, q = time.time(), _hits[_client_ip()]
    while q and now - q[0] > RATE_WINDOW:
        q.popleft()
    if len(q) >= RATE_LIMIT:
        return False
    q.append(now)
    return True


def _langs():
    src = session.get("source_lang", "Japanese")
    tgt = session.get("target_lang", "English")
    if not is_supported(src):
        src = "Japanese"
    if not is_supported(tgt):
        tgt = "English"
    session["source_lang"], session["target_lang"] = src, tgt
    return src, tgt


def _render_main(status=200, **ctx):
    source_lang, target_lang = _langs()
    base = dict(
        source_lang=source_lang,
        target_lang=target_lang,
        source_code=get_lang_code(source_lang),
        ui=get_ui_labels(target_lang),
        active_mode="text",
        translated_text=None,
        original_text=None,
        detected_lang=None,
        input_text="",
        error=None,
    )
    base.update(ctx)
    return render_template("index.html", **base), status


def _read_camera_data(data_url):
    m = re.match(r"^data:(image/[a-zA-Z0-9.+-]+);base64,(.+)$", data_url or "", re.S)
    if not m or m.group(1) not in ALLOWED_IMAGE_TYPES:
        raise TranslationError("err_image")
    try:
        return base64.b64decode(m.group(2), validate=True), m.group(1)
    except (binascii.Error, ValueError):
        raise TranslationError("err_image")


def _read_upload():
    f = request.files.get("image")
    if not f or not f.filename:
        raise TranslationError("err_image")
    if f.mimetype not in ALLOWED_IMAGE_TYPES:
        raise TranslationError("err_image")
    data = f.read()
    if not data:
        raise TranslationError("err_image")
    return data, f.mimetype


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "GET":
        return _render_main()

    source_lang, target_lang = _langs()
    mode = request.form.get("mode", "text")
    if mode not in VALID_MODES:
        mode = "text"
    ctx = {"active_mode": mode}

    try:
        if not _rate_ok():
            raise TranslationError("err_rate")

        if mode in ("text", "voice"):
            field = "direct_text" if mode == "text" else "voice_text"
            text = (request.form.get(field) or "").strip()
            ctx["input_text"] = text
            if not text:
                raise TranslationError("err_empty")
            if len(text) > MAX_TEXT_LEN:
                raise TranslationError("err_too_long")
            result = translator.translate_text(text, source_lang, target_lang)
        else:
            if mode == "image":
                data, mime = _read_upload()
            else:
                data, mime = _read_camera_data(request.form.get("camera_data"))
            result = translator.translate_image(data, mime, target_lang)

        ctx.update(
            translated_text=result["translation"] or result["source_text"],
            original_text=result["source_text"] if mode in ("image", "camera") else None,
            detected_lang=result["detected_language"] or None,
        )
    except TranslationError as e:
        ctx["error"] = get_ui_labels(target_lang).get(e.key, e.key)

    return _render_main(**ctx)


@app.errorhandler(413)
def too_large(_e):
    _, target_lang = _langs()
    return _render_main(
        status=413, active_mode="image", error=get_ui_labels(target_lang)["err_too_big"]
    )


@app.route("/select-language")
def select_language():
    lang_type = "source" if request.args.get("type") == "source" else "target"
    source_lang, target_lang = _langs()
    current = source_lang if lang_type == "source" else target_lang
    return render_template(
        "select_language.html",
        languages=LANGUAGES,
        lang_type=lang_type,
        current=current,
        ui=get_ui_labels(target_lang),
    )


@app.route("/set-language", methods=["POST"])
def set_language():
    selected = request.form.get("target_lang", "English")
    lang_type = request.form.get("lang_type", "target")
    if is_supported(selected):
        session["source_lang" if lang_type == "source" else "target_lang"] = selected
    return redirect(url_for("index"))


@app.route("/swap-language", methods=["POST"])
def swap_language():
    source, target = _langs()
    session["source_lang"], session["target_lang"] = target, source
    return redirect(url_for("index"))


@app.route("/healthz")
def healthz():
    return "ok"


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=bool(os.environ.get("FLASK_DEBUG")))
