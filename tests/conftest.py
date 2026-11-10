import os
import sys
import types

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.environ.setdefault("SECRET_KEY", "test")
os.environ["UI_LABELS_DIR"] = os.path.join(ROOT, "tests", "_labels")

# google-genai が無い環境でもテストできるよう、最小のダミーを用意（本物があればそれを使う）
try:
    import google.genai  # noqa: F401
except ImportError:
    g = types.ModuleType("google"); gg = types.ModuleType("google.genai")
    t = types.ModuleType("google.genai.types")
    t.Part = type("Part", (), {"from_bytes": staticmethod(lambda data, mime_type: ("img", mime_type))})
    gg.types = t; g.genai = gg
    sys.modules.update({"google": g, "google.genai": gg, "google.genai.types": t})

import pytest  # noqa: E402


@pytest.fixture()
def env(monkeypatch):
    import translator
    from limits import limiter, stats
    import ui_i18n
    from app import app
    app.config["TESTING"] = True
    limiter.reset(); stats.reset(); ui_i18n._mem.clear(); ui_i18n._failed_at.clear()
    monkeypatch.setattr(translator, "RETRY_WAIT", 0)
    calls = []

    def fake(parts, system=None):
        calls.append((parts, system))
        return '{"detected_language":"Japanese","source_text":"こんにちは","translation":"Hello"}'
    monkeypatch.setattr(translator, "_generate", fake)
    return app, translator, calls, monkeypatch


def start(client, lang="Japanese"):
    return client.post("/set-display-language", data={"ui_lang": lang})
