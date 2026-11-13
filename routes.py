import json
import os

from flask import Response, abort, jsonify, make_response, redirect, render_template, request, session, url_for, send_from_directory

from helpers import (
    ERROR_STATUS, MAX_TEXT_LEN, VALID_MODES, api_error, clean_context, clean_glossary,
    client_ip, get_langs, get_ui, get_ui_lang, guard, read_camera_data,
    read_pdf_upload, read_upload, remember_recent, render_main, track,
)
from limits import limiter, stats
from languages import (
    AUTO, LANGUAGES, get_lang_code, is_rtl, is_supported,
    normalize_language_name,
)
import translator
from translator import TranslationError
from phrasebook import available_languages
from ui_i18n import ensure_async, ensure_ui_labels, has_labels


# 初回に端末へ保存しておく外部ファイル（Tailwind・FontAwesome）。以後は通信できなくても画面が崩れない
CDN_PRECACHE = [
    "https://cdn.tailwindcss.com",
    "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css",
    "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/webfonts/fa-solid-900.woff2",
    "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/webfonts/fa-regular-400.woff2",
]


def register_routes(app):
    @app.route("/", methods=["GET", "POST"])
    def index():
        if request.method == "GET":
            if not get_ui_lang():
                return redirect(url_for("start"))
            ensure_async(get_ui_lang())
            return render_main()

        source_lang, target_lang = get_langs()
        mode = request.form.get("mode", "text")
        if mode not in VALID_MODES:
            mode = "text"
        ctx = {"active_mode": mode}
        formality = translator.clean_formality(request.form.get("formality"))
        want_pron = request.form.get("pron") == "1"

        try:
            if mode in ("text", "voice"):
                field = "direct_text" if mode == "text" else "voice_text"
                text = (request.form.get(field) or "").strip()
                ctx["input_text"] = text
                if not text:
                    raise TranslationError("err_empty")
                if len(text) > MAX_TEXT_LEN:
                    raise TranslationError("err_too_long")
                try:
                    glossary = clean_glossary(json.loads(request.form.get("glossary") or "[]"))
                except ValueError:
                    glossary = []
                guard()
                result = translator.translate_text(
                    text, source_lang, target_lang, glossary=glossary,
                    formality=formality, pronunciation=want_pron)
            else:
                if mode == "image":
                    data, mime = read_upload()
                else:
                    data, mime = read_camera_data(request.form.get("camera_data"))
                guard()
                if request.form.get("overlay") == "1":
                    result = translator.translate_image_blocks(data, mime, target_lang, formality=formality)
                    ctx["overlay_blocks"] = result["blocks"]
                else:
                    result = translator.translate_image(data, mime, target_lang, pronunciation=want_pron)
            track(mode)

            detected = normalize_language_name(result["detected_language"])
            if detected:
                session["last_detected"] = detected
            show_detected = mode in ("image", "camera") or source_lang == AUTO
            ctx.update(
                translated_text=result["translation"] or result["source_text"],
                original_text=result["source_text"] if mode in ("image", "camera") else None,
                detected_lang=(detected or result["detected_language"] or None) if show_detected else None,
                pronunciation=result.get("pronunciation") or None,
                same_detected=bool(detected and detected == target_lang),
            )
            if ctx["translated_text"]:
                ctx["result_entry"] = {
                    "mode": mode,
                    "src": ctx.get("input_text") or result["source_text"],
                    "out": ctx["translated_text"],
                    "srcLang": detected or (source_lang if source_lang != AUTO else "") or result["detected_language"],
                    "tgt": target_lang,
                    "tcode": get_lang_code(target_lang),
                    "pron": result.get("pronunciation") or "",
                }
        except TranslationError as e:
            if e.key not in ("err_empty", "err_too_long", "err_image"):
                track(mode, e.key)
            ctx["error"] = get_ui().get(e.key, e.key)
            return render_main(status=ERROR_STATUS.get(e.key, 502) if e.key in ("err_rate", "err_daily") else 200, **ctx)

        return render_main(**ctx)

    @app.errorhandler(413)
    def too_large(_e):
        return render_main(status=413, active_mode="image", error=get_ui()["err_too_big"])

    @app.route("/select-language")
    def select_language():
        lang_type = "source" if request.args.get("type") == "source" else "target"
        source_lang, target_lang = get_langs()
        current = source_lang if lang_type == "source" else target_lang
        return render_template(
            "select_language.html",
            languages=LANGUAGES,
            lang_type=lang_type,
            current=current,
            recent=[n for n in session.get("recent", []) if is_supported(n)],
            auto=AUTO,
            ui=get_ui(),
            ui_code=get_lang_code(get_ui_lang() or "English"),
            ui_rtl=is_rtl(get_ui_lang() or "English"),
        )

    @app.route("/start")
    def start():
        current = get_ui_lang()
        return render_template("start.html", languages=LANGUAGES, current=current, can_close=bool(current))

    @app.route("/set-display-language", methods=["POST"])
    def set_display_language():
        lang = request.form.get("ui_lang")
        if not is_supported(lang):
            return redirect(url_for("start"))
        if not has_labels(lang) and not limiter.check(client_ip()):
            ensure_ui_labels(lang)  # 未生成の言語はここで文言を自動翻訳（失敗時は英語表示）
        session.permanent = True
        session["ui_lang"] = lang
        session["target_lang"] = lang

        if session.get("source_lang") == lang:
            session["source_lang"] = "English" if lang != "English" else "Japanese"

        remember_recent(lang)
        if request.form.get("network_mode") == "offline":   # スタート画面で「オフライン」を選んだ
            return redirect(url_for("offline"))
        return redirect(url_for("index"))

    @app.route("/set-language", methods=["POST"])
    def set_language():
        selected = request.form.get("target_lang", "English")
        lang_type = "source" if request.form.get("lang_type") == "source" else "target"
        if lang_type == "source" and selected == AUTO:
            session["source_lang"] = AUTO
        elif is_supported(selected):
            session["source_lang" if lang_type == "source" else "target_lang"] = selected
            remember_recent(selected)
        return redirect(url_for("index"))

    @app.route("/swap-language", methods=["POST"])
    def swap_language():
        source, target = get_langs()
        if source == AUTO:
            detected = session.get("last_detected")
            new_target = detected if is_supported(detected) and detected != target else (
                "English" if target != "English" else "Japanese")
            session["source_lang"], session["target_lang"] = target, new_target
        else:
            session["source_lang"], session["target_lang"] = target, source
        return redirect(url_for("index"))

    @app.route("/api/translate-text", methods=["POST"])
    def api_translate_text():
        ui = get_ui()
        data = request.get_json(silent=True) or {}
        text = str(data.get("text") or "").strip()
        source, target = data.get("source"), data.get("target")

        def fail(key, status=None):
            track("api", key) if key not in ("err_empty", "err_too_long") else None
            return api_error(ui, key, status)

        if not text:
            return fail("err_empty", 400)
        if len(text) > MAX_TEXT_LEN:
            return fail("err_too_long", 400)
        if not is_supported(target) or not is_supported(source, allow_auto=True):
            return fail("err_failed", 400)
        try:
            guard()
            result = translator.translate_text(
                text, source, target,
                context=clean_context(data.get("context")),
                glossary=clean_glossary(data.get("glossary")),
                formality=translator.clean_formality(data.get("formality")),
                pronunciation=bool(data.get("pron")),
            )
        except TranslationError as e:
            return fail(e.key)
        track("api")
        return jsonify(
            translation=result["translation"] or result["source_text"],
            detected=normalize_language_name(result["detected_language"]) or result["detected_language"],
            pronunciation=result.get("pronunciation") or "",
        )

    @app.route("/api/translate-pdf", methods=["POST"])
    def api_translate_pdf():
        """PDF を数ページずつ翻訳する。クライアントが start/end をずらして繰り返し呼ぶ"""
        ui = get_ui()

        def fail(key, status=None):
            track("pdf", key) if key not in ("err_pdf", "err_pdf_big") else None
            return api_error(ui, key, status)

        target = request.form.get("target")
        if not is_supported(target):
            return fail("err_failed", 400)
        try:
            start = max(1, int(request.form.get("start") or 1))
            end = int(request.form.get("end") or start + translator.PDF_CHUNK - 1)
        except ValueError:
            return fail("err_failed", 400)
        try:
            data = read_pdf_upload()
            total = translator.pdf_page_count(data)
            limit = min(total, translator.PDF_MAX_PAGES)
            end = min(end, limit, start + translator.PDF_CHUNK - 1)
            if start > end:
                return fail("err_pdf", 400)
            guard()
            pages = translator.translate_pdf_pages(
                data, target, start, end, formality=translator.clean_formality(request.form.get("formality")))
        except TranslationError as e:
            return fail(e.key)
        track("pdf")
        return jsonify(pages=pages, total=total, limit=limit, max_pages=translator.PDF_MAX_PAGES)

    @app.route("/api/alternatives", methods=["POST"])
    def api_alternatives():
        """「別の言い方」: 同じ原文の言い換えを最大3つ返す"""
        ui = get_ui()
        data = request.get_json(silent=True) or {}
        text = str(data.get("text") or "").strip()
        current = str(data.get("translation") or "").strip()
        source, target = data.get("source"), data.get("target")

        def fail(key, status=None):
            track("alt", key) if key not in ("err_empty", "err_too_long") else None
            return api_error(ui, key, status)

        if not text or not current:
            return fail("err_empty", 400)
        if len(text) > MAX_TEXT_LEN or len(current) > MAX_TEXT_LEN:
            return fail("err_too_long", 400)
        if not is_supported(target) or not is_supported(source or AUTO, allow_auto=True):
            return fail("err_failed", 400)
        try:
            guard()
            items = translator.alternative_translations(
                text, current, source or AUTO, target,
                formality=translator.clean_formality(data.get("formality")),
            )
        except TranslationError as e:
            return fail(e.key)
        track("alt")
        return jsonify(alternatives=items)

    @app.route("/api/explain", methods=["POST"])
    def api_explain():
        ui = get_ui()
        data = request.get_json(silent=True) or {}
        text = str(data.get("text") or "").strip()

        def fail(key, status=None):
            track("api", key) if key not in ("err_empty", "err_too_long") else None
            return api_error(ui, key, status)

        if not text:
            return fail("err_empty", 400)
        if len(text) > 1000:
            return fail("err_too_long", 400)
        lang = data.get("lang")
        explain_in = data.get("explain_in")
        try:
            guard()
            explanation = translator.explain_text(
                text,
                lang if is_supported(lang) else "",
                explain_in if is_supported(explain_in) else (get_ui_lang() or "English"),
            )
        except TranslationError as e:
            return fail(e.key)
        track("explain")
        return jsonify(explanation=explanation)

    # ---- PWA（ホーム画面に追加）・オフライン ----
    @app.route("/favicon.ico")
    def favicon():
        """ブラウザが自動で取りに来る favicon（アイコン画像を返す）"""
        resp = send_from_directory(app.static_folder, "icon-192.png", mimetype="image/png")
        resp.headers["Cache-Control"] = "public, max-age=86400"
        return resp

    @app.route("/manifest.webmanifest")
    def manifest():
        data = {
            "id": "/", "name": "TOOKIE - AI Universal Translator", "short_name": "TOOKIE",
            "description": "AI translator for text, images, voice and chat",
            "start_url": "/", "scope": "/", "display": "standalone", "orientation": "portrait",
            "background_color": "#020617", "theme_color": "#0f172a",
            "icons": [
                {"src": "/static/icon-192.png", "sizes": "192x192", "type": "image/png", "purpose": "any"},
                {"src": "/static/icon-512.png", "sizes": "512x512", "type": "image/png", "purpose": "any"},
                {"src": "/static/icon-maskable-512.png", "sizes": "512x512", "type": "image/png", "purpose": "maskable"},
            ],
        }
        return Response(json.dumps(data, ensure_ascii=False), mimetype="application/manifest+json")

    @app.route("/sw.js")
    def service_worker():
        version = app.config.get("ASSET_V", "dev")
        precache = []
        static_dir = app.static_folder
        for base, _dirs, files in sorted(os.walk(static_dir)):
            for name in sorted(files):
                rel = os.path.relpath(os.path.join(base, name), static_dir).replace(os.sep, "/")
                if rel.startswith(("icon-", "apple-touch")):
                    continue   # アイコンはホーム画面登録時にブラウザが取得する
                if rel.startswith("phrasebook/"):
                    precache.append(url_for("static", filename=rel))
                else:
                    precache.append(url_for("static", filename=rel, v=version))
        body = render_template(
            "sw.js", version=version, precache=precache, cdn=CDN_PRECACHE,
            cdn_hosts=["cdn.tailwindcss.com", "cdnjs.cloudflare.com"],
        )
        resp = Response(body, mimetype="application/javascript")
        resp.headers["Cache-Control"] = "no-cache"
        resp.headers["Service-Worker-Allowed"] = "/"
        return resp

    @app.route("/offline")
    def offline():
        """通信できないとき Service Worker が出す画面。履歴・用語集・フレーズ集は端末内のデータで動く"""
        _src, target = get_langs()
        ui_lang = get_ui_lang() or "English"
        resp = make_response(render_template(
            "offline.html", offline_page=True, ui=get_ui(), ui_lang=ui_lang, ui_code=get_lang_code(ui_lang), ui_rtl=is_rtl(ui_lang),
            target_lang=target, phrase_langs=available_languages(),
            lang_list=[{"name": l["name"], "code": l["code"], "native": l["native"]} for l in LANGUAGES],
        ))
        resp.headers["Cache-Control"] = "no-cache"
        return resp

    @app.route("/api/clear-session", methods=["POST"])
    def api_clear_session():
        """「全データ削除」用。サーバー側に残る設定（Cookie）を消す"""
        session.clear()
        return jsonify(ok=True)

    @app.route("/privacy")
    def privacy():
        return render_template("privacy.html", ui=get_ui(), ui_code=get_lang_code(get_ui_lang() or "English"),
                               ui_rtl=is_rtl(get_ui_lang() or "English"))

    @app.route("/api/stats")
    def api_stats():
        """ADMIN_TOKEN を設定したときだけ有効。?token=... または X-Admin-Token ヘッダ"""
        token = os.environ.get("ADMIN_TOKEN")
        given = request.headers.get("X-Admin-Token") or request.args.get("token")
        if not token or given != token:
            abort(404)
        return jsonify(stats.snapshot())

    @app.route("/healthz")
    def healthz():
        return "ok"