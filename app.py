from datetime import timedelta
import os
import secrets

from flask import Flask

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

# ルートの登録
register_routes(app)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=bool(os.environ.get("FLASK_DEBUG")))