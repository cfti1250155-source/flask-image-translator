from datetime import timedelta
import os
import secrets

from flask import Flask

import hashlib

from limits import start_keepalive
from routes import register_routes

app = Flask(__name__)

_secret = os.environ.get("SECRET_KEY")
if not _secret:
    _secret = secrets.token_hex(32)
    print("[warn] SECRET_KEY が未設定です。再起動でセッションが無効になります。", flush=True)

app.secret_key = _secret
app.config.update(
    MAX_CONTENT_LENGTH=10 * 1024 * 1024,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    PERMANENT_SESSION_LIFETIME=timedelta(days=365),
    SESSION_COOKIE_SECURE=not os.environ.get("FLASK_DEBUG"),
)



def _asset_version():
    """static の中身から作る版番号。JS/CSSを更新したとき古いキャッシュを使わせない"""
    h = hashlib.md5()
    root = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
    for base, _dirs, files in sorted(os.walk(root)):
        for name in sorted(files):
            with open(os.path.join(base, name), "rb") as f:
                h.update(f.read())
    return h.hexdigest()[:8]


ASSET_V = _asset_version()


@app.context_processor
def _inject_asset_version():
    return {"asset_v": ASSET_V}


app.config["ASSET_V"] = ASSET_V

# ルートの登録
register_routes(app)
start_keepalive()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=bool(os.environ.get("FLASK_DEBUG")))