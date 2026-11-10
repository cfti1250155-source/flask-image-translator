import json
from flask import jsonify, redirect, render_template, request, session, url_for

from helpers import (
    MAX_TEXT_LEN, VALID_MODES, clean_context, clean_glossary,
    get_langs, get_ui, get_ui_lang, rate_ok, read_camera_data,
    read_upload, remember_recent, render_main,
)
from languages import (
    AUTO, LANGUAGES, get_lang_code, is_rtl, is_supported,
    normalize_language_name,
)
import translator
from translator import TranslationError
from ui_i18n import ensure_ui_labels, has_labels


def register_routes(app):
    @app.route("/", methods=["GET", "POST"])
    def index():
        if request.method == "GET":
            if not get_ui_lang():
                return redirect(url_for("start"))
            return render_main()

        source_lang, target_lang = get_langs()
        mode = request.form.get("mode", "text")
        if mode not in VALID_MODES:
            mode = "text"
        ctx = {"active_mode": mode}

        try:
            if not rate_ok():
                raise TranslationError("err_rate")

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
                result = translator.translate_text(text, source_lang, target_lang, glossary=glossary)
            else:
                if mode == "image":
                    data, mime = read_upload()
                else:
                    data, mime = read_camera_data(request.form.get("camera_data"))
                result = translator.translate_image(data, mime, target_lang)

            detected = normalize_language_name(result["detected_language"])
            if detected:
                session["last_detected"] = detected
            show_detected = mode in ("image", "camera") or source_lang == AUTO
            ctx.update(
                translated_text=result["translation"] or result["source_text"],
                original_text=result["source_text"] if mode in ("image", "camera") else None,
                detected_lang=(detected or result["detected_language"] or None) if show_detected else None,
            )
            if ctx["translated_text"]:
                ctx["result_entry"] = {
                    "mode": mode,
                    "src": ctx.get("input_text") or result["source_text"],
                    "out": ctx["translated_text"],
                    "srcLang": detected or (source_lang if source_lang != AUTO else "") or result["detected_language"],
                    "tgt": target_lang,
                    "tcode": get_lang_code(target_lang),
                }
        except TranslationError as e:
            ctx["error"] = get_ui().get(e.key, e.key)

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
        
        session.permanent = True
        session["ui_lang"] = lang
        session["target_lang"] = lang
        
        if session.get("source_lang") == lang:
            session["source_lang"] = "English" if lang != "English" else "Japanese"

        remember_recent(lang)
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

        def fail(key, status):
            return jsonify(error=ui.get(key, key)), status

        if not text:
            return fail("err_empty", 400)
        if len(text) > MAX_TEXT_LEN:
            return fail("err_too_long", 400)
        if not is_supported(target) or not is_supported(source, allow_auto=True):
            return fail("err_failed", 400)
        if not rate_ok():
            return fail("err_rate", 429)
        try:
            result = translator.translate_text(
                text, source, target,
                context=clean_context(data.get("context")),
                glossary=clean_glossary(data.get("glossary")),
            )
        except TranslationError as e:
            return fail(e.key, 503 if e.key == "err_no_key" else 502)
        return jsonify(
            translation=result["translation"] or result["source_text"],
            detected=normalize_language_name(result["detected_language"]) or result["detected_language"],
        )

    @app.route("/api/explain", methods=["POST"])
    def api_explain():
        ui = get_ui()
        data = request.get_json(silent=True) or {}
        text = str(data.get("text") or "").strip()

        def fail(key, status):
            return jsonify(error=ui.get(key, key)), status

        if not text:
            return fail("err_empty", 400)
        if len(text) > 1000:
            return fail("err_too_long", 400)
        if not rate_ok():
            return fail("err_rate", 429)
        lang = data.get("lang")
        explain_in = data.get("explain_in")
        try:
            explanation = translator.explain_text(
                text,
                lang if is_supported(lang) else "",
                explain_in if is_supported(explain_in) else (get_ui_lang() or "English"),
            )
        except TranslationError as e:
            return fail(e.key, 503 if e.key == "err_no_key" else 502)
        return jsonify(explanation=explanation)

    @app.route("/healthz")
    def healthz():
        return "ok"