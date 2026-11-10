"""画面の文言（UIラベル）の多言語化。

- 日本語・英語は languages.UI_LABELS に手書きで用意
- それ以外の言語は ui_labels/<言語コード>.json から読む
- ファイルが無ければ、表示言語の選択時に Gemini で自動翻訳して保存（失敗したら英語で表示）
"""
import json
import os
import threading
import time

import translator
from languages import FIXED_LABELS, LANGUAGES, UI_LABELS, get_lang_code

LABEL_DIR = os.environ.get("UI_LABELS_DIR") or os.path.join(os.path.dirname(os.path.abspath(__file__)), "ui_labels")
_lock = threading.Lock()
_mem = {}
_failed_at = {}
RETRY_AFTER = 300  # 生成に失敗した言語は5分間リトライしない（API呼び出しの乱発防止）


def _path(lang):
    return os.path.join(LABEL_DIR, get_lang_code(lang).lower() + ".json")


def _load_cached(lang):
    with _lock:
        if lang in _mem:
            return _mem[lang]
    try:
        with open(_path(lang), encoding="utf-8") as f:
            data = json.load(f)
        data = {k: v for k, v in data.items() if k in UI_LABELS["English"] and isinstance(v, str) and v.strip()}
    except (OSError, ValueError):
        return None
    with _lock:
        _mem[lang] = data
    return data


def get_ui_labels(lang):
    """表示言語のラベル。足りないキーは English で補い、From/To は常に固定"""
    labels = dict(UI_LABELS["English"])
    if lang in UI_LABELS:
        labels.update(UI_LABELS[lang])
    else:
        cached = _load_cached(lang)
        if cached:
            labels.update(cached)
    labels.update(FIXED_LABELS)
    return labels


def has_labels(lang):
    return lang in UI_LABELS or _load_cached(lang) is not None


def ensure_ui_labels(lang):
    """未生成なら Gemini で翻訳して保存する。成功すれば True（失敗しても例外は出さない）"""
    if has_labels(lang):
        return True
    if time.time() - _failed_at.get(lang, 0) < RETRY_AFTER:
        return False
    _failed_at[lang] = time.time()
    source = {k: v for k, v in UI_LABELS["English"].items() if k not in FIXED_LABELS}
    try:
        translated = translator.translate_labels(source, lang)
    except Exception as e:
        print(f"[ui_i18n] could not generate labels for {lang}: {e}", flush=True)
        return False
    if len(translated) < len(source) * 0.8:  # 欠落が多い結果は採用しない
        print(f"[ui_i18n] incomplete labels for {lang}: {len(translated)}/{len(source)}", flush=True)
        return False
    _failed_at.pop(lang, None)
    with _lock:
        _mem[lang] = translated
    try:
        os.makedirs(LABEL_DIR, exist_ok=True)
        tmp = _path(lang) + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(translated, f, ensure_ascii=False, indent=1)
        os.replace(tmp, _path(lang))
    except OSError as e:
        print(f"[ui_i18n] could not save labels for {lang}: {e}", flush=True)
    return True


def all_languages():
    return [l["name"] for l in LANGUAGES]
