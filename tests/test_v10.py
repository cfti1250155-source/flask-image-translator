"""V10: 文言・favicon・設定へのデータ統合"""
import re

from conftest import start


def test_image_tab_wording_mentions_pdf(env):
    app, *_ = env
    c = app.test_client(); start(c, "Japanese")
    html = c.get("/").get_data(as_text=True)
    assert "画像・PDFを翻訳する" in html and "画像またはPDFを選択" in html
    assert "画像を翻訳する" not in html


def test_favicon(env):
    app, *_ = env
    c = app.test_client()
    r = c.get("/favicon.ico")
    assert r.status_code == 200 and r.mimetype == "image/png" and r.data.startswith(b"\x89PNG")
    start(c)
    assert 'rel="icon"' in c.get("/").get_data(as_text=True)
    assert 'rel="icon"' in c.get("/start").get_data(as_text=True)


def test_data_lives_inside_settings_on_main(env):
    app, *_ = env
    c = app.test_client(); start(c, "Japanese")
    html = c.get("/").get_data(as_text=True)
    assert 'id="hf-data"' not in html and 'id="hf-settings"' not in html     # メインでは歯車から開く
    for pill in ("hf-all", "hf-fav", "hf-gl", "hf-phrases", "hf-study"):
        assert f'id="{pill}"' in html, pill
    s = html.index('id="settings-section"')
    e = html.index('id="glossary-section"')
    block = html[s:e]
    for needle in ('id="data-section"', "exportBackup()", "importBackup(this)", "deleteAllData()", 'id="set-pron"', 'data-setting="theme"'):
        assert needle in block, needle
    # データ欄は設定の中で常に表示（hidden ではない）
    assert not re.search(r'id="data-section" class="[^"]*hidden', html)


def test_offline_page_keeps_a_settings_pill(env):
    app, *_ = env
    c = app.test_client()
    off = c.get("/offline").get_data(as_text=True)
    assert 'id="hf-settings"' in off and 'id="data-section"' in off and 'id="hf-data"' not in off


def test_vocab_counts_in_backup_labels():
    import languages
    for lang in ("Japanese", "English"):
        L = languages.UI_LABELS[lang]
        for k in ("data_counts_v", "import_confirm_v", "import_done_v"):
            assert "{v}" in L[k], (lang, k)
        assert L["btn_file_translate"] and L["file_input_label"]
        assert L["set_group_translate"] and L["set_group_display"]
