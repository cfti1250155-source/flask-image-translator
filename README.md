# AI Universal Translator

Flask製の翻訳アプリ（テキスト／画像／音声／カメラ／チャット）。翻訳は Gemini を使います。

## 環境変数（Render の Environment に設定）
| 名前 | 内容 |
|---|---|
| `GEMINI_API_KEY` | 必須。Gemini の API キー |
| `SECRET_KEY` | 必須（render.yaml なら自動生成）。未設定だと再起動のたびに表示言語の設定が消えます |
| `GEMINI_MODEL` | 任意。既定は `gemini-2.5-flash` |

## 画面の多言語化
- 日本語・英語は `languages.py` に手書き。それ以外は `ui_labels/<言語コード>.json` を読みます。
- ファイルが無い言語は、スタート画面で選んだ時に Gemini が一度だけ自動翻訳して保存します（失敗したら英語で表示）。
  Render の無料枠はディスクが消えるため、**事前生成してコミット**しておくのがおすすめです。

```bash
export GEMINI_API_KEY=...
pip install -r requirements.txt
python tools/generate_ui_labels.py          # 未生成の言語だけ作る（--force で全作り直し）
git add ui_labels && git commit -m "Add UI labels"
```
生成された JSON は母語話者に確認してもらい、直接編集して構いません。`From` / `To` は全言語で固定です。

## AI学習（スラング・省略語への対応）
モデルの再学習ではなく、翻訳のたびに次を Gemini に渡して精度を上げています（すべて端末内に保存）。
- 直近のチャットの流れ（文脈）
- 用語集（履歴タブ → 用語集）
- 訳を直した内容（修正例。直近3件を手本として送信）

## ローカル起動
```bash
pip install -r requirements.txt
GEMINI_API_KEY=... FLASK_DEBUG=1 python app.py
```
