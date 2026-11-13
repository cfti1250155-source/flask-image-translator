# AI Universal Translator

Flask製の翻訳アプリ（テキスト／画像／音声／カメラ／チャット）。翻訳は Gemini を使います。

## 環境変数（Render の Environment に設定）
| 名前 | 内容 |
|---|---|
| `GEMINI_API_KEY` | 必須。Gemini の API キー |
| `SECRET_KEY` | 必須（render.yaml なら自動生成）。未設定だと再起動のたびに表示言語の設定が消えます |
| `GEMINI_MODEL` | 任意。既定は `gemini-3.8-flash` |
| `GEMINI_TIMEOUT` / `GEMINI_ATTEMPTS` | 任意。1回の待ち秒数（既定40）／一時的な失敗時の試行回数（既定2） |
| `RATE_PER_MIN` / `DAILY_LIMIT_PER_IP` / `SITE_DAILY_LIMIT` | 任意。1分・IP別1日・サイト全体1日の上限（既定 20 / 300 / 3000） |
| `ADMIN_TOKEN` | 任意。設定すると `/api/stats?token=...` で日別の利用件数・エラー種別を確認できます |
| `KEEP_ALIVE_URL` | 任意。`https://自分のURL/healthz` を入れると10分ごとに自分を呼んでスリープを防ぎます（外部の監視サービスで /healthz を5分おきに呼ぶ方が確実） |

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

## データの保存とバックアップ
履歴・お気に入り・用語集・チャットは、各自のブラウザ（localStorage）にだけ保存されます。履歴タブ →「データ」で次の操作ができます。
- バックアップの書き出し（JSON。iPhoneは共有シートから「ファイルに保存」）／読み込み（今のデータに追加。重複はまとめます）
- 端末のデータと設定をすべて削除
- ブラウザに保存データの永続化を依頼（Safariが長期間使われないサイトのデータを消すのを防ぐ。許可は端末次第）

## ホーム画面に追加（PWA）とオフライン
- iPhone: Safari で開き、共有ボタン →「ホーム画面に追加」。アプリのように全画面で起動します（履歴タブ →「データ」にも案内あり）。
- 通信できないときは、自動で「オフライン画面」（`/offline`）が開きます。履歴・お気に入り・用語集・フレーズ集・バックアップの書き出しが使えます。**翻訳そのものにはインターネットが必要です。**
- 画面の部品（JS/CSS/アイコン/フレーズ集）は Service Worker（`/sw.js`）が端末に保存します。デプロイして内容が変わると版番号が変わり、古い保存は自動で消えます。
- Tailwind・FontAwesome は外部CDNなので、**初回にオンラインで一度開いておく**と、以後オフラインでも見た目が崩れません。
- Service Worker は https（または localhost）でだけ動きます。

## フレーズ集（オフライン）
- 6カテゴリ×6文（あいさつ・食事・移動・買い物・宿泊・緊急）。手書きで17言語（日・英・中(簡/繁)・韓・西・仏・独・伊・葡・露・アラビア・ヒンディー・トルコ・インドネシア・タイ・ベトナム）。
- データは `tools/phrasebook_data.py`。直したら `python tools/build_phrasebook.py` で `static/phrasebook/*.json` に書き出します。
- 他の言語は `python tools/generate_phrasebook.py`（Gemini）で作れます（機械翻訳なので、できればネイティブの確認を）。
- 手書き分も、ネイティブの方に確認してもらうと安心です。

## テスト
```bash
pip install pytest playwright   # e2e を動かすときだけ playwright
python -m pytest tests -q       # サーバー側（Geminiはダミー）
python tests/e2e.py             # ブラウザ動作（Chromium）
python tests/e2e_backup.py      # バックアップ機能のブラウザ動作
python tests/e2e_pwa.py         # PWA・オフライン・フレーズ集のブラウザ動作
```
