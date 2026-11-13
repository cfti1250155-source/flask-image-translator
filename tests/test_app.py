import json
import os
import shutil

import pytest

from conftest import start
import limits
from translator import TranslationError, classify_exception


def test_healthz_and_redirect(env):
    app, *_ = env
    c = app.test_client()
    assert c.get("/healthz").data == b"ok"
    assert c.get("/").status_code == 302


def test_display_language_sets_target_and_avoids_same_from_to(env):
    """スタート画面で選んだ言語が To になり、From と同じ言語にはならない（From/To の仕様は利用者が確定したもの）"""
    app, *_ = env
    c = app.test_client()
    c.get("/")
    start(c, "Japanese")
    with c.session_transaction() as s:
        assert s["ui_lang"] == "Japanese" and s["target_lang"] == "Japanese"
        assert s.get("source_lang", "Auto") == "Auto"
    with c.session_transaction() as s:
        s["source_lang"] = "French"
    start(c, "French")      # From と同じ言語を選んだら From を English に退避
    with c.session_transaction() as s:
        assert s["target_lang"] == "French" and s["source_lang"] == "English"
    with c.session_transaction() as s:
        s["source_lang"] = "English"
    start(c, "English")
    with c.session_transaction() as s:
        assert s["target_lang"] == "English" and s["source_lang"] == "Japanese"
    assert "TOOKIE" in c.get("/").get_data(as_text=True)


def test_invalid_display_language(env):
    app, *_ = env
    r = app.test_client().post("/set-display-language", data={"ui_lang": "Klingon"})
    assert r.status_code == 302 and "/start" in r.location


def test_labels_generated_for_new_language_and_only_missing(env, tmp_path):
    app, translator, calls, mp = env
    import ui_i18n
    from languages import UI_LABELS, FIXED_LABELS
    mp.setattr(ui_i18n, "LABEL_DIR", str(tmp_path))
    full = {k: "x" for k in UI_LABELS["English"] if k not in FIXED_LABELS}
    seen = []

    def fake_labels(labels, lang):
        seen.append(set(labels)); return {k: "T" + k for k in labels}
    mp.setattr(translator, "translate_labels", fake_labels)
    c = app.test_client()
    start(c, "French")
    assert seen and len(seen[0]) == len(full)
    assert (tmp_path / "fr-fr.json").exists()
    # 新しいキーが増えた想定: 1キー欠けたファイルは差分だけ翻訳される
    p = tmp_path / "fr-fr.json"
    d = json.loads(p.read_text(encoding="utf-8")); d.pop("err_daily")
    p.write_text(json.dumps(d), encoding="utf-8")
    ui_i18n._mem.clear(); seen.clear()
    assert not ui_i18n.has_labels("French")
    ui_i18n.ensure_ui_labels("French")
    assert seen == [{"err_daily"}]
    assert ui_i18n.has_labels("French")


def post_text(c, text="こんにちは"):
    return c.post("/", data={"mode": "text", "direct_text": text, "glossary": "[]"})


def test_text_translation_ok_and_stats(env):
    app, *_ = env
    c = app.test_client(); start(c)
    r = post_text(c)
    assert r.status_code == 200 and "Hello" in r.get_data(as_text=True)
    assert limits.stats.snapshot()[limits._today()]["text:ok"] == 1


def test_empty_and_too_long(env):
    app, _, calls, _ = env
    c = app.test_client(); start(c)
    assert "入力" in post_text(c, "  ").get_data(as_text=True)
    assert "長すぎ" in post_text(c, "a" * 5001).get_data(as_text=True)
    assert not calls


@pytest.mark.parametrize("exc,key", [
    (type("ReadTimeout", (Exception,), {})("x"), "err_timeout"),
    (type("APIError", (Exception,), {"code": 429})("RESOURCE_EXHAUSTED"), "err_quota"),
    (type("APIError", (Exception,), {"code": 503})("UNAVAILABLE"), "err_overloaded"),
    (type("APIError", (Exception,), {"code": 400})("API key not valid"), "err_api_key"),
    (type("ClientError", (Exception,), {"code": 403})("denied"), "err_api_key"),
    (type("ConnectError", (Exception,), {})("boom"), "err_connection"),
    (ValueError("???"), "err_failed"),
])
def test_classify(exc, key):
    assert classify_exception(exc) == key


def test_retry_transient_then_success(env):
    app, translator, calls, mp = env
    n = {"i": 0}

    def flaky(parts, system=None):
        n["i"] += 1
        if n["i"] == 1:
            raise type("APIError", (Exception,), {"code": 503})("UNAVAILABLE")
        return '{"detected_language":"English","source_text":"a","translation":"b"}'
    mp.setattr(translator, "_generate", flaky)
    c = app.test_client(); start(c)
    assert "b" in post_text(c, "a").get_data(as_text=True)
    assert n["i"] == 2


def test_no_retry_on_quota_and_error_message(env):
    app, translator, calls, mp = env
    n = {"i": 0}

    def quota(parts, system=None):
        n["i"] += 1
        raise type("APIError", (Exception,), {"code": 429})("RESOURCE_EXHAUSTED")
    mp.setattr(translator, "_generate", quota)
    c = app.test_client(); start(c)
    assert "集中" in post_text(c, "a").get_data(as_text=True)
    assert n["i"] == 1
    assert limits.stats.snapshot()[limits._today()]["text:err_quota"] == 1


def test_timeout_after_retries(env):
    app, translator, calls, mp = env
    n = {"i": 0}

    def slow(parts, system=None):
        n["i"] += 1
        raise type("ReadTimeout", (Exception,), {})("timed out")
    mp.setattr(translator, "_generate", slow)
    c = app.test_client(); start(c)
    assert "時間がかかり" in post_text(c, "a").get_data(as_text=True)
    assert n["i"] == translator.ATTEMPTS


def test_blocked(env):
    app, translator, calls, mp = env
    mp.setattr(translator, "_generate", lambda p, system=None: (_ for _ in ()).throw(TranslationError("err_blocked")))
    c = app.test_client(); start(c)
    assert "安全" in post_text(c).get_data(as_text=True)


def test_api_error_statuses(env):
    app, translator, calls, mp = env
    c = app.test_client(); start(c)
    body = {"text": "hi", "source": "English", "target": "Japanese"}
    for key, status in [("err_timeout", 504), ("err_quota", 503), ("err_blocked", 422), ("err_api_key", 503), ("err_connection", 502)]:
        mp.setattr(translator, "translate_text", lambda *a, _k=key, **k: (_ for _ in ()).throw(TranslationError(_k)))
        r = c.post("/api/translate-text", json=body)
        assert r.status_code == status and r.get_json()["key"] == key
    assert c.post("/api/translate-text", json={"text": "", "source": "English", "target": "Japanese"}).status_code == 400


def test_rate_limit_per_minute(env):
    app, *_ = env
    c = app.test_client(); start(c)
    codes = []
    for _ in range(22):
        r = c.post("/api/translate-text", json={"text": "hi", "source": "English", "target": "Japanese"})
        codes.append(r.status_code)
    assert codes[:20] == [200] * 20 and codes[20] == 429
    assert 429 in codes
    assert r.get_json()["key"] == "err_rate"


def test_daily_limits(env):
    app, _, _, mp = env
    mp.setenv("DAILY_LIMIT_PER_IP", "3")
    c = app.test_client(); start(c)
    body = {"text": "hi", "source": "English", "target": "Japanese"}
    res = [c.post("/api/translate-text", json=body) for _ in range(5)]
    assert [r.status_code for r in res] == [200, 200, 200, 429, 429]
    assert res[-1].status_code == 429 and res[-1].get_json()["key"] == "err_daily"
    limits.limiter.reset()
    mp.setenv("DAILY_LIMIT_PER_IP", "300"); mp.setenv("SITE_DAILY_LIMIT", "2")
    r = [c.post("/api/translate-text", json=body).get_json().get("key") for _ in range(3)]
    assert r[-1] == "err_daily"


def test_image_and_bad_image(env):
    app, translator, calls, mp = env
    mp.setattr(translator, "_generate", lambda p, system=None: '{"detected_language":"English","source_text":"STOP","translation":"止まれ"}')
    c = app.test_client(); start(c)
    import io
    r = c.post("/", data={"mode": "image", "image": (io.BytesIO(b"x"), "a.png", "image/png")}, content_type="multipart/form-data")
    assert "止まれ" in r.get_data(as_text=True)
    r = c.post("/", data={"mode": "image", "image": (io.BytesIO(b"x"), "a.txt", "text/plain")}, content_type="multipart/form-data")
    assert "画像" in r.get_data(as_text=True)


def test_explain_and_stats_endpoint(env):
    app, translator, calls, mp = env
    mp.setattr(translator, "_generate", lambda p, system=None: '{"explanation":"slang"}')
    c = app.test_client(); start(c)
    assert c.post("/api/explain", json={"text": "lol", "lang": "English"}).get_json()["explanation"] == "slang"
    assert c.get("/api/stats").status_code == 404
    mp.setenv("ADMIN_TOKEN", "tok")
    assert c.get("/api/stats?token=bad").status_code == 404
    assert c.get("/api/stats", headers={"X-Admin-Token": "tok"}).get_json()[limits._today()]["explain:ok"] == 1


def test_clear_session(env):
    app, *_ = env
    c = app.test_client(); start(c)
    assert c.post("/api/clear-session").get_json() == {"ok": True}
    assert c.get("/").status_code == 302       # 設定が消えたのでスタート画面へ
    assert c.get("/api/clear-session").status_code == 405


def test_data_tab_markup(env):
    app, *_ = env
    c = app.test_client(); start(c)
    html = c.get("/").get_data(as_text=True)
    for needle in ["id=\"data-section\"", "exportBackup()", "importBackup(this)", "deleteAllData()", "js/backup.js?v="]:
        assert needle in html, needle


def test_privacy_and_assets(env):
    app, *_ = env
    c = app.test_client(); start(c)
    assert "Gemini" in c.get("/privacy").get_data(as_text=True)
    html = c.get("/").get_data(as_text=True)
    assert "js/app.js?v=" in html and "function switchTab" in html
    assert c.get("/static/icon-192.png").status_code == 200
    assert 'required' in html.split('name="direct_text"')[1].split(">")[0]
    assert "Tookie icon" not in html


def test_labels_parity_and_files():
    from languages import UI_LABELS
    assert set(UI_LABELS["Japanese"]) == set(UI_LABELS["English"])
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    assert not os.path.exists(os.path.join(root, "static/js/script.js"))
    raw = open(os.path.join(root, "requirements.txt"), "rb").read()
    assert not raw.startswith(b"\xff\xfe") and b"gunicorn" in raw


def teardown_module(_m):
    from conftest import ROOT
    shutil.rmtree(os.path.join(ROOT, "tests", "_labels"), ignore_errors=True)


# ---------------- ステップ3: PWA・オフライン・フレーズ集 ----------------
def test_manifest(env):
    app, *_ = env
    r = app.test_client().get("/manifest.webmanifest")
    assert r.status_code == 200 and r.mimetype == "application/manifest+json"
    m = r.get_json()
    assert m["display"] == "standalone" and m["start_url"] == "/" and m["short_name"] == "TOOKIE"
    for icon in m["icons"]:
        assert app.test_client().get(icon["src"]).status_code == 200
    assert {i["purpose"] for i in m["icons"]} == {"any", "maskable"}


def test_service_worker(env):
    app, *_ = env
    r = app.test_client().get("/sw.js")
    assert r.status_code == 200 and "javascript" in r.mimetype
    assert r.headers["Service-Worker-Allowed"] == "/" and "no-cache" in r.headers["Cache-Control"]
    js = r.get_data(as_text=True)
    from app import ASSET_V
    assert f'"{ASSET_V}"' in js
    for needle in ["/static/js/app.js?v=" + ASSET_V, "/static/js/phrasebook.js?v=" + ASSET_V,
                   "/static/phrasebook/ja-jp.json", "/static/phrasebook/index.json", "cdn.tailwindcss.com"]:
        assert needle in js, needle
    assert "/static/icon-512.png" not in js            # 大きいアイコンは事前保存しない
    assert "/api/" not in js.split("const PRECACHE")[1].split("const CDN_PRECACHE")[0]


def test_offline_page_needs_no_session(env):
    app, *_ = env
    c = app.test_client()                               # スタート画面を通していない（Cookieなし）
    r = c.get("/offline")
    assert r.status_code == 200
    html = r.get_data(as_text=True)
    assert "You are offline" in html and "IS_OFFLINE_PAGE" in html and 'id="phrase-section"' in html
    start(c, "Japanese")
    assert "オフラインです" in c.get("/offline").get_data(as_text=True)


def test_main_page_has_pwa_hooks(env):
    app, *_ = env
    c = app.test_client(); start(c)
    html = c.get("/").get_data(as_text=True)
    for needle in ['rel="manifest"', "apple-touch-icon.png", 'id="offline-banner"', 'id="hf-phrases"',
                   'id="install-box"', "js/pwa.js?v=", "js/phrasebook.js?v=", "js/history.js?v=", "PHRASE_LANGS"]:
        assert needle in html, needle


def test_phrasebook_data_is_complete():
    import json
    from phrasebook import DIR, available_languages
    from languages import LANGUAGES
    index = json.load(open(os.path.join(DIR, "index.json"), encoding="utf-8"))
    ids = [p["id"] for c in index for p in c["phrases"]]
    assert len(ids) == len(set(ids)) == 36
    langs = available_languages()
    assert len(langs) >= 15 and "Japanese" in langs and "English" in langs
    for l in LANGUAGES:
        if l["name"] not in langs:
            continue
        d = json.load(open(os.path.join(DIR, l["code"].lower() + ".json"), encoding="utf-8"))
        assert set(d) == set(ids), l["name"]
        assert all(isinstance(v, str) and v.strip() for v in d.values()), l["name"]
        assert len(set(d.values())) >= 34, l["name"]    # ほぼ全文が別々の文（コピペ・空欄の検知）


def test_phrasebook_build_script_matches_files(tmp_path):
    import importlib, json, sys
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tools"))
    data = importlib.import_module("phrasebook_data")
    from phrasebook import DIR
    for code, d in data.T.items():
        on_disk = json.load(open(os.path.join(DIR, code.lower() + ".json"), encoding="utf-8"))
        assert on_disk == d, code


def test_ensure_async_fills_missing_labels(env, tmp_path):
    import time, ui_i18n
    app, translator, calls, mp = env
    mp.setattr(ui_i18n, "LABEL_DIR", str(tmp_path))
    mp.setattr(translator, "translate_labels", lambda labels, lang: {k: "T" for k in labels})
    ui_i18n.ensure_async("Swahili")
    for _ in range(50):
        if ui_i18n.has_labels("Swahili"):
            break
        time.sleep(0.05)
    assert ui_i18n.has_labels("Swahili")


def test_start_screen_mode_selection(env):
    app, *_ = env
    c = app.test_client()
    html = c.get("/start").get_data(as_text=True)
    assert 'value="offline"' in html and "Coming soon" not in html and "disabled" not in html.split('value="offline"')[1].split(">")[0]
    r = c.post("/set-display-language", data={"ui_lang": "Japanese", "network_mode": "offline"})
    assert r.status_code == 302 and r.location.endswith("/offline")
    r = c.post("/set-display-language", data={"ui_lang": "Japanese", "network_mode": "online"})
    assert r.status_code == 302 and r.location.endswith("/")
    with c.session_transaction() as s:
        assert s["ui_lang"] == "Japanese" and s["target_lang"] == "Japanese"


def test_service_worker_follows_selected_mode(env):
    app, *_ = env
    js = app.test_client().get("/sw.js").get_data(as_text=True)
    assert "tookie-mode" in js and "async function netMode" in js
    nav = js.split("async function navigate")[1].split("async function cacheFirst")[0]
    assert "!== 'offline') return fetch(req)" in nav      # オンラインモードでは差し替えない
