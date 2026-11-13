"""V11: 結果カードの「…」メニュー・空港フレーズ・ゴミ箱・モデル切り替え・考える量・文言"""
import json
import os
import re

import pytest

from conftest import start

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def post_text(c, text="こんにちは"):
    return c.post("/", data={"mode": "text", "direct_text": text, "glossary": "[]"})


# ---------------- 結果カード ----------------

def test_result_card_has_speak_copy_and_more_menu(env):
    app, *_ = env
    c = app.test_client(); start(c, "Japanese")
    html = post_text(c).get_data(as_text=True)
    assert html.count('class="rc-actions"') == 1
    # 読み上げ・コピーは外に出ていて、残りの6つが「…」メニューの中にある
    menu = re.search(r'<div class="rc-menu hidden" role="menu">(.*?)\n                </div>\n            </div>', html, re.S).group(1)
    assert menu.count('role="menuitem"') == 6
    for fn in ("editResult", "showBigResult", "showAlternatives", "explainResult", "saveVocabCurrent", "toggleFavCurrent"):
        assert fn in menu, fn
    assert "speakResult" not in menu and "copyResult" not in menu
    outer = html.split('<div class="rc-menu hidden"')[0]
    assert "speakResult('resultText-text')" in outer and "copyResult('resultText-text'" in outer
    assert 'class="fav-btn' not in outer and "rc-item fav-btn" in menu     # お気に入りの★は menu 内で更新される
    head = html.split("border border-indigo-800/60 space-y-3")[1].split('class="rc-actions"')[0]
    assert "<button" not in head                                          # 旧: 上に8個並べたボタン列は無い
    assert ">その他<" not in html and 'aria-label="その他"' in html


def test_result_card_labels_in_english(env):
    app, *_ = env
    c = app.test_client(); start(c, "English")
    html = post_text(c, "a").get_data(as_text=True)
    assert 'aria-label="More"' in html and 'aria-label="Copy"' in html


def test_menu_script_and_styles_present():
    js = open(os.path.join(ROOT, "static/js/app.js"), encoding="utf-8").read()
    for fn in ("function toggleResultMenu", "function closeResultMenus", "Escape"):
        assert fn in js
    css = open(os.path.join(ROOT, "static/style.css"), encoding="utf-8").read()
    for sel in (".rc-btn", ".rc-menu", ".rc-item", ".undo-toast", "html[data-theme=light] .rc-menu"):
        assert sel in css, sel


# ---------------- 空港フレーズ ----------------

def test_airport_phrases():
    from phrasebook import DIR, available_languages
    from languages import LANGUAGES
    index = json.load(open(os.path.join(DIR, "index.json"), encoding="utf-8"))
    ap = [c for c in index if c["id"].startswith("ap_")]
    assert len(ap) == 5 and sum(len(c["phrases"]) for c in ap) == 45
    assert index[0]["id"] == "basic" and index[1]["id"] == "ap_checkin"      # 基本の次に空港
    ids = [p["id"] for c in index for p in c["phrases"]]
    # 人や場所の名前が入る穴埋め文はない（固定文だけ）
    assert not any("{" in p["ja"] or "{" in p["en"] for c in index for p in c["phrases"])
    ja = {p["id"]: p["ja"] for c in index for p in c["phrases"]}
    assert ja["ap_window"] == "窓側の席をお願いします" and ja["ap_aisle"] == "通路側の席をお願いします"
    assert ja["ap_restroom"] == "トイレに行きたいです"
    for l in LANGUAGES:
        if l["name"] not in available_languages():
            continue
        d = json.load(open(os.path.join(DIR, l["code"].lower() + ".json"), encoding="utf-8"))
        assert set(d) == set(ids), l["name"]
        assert len(set(d.values())) >= 78, l["name"]


def test_airport_phrasebook_served_and_precached(env):
    app, *_ = env
    c = app.test_client(); start(c)
    assert c.get("/static/phrasebook/en-us.json").get_json()["ap_window"] == "I'd like a window seat, please"
    sw = c.get("/sw.js").get_data(as_text=True)
    assert "/static/phrasebook/index.json" in sw


# ---------------- ゴミ箱 ----------------

def test_trash_ui_and_labels(env):
    app, *_ = env
    from languages import UI_LABELS
    c = app.test_client(); start(c, "Japanese")
    html = c.get("/").get_data(as_text=True)
    assert 'id="hf-trash"' in html and 'id="trash-section"' in html and 'id="trash-empty-btn"' in html
    keys = [k for k in UI_LABELS["English"] if k.startswith("trash_") or k == "filter_trash"]
    assert len(keys) >= 13
    for lang in UI_LABELS:
        for k in keys:
            assert k in UI_LABELS[lang], (lang, k)


def test_trash_code_paths():
    js = open(os.path.join(ROOT, "static/js/storage.js"), encoding="utf-8").read()
    for fn in ("function loadTrash", "function trashAdd", "function trashRestore", "function trashDelete", "function trashEmpty"):
        assert fn in js
    assert "TRASH_DAYS = 30" in js
    # 履歴・用語集・単語帳・チャットの削除はゴミ箱を通る
    for f, kind in (("history.js", "'history'"), ("history.js", "'glossary'"), ("study.js", "'vocab'"), ("chat.js", "'chat'")):
        assert "trashAdd(" + kind in open(os.path.join(ROOT, "static/js", f), encoding="utf-8").read(), (f, kind)
    # バックアップの書き出しにはゴミ箱を含めない
    bk = open(os.path.join(ROOT, "static/js/backup.js"), encoding="utf-8").read()
    assert "loadTrash" not in bk and "tl_trash" not in bk


# ---------------- モデル切り替え・考える量 ----------------

class _Types:
    """google.genai.types の代わり。ThinkingConfig に渡された引数を記録する"""
    class ThinkingConfig:
        def __init__(self, **kw):
            self.kw = kw


class _Err(Exception):
    def __init__(self, code, msg):
        super().__init__(msg)
        self.code = code


@pytest.mark.parametrize("model,level,expect", [
    ("gemini-2.5-flash", "low", {"thinking_budget": 0}),
    ("gemini-3.8-flash", "low", {"thinking_level": "low"}),
    ("gemini-4-hydrogen", "low", {"thinking_level": "low"}),
    ("gemini-4-hydrogen", "minimal", {"thinking_level": "minimal"}),
    ("gemini-4-hydrogen", "off", None),
    ("gemini-4-hydrogen", "", None),
    ("some-other-model", "low", None),
])
def test_thinking_config_by_model(env, model, level, expect):
    _, translator, _, mp = env
    mp.setattr(translator, "MODEL", model)
    mp.setattr(translator, "THINKING_LEVEL", level)
    mp.delenv("GEMINI_THINKING", raising=False)
    tc = translator._thinking_config(_Types)
    assert (tc.kw if tc else None) == expect


def test_thinking_config_can_be_disabled_and_never_raises(env):
    _, translator, _, mp = env
    mp.setattr(translator, "MODEL", "gemini-4-hydrogen")
    mp.setenv("GEMINI_THINKING", "1")
    assert translator._thinking_config(_Types) is None
    mp.delenv("GEMINI_THINKING")

    class Bad:
        @staticmethod
        def ThinkingConfig(**kw):
            raise ValueError("unsupported")
    assert translator._thinking_config(Bad) is None


def _run_call(translator, mp, errors, model="m1", fallback="m2"):
    """errors の順に例外を出し、尽きたら成功する偽の _generate。使われたモデルの一覧を返す"""
    used, queue = [], list(errors)

    def fake(parts, system=None):
        used.append(translator._model())
        if queue:
            raise queue.pop(0)
        return '{"translation":"ok"}'
    mp.setattr(translator, "_generate", fake)
    mp.setattr(translator, "MODEL", model)
    mp.setattr(translator, "FALLBACK_MODEL", fallback)
    mp.setattr(translator, "ATTEMPTS", 2)
    return used


def test_switches_to_fallback_model_when_overloaded(env):
    _, translator, _, mp = env
    used = _run_call(translator, mp, [_Err(503, "UNAVAILABLE high demand")])
    assert translator._call(["x"]) == '{"translation":"ok"}'
    assert used == ["m1", "m2"]
    assert translator._model() == "m1"            # 切り替えは今回のリクエストだけ


def test_switches_to_fallback_on_timeout_and_on_model_gone(env):
    _, translator, _, mp = env
    used = _run_call(translator, mp, [_Err(504, "DEADLINE_EXCEEDED")])
    translator._call(["x"])
    assert used == ["m1", "m2"]
    used = _run_call(translator, mp, [_Err(404, "NOT_FOUND model is no longer available")])
    translator._call(["x"])
    assert used == ["m1", "m2"]


def test_no_switch_for_quota_connection_or_without_fallback(env):
    _, translator, _, mp = env
    used = _run_call(translator, mp, [_Err(429, "RESOURCE_EXHAUSTED")])
    with pytest.raises(translator.TranslationError) as e:
        translator._call(["x"])
    assert e.value.key == "err_quota" and used == ["m1"]          # 上限は再試行しない
    used = _run_call(translator, mp, [ConnectionError("reset")])
    translator._call(["x"])
    assert used == ["m1", "m1"]                                    # 通信エラーは同じモデルで再試行
    used = _run_call(translator, mp, [_Err(503, "UNAVAILABLE")], fallback="")
    translator._call(["x"])
    assert used == ["m1", "m1"]
    used = _run_call(translator, mp, [_Err(503, "UNAVAILABLE")], fallback="m1")
    translator._call(["x"])
    assert used == ["m1", "m1"]


def test_all_models_failing_gives_the_friendly_error(env):
    _, translator, _, mp = env
    _run_call(translator, mp, [_Err(503, "UNAVAILABLE"), _Err(503, "UNAVAILABLE")])
    with pytest.raises(translator.TranslationError) as e:
        translator._call(["x"])
    assert e.value.key == "err_overloaded"


def test_default_model_is_current_and_fallback_differs():
    import translator
    assert translator.MODEL != translator.FALLBACK_MODEL
    assert translator.MODEL.startswith("gemini-") and translator.FALLBACK_MODEL.startswith("gemini-")


# ---------------- 文言 ----------------

def test_missing_api_key_message_is_friendly_and_logged(env, capsys):
    app, translator, _, mp = env
    from languages import UI_LABELS
    assert "GEMINI_API_KEY" not in UI_LABELS["Japanese"]["err_no_key"] and "GEMINI_API_KEY" not in UI_LABELS["English"]["err_no_key"]
    mp.delenv("GEMINI_API_KEY", raising=False)
    mp.setattr(translator, "_client", None)
    with pytest.raises(translator.TranslationError) as e:
        translator._get_client()
    assert e.value.key == "err_no_key"
    assert "GEMINI_API_KEY is not set" in capsys.readouterr().out


def test_privacy_mentions_google_free_tier_pdf_and_trash(env):
    app, *_ = env
    c = app.test_client(); start(c, "Japanese")
    html = c.get("/privacy").get_data(as_text=True)
    assert "無料枠" in html and "PDF" in html and "ゴミ箱" in html and "機密情報" in html
    assert html.count('<p class="text-sm text-slate-300 leading-relaxed">') == 6
    start(c, "English")
    en = c.get("/privacy").get_data(as_text=True)
    assert "free tier" in en and "PDFs" in en and "trash" in en


def test_clear_confirm_mentions_trash():
    from languages import UI_LABELS
    assert "ゴミ箱" in UI_LABELS["Japanese"]["confirm_clear"] and "trash" in UI_LABELS["English"]["confirm_clear"].lower()
    assert "ゴミ箱" in UI_LABELS["Japanese"]["data_delete_confirm"]


# ---------------- リポジトリの設定 ----------------

def test_gitattributes_forces_lf():
    s = open(os.path.join(ROOT, ".gitattributes"), encoding="utf-8").read()
    assert "eol=lf" in s and "*.png binary" in s


def test_readme_documents_new_settings():
    s = open(os.path.join(ROOT, "README.md"), encoding="utf-8").read()
    for k in ("GEMINI_FALLBACK_MODEL", "GEMINI_THINKING_LEVEL", "gemini-4-hydrogen", "ゴミ箱"):
        assert k in s, k
