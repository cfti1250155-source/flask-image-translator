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


def test_display_language_resets_source_and_target(env):
    """日本語を選んだら From=自動判定 / To=English（両方 English になるバグの再発防止）"""
    app, *_ = env
    c = app.test_client()
    c.get("/")
    with c.session_transaction() as s:
        s["source_lang"] = "English"; s["target_lang"] = "English"   # 壊れた状態から
    start(c, "Japanese")
    with c.session_transaction() as s:
        assert s["ui_lang"] == "Japanese"
        assert s["source_lang"] == "Auto" and s["target_lang"] == "English"
    start(c, "English")
    with c.session_transaction() as s:
        assert s["target_lang"] == "Japanese"
    html = c.get("/").get_data(as_text=True)
    assert "TOOKIE" in html


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


def test_privacy_and_assets(env):
    app, *_ = env
    c = app.test_client(); start(c)
    assert "Gemini" in c.get("/privacy").get_data(as_text=True)
    html = c.get("/").get_data(as_text=True)
    assert "js/app.js?v=" in html and "function switchTab" in html
    assert c.get("/static/tookie-icon.png").status_code == 200
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
